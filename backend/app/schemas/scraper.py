from pydantic import BaseModel

from app.schemas.listing import ListingIngestResponse


class ScraperSourceRead(BaseModel):
    key: str
    source_name: str
    description: str


class ScraperRunResponse(BaseModel):
    source: ScraperSourceRead
    ingestion: ListingIngestResponse
