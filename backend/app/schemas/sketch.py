"""Pydantic DTOs for Sketch operations."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SketchCreateDTO(BaseModel):
    """Create sketch session request."""

    name: str = Field(..., min_length=1, max_length=128)
    source_story_ids: str | None = Field(default=None)
    validation_report: str | None = Field(default=None)
    status: str = Field(default="DRAFT")


class SketchUpdateDTO(BaseModel):
    """Update sketch session request."""

    name: str | None = Field(default=None, min_length=1, max_length=128)
    source_story_ids: str | None = Field(default=None)
    page_count: int | None = Field(default=None, ge=0)
    coverage_percent: int | None = Field(default=None, ge=0, le=100)
    validation_report: str | None = Field(default=None)
    status: str | None = Field(
        default=None, pattern=r"^(DRAFT|GENERATING|GENERATED|REVIEW_PENDING|APPROVED|REJECTED|ARCHIVED)$"
    )


class SketchResponseDTO(BaseModel):
    """Sketch session response."""

    sketch_id: str
    project_id: str
    name: str
    source_story_ids: str | None
    page_count: int | None
    coverage_percent: int | None
    validation_report: str | None
    status: str
    created_at: datetime | None
    updated_at: datetime | None


class SketchGenerateDTO(BaseModel):
    """Trigger sketch generation from user stories."""

    story_ids: list[str] | None = Field(
        default=None, description="指定用户故事 ID 列表，为空则使用项目全部含 page_desc 的故事"
    )


class SketchGenerateFromRequirementsDTO(BaseModel):
    """Trigger sketch generation from detailed requirements."""

    story_ids: list[str] | None = Field(
        default=None, description="可选：指定用户故事 ID 用于路径验证"
    )
