from decimal import Decimal
from uuid import UUID

from opensearchpy import OpenSearch
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.db.models import Listing, ListingStatus

LISTINGS_INDEX = "campusrent-listings"


def get_search_client() -> OpenSearch:
    return OpenSearch(
        settings.opensearch_url,
        timeout=30,
        max_retries=3,
        retry_on_timeout=True,
    )


def ensure_listings_index(client: OpenSearch | None = None) -> None:
    client = client or get_search_client()
    if client.indices.exists(index=LISTINGS_INDEX):
        return

    client.indices.create(
        index=LISTINGS_INDEX,
        body={
            "settings": {
                "index": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                }
            },
            "mappings": {
                "properties": {
                    "listing_id": {"type": "keyword"},
                    "title": {"type": "text"},
                    "description": {"type": "text"},
                    "city": {"type": "keyword"},
                    "state": {"type": "keyword"},
                    "monthly_rent": {"type": "integer"},
                    "bedrooms": {"type": "float"},
                    "bathrooms": {"type": "float"},
                    "status": {"type": "keyword"},
                    "source_name": {"type": "keyword"},
                    "source_trust_level": {"type": "keyword"},
                    "scam_safety_score": {"type": "integer"},
                    "location": {"type": "geo_point"},
                }
            },
        },
    )


def _decimal_to_float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)


def listing_to_search_document(listing: Listing) -> dict:
    total_scam_penalty = sum(signal.severity for signal in listing.scam_signals)
    scam_safety_score = max(0, 100 - total_scam_penalty)
    document = {
        "listing_id": str(listing.id),
        "title": listing.title,
        "description": listing.description,
        "city": listing.city,
        "state": listing.state,
        "monthly_rent": listing.monthly_rent,
        "bedrooms": _decimal_to_float(listing.bedrooms),
        "bathrooms": _decimal_to_float(listing.bathrooms),
        "status": listing.status.value,
        "source_name": listing.source.name,
        "source_trust_level": listing.source.trust_level.value,
        "scam_safety_score": scam_safety_score,
    }

    if listing.latitude is not None and listing.longitude is not None:
        document["location"] = {
            "lat": float(listing.latitude),
            "lon": float(listing.longitude),
        }

    return document


def index_listing(client: OpenSearch, listing: Listing) -> None:
    client.index(
        index=LISTINGS_INDEX,
        id=str(listing.id),
        body=listing_to_search_document(listing),
        refresh=True,
    )


def remove_listing_from_index(client: OpenSearch, listing_id: UUID) -> None:
    ensure_listings_index(client)
    client.delete(
        index=LISTINGS_INDEX,
        id=str(listing_id),
        ignore=[404],
        refresh=True,
    )


def rebuild_listings_index(db: Session) -> int:
    client = get_search_client()
    if client.indices.exists(index=LISTINGS_INDEX):
        client.indices.delete(index=LISTINGS_INDEX)

    ensure_listings_index(client)

    listings = db.scalars(
        select(Listing)
        .options(selectinload(Listing.source), selectinload(Listing.scam_signals))
        .where(Listing.status == ListingStatus.ACTIVE)
    ).all()
    for listing in listings:
        index_listing(client, listing)

    return len(listings)


def search_listing_ids(
    *,
    query: str,
    city: str | None,
    state: str | None,
    max_rent: int | None,
    min_scam_safety: int | None,
    limit: int,
) -> list[UUID]:
    client = get_search_client()
    ensure_listings_index(client)

    filters = [{"term": {"status": ListingStatus.ACTIVE.value}}]
    if city:
        filters.append({"term": {"city": city}})
    if state:
        filters.append({"term": {"state": state}})
    if max_rent:
        filters.append({"range": {"monthly_rent": {"lte": max_rent}}})
    if min_scam_safety is not None:
        filters.append({"range": {"scam_safety_score": {"gte": min_scam_safety}}})

    response = client.search(
        index=LISTINGS_INDEX,
        body={
            "size": limit,
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^3", "description", "city"],
                                "fuzziness": "AUTO",
                            }
                        }
                    ],
                    "filter": filters,
                }
            },
            "sort": [
                {"_score": {"order": "desc"}},
                {"scam_safety_score": {"order": "desc"}},
                {"monthly_rent": {"order": "asc"}},
            ],
        },
    )

    return [UUID(hit["_source"]["listing_id"]) for hit in response["hits"]["hits"]]
