from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SchoolRead(BaseModel):
    id: UUID
    name: str
    city: str
    state: str
    country: str
    latitude: Decimal
    longitude: Decimal

    model_config = ConfigDict(from_attributes=True)
