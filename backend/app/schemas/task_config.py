from pydantic import BaseModel
from datetime import datetime


class TaskConfigBase(BaseModel):
    name: str
    cron_expression: str
    enabled: bool = True
    description: str | None = None


class TaskConfigCreate(TaskConfigBase):
    pass


class TaskConfigUpdate(BaseModel):
    cron_expression: str | None = None
    enabled: bool | None = None
    description: str | None = None


class TaskConfigResponse(TaskConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
