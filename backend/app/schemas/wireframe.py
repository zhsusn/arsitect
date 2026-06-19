"""Pydantic DTOs for Wireframe operations."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class WireframeCreateDTO(BaseModel):
    """Create wireframe session request."""

    name: str = Field(..., min_length=1, max_length=128)
    c4_baseline_version: str | None = Field(default=None)
    status: str = Field(default="DRAFT")


class WireframeUpdateDTO(BaseModel):
    """Update wireframe session request."""

    name: str | None = Field(default=None, min_length=1, max_length=128)
    c4_baseline_version: str | None = Field(default=None)
    pipeline_stage: str | None = Field(default=None)
    page_count: int | None = Field(default=None, ge=0)
    avg_confidence: int | None = Field(default=None, ge=0, le=100)
    status: str | None = Field(default=None, pattern=r"^(DRAFT|ACTIVE|ARCHIVED)$")


class WireframeResponseDTO(BaseModel):
    """Wireframe session response."""

    wireframe_id: str
    project_id: str
    name: str
    c4_baseline_version: str | None
    pipeline_stage: str
    page_count: int | None
    avg_confidence: int | None
    status: str
    created_at: datetime | None
    updated_at: datetime | None


class WireframeGenerateDTO(BaseModel):
    """Trigger wireframe generation from C4 DSL."""

    c4_baseline_version: str | None = Field(
        default=None, description="指定 C4 Baseline 版本，为空则使用当前版本"
    )
