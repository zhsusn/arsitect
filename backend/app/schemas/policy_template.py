"""Policy template Pydantic schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PolicyTemplateBase(BaseModel):
    """Base fields for policy template schemas."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., min_length=1, max_length=32, description="模板标识")
    name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    description: str | None = Field(None, description="描述")
    default_mode: str = Field(..., description="默认模式")
    rules_json: list[dict[str, Any]] = Field(default_factory=list, description="规则列表")


class PolicyTemplateResponse(PolicyTemplateBase):
    """DTO for returning a policy template."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class PolicyTemplateListResponse(BaseModel):
    """DTO for listing policy templates."""

    items: list[PolicyTemplateResponse]
    total: int = Field(..., ge=0)
