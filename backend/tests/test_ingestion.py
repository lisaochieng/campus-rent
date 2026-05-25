from fastapi.testclient import TestClient

from app.main import app
from app.schemas.listing import ListingIngestItem
from app.services.listing_ingestion import clean_ingested_listing

client = TestClient(app)


def test_ingestion_requires_api_key() -> None:
    response = client.post(
        "/api/v1/ingestion/listings",
        json={
            "source_name": "Manual Verified Dataset",
            "listings": [
                {
                    "source_listing_id": "test-001",
                    "source_url": "https://campusrent.local/manual/test-001",
                    "title": "Studio near campus",
                    "city": "New York",
                    "state": "NY",
                    "monthly_rent": 2500,
                }
            ],
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Valid ingestion API key required."}


def test_clean_ingested_listing_normalizes_text_fields() -> None:
    item = ListingIngestItem(
        source_listing_id=" scraped-001 ",
        source_url=" https://campusrent.local/manual/scraped-001 ",
        title="  Sunny    studio near NYU  ",
        description="  Tours     available through leasing office. ",
        address="  20 Astor Pl ",
        city="new york",
        state="ny",
        postal_code=" 10003 ",
        latitude="40.7298",
        longitude="-73.9916",
        monthly_rent=2550,
        bedrooms="0.0",
        bathrooms="1.0",
        square_feet=430,
    )

    cleaned = clean_ingested_listing(item)

    assert cleaned["source_listing_id"] == "scraped-001"
    assert cleaned["source_url"] == "https://campusrent.local/manual/scraped-001"
    assert cleaned["title"] == "Sunny studio near NYU"
    assert cleaned["description"] == "Tours available through leasing office."
    assert cleaned["address"] == "20 Astor Pl"
    assert cleaned["city"] == "New York"
    assert cleaned["state"] == "NY"
    assert cleaned["postal_code"] == "10003"


def test_clean_ingested_listing_preserves_long_global_regions() -> None:
    item = ListingIngestItem(
        source_url="https://campusrent.local/manual/london-001",
        title="Studio near campus",
        city="london",
        state="england",
        country="gb",
        monthly_rent=1800,
        currency_code="gbp",
    )

    cleaned = clean_ingested_listing(item)

    assert cleaned["city"] == "London"
    assert cleaned["state"] == "England"
    assert cleaned["country"] == "GB"
    assert cleaned["currency_code"] == "GBP"
