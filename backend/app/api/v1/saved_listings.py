from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.db.models import Listing, ListingStatus, SavedListing
from app.db.session import get_db
from app.schemas.listing import ListingCompareResponse
from app.schemas.saved_listing import SavedListingCreate, SavedListingRead, SavedListingUpdate
from app.services.listing_presentation import listing_comparison
from app.services.school_matching import find_school_by_name

router = APIRouter(prefix="/saved-listings", tags=["saved listings"])


def normalize_email(email: str) -> str:
    return email.strip().lower()


@router.get("", response_model=list[SavedListingRead])
def list_saved_listings(
    student_email: str = Query(min_length=3),
    db: Session = Depends(get_db),
) -> list[SavedListing]:
    statement = (
        select(SavedListing)
        .options(selectinload(SavedListing.listing).selectinload(Listing.source))
        .where(SavedListing.student_email == normalize_email(student_email))
        .order_by(SavedListing.created_at.desc())
    )
    return list(db.scalars(statement).all())


@router.get("/compare", response_model=ListingCompareResponse)
def compare_saved_listings(
    student_email: str = Query(min_length=3),
    school_name: str = Query(min_length=2),
    max_rent: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
) -> ListingCompareResponse:
    school = find_school_by_name(db, school_name)
    if school is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found.",
        )

    saved_listings = db.scalars(
        select(SavedListing)
        .options(
            selectinload(SavedListing.listing).selectinload(Listing.source),
            selectinload(SavedListing.listing).selectinload(Listing.scam_signals),
        )
        .where(SavedListing.student_email == normalize_email(student_email))
        .order_by(SavedListing.created_at.desc())
    ).all()
    if len(saved_listings) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least two saved listings are required for comparison.",
        )

    comparisons = [
        listing_comparison(
            listing=saved_listing.listing,
            school=school,
            max_rent=max_rent,
        )
        for saved_listing in saved_listings[:5]
    ]
    comparisons.sort(key=lambda comparison: comparison.campus_rent_score, reverse=True)

    return ListingCompareResponse(school_name=school.name, comparisons=comparisons)


@router.post("", response_model=SavedListingRead, status_code=status.HTTP_201_CREATED)
def save_listing(
    payload: SavedListingCreate,
    db: Session = Depends(get_db),
) -> SavedListing:
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

    saved_listing = SavedListing(
        student_email=normalize_email(payload.student_email),
        listing_id=payload.listing_id,
        note=payload.note,
    )
    db.add(saved_listing)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Listing is already saved for this student.",
        ) from error

    saved_listing = db.scalar(
        select(SavedListing)
        .options(selectinload(SavedListing.listing).selectinload(Listing.source))
        .where(SavedListing.id == saved_listing.id)
    )
    return saved_listing


@router.patch("/{saved_listing_id}", response_model=SavedListingRead)
def update_saved_listing(
    saved_listing_id: UUID,
    payload: SavedListingUpdate,
    db: Session = Depends(get_db),
) -> SavedListing:
    saved_listing = db.scalar(
        select(SavedListing)
        .options(selectinload(SavedListing.listing).selectinload(Listing.source))
        .where(SavedListing.id == saved_listing_id)
    )
    if saved_listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved listing not found.",
        )

    saved_listing.note = payload.note
    db.commit()
    db.refresh(saved_listing)
    return saved_listing


@router.delete("/{saved_listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_listing(saved_listing_id: UUID, db: Session = Depends(get_db)) -> None:
    saved_listing = db.get(SavedListing, saved_listing_id)
    if saved_listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved listing not found.",
        )

    db.delete(saved_listing)
    db.commit()
