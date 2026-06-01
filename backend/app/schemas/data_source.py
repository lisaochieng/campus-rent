from pydantic import BaseModel


class DataSourceRead(BaseModel):
    key: str
    source_name: str
    description: str
    requires_api_key: bool
    is_configured: bool
    coverage: str
