"""LLM policy Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.llm_policy_rule import LlmPolicyRuleResponse

PolicyScope = Literal["managed", "global", "project", "user"]
DefaultMode = Literal["allow", "ask", "deny"]


class LlmPolicyBase(BaseModel):
    """Base fields for LLM policy schemas."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., min_length=1, max_length=100, description="显示名称")
    key: str = Field(..., min_length=1, max_length=100, description="业务标识键")
    scope: PolicyScope = Field(..., description="作用域")
    scope_target: str | None = Field(None, description="作用域目标 ID")
    priority: int = Field(0, ge=0, description="优先级")
    default_mode: DefaultMode = Field("ask", description="默认模式")
    description: str | None = Field(None, description="描述")
    template_id: str | None = Field(None, description="基于的模板 ID")
    is_customized: bool = Field(False, description="是否基于模板手动修改过")
    is_enabled: bool = Field(True, description="是否启用")


class LlmPolicyCreate(LlmPolicyBase):
    """DTO for creating an LLM policy."""

    rules: list[dict[str, Any]] = Field(default_factory=list, description="初始规则")


class LlmPolicyUpdate(BaseModel):
    """DTO for updating an LLM policy."""

    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(None, min_length=1, max_length=100)
    scope: PolicyScope | None = Field(None)
    scope_target: str | None = Field(None)
    priority: int | None = Field(None, ge=0)
    default_mode: DefaultMode | None = Field(None)
    description: str | None = Field(None)
    template_id: str | None = Field(None)
    is_customized: bool | None = Field(None)
    is_enabled: bool | None = Field(None)
    rules: list[dict[str, Any]] | None = Field(None, description="全量替换规则")


class LlmPolicyResponse(LlmPolicyBase):
    """DTO for returning an LLM policy."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str = Field(..., description="策略 ID")
    rules: list[LlmPolicyRuleResponse] = Field(
        default_factory=list, description="规则列表"
    )
    created_at: datetime = Field(..., description="创建时间 ISO8601")
    updated_at: datetime = Field(..., description="更新时间 ISO8601")


class LlmPolicyListResponse(BaseModel):
    """DTO for listing LLM policies."""

    items: list[LlmPolicyResponse]
    total: int = Field(..., ge=0)


class LlmPolicyFilter(BaseModel):
    """Query parameters for listing LLM policies."""

    model_config = ConfigDict(populate_by_name=True)

    scope: PolicyScope | None = Field(None)
    scope_target: str | None = Field(None)
    keyword: str | None = Field(None)
    is_enabled: bool | None = Field(None)
    page: int = Field(1, ge=1)
    size: int = Field(100, ge=1, le=1000)


class ApplyTemplateRequest(BaseModel):
    """DTO for applying a template to a policy."""

    template_id: str = Field(..., description="模板 ID")
    base_policy_id: str | None = Field(
        None, description="目标策略 ID（为空时使用默认全局策略）"
    )


class PolicyCheckRequest(BaseModel):
    """DTO for checking a permission decision."""

    policy_key: str | None = Field(None, description="策略 key")
    policy_id: str | None = Field(None, description="策略 ID")
    scope: PolicyScope | None = Field(None)
    scope_target: str | None = Field(None, description="作用域目标 ID")
    action_type: str = Field(..., description="操作类型")
    target: str = Field(..., description="目标路径/命令/域名")
    project_id: str | None = Field(None)
    user_id: str | None = Field(None)


class PolicyCheckResponse(BaseModel):
    """DTO for permission check result."""

    allowed: bool
    permission: str
    matched_rule: dict[str, Any] | None
    message: str
    suggest_whitelist: bool
