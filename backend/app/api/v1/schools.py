from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import School
from app.db.session import get_db
from app.schemas.school import SchoolCreate, SchoolRead, SchoolSearchResult
from app.services.school_matching import school_acronym, search_schools

router = APIRouter(prefix="/schools", tags=["schools"])


def normalize_region(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) <= 3:
        return cleaned.upper()
    return cleaned.title()


@router.get("", response_model=list[SchoolRead])
def list_schools(db: Session = Depends(get_db)) -> list[School]:
    statement = select(School).order_by(School.name)
    return list(db.scalars(statement).all())


@router.post("", response_model=SchoolRead, status_code=status.HTTP_201_CREATED)
def create_school(payload: SchoolCreate, db: Session = Depends(get_db)) -> School:
    existing = db.scalar(select(School).where(School.name.ilike(payload.name)))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="School already exists.",
        )

    school = School(
        name=payload.name.strip(),
        city=payload.city.strip().title(),
        state=normalize_region(payload.state),
        country=payload.country.strip().upper(),
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


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
