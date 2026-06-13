"""Pydantic DTOs for SketchPage operations."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SketchPageCreateDTO(BaseModel):
    """Create sketch page request."""

    story_id: str | None = Field(default=None)
    page_name: str = Field(..., min_length=1, max_length=128)
    page_type: str = Field(default="UNKNOWN")
    svg_content: str | None = Field(default=None)
    fields_json: str | None = Field(default=None)
    buttons_json: str | None = Field(default=None)
    nav_targets_json: str | None = Field(default=None)
    source_module_id: str | None = Field(default=None)
    source_md_path: str | None = Field(default=None)
    status: str = Field(default="DRAFT")
    sort_order: int = Field(default=0)


class SketchPageUpdateDTO(BaseModel):
    """Update sketch page request."""

    page_name: str | None = Field(default=None, min_length=1, max_length=128)
    page_type: str | None = Field(default=None)
    svg_content: str | None = Field(default=None)
    fields_json: str | None = Field(default=None)
    buttons_json: str | None = Field(default=None)
    nav_targets_json: str | None = Field(default=None)
    source_module_id: str | None = Field(default=None)
    source_md_path: str | None = Field(default=None)
    status: str | None = Field(
        default=None,
        pattern=r"^(DRAFT|GENERATED|REVIEW_PENDING|APPROVED|REJECTED)$",
    )
    sort_order: int | None = Field(default=None)


class SketchPageResponseDTO(BaseModel):
    """Sketch page response."""

    page_id: str
    project_id: str
    story_id: str | None
    page_name: str
    page_type: str
    svg_content: str | None
    fields_json: str | None
    buttons_json: str | None
    nav_targets_json: str | None
    source_module_id: str | None
    source_md_path: str | None
    status: str
    sort_order: int
    created_at: datetime | None
    updated_at: datetime | None
