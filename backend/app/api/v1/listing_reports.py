from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Listing, ListingReport, ListingStatus
from app.db.session import get_db
from app.schemas.listing_report import (
    ListingReportCreate,
    ListingReportRead,
    ListingReportUpdate,
)
from app.services.listing_moderation import flag_listing_if_report_threshold_reached

router = APIRouter(prefix="/listing-reports", tags=["listing reports"])


def normalize_email(email: str) -> str:
    return email.strip().lower()


@router.get("", response_model=list[ListingReportRead])
def list_listing_reports(
    status_filter: str = Query(default="open", alias="status"),
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[ListingReport]:
    statement = (
        select(ListingReport)
        .options(selectinload(ListingReport.listing).selectinload(Listing.source))
        .where(ListingReport.status == status_filter)
        .order_by(ListingReport.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(statement).all())


@router.post("", response_model=ListingReportRead, status_code=status.HTTP_201_CREATED)
def report_listing(
    payload: ListingReportCreate,
    db: Session = Depends(get_db),
) -> ListingReport:
    listing = db.scalar(
        select(Listing).where(
            Listing.id == payload.listing_id,
            Listing.status == ListingStatus.ACTIVE,
        )
    )
    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active listing not found.",
        )

    report = ListingReport(
        listing_id=payload.listing_id,
        reporter_email=normalize_email(payload.reporter_email),
        reason=payload.reason.strip().lower(),
        description=payload.description,
        status="open",
    )
    db.add(report)
    db.flush()
    flag_listing_if_report_threshold_reached(db=db, listing=listing)
    db.commit()

    report = db.scalar(
        select(ListingReport)
        .options(selectinload(ListingReport.listing).selectinload(Listing.source))
        .where(ListingReport.id == report.id)
    )
    return report


@router.patch("/{report_id}", response_model=ListingReportRead)
def update_listing_report(
    report_id: UUID,
    payload: ListingReportUpdate,
    db: Session = Depends(get_db),
) -> ListingReport:
    report = db.scalar(
        select(ListingReport)
        .options(selectinload(ListingReport.listing).selectinload(Listing.source))
        .where(ListingReport.id == report_id)
    )
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing report not found.",
        )

    report.status = payload.status.strip().lower()
    db.commit()
    db.refresh(report)
    return report
