"""Pydantic DTOs for advanced enterprise endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# HistoryViewer
# ---------------------------------------------------------------------------
class TimelineStageDTO(BaseModel):
    """Aggregated timeline stage."""

    name: str
    skill_count: int
    total_duration_ms: int
    avg_duration_ms: float
    success_rate: float
    start: datetime | None = None
    end: datetime | None = None


class ProjectTimelineDTO(BaseModel):
    """Project timeline response."""

    project_id: str
    project_name: str
    stages: list[TimelineStageDTO]
    total_duration_ms: int


class HeatmapCellDTO(BaseModel):
    """Single rework heatmap cell."""

    skill_id: str
    skill_name: str
    phase: str
    retry_count: int
    intensity: float


class CompletedProjectDTO(BaseModel):
    """Completed project summary."""

    id: str
    name: str
    completed_at: str | None = None


class HistorySummaryDTO(BaseModel):
    """Application history summary."""

    total_projects: int
    completed_projects: int
    rework_count: int


# ---------------------------------------------------------------------------
# PermissionManager
# ---------------------------------------------------------------------------
class AssignRoleDTO(BaseModel):
    """Assign role request."""

    user_id: str
    role: str


class ProjectMemberDTO(BaseModel):
    """Project member response."""

    user_id: str
    project_id: str
    role: str


class PermissionCheckDTO(BaseModel):
    """Permission check request/response."""

    user_id: str
    permission: str
    allowed: bool


# ---------------------------------------------------------------------------
# PrototypeArchBinder
# ---------------------------------------------------------------------------
class ProtoInterfaceDTO(BaseModel):
    """Prototype interface input."""

    path: str
    method: str
    source_page: str | None = None
    source_type: str | None = None


class InterfaceGapDTO(BaseModel):
    """Interface gap result."""

    contract_id: str
    endpoint_path: str
    method: str
    gap_type: str
    suggestion: str
    source_page: str | None = None
    source_type: str | None = None


class GapWritebackResultDTO(BaseModel):
    """Gap writeback result."""

    created_count: int
    contracts: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# DriftDetector
# ---------------------------------------------------------------------------
class DriftRequestDTO(BaseModel):
    """Drift detection request."""

    code_dir: str


class DriftReportDTO(BaseModel):
    """Drift detection report."""

    project_id: str
    checked_at: str
    additions: list[dict[str, Any]]
    deletions: list[dict[str, Any]]
    modifications: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# MetricsCollector
# ---------------------------------------------------------------------------
class SkillMetricsDTO(BaseModel):
    """Skill metrics response."""

    skill_id: str
    project_id: str
    execution_count: int
    total_duration_ms: int
    avg_duration_ms: float
    success_count: int
    fail_count: int
    retry_count: int
    avg_gate_wait_ms: int


class ProjectMetricsDTO(BaseModel):
    """Project metrics response."""

    project_id: str
    execution_count: int
    success_count: int
    fail_count: int
    retry_count: int
    success_rate: float


# ---------------------------------------------------------------------------
# SearchEngine
# ---------------------------------------------------------------------------
class SearchResultDTO(BaseModel):
    """Search result item."""

    type: str
    id: str
    title: str
    preview: str
    path: str
    score: float


# ---------------------------------------------------------------------------
# NotificationManager
# ---------------------------------------------------------------------------
class NotificationDTO(BaseModel):
    """Notification item."""

    id: str
    type: str
    title: str
    message: str
    project_id: str
    channels: list[str]
    created_at: datetime
    read: bool


# ---------------------------------------------------------------------------
# ImportExportManager
# ---------------------------------------------------------------------------
class ExportManifestDTO(BaseModel):
    """Export manifest."""

    version: str
    exported_at: str
    project_id: str
    project_name: str
    includes: list[str]
