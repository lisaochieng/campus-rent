from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.listing import ListingRead


class ListingReportCreate(BaseModel):
    listing_id: UUID
    reporter_email: EmailStr
    reason: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=1000)


class ListingReportUpdate(BaseModel):
    status: str = Field(min_length=2, max_length=40)


class ListingReportRead(BaseModel):
    id: UUID
    reporter_email: EmailStr
    reason: str
    description: str | None
    status: str
    created_at: datetime
    listing: ListingRead

    model_config = ConfigDict(from_attributes=True)
