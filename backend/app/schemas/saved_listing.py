from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.listing import ListingRead


class SavedListingCreate(BaseModel):
    student_email: EmailStr
    listing_id: UUID
    note: str | None = Field(default=None, max_length=500)


class SavedListingUpdate(BaseModel):
    note: str | None = Field(default=None, max_length=500)


class SavedListingRead(BaseModel):
    id: UUID
    student_email: EmailStr
    note: str | None
    created_at: datetime
    listing: ListingRead

    model_config = ConfigDict(from_attributes=True)
