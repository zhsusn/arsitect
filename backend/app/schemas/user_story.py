"""Pydantic DTOs for UserStory operations."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UserStoryCreateDTO(BaseModel):
    """Create user story request."""

    title: str = Field(..., min_length=1, max_length=256)
    description: str | None = Field(default=None)
    acceptance_criteria: str | None = Field(default=None)
    page_desc: str | None = Field(default=None, description="页面描述段落，用于草图生成")
    priority: str = Field(default="P1")
    status: str = Field(default="DRAFT")


class UserStoryUpdateDTO(BaseModel):
    """Update user story request."""

    title: str | None = Field(default=None, min_length=1, max_length=256)
    description: str | None = Field(default=None)
    acceptance_criteria: str | None = Field(default=None)
    page_desc: str | None = Field(default=None)
    priority: str | None = Field(default=None, pattern=r"^(P0|P1|P2|P3)$")
    status: str | None = Field(default=None, pattern=r"^(DRAFT|ACTIVE|ARCHIVED)$")


class UserStoryResponseDTO(BaseModel):
    """User story response."""

    story_id: str
    project_id: str
    title: str
    description: str | None
    acceptance_criteria: str | None
    page_desc: str | None
    priority: str
    status: str
    created_at: datetime | None
    updated_at: datetime | None


class UserStoryImportResultDTO(BaseModel):
    """Result of importing user stories from requirements."""

    imported_count: int
    skipped_count: int
    stories: list[dict[str, str]]
