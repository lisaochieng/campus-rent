from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Listing, ListingScore, ListingStatus, School
from app.services.scoring import campus_rent_score


def refresh_baseline_listing_scores(db: Session) -> int:
    schools = list(db.scalars(select(School)).all())
    listings = list(
        db.scalars(
            select(Listing)
            .options(selectinload(Listing.source), selectinload(Listing.scam_signals))
            .where(Listing.status == ListingStatus.ACTIVE)
        ).all()
    )

    db.execute(delete(ListingScore))

    score_rows = []
    for school in schools:
        for listing in listings:
            score = campus_rent_score(listing=listing, school=school, max_budget=None)
            score_rows.append(
                ListingScore(
                    listing_id=listing.id,
                    school_id=school.id,
                    distance_miles=score["distance_miles"],
                    affordability_score=score["affordability_score"],
                    distance_score=score["distance_score"],
                    freshness_score=score["freshness_score"],
                    scam_risk_score=100 - score["scam_safety_score"],
                    campus_rent_score=score["campus_rent_score"],
                    score_details={
                        "score_type": "baseline",
                        "max_budget": None,
                        "scam_safety_score": score["scam_safety_score"],
                    },
                )
            )

    db.add_all(score_rows)
    db.flush()
    return len(score_rows)
