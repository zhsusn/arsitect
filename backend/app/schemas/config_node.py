"""Config node Pydantic schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ConfigNodeBase(BaseModel):
    """Base fields for config node schemas."""

    model_config = ConfigDict(populate_by_name=True)

    node_type: str = Field(..., description="节点类型")
    scope: Literal["managed", "global", "project", "user"] = Field(..., description="作用域")
    scope_target: str | None = Field(None, description="作用域目标 ID")
    key: str = Field(..., min_length=1, max_length=100, description="节点标识")
    name: str = Field(..., min_length=1, max_length=100, description="展示名称")
    description: str | None = Field(None, description="描述")
    is_enabled: bool = Field(True, description="是否启用")
    is_default: bool = Field(False, description="是否默认")
    priority: int = Field(0, ge=0, description="同层优先级")
    config_json: dict[str, Any] = Field(default_factory=dict, description="配置载荷")
    secret_json: dict[str, Any] | None = Field(None, description="密钥载荷")


class ConfigNodeCreate(ConfigNodeBase):
    """DTO for creating a config node."""


class ConfigNodeUpdate(BaseModel):
    """DTO for updating a config node."""

    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None)
    is_enabled: bool | None = Field(None)
    is_default: bool | None = Field(None)
    priority: int | None = Field(None, ge=0)
    config_json: dict[str, Any] | None = Field(None)
    secret_json: dict[str, Any] | None = Field(None)


class ConfigNodeResponse(ConfigNodeBase):
    """DTO for returning a config node."""

    id: str = Field(..., description="节点 ID")
    created_by: str | None = Field(None)
    updated_by: str | None = Field(None)
    created_at: str = Field(..., description="创建时间 ISO8601")
    updated_at: str = Field(..., description="更新时间 ISO8601")


class ConfigNodeListResponse(BaseModel):
    """DTO for listing config nodes."""

    items: list[ConfigNodeResponse]
    total: int = Field(..., ge=0)


class ConfigNodeFilter(BaseModel):
    """Query parameters for listing config nodes."""

    node_type: str | None = Field(None)
    scope: str | None = Field(None)
    scope_target: str | None = Field(None)
    key: str | None = Field(None)
    is_enabled: bool | None = Field(None)


class ConfigResolveRequest(BaseModel):
    """DTO for resolving effective config."""

    node_type: str = Field(...)
    project_id: str | None = Field(None)
    user_id: str | None = Field(None)


class ConfigResolveResponse(BaseModel):
    """DTO for resolved effective config."""

    node_type: str
    project_id: str | None
    user_id: str | None
    config: dict[str, Any]
    source_nodes: list[ConfigNodeResponse]


class PermissionCheckRequest(BaseModel):
    """DTO for checking a permission decision."""

    category: Literal["file_read", "file_write", "terminal", "web_fetch", "external_api"] = Field(
        ...
    )
    path: str | None = Field(None, description="文件路径，用于 file 类权限")
    command: str | None = Field(None, description="命令，用于 terminal 权限")
    domain: str | None = Field(None, description="域名，用于 web/external 权限")
    project_id: str | None = Field(None)
    user_id: str | None = Field(None)


class PermissionRuleSource(BaseModel):
    """Source of a permission rule."""

    node_id: str
    node_name: str
    scope: str
    scope_target: str | None
    decision: Literal["allow", "ask", "deny"]
    matched_pattern: str | None


class PermissionCheckResponse(BaseModel):
    """DTO for permission check result."""

    category: str
    decision: Literal["allow", "ask", "deny"]
    default_mode: Literal["allow", "ask", "deny"]
    rules: list[PermissionRuleSource]


class ProviderTestResponse(BaseModel):
    """DTO for provider connectivity test result."""

    success: bool
    message: str
    latency_ms: int | None = None
