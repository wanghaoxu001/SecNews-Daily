from datetime import datetime

from pydantic import BaseModel, field_validator


class TaggingTaskItemResponse(BaseModel):
    id: int
    task_id: int
    row_index: int
    title: str
    summary: str | None = None
    category: str
    reason: str | None = None
    is_important: bool | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaggingTaskResponse(BaseModel):
    id: int
    original_file_name: str
    status: str
    total_count: int
    current_index: int
    labeled_count: int
    imported_at: str | None = None
    created_at: datetime
    updated_at: datetime


class TaggingTaskDetailResponse(BaseModel):
    task: TaggingTaskResponse
    current_item: TaggingTaskItemResponse | None = None
    items: list[TaggingTaskItemResponse]


class CreateTaggingTaskResponse(BaseModel):
    task: TaggingTaskResponse
    current_item: TaggingTaskItemResponse | None = None


class UpdateTaggingTaskCursorRequest(BaseModel):
    current_index: int

    @field_validator("current_index")
    @classmethod
    def validate_current_index(cls, value: int) -> int:
        if value < 0:
            raise ValueError("current_index must be >= 0")
        return value


class UpdateTaggingTaskItemRequest(BaseModel):
    is_important: bool | None = None


class UpdateTaggingTaskResponse(BaseModel):
    task: TaggingTaskResponse
    current_item: TaggingTaskItemResponse | None = None


class UpdateTaggingTaskItemResponse(BaseModel):
    task: TaggingTaskResponse
    item: TaggingTaskItemResponse


class ImportTaggingTaskResponse(BaseModel):
    task: TaggingTaskResponse
    imported_count: int
    skipped_count: int
