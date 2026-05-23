from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import School
from app.db.session import get_db
from app.schemas.school import SchoolRead, SchoolSearchResult
from app.services.school_matching import school_acronym, search_schools

router = APIRouter(prefix="/schools", tags=["schools"])


@router.get("", response_model=list[SchoolRead])
def list_schools(db: Session = Depends(get_db)) -> list[School]:
    statement = select(School).order_by(School.name)
    return list(db.scalars(statement).all())


@router.get("/search", response_model=list[SchoolSearchResult])
def search_school_options(
    q: str = Query(min_length=2),
    limit: int = Query(default=10, ge=1, le=25),
    db: Session = Depends(get_db),
) -> list[SchoolSearchResult]:
    return [
        SchoolSearchResult(
            id=school.id,
            name=school.name,
            city=school.city,
            state=school.state,
            country=school.country,
            latitude=school.latitude,
            longitude=school.longitude,
            acronym=school_acronym(school.name),
        )
        for school in search_schools(db, q, limit)
    ]
