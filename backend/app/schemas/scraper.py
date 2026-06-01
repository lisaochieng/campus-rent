from pydantic import BaseModel

from app.schemas.listing import ListingIngestResponse


class ScraperSourceRead(BaseModel):
    key: str
    source_name: str
    description: str
    requires_api_key: bool
    is_configured: bool


class ScraperRunResponse(BaseModel):
    source: ScraperSourceRead
    ingestion: ListingIngestResponse
