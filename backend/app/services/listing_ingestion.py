import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Listing, ListingSource, ListingStatus
from app.schemas.listing import ListingIngestItem
from app.services.cache import clear_fast_search_cache
from app.services.scam_detection import refresh_persisted_scam_signals
from app.services.score_persistence import refresh_listing_scores
from app.services.search_index import get_search_client, index_listing


WHITESPACE_RE = re.compile(r"\s+")


@dataclass
class IngestionResult:
    source_name: str
    received: int
    created: int = 0
    updated: int = 0
    skipped: int = 0
    indexed: int = 0
    cache_keys_cleared: int = 0
    listing_ids: list[UUID] = field(default_factory=list)
    skipped_reasons: list[str] = field(default_factory=list)


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = WHITESPACE_RE.sub(" ", value.strip())
    return cleaned or None


def clean_state(value: str) -> str:
    return clean_text(value).upper()


def clean_city(value: str) -> str:
    cleaned = clean_text(value)
    return cleaned.title()


def clean_ingested_listing(item: ListingIngestItem) -> dict:
    return {
        "source_listing_id": clean_text(item.source_listing_id),
        "source_url": clean_text(item.source_url),
        "title": clean_text(item.title),
        "description": clean_text(item.description),
        "address": clean_text(item.address),
        "city": clean_city(item.city),
        "state": clean_state(item.state),
        "postal_code": clean_text(item.postal_code),
        "latitude": item.latitude,
        "longitude": item.longitude,
        "monthly_rent": item.monthly_rent,
        "bedrooms": item.bedrooms,
        "bathrooms": item.bathrooms,
        "square_feet": item.square_feet,
        "status": ListingStatus.ACTIVE,
        "raw_payload": item.model_dump(mode="json"),
    }


def ingest_listing_batch(
    *,
    db: Session,
    source_name: str,
    items: list[ListingIngestItem],
) -> IngestionResult:
    source = db.scalar(select(ListingSource).where(ListingSource.name == source_name))
    if source is None:
        raise ValueError(f"Unknown listing source: {source_name}")

    result = IngestionResult(source_name=source.name, received=len(items))
    seen_source_urls: set[str] = set()

    for item in items:
        cleaned = clean_ingested_listing(item)
        source_url = cleaned["source_url"]
        if source_url in seen_source_urls:
            result.skipped += 1
            result.skipped_reasons.append(f"Duplicate source_url in request: {source_url}")
            continue
        seen_source_urls.add(source_url)

        listing = db.scalar(select(Listing).where(Listing.source_url == source_url))
        if listing is None and cleaned["source_listing_id"]:
            listing = db.scalar(
                select(Listing).where(
                    Listing.source_id == source.id,
                    Listing.source_listing_id == cleaned["source_listing_id"],
                )
            )

        if listing is None:
            listing = Listing(source_id=source.id, **cleaned)
            db.add(listing)
            result.created += 1
        else:
            for key, value in cleaned.items():
                setattr(listing, key, value)
            listing.source_id = source.id
            listing.last_seen_at = datetime.now(UTC)
            result.updated += 1

        db.flush()
        refresh_persisted_scam_signals(db, listing)
        refresh_listing_scores(db, listing.id)
        result.listing_ids.append(listing.id)

    db.commit()

    if result.listing_ids:
        client = get_search_client()
        indexed_listings = db.scalars(
            select(Listing)
            .options(selectinload(Listing.source), selectinload(Listing.scam_signals))
            .where(Listing.id.in_(result.listing_ids))
        ).all()
        for listing in indexed_listings:
            index_listing(client, listing)
            result.indexed += 1

        result.cache_keys_cleared = clear_fast_search_cache()

    return result
