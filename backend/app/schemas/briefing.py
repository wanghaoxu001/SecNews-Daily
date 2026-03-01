from pydantic import BaseModel
from datetime import datetime, date


class BriefingItemBase(BaseModel):
    title: str
    summary: str | None = None
    category: str | None = None
    sort_order: int = 0


class BriefingItemCreate(BriefingItemBase):
    news_id: int | None = None


class BriefingItemUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    category: str | None = None
    sort_order: int | None = None


class BriefingItemResponse(BriefingItemBase):
    id: int
    briefing_id: int
    news_id: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BriefingBase(BaseModel):
    title: str
    date: date


class BriefingCreate(BaseModel):
    title: str
    date: date
    news_ids: list[int] = []


class BriefingUpdate(BaseModel):
    title: str | None = None
    status: str | None = None


class BriefingResponse(BriefingBase):
    id: int
    status: str
    items: list[BriefingItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BriefingListResponse(BaseModel):
    id: int
    title: str
    date: date
    status: str
    item_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}
