from decimal import Decimal

from pydantic import BaseModel


class BedroomRentSummary(BaseModel):
    bedrooms: Decimal | None
    listing_count: int
    average_rent: int
    min_rent: int
    max_rent: int


class MarketSummary(BaseModel):
    school_name: str
    city: str
    state: str
    listing_count: int
    safe_listing_count: int
    average_rent: int | None
    min_rent: int | None
    max_rent: int | None
    average_distance_miles: float | None
    bedroom_summaries: list[BedroomRentSummary]
    budget_hint: str
