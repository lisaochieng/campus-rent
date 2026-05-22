from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import School
from app.db.session import get_db
from app.schemas.school import SchoolRead

router = APIRouter(prefix="/schools", tags=["schools"])


@router.get("", response_model=list[SchoolRead])
def list_schools(db: Session = Depends(get_db)) -> list[School]:
    statement = select(School).order_by(School.name)
    return list(db.scalars(statement).all())
