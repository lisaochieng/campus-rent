from abc import ABC, abstractmethod
from decimal import Decimal

from app.schemas.listing import ListingIngestItem


class ListingScraper(ABC):
    key: str
    source_name: str
    base_url: str
    description: str

    @abstractmethod
    def fetch(self) -> list[ListingIngestItem]:
        raise NotImplementedError


class DemoGlobalHousingScraper(ListingScraper):
    key = "demo-global-feed"
    source_name = "CampusRent Demo Global Feed"
    base_url = "https://campusrent.local/demo-global-feed"
    description = "Demo adapter showing how external global housing sources feed CampusRent."

    def fetch(self) -> list[ListingIngestItem]:
        return [
            ListingIngestItem(
                source_listing_id="demo-ucl-001",
                source_url=f"{self.base_url}/ucl-001",
                title="Bright studio near University College London",
                description="External demo listing for a central London student rental.",
                address="12 Gower Street",
                city="London",
                state="England",
                country="GB",
                postal_code="WC1E",
                latitude=Decimal("51.524600"),
                longitude=Decimal("-0.133900"),
                monthly_rent=1850,
                currency_code="GBP",
                bedrooms=Decimal("0.0"),
                bathrooms=Decimal("1.0"),
                square_feet=310,
            ),
            ListingIngestItem(
                source_listing_id="demo-toronto-001",
                source_url=f"{self.base_url}/toronto-001",
                title="One bedroom close to University of Toronto",
                description="External demo listing near downtown Toronto campus.",
                address="75 St George Street",
                city="Toronto",
                state="ON",
                country="CA",
                postal_code="M5S",
                latitude=Decimal("43.662900"),
                longitude=Decimal("-79.395700"),
                monthly_rent=2400,
                currency_code="CAD",
                bedrooms=Decimal("1.0"),
                bathrooms=Decimal("1.0"),
                square_feet=520,
            ),
            ListingIngestItem(
                source_listing_id="demo-tokyo-001",
                source_url=f"{self.base_url}/tokyo-001",
                title="Compact apartment near University of Tokyo",
                description="External demo listing for an international student rental in Tokyo.",
                address="7 Hongo",
                city="Tokyo",
                state="Tokyo",
                country="JP",
                postal_code="113",
                latitude=Decimal("35.713200"),
                longitude=Decimal("139.762100"),
                monthly_rent=145000,
                currency_code="JPY",
                bedrooms=Decimal("1.0"),
                bathrooms=Decimal("1.0"),
                square_feet=260,
            ),
            ListingIngestItem(
                source_listing_id="demo-lagos-001",
                source_url=f"{self.base_url}/lagos-001",
                title="Shared flat near University of Lagos",
                description="External demo listing for student housing in Lagos.",
                address="Akoka Road",
                city="Lagos",
                state="Lagos",
                country="NG",
                postal_code=None,
                latitude=Decimal("6.515800"),
                longitude=Decimal("3.389900"),
                monthly_rent=850000,
                currency_code="NGN",
                bedrooms=Decimal("1.0"),
                bathrooms=Decimal("1.0"),
                square_feet=430,
            ),
        ]


SCRAPERS: dict[str, ListingScraper] = {
    DemoGlobalHousingScraper.key: DemoGlobalHousingScraper(),
}


def get_scraper(key: str) -> ListingScraper | None:
    return SCRAPERS.get(key)


def list_scrapers() -> list[ListingScraper]:
    return list(SCRAPERS.values())
