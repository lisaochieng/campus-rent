from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Listing, ListingReport, ListingStatus
from app.services.cache import clear_fast_search_cache
from app.services.search_index import get_search_client, remove_listing_from_index

OPEN_REPORT_FLAG_THRESHOLD = 2


def count_open_reports(db: Session, listing: Listing) -> int:
    return db.scalar(
        select(func.count())
        .select_from(ListingReport)
        .where(
            ListingReport.listing_id == listing.id,
            ListingReport.status == "open",
        )
    )


def flag_listing_if_report_threshold_reached(
    *,
    db: Session,
    listing: Listing,
) -> bool:
    if listing.status != ListingStatus.ACTIVE:
        return False

    open_report_count = count_open_reports(db, listing)
    if open_report_count < OPEN_REPORT_FLAG_THRESHOLD:
        return False

    listing.status = ListingStatus.FLAGGED
    db.flush()
    remove_listing_from_index(get_search_client(), listing.id)
    clear_fast_search_cache()
    return True
