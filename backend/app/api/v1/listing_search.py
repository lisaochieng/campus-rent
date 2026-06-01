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


def source_name(url: str) -> str:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return host or "listing source"


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
    if not settings.serpapi_api_key:
        return []

    school = find_or_fetch_school(db, school_name)
    city = school.city if school else None
    state = school.state if school else None
    country = school.country if school else None
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

    results: list[ListingSearchResultRead] = []
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
