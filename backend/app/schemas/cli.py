"""AI CLI Terminal Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class CliMode:
    """CLI working mode constants."""

    BUG = "bug"
    ARCH = "arch"


class ErrorResponse(BaseModel):
    """Error response payload."""

    code: str = Field(..., description="错误码")
    message: str = Field(..., description="错误信息")
    detail: dict[str, Any] | None = Field(None, description="额外错误详情")


class CliSessionCreate(BaseModel):
    """DTO for creating a CLI session."""

    project_id: str = Field(..., description="关联项目 ID")
    mode: Literal["bug", "arch"] = Field(default="bug", description="工作模式")


class CliSessionResponse(BaseModel):
    """DTO for a CLI session response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="会话唯一标识")
    project_id: str = Field(..., description="关联项目 ID")
    user_id: str = Field(..., description="创建用户 ID")
    mode: Literal["bug", "arch"] = Field(..., description="当前工作模式")
    status: Literal["active", "paused", "closed"] = Field(..., description="会话状态")
    created_at: datetime = Field(..., description="创建时间")
    closed_at: datetime | None = Field(None, description="关闭时间")
    updated_at: datetime = Field(..., description="更新时间")


class CliMessageResponse(BaseModel):
    """DTO for a CLI message response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="消息唯一标识")
    session_id: str = Field(..., description="所属会话 ID")
    message_type: Literal[
        "user", "ai", "system", "error", "success", "card", "progress", "thinking"
    ] = Field(..., description="消息类型")
    content: str | None = Field(None, description="文本内容")
    card_data: dict[str, Any] | None = Field(None, description="卡片数据")
    meta_data: dict[str, Any] | None = Field(
        None, serialization_alias="metadata", description="元数据"
    )
    sequence_no: int = Field(..., description="会话内消息序号")
    created_at: datetime = Field(..., description="创建时间")


class CliMessageListResponse(BaseModel):
    """DTO for listing CLI messages."""

    data: list[CliMessageResponse] = Field(..., description="消息列表")


class CliSessionCloseResponse(BaseModel):
    """DTO for closing a CLI session."""

    status: str = Field(..., description="操作状态")
    session_id: str = Field(..., description="会话 ID")


class CliSessionModeRequest(BaseModel):
    """DTO for switching CLI session mode."""

    mode: Literal["bug", "arch"] = Field(..., description="目标工作模式")


class CliCardAction(BaseModel):
    """Action button in a CLI card."""

    label: str = Field(..., description="按钮文字")
    command: str = Field(..., description="触发命令")
    style: Literal["primary", "danger", "default"] | None = Field(None, description="按钮样式")


class CliCard(BaseModel):
    """Interactive card pushed to the CLI."""

    type: Literal["bug-report", "fix-proposal", "arch-decision", "progress", "confirm"] = Field(
        ..., description="卡片类型"
    )
    data: dict[str, Any] = Field(..., description="卡片业务数据")
    actions: list[CliCardAction] = Field(..., description="可用操作")


class CliRequestPayload(BaseModel):
    """Payload inside a client-to-server CLI WebSocket message."""

    text: str | None = Field(None, description="用户输入文本")
    command: str | None = Field(None, description="命令字符串")
    action_type: str | None = Field(None, description="动作类型")
    metadata: dict[str, Any] | None = Field(None, description="附加元数据")


class CliRequest(BaseModel):
    """Client-to-server CLI WebSocket message."""

    type: Literal["command", "input", "action", "abort", "ping"] = Field(
        ..., description="消息类型"
    )
    session_id: str = Field(
        ...,
        validation_alias=AliasChoices("session_id", "sessionId"),
        description="会话 ID",
    )
    payload: CliRequestPayload = Field(
        default_factory=CliRequestPayload.model_construct, description="消息载荷"
    )


class CliProgressPayload(BaseModel):
    """Progress information in a CLI response."""

    current: int = Field(..., description="当前进度")
    total: int = Field(..., description="总进度")
    label: str = Field(..., description="进度描述")


class CliResponsePayload(BaseModel):
    """Payload inside a server-to-client CLI WebSocket message."""

    text: str | None = Field(None, description="文本输出")
    card: CliCard | None = Field(None, description="交互卡片")
    progress: CliProgressPayload | None = Field(None, description="进度更新")
    error: ErrorResponse | None = Field(None, description="错误信息")


class CliResponse(BaseModel):
    """Server-to-client CLI WebSocket message."""

    type: Literal["text", "card", "progress", "error", "done", "prompt", "pong", "thinking"] = (
        Field(..., description="消息类型")
    )
    session_id: str = Field(..., description="会话 ID")
    payload: CliResponsePayload = Field(
        default_factory=CliResponsePayload.model_construct, description="消息载荷"
    )
    timestamp: int = Field(..., description="Unix 毫秒时间戳")


class BugRecordCreate(BaseModel):
    """DTO for creating a bug record."""

    project_id: str = Field(..., description="关联项目 ID")
    session_id: str = Field(..., description="关联会话 ID")
    error_input: str = Field(..., description="用户粘贴的原始异常信息")


class BugRecordResponse(BaseModel):
    """DTO for a bug record response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Bug 唯一标识")
    project_id: str = Field(..., description="关联项目 ID")
    session_id: str = Field(..., description="关联会话 ID")
    error_signature: str = Field(..., description="错误签名")
    error_type: str = Field(..., description="错误类型")
    error_input: str = Field(..., description="原始异常信息")
    error_stack: str | None = Field(None, description="异常堆栈")
    root_cause: str | None = Field(None, description="根因分析")
    affected_files: list[str] | None = Field(None, description="影响文件列表")
    fix_diff: str | None = Field(None, description="修复 Diff")
    fix_risk: Literal["low", "medium", "high"] = Field(..., description="修复风险")
    status: Literal["pending", "executed", "verified", "failed", "ignored"] = Field(
        ..., description="修复状态"
    )
    executed_by: str = Field(..., description="执行主体")
    verified_result: str | None = Field(None, description="验证结果")
    similar_bug_id: str | None = Field(None, description="相似 Bug ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class BugRecordListResponse(BaseModel):
    """DTO for listing bug records."""

    data: list[BugRecordResponse] = Field(..., description="Bug 记录列表")


class BugRecordExecuteRequest(BaseModel):
    """DTO for executing a bug fix."""

    edited_diff: str | None = Field(None, description="用户编辑后的 Diff")


class ExecResult(BaseModel):
    """Execution result payload."""

    success: bool = Field(..., description="是否成功")
    output: str | None = Field(None, description="标准输出")
    error: str | None = Field(None, description="错误输出")
    branch: str | None = Field(None, description="临时分支名")


class ArchIssueResponse(BaseModel):
    """DTO for an architecture governance issue response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="治理项唯一标识")
    project_id: str = Field(..., description="关联项目 ID")
    session_id: str = Field(..., description="关联会话 ID")
    issue_type: str = Field(..., description="问题类型")
    severity: Literal["critical", "warning", "info"] = Field(..., description="严重级别")
    rule_id: str | None = Field(None, description="命中规则 ID")
    title: str = Field(..., description="问题标题")
    description: str | None = Field(None, description="问题描述")
    location: str | None = Field(None, description="问题位置")
    impact_analysis: str | None = Field(None, description="影响面分析")
    governance_plan: str | None = Field(None, description="治理方案")
    refactor_diff: str | None = Field(None, description="重构 Diff")
    review_points: list[str] | None = Field(None, description="审查要点")
    status: Literal["detected", "planned", "executed", "verified", "closed", "skipped"] = Field(
        ..., description="治理状态"
    )
    executed_at: datetime | None = Field(None, description="执行时间")
    adr_id: str | None = Field(None, description="ADR 记录 ID")
    backup_path: str | None = Field(None, description="备份文件路径")
    change_data: dict[str, Any] | None = Field(None, description="变更元数据")
    exec_result: dict[str, Any] | None = Field(None, description="执行结果")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ArchIssueListResponse(BaseModel):
    """DTO for listing architecture governance issues."""

    data: list[ArchIssueResponse] = Field(..., description="治理项列表")


class ArchScanRequest(BaseModel):
    """DTO for triggering an architecture scan."""

    project_id: str = Field(..., description="关联项目 ID")
    session_id: str = Field(..., description="关联会话 ID")
    rules: list[str] | None = Field(None, description="指定启用的规则 ID 列表")


class ArchScanResponse(BaseModel):
    """DTO for architecture scan acceptance response."""

    scan_id: str = Field(..., description="扫描任务 ID")
    status: str = Field(..., description="扫描状态")


class ScanRule(BaseModel):
    """Architecture scan rule configuration."""

    rule_id: str = Field(..., description="规则 ID")
    name: str = Field(..., description="规则名称")
    description: str | None = Field(None, description="规则描述")
    enabled: bool = Field(..., description="是否启用")
    severity: Literal["critical", "warning", "info"] = Field(..., description="严重级别")
