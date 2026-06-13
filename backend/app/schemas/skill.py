"""Skill and DAG related Pydantic schemas."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class SkillResponseDTO(BaseModel):
    """Response model for Skill data."""

    model_config = {"from_attributes": True}

    skill_id: str | None = None
    skill_name: str
    version: str
    pattern: str
    tags: list[str] | None = None
    platforms: list[str] | None = None
    description: str | None = None
    directory_path: str
    parse_status: str = "PARSED"

    @field_validator("tags", "platforms", mode="before")
    @classmethod
    def _parse_json_text(cls, v: Any) -> list[str] | None:
        if isinstance(v, str):
            data = json.loads(v)
            if isinstance(data, list):
                return [str(item) for item in data]
            return None
        if isinstance(v, list):
            return v
        return None


class SkillListResponseDTO(BaseModel):
    """Response model for skill list."""

    data: list[SkillResponseDTO]
    total_count: int


class SkillScanRequestDTO(BaseModel):
    """Request to scan a directory for skills."""

    directory_path: str = Field(..., max_length=4096)


class SkillScanResultItemDTO(BaseModel):
    """A single parsed skill in scan result."""

    skill_name: str
    version: str
    pattern: str
    tags: list[str]
    platforms: list[str]
    description: str
    directory_path: str
    parse_status: str = "PARSED"
    parse_error_reason: str | None = None


class SkillConflictItemDTO(BaseModel):
    """A single conflict in scan result."""

    new_skill: SkillScanResultItemDTO
    existing_skill: SkillResponseDTO | None = None


class SkillScanResultDTO(BaseModel):
    """Result of scanning a directory."""

    parsed_skills: list[SkillScanResultItemDTO]
    conflicts: list[SkillConflictItemDTO]
    errors: list[str]


class ConflictResolutionItemDTO(BaseModel):
    """Resolution decision for a single conflict."""

    skill_name: str
    action: str  # overwrite | skip | rename
    new_name: str | None = None


class SkillImportConfirmDTO(BaseModel):
    """Request to confirm skill import."""

    skills_to_import: list[SkillScanResultItemDTO]
    resolutions: list[ConflictResolutionItemDTO] | None = None


class SkillImportSummaryDTO(BaseModel):
    """Summary after importing skills."""

    imported: int
    skipped: int
    errors: list[str]


class SkillExecutionHistoryDTO(BaseModel):
    """DTO for skill execution history."""

    model_config = {"from_attributes": True}

    execution_id: str
    stage_id: str
    skill_name: str
    trigger_action: str
    overall_status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class BoundStageDTO(BaseModel):
    """DTO for a stage bound to a skill."""

    stage_id: str
    stage_name: str
    template_id: str | None = None
    binding_type: str  # primary | auxiliary


class DAGNodeDTO(BaseModel):
    """DTO for a DAG node."""

    model_config = {"from_attributes": True}

    node_id: str
    skill_id: str
    position_x: float = 0.0
    position_y: float = 0.0


class DAGEdgeDTO(BaseModel):
    """DTO for a DAG edge."""

    model_config = {"from_attributes": True}

    edge_id: str
    source_node_id: str
    target_node_id: str
    confidence: int = 100
    is_auto_parsed: bool = False


class DAGSnapshotDTO(BaseModel):
    """Full DAG snapshot."""

    nodes: list[DAGNodeDTO]
    edges: list[DAGEdgeDTO]


class DAGChangeLogDTO(BaseModel):
    """DTO for DAG change log."""

    model_config = {"from_attributes": True}

    log_id: str
    session_id: str
    operation_type: str
    target_id: str
    before_snapshot: str | None = None
    after_snapshot: str | None = None


class AddDAGNodeRequestDTO(BaseModel):
    """Request to add a DAG node."""

    node_id: str
    skill_id: str
    position_x: float = 0.0
    position_y: float = 0.0


class AddDAGEdgeRequestDTO(BaseModel):
    """Request to add a DAG edge."""

    edge_id: str
    source_node_id: str
    target_node_id: str


class DAGUndoRedoRequestDTO(BaseModel):
    """Request to undo/redo DAG operation."""

    session_id: str
