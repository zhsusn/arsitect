"""Chat Pydantic schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.cli import CliMessageResponse, CliSessionResponse


class ChatSessionCreate(BaseModel):
    """DTO for creating a chat session."""

    project_id: str = Field(..., description="关联项目 ID")
    task_mode: Literal["free-chat", "bug", "arch-fix"] = Field(
        default="free-chat", description="任务模式"
    )
    llm_provider: str | None = Field(None, description="LLM 提供商")


class ChatSessionModeRequest(BaseModel):
    """DTO for updating a chat session mode/provider/context."""

    task_mode: Literal["free-chat", "bug", "arch-fix"] | None = Field(
        None, description="任务模式"
    )
    llm_provider: str | None = Field(None, description="LLM 提供商")
    context_json: dict[str, Any] | None = Field(None, description="会话上下文 JSON")


class ChatSessionResponse(BaseModel):
    """DTO for a chat session including history."""

    session: CliSessionResponse | None = Field(None, description="会话信息")
    messages: list[CliMessageResponse] = Field(default_factory=list, description="消息列表")
    history: list[CliSessionResponse] = Field(
        default_factory=list, description="兼容字段：历史消息"
    )
