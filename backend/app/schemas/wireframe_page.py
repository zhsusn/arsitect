"""Pydantic DTOs for WireframePage operations."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class WireframePageCreateDTO(BaseModel):
    """Create wireframe page request."""

    wireframe_id: str = Field(...)
    entity_id: str | None = Field(default=None)
    entity_name: str | None = Field(default=None)
    page_name: str = Field(..., min_length=1, max_length=128)
    page_type: str = Field(default="UNKNOWN")
    confidence: int | None = Field(default=None, ge=0, le=100)
    mapping_source: str = Field(default="auto")
    svg_content: str | None = Field(default=None)
    layout_json: str | None = Field(default=None)
    status: str = Field(default="PENDING_MAPPING")
    sort_order: int = Field(default=0)


class WireframePageUpdateDTO(BaseModel):
    """Update wireframe page request."""

    page_name: str | None = Field(default=None, min_length=1, max_length=128)
    page_type: str | None = Field(default=None)
    confidence: int | None = Field(default=None, ge=0, le=100)
    mapping_source: str | None = Field(default=None)
    svg_content: str | None = Field(default=None)
    layout_json: str | None = Field(default=None)
    status: str | None = Field(default=None)
    sort_order: int | None = Field(default=None)


class WireframePageResponseDTO(BaseModel):
    """Wireframe page response."""

    page_id: str
    wireframe_id: str
    project_id: str
    entity_id: str | None
    entity_name: str | None
    page_name: str
    page_type: str
    confidence: int | None
    mapping_source: str
    svg_content: str | None
    layout_json: str | None
    status: str
    sort_order: int
    created_at: datetime | None
    updated_at: datetime | None
