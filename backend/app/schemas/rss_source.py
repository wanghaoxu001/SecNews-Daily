from pydantic import BaseModel
from datetime import datetime


class RssSourceBase(BaseModel):
    name: str
    url: str
    enabled: bool = True
    description: str | None = None


class RssSourceCreate(RssSourceBase):
    pass


class RssSourceUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    enabled: bool | None = None
    description: str | None = None


class RssSourceResponse(RssSourceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
