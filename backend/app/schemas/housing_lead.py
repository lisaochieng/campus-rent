from decimal import Decimal

from pydantic import BaseModel


class HousingLeadRead(BaseModel):
    id: str
    name: str
    address: str | None
    latitude: Decimal
    longitude: Decimal
    source_url: str
    website: str | None
    phone: str | None
    email: str | None
    source_name: str
