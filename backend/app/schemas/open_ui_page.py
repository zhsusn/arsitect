"""Pydantic DTOs for OpenUIPage operations."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class OpenUIPageCreateDTO(BaseModel):
    """Create OpenUI page request."""

    spec_id: str = Field(...)
    container_id: str | None = Field(default=None)
    page_title: str = Field(..., min_length=1, max_length=128)
    html_content: str | None = Field(default=None)
    page_index: int = Field(default=0)
    status: str = Field(default="DRAFT")


class OpenUIPageUpdateDTO(BaseModel):
    """Update OpenUI page request."""

    page_title: str | None = Field(default=None, min_length=1, max_length=128)
    html_content: str | None = Field(default=None)
    page_index: int | None = Field(default=None)
    status: str | None = Field(default=None)


class OpenUIPageResponseDTO(BaseModel):
    """OpenUI page response."""

    page_id: str
    spec_id: str
    project_id: str
    container_id: str | None
    page_title: str
    html_content: str | None
    page_index: int
    status: str
    created_at: datetime | None
    updated_at: datetime | None
