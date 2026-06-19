"""Stage-level execution status schema."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LatestExecutionDTO(BaseModel):
    """Summary of the latest skill execution for a stage."""

    model_config = {"from_attributes": True}

    execution_id: str = Field(description="执行 ID")
    skill_name: str = Field(description="Skill 名称")
    overall_status: str = Field(description="整体状态")
    current_phase: str = Field(description="当前阶段")


class StageExecutionStatusDTO(BaseModel):
    """Aggregated real-time execution status for a project stage."""

    stage_id: str = Field(description="Stage ID")
    runtime_status: str = Field(description="阶段运行时状态")
    current_phase: str = Field(description="当前执行阶段")
    overall_status: str = Field(description="整体执行状态")
    progress_percent: int = Field(ge=0, le=100, description="进度百分比")
    error_summary: str | None = Field(default=None, description="错误摘要")
    artifact_paths: list[str] = Field(default_factory=list, description="产物路径列表")
    running_execution_ids: list[str] = Field(default_factory=list, description="运行中执行 ID 列表")
    latest_execution: LatestExecutionDTO | None = Field(default=None, description="最新执行摘要")
