from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Listing, ListingSource, ListingStatus, School
from app.db.session import get_db
from app.schemas.listing import ListingCreate, ListingRead, ListingSearchResult, ScamSignalRead
from app.services.scam_detection import detect_scam_signals, refresh_persisted_scam_signals
from app.services.scoring import campus_rent_score

router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("", response_model=list[ListingRead])
def list_listings(
    city: str | None = None,
    state: str | None = None,
    max_rent: int | None = Query(default=None, gt=0),
    min_bedrooms: Decimal | None = Query(default=None, ge=0),
    status_filter: ListingStatus = Query(default=ListingStatus.ACTIVE, alias="status"),
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[Listing]:
    statement = (
        select(Listing)
        .options(selectinload(Listing.source), selectinload(Listing.scam_signals))
        .where(Listing.status == status_filter)
        .order_by(Listing.monthly_rent.asc(), Listing.created_at.desc())
        .limit(limit)
    )

    if city:
        statement = statement.where(Listing.city.ilike(city))
    if state:
        statement = statement.where(Listing.state.ilike(state))
    if max_rent:
        statement = statement.where(Listing.monthly_rent <= max_rent)
    if min_bedrooms is not None:
        statement = statement.where(Listing.bedrooms >= min_bedrooms)

    return list(db.scalars(statement).all())


@router.get("/search", response_model=list[ListingSearchResult])
def search_listings_for_school(
    school_id: UUID,
    max_rent: int | None = Query(default=None, gt=0),
    min_bedrooms: Decimal | None = Query(default=None, ge=0),
    max_distance_miles: float | None = Query(default=None, gt=0),
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[ListingSearchResult]:
    school = db.get(School, school_id)
    if school is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found.",
        )

    statement = (
        select(Listing)
        .options(selectinload(Listing.source), selectinload(Listing.scam_signals))
        .where(Listing.status == ListingStatus.ACTIVE)
    )
    if max_rent:
        statement = statement.where(Listing.monthly_rent <= max_rent)
    if min_bedrooms is not None:
        statement = statement.where(Listing.bedrooms >= min_bedrooms)

    listings = db.scalars(statement).all()
    results = []
    for listing in listings:
        score = campus_rent_score(listing=listing, school=school, max_budget=max_rent)
        scam_signals = listing.scam_signals or detect_scam_signals(listing)
        if (
            max_distance_miles is not None
            and score["distance_miles"] > max_distance_miles
        ):
            continue

        results.append(
            ListingSearchResult(
                listing=listing,
                distance_miles=score["distance_miles"],
                distance_score=score["distance_score"],
                affordability_score=score["affordability_score"],
                freshness_score=score["freshness_score"],
                scam_safety_score=score["scam_safety_score"],
                scam_signals=[
                    ScamSignalRead(
                        signal_type=signal.signal_type,
                        severity=signal.severity,
                        explanation=signal.explanation,
                    )
                    for signal in scam_signals
                ],
                campus_rent_score=score["campus_rent_score"],
            )
        )

    results.sort(key=lambda result: result.campus_rent_score, reverse=True)
    return results[:limit]


@router.post("", response_model=ListingRead, status_code=status.HTTP_201_CREATED)
def create_listing(payload: ListingCreate, db: Session = Depends(get_db)) -> Listing:
    source = db.scalar(select(ListingSource).where(ListingSource.name == payload.source_name))
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown listing source: {payload.source_name}",
        )

    existing = db.scalar(select(Listing).where(Listing.source_url == payload.source_url))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A listing with this source_url already exists.",
        )

    listing = Listing(
        source_id=source.id,
        source_listing_id=payload.source_listing_id,
        source_url=payload.source_url,
        title=payload.title,
        description=payload.description,
        address=payload.address,
        city=payload.city,
        state=payload.state,
        postal_code=payload.postal_code,
        latitude=payload.latitude,
        longitude=payload.longitude,
        monthly_rent=payload.monthly_rent,
        bedrooms=payload.bedrooms,
        bathrooms=payload.bathrooms,
        square_feet=payload.square_feet,
        status=ListingStatus.ACTIVE,
        raw_payload=payload.model_dump(mode="json"),
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    refresh_persisted_scam_signals(db, listing)
    db.commit()
    db.refresh(listing)

    return listing
