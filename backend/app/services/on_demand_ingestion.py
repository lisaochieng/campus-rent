from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Listing, ListingSource, ListingStatus, School, SourceTrustLevel
from app.services.listing_ingestion import ingest_listing_batch
from app.services.scraper_registry import get_scraper


def ensure_source_for_scraper(db: Session, scraper) -> None:
    source = db.scalar(select(ListingSource).where(ListingSource.name == scraper.source_name))
    if source is not None:
        return

    db.add(
        ListingSource(
            name=scraper.source_name,
            base_url=scraper.base_url,
            trust_level=SourceTrustLevel.MEDIUM,
            is_active=True,
            notes="On-demand real listing source.",
        )
    )
    db.commit()


def ingest_real_listings_for_school_if_needed(db: Session, school: School) -> None:
    if school.country.upper() != "US":
        return

    existing_count = db.scalar(
        select(func.count())
        .select_from(Listing)
        .where(
            Listing.status == ListingStatus.ACTIVE,
            Listing.city.ilike(school.city),
            Listing.state.ilike(school.state),
        )
    )
    if existing_count:
        return

    scraper = get_scraper("rentcast-rentals")
    if scraper is None or not scraper.is_configured():
        scraper = get_scraper("craigslist-rss-rentals")
    if scraper is None or not scraper.is_configured():
        return

    ensure_source_for_scraper(db, scraper)
    try:
        items = scraper.fetch(
            city=school.city,
            state=school.state,
            latitude=school.latitude,
            longitude=school.longitude,
            radius_miles=15,
            limit=50,
        )
    except RuntimeError:
        return

    ingest_listing_batch(db=db, source_name=scraper.source_name, items=items)
