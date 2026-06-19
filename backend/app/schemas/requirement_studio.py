"""Requirement Studio Pydantic schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StageStatusItem(BaseModel):
    """Status item for a single stage in the requirement studio."""

    stage_id: str = Field(description="业务阶段标识")
    stage_name: str = Field(description="阶段名称")
    status: str = Field(description="UI 状态: locked | not_started | in_progress | review_pending | passed")
    progress: int = Field(description="进度百分比 0-100")
    can_enter: bool = Field(description="是否可进入该阶段")


class RequirementStudioStatusResponse(BaseModel):
    """Response for GET /{project_id}/status."""

    project_id: str
    current_stage: str
    stages: list[StageStatusItem]


class StageTaskItem(BaseModel):
    """Task-like item derived from a StageSkillBinding."""

    task_id: str
    task_name: str
    task_type: str
    status: str
    skill_id: str
    output_artifact: str | None = None


class StageTasksResponse(BaseModel):
    """Response for GET /{project_id}/stage/{stage_id}/tasks."""

    stage_id: str
    tasks: list[StageTaskItem]


class StageExecuteRequest(BaseModel):
    """Request for POST /{project_id}/stage/{stage_id}/execute."""

    skill_id: str | None = Field(default=None, max_length=36)
    context: dict[str, Any] | None = Field(default=None)
    reference_materials: list[str] | None = Field(default=None)


class StageExecuteResponse(BaseModel):
    """Response for stage execution trigger."""

    execution_id: str
    status: str


class StageReviewRequest(BaseModel):
    """Request for POST /{project_id}/stage/{stage_id}/review."""

    comments: list[str] | None = Field(default=None)
    suggestions: list[str] | None = Field(default=None)
    action: str = Field(..., description="pass | regenerate")


class StageReviewResponse(BaseModel):
    """Response for stage review submission."""

    stage_id: str
    status: str
    next_stage_id: str | None = None


class ArtifactFileItem(BaseModel):
    """Artifact file summary within a stage group."""

    artifact_id: str
    file_name: str
    version: str
    status: str


class StageArtifactGroup(BaseModel):
    """Artifacts grouped by stage."""

    stage_id: str
    stage_name: str
    files: list[ArtifactFileItem]


class ArtifactsResponse(BaseModel):
    """Response for GET /{project_id}/artifacts."""

    artifacts: list[StageArtifactGroup]


class ArtifactVersionItem(BaseModel):
    """Artifact version snapshot."""

    version: str
    created_at: str


class ArtifactContentResponse(BaseModel):
    """Response for GET /{project_id}/artifacts/{artifact_id}."""

    content: str
    versions: list[ArtifactVersionItem]


class ArtifactEditRequest(BaseModel):
    """Request for POST /{project_id}/artifacts/{artifact_id}/edit."""

    content: str
    version: str | None = Field(default=None)


class ArtifactEditResponse(BaseModel):
    """Response for artifact edit."""

    artifact_id: str
    version: str
    has_conflict: bool


class BaselineRequest(BaseModel):
    """Request for POST /{project_id}/governance/baseline."""

    artifact_ids: list[str]
    description: str | None = Field(default=None)


class BaselineResponse(BaseModel):
    """Response for baseline creation."""

    baseline_id: str
    version: str
    created_at: str


class StaleImpactItem(BaseModel):
    """Impact chain item for a stale artifact."""

    type: str
    target: str
    suggestion: str


class StaleArtifactItem(BaseModel):
    """Stale artifact detail."""

    artifact_id: str
    artifact_name: str
    version: str
    impact: list[StaleImpactItem]


class StaleAnalysisResponse(BaseModel):
    """Response for GET /{project_id}/governance/stale-analysis."""

    stale_artifacts: list[StaleArtifactItem]


class ChangeRequestRequest(BaseModel):
    """Request for POST /{project_id}/governance/change-request."""

    target_artifact_id: str
    change_type: str
    reason: str


class ChangeRequestResponse(BaseModel):
    """Response for change request creation."""

    change_request_id: str
    status: str
