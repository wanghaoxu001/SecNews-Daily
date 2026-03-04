from pydantic import BaseModel, field_validator
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
    crawl_error_code: str | None = None
    crawl_error_detail: str | None = None
    crawl_attempts: int | None = None
    crawl_last_duration_ms: int | None = None
    crawl_last_attempt_at: datetime | None = None
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


class BatchReprocessRequest(BaseModel):
    news_ids: list[int]
    target_status: str

    @field_validator("target_status")
    @classmethod
    def validate_target_status(cls, v: str) -> str:
        allowed = {"pending", "processed", "similarity_checked"}
        if v not in allowed:
            raise ValueError(f"target_status must be one of {allowed}")
        return v

    @field_validator("news_ids")
    @classmethod
    def validate_news_ids(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("news_ids must not be empty")
        if len(v) > 500:
            raise ValueError("news_ids must not exceed 500")
        return v


class BatchReprocessResponse(BaseModel):
    reset_count: int
    pipeline_result: dict | None = None


class BatchDeleteRequest(BaseModel):
    news_ids: list[int]

    @field_validator("news_ids")
    @classmethod
    def validate_news_ids(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("news_ids must not be empty")
        if len(v) > 500:
            raise ValueError("news_ids must not exceed 500")
        return v


class BatchDeleteResponse(BaseModel):
    deleted_count: int
