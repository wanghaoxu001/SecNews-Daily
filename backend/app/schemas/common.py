from pydantic import BaseModel
from typing import Generic, TypeVar, Sequence

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20


class PaginatedResponse(BaseModel, Generic[T]):
    items: Sequence[T]
    total: int
    page: int
    page_size: int
