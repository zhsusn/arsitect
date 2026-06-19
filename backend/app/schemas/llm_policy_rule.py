"""LLM policy rule Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

RuleCategory = Literal["high_risk", "file_system", "terminal", "network"]
RuleActionType = Literal[
    "file_read", "file_write", "file_delete", "terminal", "web_fetch", "external_api"
]
RulePermission = Literal["allow", "ask", "deny"]


class LlmPolicyRuleBase(BaseModel):
    """Base fields for LLM policy rule schemas."""

    model_config = ConfigDict(populate_by_name=True)

    category: RuleCategory = Field(..., description="规则分组")
    action_type: RuleActionType = Field(..., description="操作类型")
    permission: RulePermission = Field(..., description="权限")
    pattern: str = Field(..., min_length=1, max_length=255, description="匹配模式")
    description: str | None = Field(None, description="描述")
    sort_order: int = Field(0, description="组内排序")
    extra_json: dict[str, Any] | None = Field(None, description="扩展字段")


class LlmPolicyRuleCreate(LlmPolicyRuleBase):
    """DTO for creating a single policy rule."""


class LlmPolicyRuleUpdate(BaseModel):
    """DTO for updating a single policy rule."""

    model_config = ConfigDict(populate_by_name=True)

    category: RuleCategory | None = Field(None)
    action_type: RuleActionType | None = Field(None)
    permission: RulePermission | None = Field(None)
    pattern: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None)
    sort_order: int | None = Field(None)
    extra_json: dict[str, Any] | None = Field(None)


class LlmPolicyRuleResponse(LlmPolicyRuleBase):
    """DTO for returning a policy rule."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str = Field(..., description="规则 ID")
    policy_id: str = Field(..., description="所属策略 ID")
    created_at: datetime = Field(..., description="创建时间 ISO8601")
    updated_at: datetime = Field(..., description="更新时间 ISO8601")


class LlmPolicyRuleListResponse(BaseModel):
    """DTO for listing policy rules."""

    items: list[LlmPolicyRuleResponse]
    total: int = Field(..., ge=0)


class UpdateRuleOrderRequest(BaseModel):
    """DTO for reordering policy rules."""

    rule_ids: list[str] = Field(..., description="按新顺序排列的规则 ID 列表")
