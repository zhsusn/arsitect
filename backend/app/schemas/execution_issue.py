"""ExecutionIssue Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IssueCreateDTO(BaseModel):
    """DTO for creating an execution issue."""

    task_id: str | None = Field(default=None, max_length=36)
    issue_type: str = Field(..., max_length=16)
    error_log: str | None = Field(default=None)
    related_artifacts: list[str] | None = Field(default=None)
    suggested_action: str | None = Field(default=None)
    target_artifact_id: str | None = Field(default=None, max_length=36)
    change_request_id: str | None = Field(default=None, max_length=36)


class IssueUpdateDTO(BaseModel):
    """DTO for updating an execution issue."""

    issue_type: str | None = Field(default=None, max_length=16)
    error_log: str | None = Field(default=None)
    related_artifacts: list[str] | None = Field(default=None)
    suggested_action: str | None = Field(default=None)
    target_artifact_id: str | None = Field(default=None, max_length=36)
    change_request_id: str | None = Field(default=None, max_length=36)
    status: str | None = Field(default=None, max_length=16)


class IssueResponseDTO(BaseModel):
    """DTO for execution issue response."""

    model_config = ConfigDict(from_attributes=True)

    issue_id: str
    project_id: str
    task_id: str | None = None
    issue_type: str
    error_log: str | None = None
    related_artifacts: list[str] | None = None
    suggested_action: str | None = None
    feedback_to_architecture: bool = False
    target_artifact_id: str | None = None
    change_request_id: str | None = None
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class IssueFeedbackDTO(BaseModel):
    """DTO for providing feedback to architecture."""

    feedback_to_architecture: bool = Field(default=False)


class IssueFeedbackToArchitectureRequestDTO(BaseModel):
    """DTO for feedback-to-architecture with CR creation."""

    target_artifact_id: str = Field(..., max_length=36)
    change_description: str | None = Field(default=None)


class IssueFeedbackToArchitectureResponseDTO(BaseModel):
    """DTO for feedback-to-architecture response."""

    issue_id: str
    change_request_id: str
    status: str
