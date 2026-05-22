from decimal import Decimal

from sqlalchemy import select

from app.db.models import ListingSource, School, SourceTrustLevel
from app.db.session import SessionLocal

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


def main() -> None:
    upsert_schools()
    upsert_sources()
    print("Seeded schools and listing sources.")


if __name__ == "__main__":
    main()
