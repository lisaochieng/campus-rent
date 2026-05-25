from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SchoolRead(BaseModel):
    id: UUID
    name: str
    city: str
    state: str
    country: str
    latitude: Decimal
    longitude: Decimal

    model_config = ConfigDict(from_attributes=True)


class SchoolSearchResult(SchoolRead):
    acronym: str


class SchoolCreate(BaseModel):
    name: str = Field(max_length=255)
    city: str = Field(max_length=120)
    state: str = Field(max_length=80)
    country: str = Field(max_length=80)
    latitude: Decimal
    longitude: Decimal
