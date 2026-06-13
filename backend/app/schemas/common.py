"""Common Pydantic schemas shared across API endpoints."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Problem(BaseModel):
    """RFC 7807 Problem Details for HTTP APIs."""

    type: str = Field(description="问题类型 URI")
    title: str = Field(description="简短可读标题")
    status: int = Field(description="HTTP 状态码")
    detail: str | None = Field(default=None, description="详细描述")
    instance: str | None = Field(default=None, description="问题发生实例 URI")


class PageResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    data: Sequence[T] = Field(description="当前页数据")
    total_count: int = Field(ge=0, description="总记录数")
    page: int = Field(ge=1, description="当前页码")
    page_size: int = Field(ge=1, description="每页条数")
    total_pages: int = Field(ge=0, description="总页数")
    has_next: bool = Field(description="是否有下一页")
    has_previous: bool = Field(description="是否有上一页")


class FileUploadResult(BaseModel):
    """Result of a file upload operation."""

    file_id: str = Field(description="文件唯一标识")
    file_name: str = Field(description="原始文件名")
    file_url: str = Field(description="文件访问 URL")
    file_size_bytes: int | None = Field(default=None, description="文件大小（字节）")
    mime_type: str = Field(description="MIME 类型")
    uploaded_at: datetime = Field(description="上传时间")
    expires_at: datetime | None = Field(default=None, description="过期时间")
