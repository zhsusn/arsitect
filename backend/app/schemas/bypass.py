"""Pydantic DTOs for bypass operations."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class BypassApplyDTO(BaseModel):
    """Apply for bypass request."""

    plan_id: str | None = None
    stage_id: str
    skill_id: str
    triggered_by: str
    reason: str = Field(..., min_length=5, max_length=500)
    authorizer_token: str
    deadline_hours: int = 24


class BypassResponseDTO(BaseModel):
    """Bypass record response."""

    record_id: str
    gate_decision_id: str | None = None
    plan_id: str
    stage_id: str
    skill_id: str
    triggered_by: str
    reason: str | None
    status: str
    deadline_at: datetime | None
    closed_at: datetime | None
    created_at: datetime | None


class BypassApproveDTO(BaseModel):
    """Approve bypass request."""

    approved_by: str
