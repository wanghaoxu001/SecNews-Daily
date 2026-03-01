from pydantic import BaseModel
from datetime import datetime


class LlmConfigBase(BaseModel):
    task_type: str
    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None


class LlmConfigCreate(LlmConfigBase):
    pass


class LlmConfigUpdate(BaseModel):
    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None


class LlmConfigResponse(LlmConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
