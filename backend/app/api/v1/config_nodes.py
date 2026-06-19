"""Config node API routes."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.infrastructure.database.session import get_db
from app.schemas.config_node import (
    ConfigNodeCreate,
    ConfigNodeListResponse,
    ConfigNodeResponse,
    ConfigNodeUpdate,
    ConfigResolveRequest,
    ConfigResolveResponse,
    PermissionCheckRequest,
    PermissionCheckResponse,
    ProviderTestResponse,
)
from app.services.config_service import ConfigService
from app.services.llm.base import LLMProvider
from app.services.llm.kimi_cli import KimiCLIProvider
from app.services.llm.openai import OpenAIProvider
from app.services.llm_permission_service import (
    LLMPermissionService,
    PermissionCheckContext,
)

router = APIRouter(prefix="/config", tags=["Config Nodes"])


def _current_user_id() -> str:
    """Placeholder authentication dependency."""
    return "user-mvp"


def _mask_secrets(secret_json: dict[str, Any] | None) -> dict[str, Any] | None:
    """Mask secret values before returning in API responses."""
    if not secret_json:
        return None
    masked: dict[str, Any] = {}
    for key, value in secret_json.items():
        if isinstance(value, str) and value:
            masked[key] = "•" * min(len(value), 8)
        elif value:
            masked[key] = "••••••"
        else:
            masked[key] = value
    return masked


def _node_to_response(node: Any) -> ConfigNodeResponse:
    """Convert ORM node to response schema."""
    return ConfigNodeResponse(
        id=node.id,
        node_type=node.node_type,
        scope=node.scope,
        scope_target=node.scope_target,
        key=node.key,
        name=node.name,
        description=node.description,
        is_enabled=node.is_enabled,
        is_default=node.is_default,
        priority=node.priority,
        config_json=dict(node.config_json),
        secret_json=_mask_secrets(node.secret_json),
        created_by=node.created_by,
        updated_by=node.updated_by,
        created_at=node.created_at.isoformat() if node.created_at else "",
        updated_at=node.updated_at.isoformat() if node.updated_at else "",
    )


class ConfigNodeQuery(BaseModel):
    """Query model for listing config nodes."""

    node_type: str | None = Query(None)
    scope: str | None = Query(None)
    scope_target: str | None = Query(None)
    key: str | None = Query(None)
    is_enabled: bool | None = Query(None)
    limit: int = Query(100, ge=1, le=1000)
    offset: int = Query(0, ge=0)


@router.get("/nodes", response_model=ConfigNodeListResponse)
async def list_nodes(
    q: ConfigNodeQuery = Depends(),
    db: AsyncSession = Depends(get_db),
) -> ConfigNodeListResponse:
    """List config nodes with filters."""
    svc = ConfigService(db)
    nodes, total = await svc.list_nodes(
        node_type=q.node_type,
        scope=q.scope,
        scope_target=q.scope_target,
        key=q.key,
        is_enabled=q.is_enabled,
        limit=q.limit,
        offset=q.offset,
    )
    return ConfigNodeListResponse(
        items=[_node_to_response(n) for n in nodes],
        total=total,
    )


@router.post("/nodes", response_model=ConfigNodeResponse, status_code=status.HTTP_201_CREATED)
async def create_node(
    dto: ConfigNodeCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(_current_user_id),
) -> ConfigNodeResponse:
    """Create a config node."""
    svc = ConfigService(db)
    node = await svc.create_node(dto, user_id=user_id)
    return _node_to_response(node)


@router.get("/nodes/{node_id}", response_model=ConfigNodeResponse)
async def get_node(
    node_id: str,
    db: AsyncSession = Depends(get_db),
) -> ConfigNodeResponse:
    """Get a config node by ID."""
    svc = ConfigService(db)
    node = await svc.get_node(node_id)
    return _node_to_response(node)


@router.put("/nodes/{node_id}", response_model=ConfigNodeResponse)
async def update_node(
    node_id: str,
    dto: ConfigNodeUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(_current_user_id),
) -> ConfigNodeResponse:
    """Update a config node."""
    svc = ConfigService(db)
    node = await svc.update_node(node_id, dto, user_id=user_id)
    return _node_to_response(node)


@router.delete("/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_node(
    node_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a config node."""
    svc = ConfigService(db)
    await svc.delete_node(node_id)


@router.post("/nodes/{node_id}/clone", response_model=ConfigNodeResponse)
async def clone_node(
    node_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(_current_user_id),
) -> ConfigNodeResponse:
    """Clone a config node."""
    svc = ConfigService(db)
    node = await svc.clone_node(node_id, user_id=user_id)
    return _node_to_response(node)


@router.post("/nodes/{node_id}/test", response_model=ProviderTestResponse)
async def test_provider_node(
    node_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProviderTestResponse:
    """Test connectivity of an llm_provider config node."""
    svc = ConfigService(db)
    try:
        node = await svc.get_node(node_id)
    except NotFoundError as exc:
        return ProviderTestResponse(success=False, message=str(exc))

    if node.node_type != "llm_provider":
        return ProviderTestResponse(success=False, message="只能测试 llm_provider 类型节点")

    config = dict(node.config_json)
    provider = config.get("provider", "kimi-cli")
    start = datetime.now(UTC)
    try:
        if provider in {"kimi", "kimi-cli"}:
            cli_path = config.get("kimi_cli_path", "kimi")
            p: LLMProvider = KimiCLIProvider(cli_path=cli_path)
            await p.generate("ping", temperature=0.2)
        elif provider == "openai":
            p = OpenAIProvider(
                api_base=config.get("api_base"),
                api_key=config.get("api_key"),
                model=config.get("model", "gpt-4o-mini"),
            )
            await p.generate("ping", temperature=0.2)
        else:
            return ProviderTestResponse(success=False, message=f"未知 provider: {provider}")
        latency = int((datetime.now(UTC) - start).total_seconds() * 1000)
        return ProviderTestResponse(success=True, message="连接成功", latency_ms=latency)
    except Exception as exc:  # noqa: BLE001
        return ProviderTestResponse(success=False, message=f"连接失败: {exc}")


@router.post("/resolve", response_model=ConfigResolveResponse)
async def resolve_config(
    req: ConfigResolveRequest,
    db: AsyncSession = Depends(get_db),
) -> ConfigResolveResponse:
    """Resolve effective config for a node type across scopes."""
    svc = ConfigService(db)
    resolved = await svc.resolve(
        req.node_type,
        project_id=req.project_id,
        user_id=req.user_id,
    )
    return ConfigResolveResponse(
        node_type=resolved["node_type"],
        project_id=resolved["project_id"],
        user_id=resolved["user_id"],
        config=resolved["config"],
        source_nodes=[_node_to_response(n) for n in resolved["source_nodes"]],
    )


@router.post("/check-permission", response_model=PermissionCheckResponse)
async def check_permission(
    req: PermissionCheckRequest,
    db: AsyncSession = Depends(get_db),
) -> PermissionCheckResponse:
    """Check permission decision for a tool request."""
    config_svc = ConfigService(db)
    perm_svc = LLMPermissionService(config_svc)
    ctx = PermissionCheckContext(
        category=req.category,
        path=req.path,
        command=req.command,
        domain=req.domain,
        project_id=req.project_id,
        user_id=req.user_id,
    )
    result = await perm_svc.check(ctx)
    return PermissionCheckResponse(
        category=result["category"],
        decision=result["decision"],
        default_mode=result["default_mode"],
        rules=result["rules"],
    )


@router.get("/default-llm-provider", response_model=dict[str, Any])
async def get_default_llm_provider(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get default LLM provider config."""
    svc = ConfigService(db)
    return await svc.get_default_llm_provider() or {}


@router.get("/default-permission-policy", response_model=dict[str, Any])
async def get_default_permission_policy() -> dict[str, Any]:
    """Get a safe default permission policy template."""
    svc = LLMPermissionService(ConfigService(None))  # type: ignore[arg-type]
    return svc.get_default_policy()
