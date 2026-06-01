from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_ingestion_api_key
from app.db.models import ListingSource, SourceTrustLevel
from app.db.session import get_db
from app.schemas.scraper import ScraperRunResponse, ScraperSourceRead
from app.services.listing_ingestion import ingest_listing_batch
from app.services.scraper_registry import get_scraper, list_scrapers

router = APIRouter(
    prefix="/scraper-runs",
    tags=["scraper runs"],
    dependencies=[Depends(require_ingestion_api_key)],
)


def scraper_read_model(scraper) -> ScraperSourceRead:
    return ScraperSourceRead(
        key=scraper.key,
        source_name=scraper.source_name,
        description=scraper.description,
        requires_api_key=scraper.requires_api_key,
        is_configured=scraper.is_configured(),
    )


def ensure_scraper_source(db: Session, scraper) -> None:
    source = db.scalar(select(ListingSource).where(ListingSource.name == scraper.source_name))
    if source is not None:
        return

    db.add(
        ListingSource(
            name=scraper.source_name,
            base_url=scraper.base_url,
            trust_level=SourceTrustLevel.MEDIUM,
            is_active=True,
            notes="Registered scraper source.",
        )
    )
    db.commit()


@router.get("/sources", response_model=list[ScraperSourceRead])
def get_scraper_sources() -> list[ScraperSourceRead]:
    return [scraper_read_model(scraper) for scraper in list_scrapers()]


@router.post("/{source_key}", response_model=ScraperRunResponse)
def run_scraper_source(
    source_key: str,
    city: str | None = Query(default=None, min_length=2, max_length=120),
    state: str | None = Query(default=None, min_length=2, max_length=80),
    latitude: Decimal | None = Query(default=None),
    longitude: Decimal | None = Query(default=None),
    radius_miles: int = Query(default=10, ge=1, le=50),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ScraperRunResponse:
    scraper = get_scraper(source_key)
    if scraper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scraper source not found.",
        )

    ensure_scraper_source(db, scraper)
    try:
        items = scraper.fetch(
            city=city,
            state=state,
            latitude=latitude,
            longitude=longitude,
            radius_miles=radius_miles,
            limit=limit,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    ingestion = ingest_listing_batch(
        db=db,
        source_name=scraper.source_name,
        items=items,
    )

    return ScraperRunResponse(
        source=scraper_read_model(scraper),
        ingestion=ingestion.__dict__,
    )
