from pydantic import BaseModel
from datetime import datetime


class ImportanceExampleBase(BaseModel):
    title: str
    summary: str | None = None
    category: str
    is_important: bool
    reason: str | None = None


class ImportanceExampleCreate(ImportanceExampleBase):
    pass


class ImportanceExampleUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    category: str | None = None
    is_important: bool | None = None
    reason: str | None = None


class ImportanceExampleResponse(ImportanceExampleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
