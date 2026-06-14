"""Unified configuration node service."""

from __future__ import annotations

from collections import OrderedDict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, asc, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.models.config_node import ConfigNode, ConfigNodeScope, ConfigNodeType
from app.schemas.config_node import ConfigNodeCreate, ConfigNodeUpdate


class ConfigService:
    """CRUD and resolution for unified config nodes."""

    # Scope precedence: higher number wins for deny/allow rules.
    _SCOPE_ORDER: OrderedDict[str, int] = OrderedDict(
        [
            (ConfigNodeScope.MANAGED.value, 3),
            (ConfigNodeScope.GLOBAL.value, 0),
            (ConfigNodeScope.PROJECT.value, 1),
            (ConfigNodeScope.USER.value, 2),
        ]
    )

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with async session."""
        self._session = session

    async def list_nodes(
        self,
        *,
        node_type: str | None = None,
        scope: str | None = None,
        scope_target: str | None = None,
        key: str | None = None,
        is_enabled: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ConfigNode], int]:
        """List config nodes with filters and total count."""
        filters = []
        if node_type:
            filters.append(ConfigNode.node_type == node_type)
        if scope:
            filters.append(ConfigNode.scope == scope)
        if scope_target:
            filters.append(ConfigNode.scope_target == scope_target)
        if key:
            filters.append(ConfigNode.key.ilike(f"%{key}%"))
        if is_enabled is not None:
            filters.append(ConfigNode.is_enabled == is_enabled)

        total_stmt = select(ConfigNode.id)
        list_stmt = select(ConfigNode)
        if filters:
            clause = and_(*filters)
            total_stmt = total_stmt.where(clause)
            list_stmt = list_stmt.where(clause)

        total_result = await self._session.execute(total_stmt)
        total = len(total_result.scalars().all())

        result = await self._session.execute(
            list_stmt.order_by(
                asc(ConfigNode.node_type),
                desc(ConfigNode.priority),
                desc(ConfigNode.updated_at),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_node(self, node_id: str) -> ConfigNode:
        """Get a single config node by ID."""
        result = await self._session.execute(
            select(ConfigNode).where(ConfigNode.id == node_id)
        )
        node = result.scalar_one_or_none()
        if node is None:
            raise NotFoundError(f"Config node not found: {node_id}")
        return node

    async def get_node_by_key(
        self,
        node_type: str,
        scope: str,
        scope_target: str | None,
        key: str,
    ) -> ConfigNode | None:
        """Get a config node by unique composite key."""
        result = await self._session.execute(
            select(ConfigNode).where(
                and_(
                    ConfigNode.node_type == node_type,
                    ConfigNode.scope == scope,
                    ConfigNode.scope_target == scope_target,
                    ConfigNode.key == key,
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_node(
        self, dto: ConfigNodeCreate, *, user_id: str | None = None
    ) -> ConfigNode:
        """Create a new config node."""
        existing = await self.get_node_by_key(
            dto.node_type, dto.scope, dto.scope_target, dto.key
        )
        if existing:
            raise ValueError(
                f"Config node already exists: {dto.node_type}/{dto.scope}/"
                f"{dto.scope_target or '-'}/{dto.key}"
            )

        now = datetime.now(UTC)
        node = ConfigNode(
            node_type=dto.node_type,
            scope=dto.scope,
            scope_target=dto.scope_target,
            key=dto.key,
            name=dto.name,
            description=dto.description,
            is_enabled=dto.is_enabled,
            is_default=dto.is_default,
            priority=dto.priority,
            config_json=dict(dto.config_json),
            secret_json=dict(dto.secret_json) if dto.secret_json else None,
            created_by=user_id,
            updated_by=user_id,
            created_at=now,
            updated_at=now,
        )
        self._session.add(node)
        await self._session.flush()
        await self._session.refresh(node)
        return node

    async def update_node(
        self,
        node_id: str,
        dto: ConfigNodeUpdate,
        *,
        user_id: str | None = None,
    ) -> ConfigNode:
        """Update an existing config node."""
        node = await self.get_node(node_id)
        update_data = dto.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(node, field, value)
        node.updated_by = user_id
        node.updated_at = datetime.now(UTC)
        self._session.add(node)
        await self._session.flush()
        await self._session.refresh(node)
        return node

    async def delete_node(self, node_id: str) -> None:
        """Delete a config node."""
        node = await self.get_node(node_id)
        await self._session.delete(node)
        await self._session.flush()

    async def clone_node(
        self, node_id: str, *, user_id: str | None = None
    ) -> ConfigNode:
        """Clone a config node with a new key."""
        source = await self.get_node(node_id)
        new_key = f"{source.key}-copy"
        counter = 1
        while await self.get_node_by_key(
            source.node_type, source.scope, source.scope_target, new_key
        ):
            new_key = f"{source.key}-copy-{counter}"
            counter += 1

        now = datetime.now(UTC)
        node = ConfigNode(
            node_type=source.node_type,
            scope=source.scope,
            scope_target=source.scope_target,
            key=new_key,
            name=f"{source.name} (副本)",
            description=source.description,
            is_enabled=source.is_enabled,
            is_default=False,
            priority=source.priority,
            config_json=dict(source.config_json),
            secret_json=dict(source.secret_json) if source.secret_json else None,
            created_by=user_id,
            updated_by=user_id,
            created_at=now,
            updated_at=now,
        )
        self._session.add(node)
        await self._session.flush()
        await self._session.refresh(node)
        return node

    async def resolve(
        self,
        node_type: str,
        *,
        project_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Resolve effective config for a node type across scopes.

        Precedence: managed > user > project > global.
        Within same scope: higher priority wins, then latest updated_at.
        """
        scopes: list[tuple[str, str | None]] = [
            (ConfigNodeScope.GLOBAL.value, None),
        ]
        if project_id:
            scopes.append((ConfigNodeScope.PROJECT.value, project_id))
        if user_id:
            scopes.append((ConfigNodeScope.USER.value, user_id))
        scopes.append((ConfigNodeScope.MANAGED.value, None))

        conditions = [
            and_(
                ConfigNode.node_type == node_type,
                ConfigNode.scope == scope,
                ConfigNode.scope_target == target,
                ConfigNode.is_enabled == True,  # noqa: E712
            )
            for scope, target in scopes
        ]

        result = await self._session.execute(
            select(ConfigNode)
            .where(or_(*conditions))
            .order_by(
                asc(ConfigNode.priority),
                asc(ConfigNode.updated_at),
            )
        )
        nodes = list(result.scalars().all())

        merged: dict[str, Any] = {}
        source_nodes: list[ConfigNode] = []
        for node in nodes:
            source_nodes.append(node)
            node_config = dict(node.config_json)
            # Top-level keys are merged; lists are replaced by higher-priority node.
            for key, value in node_config.items():
                if isinstance(value, list):
                    if key not in merged:
                        merged[key] = list(value)
                    else:
                        # Higher priority list replaces lower priority list.
                        merged[key] = list(value)
                elif isinstance(value, dict):
                    if key not in merged:
                        merged[key] = dict(value)
                    else:
                        merged[key].update(value)
                else:
                    merged[key] = value

        return {
            "node_type": node_type,
            "project_id": project_id,
            "user_id": user_id,
            "config": merged,
            "source_nodes": source_nodes,
        }

    async def get_default_llm_provider(self) -> dict[str, Any] | None:
        """Return default llm_provider config (without secrets), fallback to env vars."""
        config = await self._get_default_llm_provider_full()
        config.pop("api_key", None)
        return config

    async def _get_default_llm_provider_full(self) -> dict[str, Any]:
        """Return default llm_provider config including secrets; internal use only."""
        result = await self._session.execute(
            select(ConfigNode).where(
                and_(
                    ConfigNode.node_type == ConfigNodeType.LLM_PROVIDER.value,
                    ConfigNode.is_enabled == True,  # noqa: E712
                    ConfigNode.is_default == True,  # noqa: E712
                )
            )
        )
        node = result.scalar_one_or_none()
        if node:
            merged = dict(node.config_json)
            if node.secret_json:
                merged.update(node.secret_json)
            return merged
        return {
            "provider": settings.GOVERNANCE_LLM_PROVIDER,
            "kimi_cli_path": settings.KIMI_CLI_PATH,
            "api_base": settings.OPENAI_API_BASE,
            "api_key": settings.OPENAI_API_KEY,
            "model": settings.OPENAI_MODEL,
        }
