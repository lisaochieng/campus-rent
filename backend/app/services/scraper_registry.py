from abc import ABC, abstractmethod
from decimal import Decimal
import json
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from app.core.config import settings
from app.schemas.listing import ListingIngestItem

CRAIGSLIST_MARKETS_BY_STATE = {
    "AL": "bham",
    "AZ": "phoenix",
    "CA": "sfbay",
    "CO": "denver",
    "CT": "newhaven",
    "DC": "washingtondc",
    "FL": "miami",
    "GA": "atlanta",
    "IL": "chicago",
    "IN": "indianapolis",
    "MA": "boston",
    "MD": "baltimore",
    "MI": "annarbor",
    "MN": "minneapolis",
    "MO": "stlouis",
    "NC": "raleigh",
    "NJ": "newjersey",
    "NY": "newyork",
    "OH": "columbus",
    "OR": "portland",
    "PA": "philadelphia",
    "TN": "nashville",
    "TX": "austin",
    "VA": "richmond",
    "WA": "seattle",
    "WI": "madison",
}

CRAIGSLIST_MARKETS_BY_CITY = {
    "ann arbor": "annarbor",
    "athens": "athensga",
    "austin": "austin",
    "berkeley": "sfbay",
    "boston": "boston",
    "cambridge": "boston",
    "champaign": "chambana",
    "charlottesville": "charlottesville",
    "chicago": "chicago",
    "college station": "collegestation",
    "columbus": "columbus",
    "davis": "sacramento",
    "durham": "raleigh",
    "ithaca": "ithaca",
    "los angeles": "losangeles",
    "madison": "madison",
    "new york": "newyork",
    "philadelphia": "philadelphia",
    "pittsburgh": "pittsburgh",
    "providence": "providence",
    "san diego": "sandiego",
    "seattle": "seattle",
    "washington": "washingtondc",
}


class ListingScraper(ABC):
    key: str
    source_name: str
    base_url: str
    description: str
    requires_api_key = False

    def is_configured(self) -> bool:
        return True

    @abstractmethod
    def fetch(
        self,
        *,
        city: str | None = None,
        state: str | None = None,
        latitude: Decimal | None = None,
        longitude: Decimal | None = None,
        radius_miles: int = 10,
        limit: int = 20,
    ) -> list[ListingIngestItem]:
        raise NotImplementedError


class DemoGlobalHousingScraper(ListingScraper):
    key = "demo-global-feed"
    source_name = "CampusRent Demo Global Feed"
    base_url = "https://campusrent.local/demo-global-feed"
    description = "Demo adapter showing how external global housing sources feed CampusRent."

    def fetch(
        self,
        *,
        city: str | None = None,
        state: str | None = None,
        latitude: Decimal | None = None,
        longitude: Decimal | None = None,
        radius_miles: int = 10,
        limit: int = 20,
    ) -> list[ListingIngestItem]:
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


class ListingCardParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.cards: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "article":
            return

        attributes = {key: value for key, value in attrs if value is not None}
        if attributes.get("data-kind") != "rental-listing":
            return

        self.cards.append(attributes)


class DemoHtmlHousingScraper(ListingScraper):
    key = "demo-html-feed"
    source_name = "CampusRent Demo HTML Feed"
    base_url = "https://campusrent.local/demo-html-feed"
    description = "Demo HTML scraper adapter that parses listing cards from markup."

    def fetch(
        self,
        *,
        city: str | None = None,
        state: str | None = None,
        latitude: Decimal | None = None,
        longitude: Decimal | None = None,
        radius_miles: int = 10,
        limit: int = 20,
    ) -> list[ListingIngestItem]:
        fixture_path = Path(__file__).parent / "fixtures" / "demo_housing_feed.html"
        parser = ListingCardParser()
        parser.feed(fixture_path.read_text(encoding="utf-8"))

        listings = []
        for card in parser.cards:
            listings.append(
                ListingIngestItem(
                    source_listing_id=card.get("data-id"),
                    source_url=card["data-url"],
                    title=card["data-title"],
                    description=card.get("data-description"),
                    address=card.get("data-address"),
                    city=card["data-city"],
                    state=card["data-state"],
                    country=card["data-country"],
                    postal_code=card.get("data-postal-code"),
                    latitude=Decimal(card["data-latitude"]),
                    longitude=Decimal(card["data-longitude"]),
                    monthly_rent=int(card["data-monthly-rent"]),
                    currency_code=card["data-currency-code"],
                    bedrooms=Decimal(card["data-bedrooms"]),
                    bathrooms=Decimal(card["data-bathrooms"]),
                    square_feet=int(card["data-square-feet"])
                    if card.get("data-square-feet")
                    else None,
                )
            )

        return listings


class RentCastRentalScraper(ListingScraper):
    key = "rentcast-rentals"
    source_name = "RentCast Rental Listings"
    base_url = "https://api.rentcast.io/v1/listings/rental/long-term"
    description = "Real long-term rental listings from RentCast. Requires RENTCAST_API_KEY."
    requires_api_key = True

    def is_configured(self) -> bool:
        return bool(settings.rentcast_api_key)

    def fetch(
        self,
        *,
        city: str | None = None,
        state: str | None = None,
        latitude: Decimal | None = None,
        longitude: Decimal | None = None,
        radius_miles: int = 10,
        limit: int = 20,
    ) -> list[ListingIngestItem]:
        if not settings.rentcast_api_key:
            raise RuntimeError("RENTCAST_API_KEY must be set before running the RentCast scraper.")

        query: dict[str, str | int] = {"limit": limit}
        if latitude is not None and longitude is not None:
            query.update(
                {
                    "latitude": str(latitude),
                    "longitude": str(longitude),
                    "radius": radius_miles,
                }
            )
        elif city and state:
            query.update({"city": city, "state": state})
        else:
            raise RuntimeError("RentCast scraper requires either latitude/longitude or city/state.")

        request = Request(
            f"{self.base_url}?{urlencode(query)}",
            headers={"X-Api-Key": settings.rentcast_api_key, "Accept": "application/json"},
        )

        try:
            with urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise RuntimeError(f"RentCast request failed with HTTP {exc.code}.") from exc
        except URLError as exc:
            raise RuntimeError(f"RentCast request failed: {exc.reason}") from exc

        records = payload if isinstance(payload, list) else payload.get("listings", [])
        return [item for record in records[:limit] if (item := self._to_ingest_item(record, city, state))]

    def _to_ingest_item(
        self,
        record: dict,
        fallback_city: str | None,
        fallback_state: str | None,
    ) -> ListingIngestItem | None:
        source_id = str(record.get("id") or record.get("listingId") or record.get("propertyId") or "")
        address = record.get("formattedAddress") or record.get("addressLine1") or record.get("address")
        monthly_rent = record.get("price") or record.get("rent") or record.get("monthlyRent")
        city = record.get("city") or fallback_city
        state = record.get("state") or fallback_state

        if not source_id or not address or not monthly_rent or not city or not state:
            return None

        return ListingIngestItem(
            source_listing_id=source_id,
            source_url=self._source_url(record, source_id),
            title=record.get("title") or f"Rental listing at {address}",
            description=record.get("description"),
            address=address,
            city=city,
            state=state,
            country=record.get("country") or "US",
            postal_code=record.get("zipCode") or record.get("postalCode"),
            latitude=self._decimal_or_none(record.get("latitude")),
            longitude=self._decimal_or_none(record.get("longitude")),
            monthly_rent=int(monthly_rent),
            currency_code=record.get("currency") or record.get("currencyCode") or "USD",
            bedrooms=self._decimal_or_none(record.get("bedrooms")),
            bathrooms=self._decimal_or_none(record.get("bathrooms")),
            square_feet=self._int_or_none(record.get("squareFootage") or record.get("squareFeet")),
            contact_name=self._contact_name(record),
            contact_phone=self._contact_phone(record),
            contact_email=self._contact_email(record),
            image_url=self._image_url(record),
        )

    def _decimal_or_none(self, value) -> Decimal | None:
        if value is None:
            return None
        return Decimal(str(value))

    def _int_or_none(self, value) -> int | None:
        if value is None:
            return None
        return int(value)

    def _source_url(self, record: dict, source_id: str) -> str:
        listing_office = record.get("listingOffice") or {}
        listing_agent = record.get("listingAgent") or {}
        return (
            record.get("url")
            or record.get("listingUrl")
            or record.get("sourceUrl")
            or listing_office.get("website")
            or listing_agent.get("website")
            or f"{self.base_url}/{source_id}"
        )

    def _image_url(self, record: dict) -> str | None:
        for key in ("imageUrl", "image_url", "thumbnail", "primaryPhotoUrl"):
            value = record.get(key)
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                return value

        photos = record.get("photos") or record.get("images") or record.get("propertyImages")
        if isinstance(photos, list):
            for photo in photos:
                if isinstance(photo, str) and photo.startswith(("http://", "https://")):
                    return photo
                if isinstance(photo, dict):
                    for key in ("url", "href", "imageUrl"):
                        value = photo.get(key)
                        if isinstance(value, str) and value.startswith(("http://", "https://")):
                            return value
        return None

    def _contact_name(self, record: dict) -> str | None:
        listing_agent = record.get("listingAgent") or {}
        listing_office = record.get("listingOffice") or {}
        return (
            record.get("contactName")
            or listing_agent.get("name")
            or listing_office.get("name")
        )

    def _contact_phone(self, record: dict) -> str | None:
        listing_agent = record.get("listingAgent") or {}
        listing_office = record.get("listingOffice") or {}
        return (
            record.get("contactPhone")
            or listing_agent.get("phone")
            or listing_office.get("phone")
        )

    def _contact_email(self, record: dict) -> str | None:
        listing_agent = record.get("listingAgent") or {}
        listing_office = record.get("listingOffice") or {}
        return (
            record.get("contactEmail")
            or listing_agent.get("email")
            or listing_office.get("email")
        )


class CraigslistRssRentalScraper(ListingScraper):
    key = "craigslist-rss-rentals"
    source_name = "Craigslist Public Rental RSS"
    base_url = "https://craigslist.org"
    description = "Public Craigslist apartment RSS results for US rental discovery."

    def fetch(
        self,
        *,
        city: str | None = None,
        state: str | None = None,
        latitude: Decimal | None = None,
        longitude: Decimal | None = None,
        radius_miles: int = 10,
        limit: int = 20,
    ) -> list[ListingIngestItem]:
        market = self._market_for_location(city, state)
        if market is None:
            raise RuntimeError("Craigslist RSS does not have a configured market for this school yet.")

        params = urlencode(
            {
                "format": "rss",
                "query": city or "apartment",
                "search_distance": radius_miles,
                "availabilityMode": 0,
                "sort": "date",
            }
        )
        request = Request(
            f"https://{market}.craigslist.org/search/apa?{params}",
            headers={
                "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
                "User-Agent": "CampusRent student housing search (local development)",
            },
        )

        try:
            with urlopen(request, timeout=8) as response:
                payload = response.read()
        except HTTPError as exc:
            raise RuntimeError(f"Craigslist RSS request failed with HTTP {exc.code}.") from exc
        except URLError as exc:
            raise RuntimeError(f"Craigslist RSS request failed: {exc.reason}") from exc

        root = ElementTree.fromstring(payload)
        items = root.findall(".//item")
        return [
            listing
            for item in items[:limit]
            if (listing := self._item_to_listing(item, market, city, state))
        ]

    def _market_for_location(self, city: str | None, state: str | None) -> str | None:
        if city:
            market = CRAIGSLIST_MARKETS_BY_CITY.get(city.strip().lower())
            if market:
                return market
        if state:
            return CRAIGSLIST_MARKETS_BY_STATE.get(state.strip().upper())
        return None

    def _item_to_listing(
        self,
        item: ElementTree.Element,
        market: str,
        city: str | None,
        state: str | None,
    ) -> ListingIngestItem | None:
        title = self._text(item, "title")
        link = self._text(item, "link")
        description = self._text(item, "description")
        if not title or not link:
            return None

        rent = self._extract_rent(title) or self._extract_rent(description)
        if rent is None:
            return None

        latitude, longitude = self._extract_geo_point(item)
        return ListingIngestItem(
            source_listing_id=link.rstrip("/").split("/")[-1].replace(".html", ""),
            source_url=link,
            title=title[:300],
            description=description,
            address=None,
            city=city or market,
            state=state or "US",
            country="US",
            postal_code=None,
            latitude=latitude,
            longitude=longitude,
            monthly_rent=rent,
            currency_code="USD",
            bedrooms=self._extract_bedrooms(title),
            bathrooms=None,
            square_feet=self._extract_square_feet(title),
            contact_name="Craigslist listing contact",
            contact_phone=None,
            contact_email=None,
        )

    def _text(self, item: ElementTree.Element, name: str) -> str | None:
        value = item.findtext(name)
        if value is None:
            return None
        return value.strip()

    def _extract_rent(self, value: str | None) -> int | None:
        if not value:
            return None
        match = re.search(r"\$([0-9][0-9,]{2,6})", value)
        if match is None:
            return None
        return int(match.group(1).replace(",", ""))

    def _extract_bedrooms(self, value: str) -> Decimal | None:
        match = re.search(r"\b([0-9]+)\s*(?:br|bd|bed|beds|bedroom)", value, re.IGNORECASE)
        if match is None:
            return None
        return Decimal(match.group(1))

    def _extract_square_feet(self, value: str) -> int | None:
        match = re.search(r"\b([0-9]{3,5})\s*(?:ft2|sqft|sq\.?\s*ft)", value, re.IGNORECASE)
        if match is None:
            return None
        return int(match.group(1))

    def _extract_geo_point(self, item: ElementTree.Element) -> tuple[Decimal | None, Decimal | None]:
        for child in item.iter():
            if child.tag.endswith("point") and child.text:
                parts = child.text.strip().split()
                if len(parts) == 2:
                    return Decimal(parts[0]), Decimal(parts[1])
        return None, None


SCRAPERS: dict[str, ListingScraper] = {
    DemoGlobalHousingScraper.key: DemoGlobalHousingScraper(),
    DemoHtmlHousingScraper.key: DemoHtmlHousingScraper(),
    RentCastRentalScraper.key: RentCastRentalScraper(),
    CraigslistRssRentalScraper.key: CraigslistRssRentalScraper(),
}


def get_scraper(key: str) -> ListingScraper | None:
    return SCRAPERS.get(key)


def list_scrapers() -> list[ListingScraper]:
    return list(SCRAPERS.values())
