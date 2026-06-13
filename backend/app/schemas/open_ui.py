"""Pydantic DTOs for OpenUISpec operations."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class OpenUICreateDTO(BaseModel):
    """Create OpenUI spec request."""

    spec_name: str = Field(..., min_length=1, max_length=128)
    status: str = Field(default="DRAFT")


class OpenUIUpdateDTO(BaseModel):
    """Update OpenUI spec request."""

    spec_name: str | None = Field(default=None, min_length=1, max_length=128)
    prompt_text: str | None = Field(default=None)
    page_count: int | None = Field(default=None, ge=0)
    page_titles_json: str | None = Field(default=None)
    service_status: str | None = Field(default=None)
    generation_duration_ms: int | None = Field(default=None)
    content_hash: str | None = Field(default=None)
    status: str | None = Field(
        default=None,
        pattern=r"^(DRAFT|GENERATING|GENERATED|RENDERING|FALLBACK|ARCHIVED)$",
    )


class OpenUIResponseDTO(BaseModel):
    """OpenUI spec response."""

    spec_id: str
    project_id: str
    spec_name: str
    prompt_text: str | None
    page_count: int | None
    page_titles_json: str | None
    service_status: str
    generation_duration_ms: int | None
    content_hash: str | None
    status: str
    created_at: datetime | None
    updated_at: datetime | None


class OpenUIGenerateDTO(BaseModel):
    """Trigger OpenUI prototype generation."""

    c4_baseline_version: str | None = Field(
        default=None, description="指定 C4 Baseline 版本，为空则使用当前版本"
    )


class OpenUIHealthResponseDTO(BaseModel):
    """OpenUI service health check response."""

    status: str
    available: bool
