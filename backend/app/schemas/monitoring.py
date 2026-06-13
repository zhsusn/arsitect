"""Pydantic DTOs for monitoring operations."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MonitoringOverviewDTO(BaseModel):
    """Global monitoring overview response."""

    total_projects: int
    active_projects: int
    risk_projects: int
    pending_gates: int
    total_executions: int


class ProjectStatsDTO(BaseModel):
    """Per-project monitoring stats response."""

    stage_count: int
    execution_count: int
    gate_count: int
    log_count: int


class OperationLogDTO(BaseModel):
    """Operation log entry response."""

    log_id: str
    project_id: str
    operator_id: str | None
    action: str
    target_type: str | None
    target_id: str | None
    detail: str | None
    created_at: datetime | None


class OperationLogListDTO(BaseModel):
    """Paginated operation log list response."""

    logs: list[OperationLogDTO]
    total: int
