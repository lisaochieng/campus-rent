from app.db.models import Listing, School
from app.schemas.listing import ListingComparison, ListingSearchResult, ScamSignalRead
from app.services.scam_detection import detect_scam_signals
from app.services.scoring import campus_rent_score


def listing_search_result(
    *,
    listing: Listing,
    school: School,
    max_rent: int | None,
) -> ListingSearchResult:
    score = campus_rent_score(listing=listing, school=school, max_budget=max_rent)
    scam_signals = listing.scam_signals or detect_scam_signals(listing)

    return ListingSearchResult(
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


def listing_comparison(
    *,
    listing: Listing,
    school: School,
    max_rent: int | None,
) -> ListingComparison:
    result = listing_search_result(listing=listing, school=school, max_rent=max_rent)
    strengths = []
    tradeoffs = []

    if result.distance_miles <= 1:
        strengths.append("Very close to campus")
    elif result.distance_miles > 5:
        tradeoffs.append("Farther from campus")

    if max_rent is not None:
        if listing.monthly_rent <= max_rent:
            strengths.append("Within budget")
        else:
            tradeoffs.append("Above budget")

    if result.scam_safety_score >= 90:
        strengths.append("Low scam risk")
    elif result.scam_safety_score < 70:
        tradeoffs.append("Needs extra verification")

    if not strengths:
        strengths.append("Balanced option")
    if not tradeoffs:
        tradeoffs.append("No major tradeoffs detected")

    return ListingComparison(
        listing=listing,
        distance_miles=result.distance_miles,
        monthly_rent=listing.monthly_rent,
        rent_delta_from_budget=(
            listing.monthly_rent - max_rent if max_rent is not None else None
        ),
        scam_safety_score=result.scam_safety_score,
        campus_rent_score=result.campus_rent_score,
        strengths=strengths,
        tradeoffs=tradeoffs,
    )
