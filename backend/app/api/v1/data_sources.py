from fastapi import APIRouter

from app.schemas.data_source import DataSourceRead
from app.services.scraper_registry import list_scrapers

router = APIRouter(prefix="/data-sources", tags=["data sources"])


def coverage_for_source(key: str) -> str:
    if key == "rentcast-rentals":
        return "US rental listings when RENTCAST_API_KEY is configured"
    if key == "craigslist-rss-rentals":
        return "US public rental RSS fallback for supported Craigslist markets"
    if key == "openstreetmap-overpass-housing":
        return "Nearby apartment/residential building map leads, no API key required"
    if key == "demo-global-feed":
        return "Development demo listings across several global cities"
    if key == "demo-html-feed":
        return "Development HTML parsing fixture for scraper testing"
    return "Registered listing source"


@router.get("", response_model=list[DataSourceRead])
def list_data_sources() -> list[DataSourceRead]:
    sources = [
        DataSourceRead(
            key=scraper.key,
            source_name=scraper.source_name,
            description=scraper.description,
            requires_api_key=scraper.requires_api_key,
            is_configured=scraper.is_configured(),
            coverage=coverage_for_source(scraper.key),
        )
        for scraper in list_scrapers()
    ]
    sources.append(
        DataSourceRead(
            key="openstreetmap-overpass-housing",
            source_name="OpenStreetMap Overpass Housing Leads",
            description="Real nearby apartment and residential building map data from OpenStreetMap.",
            requires_api_key=False,
            is_configured=True,
            coverage=coverage_for_source("openstreetmap-overpass-housing"),
        )
    )
    return sources
