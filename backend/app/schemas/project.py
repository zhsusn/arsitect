"""Project related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreateDTO(BaseModel):
    """DTO for creating a project."""

    project_id: str | None = Field(None, description="Optional project ID")
    project_name: str = Field(..., max_length=64)
    project_description: str | None = Field(None, max_length=256)
    template_level: str = Field(...)


class ProjectUpdateDTO(BaseModel):
    """DTO for updating a project."""

    project_name: str | None = Field(None, max_length=64)
    project_description: str | None = Field(None, max_length=256)


class ProjectResponseDTO(BaseModel):
    """DTO for project response."""

    model_config = ConfigDict(from_attributes=True)

    project_id: str
    project_name: str
    project_description: str | None
    project_status: str
    application_id: str
    template_level: str
    progress_percent: int
    current_stage: str | None
    risk_level: str
    last_activity_at: str | None = None
    last_activity_type: str | None
    size_estimate_id: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RiskAlertDTO(BaseModel):
    """DTO for a risk alert."""

    alert_type: str
    severity: str
    message: str
    project_id: str | None = None
    stage_id: str | None = None


class TimeboxEntryDTO(BaseModel):
    """DTO for a timebox entry."""

    stage_id: str
    stage_name: str
    planned_days: float
    elapsed_days: float
    remaining_days: float
    deviation_percent: float
    alert_level: str | None


class StageProgressDTO(BaseModel):
    """DTO for project stage progress."""

    stage_id: str
    stage_name: str
    order_index: int
    status: str
    execution_status: str
    progress_percent: int = Field(default=0, ge=0, le=100)
    planned_days: float | None = None
    elapsed_days: float | None = None
    skippable: bool = False


class ArtifactSummaryDTO(BaseModel):
    """DTO for artifact summary in project detail."""

    artifact_id: str
    file_name: str
    file_type: str
    stage_id: str | None
    created_at: str | None


class OperationLogItemDTO(BaseModel):
    """DTO for operation log item in project detail."""

    log_id: str
    action: str
    operator_id: str | None
    target_type: str | None
    detail: str | None
    created_at: str | None


class SizeEstimateResultDTO(BaseModel):
    """DTO for size estimate result bound to project."""

    estimate_id: str | None
    module_count: int | None
    interface_count: int | None
    page_count: int | None
    tech_complexity: str | None
    risk_level: str | None
    optimistic_score: int | None
    expected_score: int | None
    conservative_score: int | None
    complexity_level: str | None


class ProjectOverviewDTO(BaseModel):
    """DTO for project overview in detail drawer."""

    project: ProjectResponseDTO
    size_estimate: SizeEstimateResultDTO | None
    stages: list[StageProgressDTO]
    artifacts: list[ArtifactSummaryDTO]
    operation_logs: list[OperationLogItemDTO]


class BindSizeEstimateDTO(BaseModel):
    """DTO for binding size estimate to project."""

    estimate_id: str | None = Field(None, description="规模评估ID，null表示解绑")
