from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.listing import ListingIngestRequest, ListingIngestResponse
from app.services.listing_ingestion import ingest_listing_batch

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post(
    "/listings",
    response_model=ListingIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def ingest_listings(
    payload: ListingIngestRequest,
    db: Session = Depends(get_db),
) -> ListingIngestResponse:
    try:
        result = ingest_listing_batch(
            db=db,
            source_name=payload.source_name,
            items=payload.listings,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return ListingIngestResponse(**result.__dict__)
