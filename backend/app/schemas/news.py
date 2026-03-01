from pydantic import BaseModel
from datetime import datetime


class NewsBase(BaseModel):
    title: str
    url: str


class NewsResponse(BaseModel):
    id: int
    title: str
    url: str
    summary: str | None = None
    content: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    source_id: int | None = None
    source_name: str | None = None
    title_zh: str | None = None
    summary_zh: str | None = None
    category: str | None = None
    process_status: str
    process_error: str | None = None
    is_similar: bool = False
    similar_to_id: int | None = None
    similarity_details: dict | None = None
    is_important: bool | None = None
    importance_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NewsListResponse(BaseModel):
    items: list[NewsResponse]
    total: int
    page: int
    page_size: int
