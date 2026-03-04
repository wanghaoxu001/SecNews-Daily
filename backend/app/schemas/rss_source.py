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
    domain: str | None = None
    probe_status: str | None = None
    probe_last_run_at: datetime | None = None
    probe_last_error: str | None = None
    effective_wait_for_chain: list[str] | None = None
    effective_timeouts_ms: list[int] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
