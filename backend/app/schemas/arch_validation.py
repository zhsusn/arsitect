"""Pydantic DTOs for arch validation operations."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ArchValidationTriggerDTO(BaseModel):
    """Trigger arch validation request."""

    level: str = Field(..., pattern=r"^(L1|L2|L3|L4)$")


class ArchValidationDiffDTO(BaseModel):
    """Arch validation diff response."""

    session_id: str
    project_id: str
    level: str
    diff_summary: str | None
    status: str
    created_at: datetime | None
    baseline_dsl: str | None = None
    current_dsl: str | None = None


class ArchValidationBaselineUpdateDTO(BaseModel):
    """Update baseline request."""

    level: str = Field(..., pattern=r"^(L1|L2|L3|L4)$")
