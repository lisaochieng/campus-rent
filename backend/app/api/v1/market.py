from collections import defaultdict
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Listing, ListingStatus
from app.db.session import get_db
from app.schemas.market import BedroomRentSummary, MarketSummary
from app.services.listing_presentation import listing_search_result
from app.services.school_matching import find_school_by_name

router = APIRouter(prefix="/market", tags=["market"])


def average(values: list[int]) -> int | None:
    if not values:
        return None
    return round(sum(values) / len(values))


def average_float(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def budget_hint(average_rent: int | None) -> str:
    if average_rent is None:
        return "Not enough listing data yet."
    if average_rent < 1800:
        return "This market has some relatively affordable student options."
    if average_rent < 3000:
        return "Plan for a moderate student rental budget in this market."
    return "This is a high-rent student market, so roommate options may matter."


@router.get("/summary", response_model=MarketSummary)
def get_market_summary(
    school_name: str = Query(min_length=2),
    min_scam_safety: int = Query(default=70, ge=0, le=100),
    db: Session = Depends(get_db),
) -> MarketSummary:
    school = find_school_by_name(db, school_name)
    if school is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found.",
        )

    listings = db.scalars(
        select(Listing)
        .options(selectinload(Listing.source), selectinload(Listing.scam_signals))
        .where(
            Listing.status == ListingStatus.ACTIVE,
            Listing.state.ilike(school.state),
        )
    ).all()

    scored_results = [
        listing_search_result(listing=listing, school=school, max_rent=None)
        for listing in listings
    ]
    safe_results = [
        result for result in scored_results if result.scam_safety_score >= min_scam_safety
    ]

    rents = [result.listing.monthly_rent for result in safe_results]
    distances = [result.distance_miles for result in safe_results]
    rents_by_bedroom: dict[Decimal | None, list[int]] = defaultdict(list)
    for result in safe_results:
        rents_by_bedroom[result.listing.bedrooms].append(result.listing.monthly_rent)

    bedroom_summaries = [
        BedroomRentSummary(
            bedrooms=bedrooms,
            listing_count=len(bedroom_rents),
            average_rent=round(sum(bedroom_rents) / len(bedroom_rents)),
            min_rent=min(bedroom_rents),
            max_rent=max(bedroom_rents),
        )
        for bedrooms, bedroom_rents in sorted(
            rents_by_bedroom.items(),
            key=lambda item: (item[0] is None, item[0] or Decimal("999")),
        )
    ]

    average_rent = average(rents)
    return MarketSummary(
        school_name=school.name,
        city=school.city,
        state=school.state,
        listing_count=len(scored_results),
        safe_listing_count=len(safe_results),
        average_rent=average_rent,
        min_rent=min(rents) if rents else None,
        max_rent=max(rents) if rents else None,
        average_distance_miles=average_float(distances),
        bedroom_summaries=bedroom_summaries,
        budget_hint=budget_hint(average_rent),
    )
