"""Gate decision Pydantic schemas."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GateDecisionResponseDTO(BaseModel):
    """DTO for gate decision response."""

    model_config = ConfigDict(from_attributes=True)

    decision_id: str
    gate_id: str
    project_id: str
    gate_type: str
    status: str
    confidence: str | None
    decision_type: str | None
    decision_by: str | None
    decision_at: datetime | None
    duration_sec: int | None
    reason: str | None
    unlocked_stages: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("unlocked_stages", mode="before")
    @classmethod
    def _parse_json(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            parsed = json.loads(v)
            if isinstance(parsed, list):
                return parsed
            return []
        if v is None:
            return []
        if isinstance(v, list):
            return v
        return []


class GateRejectRequestDTO(BaseModel):
    """DTO for rejecting a gate decision."""

    reason: str


class GateSelfCheckResponseDTO(BaseModel):
    """DTO for gate self-check summary."""

    confidence: str
    artifact_integrity: str
    quality_gate: str
    risk_level: str
    artifact_count: int
    required_artifacts: int
