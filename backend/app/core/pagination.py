"""Pagination DTOs and utilities."""

from __future__ import annotations

from collections.abc import Sequence
from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")


class PageRequest(BaseModel):
    """Paginated query parameters."""

    page: int = Field(default=1, ge=1, description="页码，从1开始")
    page_size: int = Field(default=50, ge=1, le=200, description="每页条数")
    sort_by: str | None = Field(default=None, description="排序字段")
    sort_order: str = Field(default="desc", pattern=r"^(asc|desc)$", description="排序方向")

    @field_validator("page", mode="before")
    @classmethod
    def _coerce_page(cls, v: int | None) -> int:
        """Coerce missing or invalid page to 1."""
        if v is None or not isinstance(v, int):
            return 1
        return max(1, v)

    @field_validator("page_size", mode="before")
    @classmethod
    def _coerce_page_size(cls, v: int | None) -> int:
        """Coerce missing or invalid page_size to 50, cap at 200."""
        if v is None or not isinstance(v, int):
            return 50
        if v < 1:
            return 1
        if v > 200:
            return 200
        return v

    @property
    def offset(self) -> int:
        """Calculate SQL OFFSET."""
        return (self.page - 1) * self.page_size


class PageResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    data: Sequence[T] = Field(description="当前页数据")
    total_count: int = Field(ge=0, description="总记录数")
    page: int = Field(ge=1, description="当前页码")
    page_size: int = Field(ge=1, description="每页条数")
    total_pages: int = Field(ge=0, description="总页数")
    has_next: bool = Field(description="是否有下一页")
    has_previous: bool = Field(description="是否有上一页")

    @classmethod
    def from_items(
        cls,
        items: Sequence[T],
        *,
        total_count: int,
        page: int,
        page_size: int,
    ) -> PageResponse[T]:
        """Build a PageResponse from a slice of items and total count."""
        total_pages = ceil(total_count / page_size) if page_size > 0 else 0
        return cls(
            data=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )
