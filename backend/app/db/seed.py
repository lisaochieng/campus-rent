from decimal import Decimal

from sqlalchemy import select

from app.db.models import Listing, ListingSource, ListingStatus, School, SourceTrustLevel
from app.db.session import SessionLocal
from app.services.cache import clear_fast_search_cache
from app.services.scam_detection import refresh_persisted_scam_signals
from app.services.score_persistence import refresh_baseline_listing_scores
from app.services.search_index import rebuild_listings_index

SEED_SCHOOLS = [
    {
        "name": "New York University",
        "city": "New York",
        "state": "NY",
        "country": "US",
        "latitude": Decimal("40.729513"),
        "longitude": Decimal("-73.996461"),
    },
    {
        "name": "Columbia University",
        "city": "New York",
        "state": "NY",
        "country": "US",
        "latitude": Decimal("40.807536"),
        "longitude": Decimal("-73.962573"),
    },
    {
        "name": "University of California, Berkeley",
        "city": "Berkeley",
        "state": "CA",
        "country": "US",
        "latitude": Decimal("37.871899"),
        "longitude": Decimal("-122.258540"),
    },
    {
        "name": "University College London",
        "city": "London",
        "state": "England",
        "country": "GB",
        "latitude": Decimal("51.524600"),
        "longitude": Decimal("-0.134000"),
    },
    {
        "name": "University of Toronto",
        "city": "Toronto",
        "state": "ON",
        "country": "CA",
        "latitude": Decimal("43.662900"),
        "longitude": Decimal("-79.395700"),
    },
    {
        "name": "University of Tokyo",
        "city": "Tokyo",
        "state": "Tokyo",
        "country": "JP",
        "latitude": Decimal("35.713200"),
        "longitude": Decimal("139.762100"),
    },
    {
        "name": "University of Lagos",
        "city": "Lagos",
        "state": "Lagos",
        "country": "NG",
        "latitude": Decimal("6.515800"),
        "longitude": Decimal("3.389900"),
    },
    {
        "name": "University of Sydney",
        "city": "Sydney",
        "state": "NSW",
        "country": "AU",
        "latitude": Decimal("-33.888600"),
        "longitude": Decimal("151.187300"),
    },
    {
        "name": "University of Cape Town",
        "city": "Cape Town",
        "state": "Western Cape",
        "country": "ZA",
        "latitude": Decimal("-33.957700"),
        "longitude": Decimal("18.461200"),
    },
]

SEED_SOURCES = [
    {
        "name": "Manual Verified Dataset",
        "base_url": "https://campusrent.local/manual",
        "trust_level": SourceTrustLevel.HIGH,
        "is_active": True,
        "notes": "Internal seed source for manually verified development data.",
    }
]

SEED_LISTINGS = [
    {
        "source_listing_id": "manual-nyu-001",
        "source_url": "https://campusrent.local/manual/nyu-001",
        "title": "Studio near Washington Square Park",
        "description": "Verified starter listing for local development near NYU.",
        "address": "12 Waverly Pl",
        "city": "New York",
        "state": "NY",
        "postal_code": "10003",
        "latitude": Decimal("40.730100"),
        "longitude": Decimal("-73.995700"),
        "monthly_rent": 2450,
        "bedrooms": Decimal("0.0"),
        "bathrooms": Decimal("1.0"),
        "square_feet": 420,
        "status": ListingStatus.ACTIVE,
    },
    {
        "source_listing_id": "manual-nyu-002",
        "source_url": "https://campusrent.local/manual/nyu-002",
        "title": "Two bedroom apartment in East Village",
        "description": "Roommate-friendly mock listing with a strong transit location.",
        "address": "210 E 9th St",
        "city": "New York",
        "state": "NY",
        "postal_code": "10003",
        "latitude": Decimal("40.729000"),
        "longitude": Decimal("-73.987200"),
        "monthly_rent": 3900,
        "bedrooms": Decimal("2.0"),
        "bathrooms": Decimal("1.0"),
        "square_feet": 760,
        "status": ListingStatus.ACTIVE,
    },
    {
        "source_listing_id": "manual-columbia-001",
        "source_url": "https://campusrent.local/manual/columbia-001",
        "title": "One bedroom near Morningside Heights",
        "description": "Verified starter listing for students near Columbia University.",
        "address": "501 W 112th St",
        "city": "New York",
        "state": "NY",
        "postal_code": "10025",
        "latitude": Decimal("40.805900"),
        "longitude": Decimal("-73.963300"),
        "monthly_rent": 2850,
        "bedrooms": Decimal("1.0"),
        "bathrooms": Decimal("1.0"),
        "square_feet": 610,
        "status": ListingStatus.ACTIVE,
    },
    {
        "source_listing_id": "manual-berkeley-001",
        "source_url": "https://campusrent.local/manual/berkeley-001",
        "title": "Shared apartment close to UC Berkeley",
        "description": "Budget-oriented mock listing within walking distance of campus.",
        "address": "2400 Durant Ave",
        "city": "Berkeley",
        "state": "CA",
        "postal_code": "94704",
        "latitude": Decimal("37.867900"),
        "longitude": Decimal("-122.260700"),
        "monthly_rent": 1650,
        "bedrooms": Decimal("1.0"),
        "bathrooms": Decimal("1.0"),
        "square_feet": 540,
        "status": ListingStatus.ACTIVE,
    },
    {
        "source_listing_id": "manual-risky-001",
        "source_url": "https://campusrent.local/manual/risky-001",
        "title": "Cheap luxury studio urgent deal no viewing needed",
        "description": "Owner is out of country. Deposit before viewing by wire money to hold unit.",
        "address": None,
        "city": "New York",
        "state": "NY",
        "postal_code": "10003",
        "latitude": None,
        "longitude": None,
        "monthly_rent": 700,
        "bedrooms": Decimal("0.0"),
        "bathrooms": Decimal("1.0"),
        "square_feet": None,
        "status": ListingStatus.ACTIVE,
    },
]


def json_safe_payload(data: dict) -> dict:
    payload = {}
    for key, value in data.items():
        if isinstance(value, Decimal):
            payload[key] = str(value)
        elif isinstance(value, ListingStatus):
            payload[key] = value.value
        else:
            payload[key] = value

    return payload


def upsert_schools() -> None:
    with SessionLocal() as session:
        for school_data in SEED_SCHOOLS:
            school = session.scalar(select(School).where(School.name == school_data["name"]))
            if school is None:
                session.add(School(**school_data))
                continue

            for key, value in school_data.items():
                setattr(school, key, value)

        session.commit()


def upsert_sources() -> None:
    with SessionLocal() as session:
        for source_data in SEED_SOURCES:
            source = session.scalar(
                select(ListingSource).where(ListingSource.name == source_data["name"])
            )
            if source is None:
                session.add(ListingSource(**source_data))
                continue

            for key, value in source_data.items():
                setattr(source, key, value)

        session.commit()


def upsert_listings() -> None:
    with SessionLocal() as session:
        source = session.scalar(
            select(ListingSource).where(ListingSource.name == "Manual Verified Dataset")
        )
        if source is None:
            raise RuntimeError("Manual Verified Dataset source must be seeded before listings.")

        for listing_data in SEED_LISTINGS:
            listing = session.scalar(
                select(Listing).where(Listing.source_url == listing_data["source_url"])
            )
            payload = {
                **listing_data,
                "source_id": source.id,
                "raw_payload": json_safe_payload(listing_data),
            }

            if listing is None:
                session.add(Listing(**payload))
                continue

            for key, value in payload.items():
                setattr(listing, key, value)

        session.flush()

        for listing_data in SEED_LISTINGS:
            listing = session.scalar(
                select(Listing).where(Listing.source_url == listing_data["source_url"])
            )
            if listing is not None:
                refresh_persisted_scam_signals(session, listing)

        session.commit()


def main() -> None:
    upsert_schools()
    upsert_sources()
    upsert_listings()
    with SessionLocal() as session:
        score_count = refresh_baseline_listing_scores(session)
        session.commit()
        indexed_count = rebuild_listings_index(session)
        cleared_cache_count = clear_fast_search_cache()

    print(
        "Seeded schools, listing sources, mock listings, "
        f"{score_count} baseline scores, {indexed_count} search documents, "
        f"and cleared {cleared_cache_count} fast-search cache keys."
    )


if __name__ == "__main__":
    main()
