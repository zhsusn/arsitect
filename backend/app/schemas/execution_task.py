"""ExecutionTask Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskCreateDTO(BaseModel):
    """DTO for creating an execution task."""

    name: str = Field(..., max_length=128)
    type: str = Field(default="coding", max_length=16)
    input_artifacts: list[str] | None = Field(default=None)
    assigned_skill_id: str | None = Field(default=None, max_length=36)
    parent_module: str | None = Field(default=None, max_length=64)
    output_artifact_path: str | None = Field(default=None)


class TaskUpdateDTO(BaseModel):
    """DTO for updating an execution task."""

    name: str | None = Field(default=None, max_length=128)
    status: str | None = Field(default=None, max_length=16)
    input_artifacts: list[str] | None = Field(default=None)
    assigned_skill_id: str | None = Field(default=None, max_length=36)
    parent_module: str | None = Field(default=None, max_length=64)
    output_artifact_path: str | None = Field(default=None)
    retry_count: int | None = Field(default=None, ge=0, le=3)


class TaskResponseDTO(BaseModel):
    """DTO for execution task response."""

    model_config = ConfigDict(from_attributes=True)

    task_id: str
    project_id: str
    name: str
    type: str
    status: str
    input_artifacts: list[str] | None = None
    assigned_skill_id: str | None = None
    parent_module: str | None = None
    output_artifact_path: str | None = None
    retry_count: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TaskListDTO(BaseModel):
    """DTO for listing execution tasks."""

    model_config = ConfigDict(from_attributes=True)

    tasks: list[TaskResponseDTO]
    total_count: int


class TaskAutoGenerateRequestDTO(BaseModel):
    """DTO for auto-generating execution tasks from design artifacts."""

    design_artifact_ids: list[str] | None = Field(default=None)


class TaskAutoGenerateResponseDTO(BaseModel):
    """DTO for auto-generated execution tasks response."""

    tasks: list[TaskResponseDTO]


class MarkBugRequestDTO(BaseModel):
    """DTO for marking a failed task as a bug."""

    error_log: str
    issue_type: str = Field(..., max_length=16)


class MarkBugResponseDTO(BaseModel):
    """DTO for mark-bug response."""

    task_id: str
    issue_id: str
