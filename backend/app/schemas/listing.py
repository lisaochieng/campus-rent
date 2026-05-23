from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import ListingStatus


class ListingSourceRead(BaseModel):
    id: UUID
    name: str
    trust_level: str

    model_config = ConfigDict(from_attributes=True)


class ListingRead(BaseModel):
    id: UUID
    source_url: str
    title: str
    description: str | None
    address: str | None
    city: str
    state: str
    postal_code: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    monthly_rent: int
    bedrooms: Decimal | None
    bathrooms: Decimal | None
    square_feet: int | None
    status: ListingStatus
    first_seen_at: datetime
    last_seen_at: datetime
    source: ListingSourceRead

    model_config = ConfigDict(from_attributes=True)


class ScamSignalRead(BaseModel):
    signal_type: str
    severity: int
    explanation: str

    model_config = ConfigDict(from_attributes=True)


class ListingScoreRead(BaseModel):
    school_id: UUID
    distance_miles: Decimal | None
    affordability_score: int
    distance_score: int
    freshness_score: int
    scam_risk_score: int
    campus_rent_score: int
    score_details: dict | None

    model_config = ConfigDict(from_attributes=True)


class ListingDetailRead(ListingRead):
    scam_signals: list[ScamSignalRead]
    scores: list[ListingScoreRead]


class ListingSearchResult(BaseModel):
    listing: ListingRead
    distance_miles: float
    distance_score: int
    affordability_score: int
    freshness_score: int
    scam_safety_score: int
    scam_signals: list[ScamSignalRead]
    campus_rent_score: int


class ListingFilterOptions(BaseModel):
    school_name: str
    city: str
    state: str
    total_listings: int
    safe_listings: int
    min_rent: int | None
    max_rent: int | None
    bedroom_options: list[Decimal]
    city_options: list[str]
    suggested_max_distance_miles: list[float]


class ListingCompareRequest(BaseModel):
    school_name: str = Field(min_length=2, max_length=255)
    listing_ids: list[UUID] = Field(min_length=2, max_length=5)
    max_rent: int | None = Field(default=None, gt=0)


class ListingComparison(BaseModel):
    listing: ListingRead
    distance_miles: float
    monthly_rent: int
    rent_delta_from_budget: int | None
    scam_safety_score: int
    campus_rent_score: int
    strengths: list[str]
    tradeoffs: list[str]


class ListingCompareResponse(BaseModel):
    school_name: str
    comparisons: list[ListingComparison]


class ListingCreate(BaseModel):
    source_name: str = Field(default="Manual Verified Dataset", max_length=120)
    source_listing_id: str | None = Field(default=None, max_length=255)
    source_url: str = Field(max_length=1000)
    title: str = Field(max_length=300)
    description: str | None = None
    address: str | None = Field(default=None, max_length=500)
    city: str = Field(max_length=120)
    state: str = Field(max_length=80)
    postal_code: str | None = Field(default=None, max_length=20)
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    monthly_rent: int = Field(gt=0)
    bedrooms: Decimal | None = Field(default=None, ge=0)
    bathrooms: Decimal | None = Field(default=None, ge=0)
    square_feet: int | None = Field(default=None, gt=0)


class ListingIngestItem(BaseModel):
    source_listing_id: str | None = Field(default=None, max_length=255)
    source_url: str = Field(max_length=1000)
    title: str = Field(max_length=300)
    description: str | None = None
    address: str | None = Field(default=None, max_length=500)
    city: str = Field(max_length=120)
    state: str = Field(max_length=80)
    postal_code: str | None = Field(default=None, max_length=20)
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    monthly_rent: int = Field(gt=0)
    bedrooms: Decimal | None = Field(default=None, ge=0)
    bathrooms: Decimal | None = Field(default=None, ge=0)
    square_feet: int | None = Field(default=None, gt=0)


class ListingIngestRequest(BaseModel):
    source_name: str = Field(max_length=120)
    listings: list[ListingIngestItem] = Field(min_length=1, max_length=100)


class ListingIngestResponse(BaseModel):
    source_name: str
    received: int
    created: int
    updated: int
    skipped: int
    indexed: int
    cache_keys_cleared: int
    listing_ids: list[UUID]
    skipped_reasons: list[str]
