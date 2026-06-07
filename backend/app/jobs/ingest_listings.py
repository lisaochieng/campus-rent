import argparse
import logging
from collections.abc import Sequence

from sqlalchemy import func, select

from app.db.models import Listing, ListingStatus, School
from app.db.session import SessionLocal
from app.services.external_school_search import find_or_fetch_school
from app.services.listing_ingestion import IngestionResult, ingest_listing_batch
from app.services.on_demand_ingestion import ensure_source_for_scraper
from app.services.scraper_registry import get_scraper, normalize_us_state


DEFAULT_SCHOOLS = (
    "New York University",
    "Princeton University",
    "The University of Texas at Austin",
    "University of California, Berkeley",
    "Boston University",
)
DEFAULT_SOURCES = ("rentcast-rentals", "trellistate-public-listings", "craigslist-rss-rentals")
LOGGER = logging.getLogger("campusrent.ingestion")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest real rental listings into the CampusRent database cache.",
    )
    parser.add_argument(
        "--school",
        action="append",
        dest="schools",
        help="School name to ingest around. Repeat this flag for multiple schools.",
    )
    parser.add_argument(
        "--source",
        action="append",
        dest="sources",
        choices=DEFAULT_SOURCES,
        help="Listing source adapter to use. Defaults to RentCast, then Craigslist RSS.",
    )
    parser.add_argument("--limit", type=int, default=50, help="Maximum listings per source.")
    parser.add_argument("--radius-miles", type=int, default=10, help="Search radius around campus.")
    parser.add_argument(
        "--fail-empty",
        action="store_true",
        help="Exit with an error when no upstream source returns listings.",
    )
    return parser.parse_args()


def active_listing_count_for_school(db, school: School) -> int:
    state_variants = {school.state}
    normalized_state = normalize_us_state(school.state)
    if normalized_state:
        state_variants.add(normalized_state)

    return db.scalar(
        select(func.count())
        .select_from(Listing)
        .where(
            Listing.status == ListingStatus.ACTIVE,
            Listing.city.ilike(school.city),
            Listing.state.in_(state_variants),
        )
    ) or 0


def ingest_school_source(
    *,
    db,
    school: School,
    source_key: str,
    limit: int,
    radius_miles: int,
) -> IngestionResult | None:
    scraper = get_scraper(source_key)
    if scraper is None:
        LOGGER.warning("Unknown scraper skipped: %s", source_key)
        return None
    if not scraper.is_configured():
        LOGGER.info("Source not configured, skipped: %s", scraper.source_name)
        return None

    ensure_source_for_scraper(db, scraper)
    try:
        items = scraper.fetch(
            city=school.city,
            state=school.state,
            latitude=school.latitude,
            longitude=school.longitude,
            radius_miles=radius_miles,
            limit=limit,
        )
    except RuntimeError as exc:
        LOGGER.warning("%s failed for %s: %s", scraper.source_name, school.name, exc)
        return None

    if not items:
        LOGGER.info("%s returned no priced listings for %s.", scraper.source_name, school.name)
        return None

    result = ingest_listing_batch(db=db, source_name=scraper.source_name, items=items)
    LOGGER.info(
        "%s for %s: received=%s created=%s updated=%s skipped=%s indexed=%s",
        result.source_name,
        school.name,
        result.received,
        result.created,
        result.updated,
        result.skipped,
        result.indexed,
    )
    return result


def ingest_schools(
    *,
    schools: Sequence[str],
    sources: Sequence[str],
    limit: int,
    radius_miles: int,
    fail_empty: bool = False,
) -> int:
    total_received = 0
    total_created = 0
    total_updated = 0

    with SessionLocal() as db:
        for school_name in schools:
            school = find_or_fetch_school(db, school_name)
            if school is None:
                LOGGER.warning("Could not resolve school: %s", school_name)
                continue

            before_count = active_listing_count_for_school(db, school)
            LOGGER.info(
                "Ingesting around %s (%s, %s). Cached active listings before run: %s",
                school.name,
                school.city,
                school.state,
                before_count,
            )

            for source_key in sources:
                result = ingest_school_source(
                    db=db,
                    school=school,
                    source_key=source_key,
                    limit=limit,
                    radius_miles=radius_miles,
                )
                if result is None:
                    continue
                total_received += result.received
                total_created += result.created
                total_updated += result.updated

            after_count = active_listing_count_for_school(db, school)
            LOGGER.info("Cached active listings after %s run: %s", school.name, after_count)

    LOGGER.info(
        "Ingestion complete: received=%s created=%s updated=%s",
        total_received,
        total_created,
        total_updated,
    )
    return 1 if fail_empty and not total_received else 0


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = parse_args()
    schools = args.schools or list(DEFAULT_SCHOOLS)
    sources = args.sources or list(DEFAULT_SOURCES)
    return ingest_schools(
        schools=schools,
        sources=sources,
        limit=args.limit,
        radius_miles=args.radius_miles,
        fail_empty=args.fail_empty,
    )


if __name__ == "__main__":
    raise SystemExit(main())
