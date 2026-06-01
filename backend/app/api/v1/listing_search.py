import hashlib
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.schemas.listing_search import ListingSearchResultRead
from app.services.external_school_search import find_or_fetch_school

router = APIRouter(prefix="/listing-search", tags=["listing search"])

SERPAPI_URL = "https://serpapi.com/search.json"
RENTCAST_URL = "https://api.rentcast.io/v1/listings/rental/long-term"
TRELLISTATE_URL = "https://trellistate.com/api/v1/listings"
TRUSTED_RENTAL_DOMAINS = (
    "apartments.com",
    "zillow.com",
    "realtor.com",
    "trulia.com",
    "hotpads.com",
    "rent.com",
    "apartmentguide.com",
    "rightmove.co.uk",
    "zoopla.co.uk",
    "spareroom.co.uk",
    "realestate.com.au",
    "domain.com.au",
    "immobilienscout24.de",
    "seloger.com",
    "idealista.com",
    "daft.ie",
    "rentals.ca",
    "kijiji.ca",
)
PRICE_PATTERN = re.compile(
    r"(?P<symbol>[$£€]|C\$|A\$|CA\$|AU\$)?\s?(?P<amount>\d{1,3}(?:,\d{3})+|\d{3,5})(?:\s?(?:/|per)\s?(?:mo|month|pcm|week|wk))?",
    re.IGNORECASE,
)
CURRENCY_BY_SYMBOL = {
    "$": "USD",
    "C$": "CAD",
    "CA$": "CAD",
    "A$": "AUD",
    "AU$": "AUD",
    "£": "GBP",
    "€": "EUR",
}
COUNTRY_CURRENCY = {
    "United States": "USD",
    "Canada": "CAD",
    "United Kingdom": "GBP",
    "Ireland": "EUR",
    "France": "EUR",
    "Germany": "EUR",
    "Spain": "EUR",
    "Italy": "EUR",
    "Australia": "AUD",
    "New Zealand": "NZD",
}
US_STATE_ABBREVIATIONS = {
    "alabama": "AL",
    "alaska": "AK",
    "arizona": "AZ",
    "arkansas": "AR",
    "california": "CA",
    "colorado": "CO",
    "connecticut": "CT",
    "delaware": "DE",
    "district of columbia": "DC",
    "florida": "FL",
    "georgia": "GA",
    "hawaii": "HI",
    "idaho": "ID",
    "illinois": "IL",
    "indiana": "IN",
    "iowa": "IA",
    "kansas": "KS",
    "kentucky": "KY",
    "louisiana": "LA",
    "maine": "ME",
    "maryland": "MD",
    "massachusetts": "MA",
    "michigan": "MI",
    "minnesota": "MN",
    "mississippi": "MS",
    "missouri": "MO",
    "montana": "MT",
    "nebraska": "NE",
    "nevada": "NV",
    "new hampshire": "NH",
    "new jersey": "NJ",
    "new mexico": "NM",
    "new york": "NY",
    "north carolina": "NC",
    "north dakota": "ND",
    "ohio": "OH",
    "oklahoma": "OK",
    "oregon": "OR",
    "pennsylvania": "PA",
    "rhode island": "RI",
    "south carolina": "SC",
    "south dakota": "SD",
    "tennessee": "TN",
    "texas": "TX",
    "utah": "UT",
    "vermont": "VT",
    "virginia": "VA",
    "washington": "WA",
    "west virginia": "WV",
    "wisconsin": "WI",
    "wyoming": "WY",
}


def source_name(url: str) -> str:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return host or "listing source"


def normalize_us_state(state: str | None) -> str | None:
    if not state or state == "Unknown":
        return None
    cleaned = state.strip()
    if len(cleaned) == 2:
        return cleaned.upper()
    return US_STATE_ABBREVIATIONS.get(cleaned.lower(), cleaned)


def is_likely_listing_result(result: dict) -> bool:
    link = str(result.get("link") or "")
    if not link.startswith(("http://", "https://")):
        return False

    host = urlparse(link).netloc.lower()
    if not any(domain in host for domain in TRUSTED_RENTAL_DOMAINS):
        return False

    text = f"{result.get('title') or ''} {result.get('snippet') or ''}".lower()
    listing_words = ("rent", "rental", "apartment", "flat", "studio", "bedroom", "housing")
    return any(word in text for word in listing_words)


def infer_currency(symbol: str | None, country: str | None) -> str:
    if symbol and symbol in CURRENCY_BY_SYMBOL:
        return CURRENCY_BY_SYMBOL[symbol]
    if country in COUNTRY_CURRENCY:
        return COUNTRY_CURRENCY[country]
    return "USD"


def extract_price(result: dict, country: str | None) -> tuple[int, str, str] | None:
    text = " ".join(
        str(part)
        for part in [
            result.get("title"),
            result.get("snippet"),
            result.get("rich_snippet"),
        ]
        if part
    )
    matches = list(PRICE_PATTERN.finditer(text))
    if not matches:
        return None

    candidates: list[tuple[int, str, str]] = []
    for match in matches:
        amount = int(match.group("amount").replace(",", ""))
        if amount < 250 or amount > 25000:
            continue
        symbol = match.group("symbol")
        currency = infer_currency(symbol, country)
        candidates.append((amount, currency, match.group(0).strip()))

    if not candidates:
        return None
    return min(candidates, key=lambda candidate: candidate[0])


def extract_image_url(result: dict) -> str | None:
    direct = result.get("thumbnail")
    if isinstance(direct, str) and direct.startswith(("http://", "https://")):
        return direct

    rich_snippet = result.get("rich_snippet")
    if isinstance(rich_snippet, dict):
        top = rich_snippet.get("top")
        if isinstance(top, dict):
            thumbnail = top.get("thumbnail")
            if isinstance(thumbnail, str) and thumbnail.startswith(("http://", "https://")):
                return thumbnail

    return None


def extract_trellistate_image(record: dict) -> str | None:
    for key in ("image_url", "imageUrl", "thumbnail", "photo", "photo_url", "photoUrl", "primary_photo_url"):
        value = record.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return value

    photos = record.get("photos") or record.get("images")
    if isinstance(photos, list):
        for photo in photos:
            if isinstance(photo, str) and photo.startswith(("http://", "https://")):
                return photo
            if isinstance(photo, dict):
                for key in ("url", "href", "image_url", "imageUrl"):
                    value = photo.get(key)
                    if isinstance(value, str) and value.startswith(("http://", "https://")):
                        return value
    return None


def extract_record_image(record: dict) -> str | None:
    for key in ("imageUrl", "image_url", "thumbnail", "photo", "primaryPhotoUrl", "primary_photo_url"):
        value = record.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return value

    photos = record.get("photos") or record.get("images") or record.get("propertyImages")
    if isinstance(photos, list):
        for photo in photos:
            if isinstance(photo, str) and photo.startswith(("http://", "https://")):
                return photo
            if isinstance(photo, dict):
                for key in ("url", "href", "imageUrl", "image_url"):
                    value = photo.get(key)
                    if isinstance(value, str) and value.startswith(("http://", "https://")):
                        return value
    return None


def rentcast_source_url(record: dict) -> str | None:
    listing_office = record.get("listingOffice") if isinstance(record.get("listingOffice"), dict) else {}
    listing_agent = record.get("listingAgent") if isinstance(record.get("listingAgent"), dict) else {}
    for value in (
        record.get("url"),
        record.get("listingUrl"),
        record.get("sourceUrl"),
        record.get("propertyUrl"),
        listing_office.get("website"),
        listing_agent.get("website"),
    ):
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return value
    return None


def search_rentcast(
    *,
    city: str | None,
    state: str | None,
    latitude,
    longitude,
    radius_miles: int,
    limit: int,
) -> list[ListingSearchResultRead]:
    if not settings.rentcast_api_key:
        return []

    params: dict[str, str | int] = {"limit": min(limit, 20)}
    if latitude is not None and longitude is not None:
        params.update(
            {
                "latitude": str(latitude),
                "longitude": str(longitude),
                "radius": radius_miles,
            }
        )
    elif city and state:
        params["city"] = city
        params["state"] = normalize_us_state(state) or state
    else:
        return []

    request = Request(
        f"{RENTCAST_URL}?{urlencode(params)}",
        headers={
            "Accept": "application/json",
            "X-Api-Key": settings.rentcast_api_key,
            "User-Agent": "CampusRent live rental listing search",
        },
    )

    try:
        with urlopen(request, timeout=14) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return []

    records = payload if isinstance(payload, list) else payload.get("listings", [])
    if not isinstance(records, list):
        return []

    results: list[ListingSearchResultRead] = []
    seen_urls: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            continue
        source_url = rentcast_source_url(record)
        monthly_rent = record.get("price") or record.get("rent") or record.get("monthlyRent")
        if not source_url or source_url in seen_urls or monthly_rent is None:
            continue
        try:
            rent = int(monthly_rent)
        except (TypeError, ValueError):
            continue
        if rent < 250 or rent > 25000:
            continue

        seen_urls.add(source_url)
        address = record.get("formattedAddress") or record.get("addressLine1") or record.get("address")
        title = record.get("title") or (f"Rental listing at {address}" if address else "Rental listing")
        description = record.get("description") or record.get("propertyType") or address
        stable_id = hashlib.sha1(source_url.encode("utf-8")).hexdigest()[:16]
        results.append(
            ListingSearchResultRead(
                id=f"rentcast-{stable_id}",
                title=str(title),
                source_url=source_url,
                display_url=source_name(source_url),
                snippet=str(description) if description else None,
                monthly_rent=rent,
                currency_code=str(record.get("currency") or record.get("currencyCode") or "USD"),
                price_label=f"{rent}",
                image_url=extract_record_image(record),
                source_name="RentCast",
                provider="RentCast Rental Listings",
                rank=len(results) + 1,
            )
        )
        if len(results) >= limit:
            break

    return results


def extract_trellistate_price(record: dict, country: str | None) -> tuple[int, str, str] | None:
    for key in ("monthly_rent", "monthlyRent", "rent", "price", "list_price", "listPrice"):
        value = record.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            match = PRICE_PATTERN.search(value)
            if match:
                amount = int(match.group("amount").replace(",", ""))
                return amount, infer_currency(match.group("symbol"), country), match.group(0).strip()
            continue
        try:
            amount = int(value)
        except (TypeError, ValueError):
            continue
        if 250 <= amount <= 25000:
            currency_code = str(record.get("currency_code") or record.get("currencyCode") or record.get("currency") or infer_currency(None, country))
            return amount, currency_code, f"{amount}"
    return None


def trellistate_source_url(record: dict) -> str | None:
    for key in ("url", "listing_url", "listingUrl", "source_url", "sourceUrl", "canonical_url", "canonicalUrl", "public_url"):
        value = record.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return value

    listing_id = record.get("id") or record.get("listing_id") or record.get("slug")
    if listing_id:
        return f"https://trellistate.com/listings/{listing_id}"
    return None


def trellistate_records(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("listings", "data", "items", "results"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def search_trellistate(
    *,
    city: str | None,
    state: str | None,
    country: str | None,
    limit: int,
) -> list[ListingSearchResultRead]:
    if not city:
        return []

    params = {
        "city": city,
        "listing_type": "rent",
        "limit": min(limit, 20),
    }
    normalized_state = normalize_us_state(state)
    if normalized_state:
        params["state"] = normalized_state

    request = Request(
        f"{TRELLISTATE_URL}?{urlencode(params)}",
        headers={"User-Agent": "CampusRent public rental listing search"},
    )

    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return []

    results: list[ListingSearchResultRead] = []
    seen_urls: set[str] = set()
    for record in trellistate_records(payload):
        source_url = trellistate_source_url(record)
        price = extract_trellistate_price(record, country)
        if source_url is None or price is None or source_url in seen_urls:
            continue
        seen_urls.add(source_url)

        monthly_rent, currency_code, price_label = price
        title = (
            record.get("title")
            or record.get("name")
            or record.get("address")
            or f"Rental listing in {city}"
        )
        description = record.get("description") or record.get("summary")
        stable_id = hashlib.sha1(source_url.encode("utf-8")).hexdigest()[:16]
        results.append(
            ListingSearchResultRead(
                id=f"trellistate-{stable_id}",
                title=str(title),
                source_url=source_url,
                display_url=source_name(source_url),
                snippet=str(description) if description else None,
                monthly_rent=monthly_rent,
                currency_code=currency_code,
                price_label=price_label,
                image_url=extract_trellistate_image(record),
                source_name="trellistate.com",
                provider="Trellistate Public Listings",
                rank=len(results) + 1,
            )
        )
        if len(results) >= limit:
            break

    return results


def search_query(school_name: str, city: str | None, state: str | None) -> str:
    location = " ".join(part for part in [city, state] if part and part != "Unknown")
    place = f"{school_name} {location}".strip()
    domains = " OR ".join(f"site:{domain}" for domain in TRUSTED_RENTAL_DOMAINS[:10])
    return f"({domains}) apartments rentals near {place}"


@router.get("/nearby", response_model=list[ListingSearchResultRead])
def get_listing_search_results(
    school_name: str = Query(min_length=2),
    limit: int = Query(default=8, ge=1, le=20),
    db: Session = Depends(get_db),
) -> list[ListingSearchResultRead]:
    school = find_or_fetch_school(db, school_name)
    city = school.city if school else None
    state = school.state if school else None
    country = school.country if school else None
    latitude = school.latitude if school else None
    longitude = school.longitude if school else None
    results = search_rentcast(
        city=city,
        state=state,
        latitude=latitude,
        longitude=longitude,
        radius_miles=10,
        limit=limit,
    )
    if len(results) < limit:
        results.extend(
            search_trellistate(
                city=city,
                state=state,
                country=country,
                limit=limit - len(results),
            )
        )
    if len(results) >= limit or not settings.serpapi_api_key:
        return results

    query = search_query(school.name if school else school_name, city, state)
    params = {
        "engine": "google",
        "q": query,
        "api_key": settings.serpapi_api_key,
        "num": min(limit * 2, 20),
        "hl": "en",
    }

    request = Request(
        f"{SERPAPI_URL}?{urlencode(params)}",
        headers={"User-Agent": "CampusRent legal listing search adapter"},
    )

    try:
        with urlopen(request, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return []

    seen_urls: set[str] = set()
    for result in payload.get("organic_results", []):
        if not is_likely_listing_result(result):
            continue
        price = extract_price(result, country)
        if price is None:
            continue
        monthly_rent, currency_code, price_label = price
        link = result["link"]
        if link in seen_urls:
            continue
        seen_urls.add(link)
        stable_id = hashlib.sha1(link.encode("utf-8")).hexdigest()[:16]
        results.append(
            ListingSearchResultRead(
                id=f"search-{stable_id}",
                title=result.get("title") or "Rental listing result",
                source_url=link,
                display_url=result.get("displayed_link"),
                snippet=result.get("snippet"),
                monthly_rent=monthly_rent,
                currency_code=currency_code,
                price_label=price_label,
                image_url=extract_image_url(result),
                source_name=source_name(link),
                provider="SerpAPI Google Search",
                rank=len(results) + 1,
            )
        )
        if len(results) >= limit:
            break

    return results
