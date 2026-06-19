"""LLM provider Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ProviderType = Literal["kimi-cli", "kimi-api", "openai", "arsitect-agent"]
ProviderScope = Literal["managed", "global", "project", "user"]


class ProviderConfigJson(BaseModel):
    """Provider-specific configuration payload."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    provider: str = Field("kimi-cli", description="Provider 类型")
    kimi_cli_path: str | None = Field(None, description="Kimi CLI 可执行文件路径")
    api_base: str | None = Field(None, description="API 基础地址")
    model: str | None = Field(None, description="模型名称")
    timeout: int | None = Field(120, description="超时时间（秒）")


class LlmProviderBase(BaseModel):
    """Base fields for LLM provider schemas."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., min_length=1, max_length=100, description="显示名称")
    key: str = Field(..., min_length=1, max_length=100, description="业务标识键")
    scope: ProviderScope = Field(..., description="作用域")
    scope_target: str | None = Field(None, description="作用域目标 ID")
    priority: int = Field(0, ge=0, description="优先级")
    provider_type: ProviderType = Field(..., description="Provider 类型")
    config_json: dict[str, Any] = Field(
        default_factory=dict, description="类型专属配置"
    )
    api_key: str | None = Field(None, description="API 密钥（仅写入）")
    description: str | None = Field(None, description="描述")
    is_default: bool = Field(False, description="是否为默认节点")
    is_enabled: bool = Field(True, description="是否启用")


class LlmProviderCreate(LlmProviderBase):
    """DTO for creating an LLM provider."""


class LlmProviderUpdate(BaseModel):
    """DTO for updating an LLM provider."""

    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(None, min_length=1, max_length=100)
    scope: ProviderScope | None = Field(None)
    scope_target: str | None = Field(None)
    priority: int | None = Field(None, ge=0)
    provider_type: ProviderType | None = Field(None)
    config_json: dict[str, Any] | None = Field(None)
    api_key: str | None = Field(None)
    description: str | None = Field(None)
    is_default: bool | None = Field(None)
    is_enabled: bool | None = Field(None)


class LlmProviderResponse(LlmProviderBase):
    """DTO for returning an LLM provider."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str = Field(..., description="Provider ID")
    api_key: str | None = Field(None, exclude=True)
    has_api_key: bool = Field(False, description="是否已配置 API 密钥")
    created_at: datetime = Field(..., description="创建时间 ISO8601")
    updated_at: datetime = Field(..., description="更新时间 ISO8601")


class LlmProviderListResponse(BaseModel):
    """DTO for listing LLM providers."""

    items: list[LlmProviderResponse]
    total: int = Field(..., ge=0)


class LlmProviderFilter(BaseModel):
    """Query parameters for listing LLM providers."""

    model_config = ConfigDict(populate_by_name=True)

    scope: ProviderScope | None = Field(None)
    scope_target: str | None = Field(None)
    keyword: str | None = Field(None)
    is_enabled: bool | None = Field(None)
    page: int = Field(1, ge=1)
    size: int = Field(100, ge=1, le=1000)


class ProviderTestResponse(BaseModel):
    """DTO for provider connectivity test result."""

    success: bool
    message: str
    latency_ms: int | None = None
