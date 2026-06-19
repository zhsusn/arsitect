"""SkillExecution Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExecutionTriggerDTO(BaseModel):
    """执行触发请求 DTO."""

    trigger_action: str = Field(description="触发动作: SINGLE_EXECUTE | BATCH_EXECUTE | RETRY")
    target_stage_id: str = Field(description="目标 Stage ID")
    target_skill_name: str | None = Field(default=None, description="SINGLE_EXECUTE 时必填")
    confirm_release: bool | None = Field(default=None, description="发布类 Skill 必须 true")
    previous_execution_id: str | None = Field(default=None, description="RETRY 时必填")


class TriggerValidationResultDTO(BaseModel):
    """触发校验结果 DTO."""

    valid: bool = Field(description="是否通过校验")
    error_code: str | None = Field(default=None, description="错误码")
    message: str | None = Field(default=None, description="错误消息")


class ExecutionStatusDTO(BaseModel):
    """执行状态 DTO."""

    model_config = ConfigDict(from_attributes=True)

    execution_id: str = Field(description="执行 ID")
    current_phase: str = Field(description="当前阶段: PREP | EXEC | POST | NONE")
    phase_status: str = Field(description="阶段状态: RUNNING | COMPLETED | FAILED | STOPPED")
    overall_status: str = Field(
        description="整体状态: NOT_STARTED | RUNNING | SUCCESS | FAILED | STOPPED | UNKNOWN"
    )
    stage_progress_percent: int = Field(ge=0, le=100, description="Stage 进度百分比")
    status_timestamp: datetime = Field(description="状态时间戳")
    artifact_paths: list[str] = Field(default_factory=list, description="产物路径列表")
    error_summary: str | None = Field(default=None, description="错误摘要")


class ExecutionStatusDeltaDTO(BaseModel):
    """执行状态增量 DTO."""

    execution_id: str = Field(description="执行 ID")
    changed_fields: dict[str, Any] = Field(default_factory=dict, description="变更字段")
    new_anchor: str = Field(description="新游标")


class SSEEventDTO(BaseModel):
    """SSE 事件 DTO."""

    event: str = Field(default="status_update", description="事件类型")
    data: dict[str, Any] = Field(default_factory=dict, description="事件数据")


class StageProgressDTO(BaseModel):
    """Stage 进度 DTO."""

    execution_id: str = Field(description="执行 ID")
    stage_progress_percent: int = Field(ge=0, le=100, description="进度百分比")
    estimated_remaining_seconds: int | None = Field(default=None, description="预估剩余秒数")


class LogFilterDTO(BaseModel):
    """日志过滤 DTO."""

    keyword: str | None = Field(default=None, max_length=100, description="关键词")
    level: str = Field(default="ALL", description="级别: ALL | INFO | WARN | ERROR | DEBUG")
    anchor: str | None = Field(default=None, description="上次拉取的日志游标")


class LogEntryDTO(BaseModel):
    """日志条目 DTO."""

    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime = Field(description="时间戳")
    level: str = Field(description="级别")
    content: str = Field(description="内容")


class LogQueryResultDTO(BaseModel):
    """日志查询结果 DTO."""

    log_entries: list[LogEntryDTO] = Field(default_factory=list, description="日志条目")
    total_count: int = Field(ge=0, description="总条数")
    next_anchor: str | None = Field(default=None, description="下一页游标")


class RetryResultDTO(BaseModel):
    """重试结果 DTO."""

    success: bool = Field(description="是否成功")
    new_execution_id: str | None = Field(default=None, description="新执行 ID")
    message: str | None = Field(default=None, description="消息")


class SkillExecutionResponseDTO(BaseModel):
    """SkillExecution 响应 DTO."""

    model_config = ConfigDict(from_attributes=True)

    execution_id: str = Field(description="执行 ID")
    project_id: str = Field(description="项目 ID")
    stage_id: str = Field(description="Stage ID")
    skill_id: str = Field(description="Skill ID")
    skill_name: str = Field(description="Skill 名称")
    trigger_action: str = Field(description="触发动作")
    current_phase: str = Field(description="当前阶段")
    phase_status: str = Field(description="阶段状态")
    overall_status: str = Field(description="整体状态")
    retry_count: int = Field(description="重试次数")
    previous_execution_id: str | None = Field(default=None, description="前次执行 ID")
    is_release_skill: bool = Field(description="是否为发布类 Skill")
    release_confirmed: bool = Field(description="是否已确认发布")
    started_at: datetime | None = Field(default=None, description="开始时间")
    completed_at: datetime | None = Field(default=None, description="完成时间")
    created_at: datetime = Field(description="创建时间")
