from pydantic import BaseModel, HttpUrl


class ListingSearchResultRead(BaseModel):
    id: str
    title: str
    source_url: HttpUrl
    display_url: str | None = None
    snippet: str | None = None
    monthly_rent: int
    currency_code: str
    price_label: str
    image_url: str | None = None
    source_name: str
    provider: str
    rank: int
