from pydantic import BaseModel
from datetime import datetime


class ProcessingConfigBase(BaseModel):
    key: str
    value: str
    description: str | None = None


class ProcessingConfigCreate(ProcessingConfigBase):
    pass


class ProcessingConfigUpdate(BaseModel):
    value: str | None = None
    description: str | None = None


class ProcessingConfigResponse(ProcessingConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
