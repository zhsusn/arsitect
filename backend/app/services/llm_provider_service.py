"""LLM provider CRUD service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestError, NotFoundError
from app.models.llm_provider import LlmProvider
from app.schemas.llm_provider import LlmProviderCreate, LlmProviderUpdate
from app.services.llm.factory import get_llm_provider_from_config


class LlmProviderService:
    """CRUD, default management and resolution for LLM providers."""

    # Resolution precedence: higher index wins when explicit scopes are present;
    # managed always overrides everything else.
    _SCOPE_ORDER: tuple[str, ...] = ("global", "project", "user", "managed")

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with async session."""
        self._session = session

    async def list_providers(
        self,
        *,
        scope: str | None = None,
        scope_target: str | None = None,
        keyword: str | None = None,
        is_enabled: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[LlmProvider], int]:
        """List LLM providers with filters and total count."""
        filters = []
        if scope:
            filters.append(LlmProvider.scope == scope)
        if scope_target:
            filters.append(LlmProvider.scope_target == scope_target)
        if keyword:
            filters.append(
                or_(
                    LlmProvider.name.ilike(f"%{keyword}%"),
                    LlmProvider.key.ilike(f"%{keyword}%"),
                )
            )
        if is_enabled is not None:
            filters.append(LlmProvider.is_enabled == is_enabled)

        total_stmt = select(func.count(LlmProvider.id))
        list_stmt = select(LlmProvider)
        if filters:
            clause = and_(*filters)
            total_stmt = total_stmt.where(clause)
            list_stmt = list_stmt.where(clause)

        total = (await self._session.execute(total_stmt)).scalar_one()

        result = await self._session.execute(
            list_stmt.order_by(
                desc(LlmProvider.priority),
                desc(LlmProvider.updated_at),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_provider(self, provider_id: str) -> LlmProvider:
        """Get an LLM provider by ID."""
        result = await self._session.execute(
            select(LlmProvider).where(LlmProvider.id == provider_id)
        )
        provider = result.scalar_one_or_none()
        if provider is None:
            raise NotFoundError(f"LLM provider not found: {provider_id}")
        return provider

    async def get_provider_by_key(
        self,
        scope: str,
        scope_target: str | None,
        key: str,
    ) -> LlmProvider | None:
        """Get an LLM provider by unique composite key."""
        result = await self._session.execute(
            select(LlmProvider)
            .where(
                and_(
                    LlmProvider.scope == scope,
                    LlmProvider.scope_target == scope_target,
                    LlmProvider.key == key,
                )
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_provider(
        self, dto: LlmProviderCreate, *, user_id: str | None = None
    ) -> LlmProvider:
        """Create a new LLM provider."""
        existing = await self.get_provider_by_key(dto.scope, dto.scope_target, dto.key)
        if existing:
            raise ValueError(
                f"LLM provider already exists: {dto.scope}/{dto.scope_target or '-'}/{dto.key}"
            )

        now = datetime.now(UTC)
        secret_json: dict[str, Any] | None = None
        if dto.api_key:
            secret_json = {"api_key": dto.api_key}

        provider = LlmProvider(
            name=dto.name,
            key=dto.key,
            scope=dto.scope,
            scope_target=dto.scope_target,
            priority=dto.priority,
            provider_type=dto.provider_type,
            config_json=dict(dto.config_json),
            secret_json=secret_json,
            description=dto.description,
            is_default=dto.is_default,
            is_enabled=dto.is_enabled,
            created_at=now,
            updated_at=now,
        )
        self._session.add(provider)
        await self._session.flush()
        await self._session.refresh(provider)

        if provider.is_default:
            await self._unset_other_defaults(provider)

        return provider

    async def update_provider(
        self,
        provider_id: str,
        dto: LlmProviderUpdate,
        *,
        user_id: str | None = None,
    ) -> LlmProvider:
        """Update an existing LLM provider."""
        provider = await self.get_provider(provider_id)
        update_data = dto.model_dump(exclude_unset=True)

        if "api_key" in update_data:
            api_key = update_data.pop("api_key")
            if api_key:
                provider.secret_json = {"api_key": api_key}
            elif api_key is None and provider.secret_json:
                provider.secret_json = None

        for field, value in update_data.items():
            setattr(provider, field, value)
        provider.updated_at = datetime.now(UTC)
        self._session.add(provider)
        await self._session.flush()
        await self._session.refresh(provider)

        if dto.is_default:
            await self._unset_other_defaults(provider)

        return provider

    async def delete_provider(self, provider_id: str) -> None:
        """Delete an LLM provider."""
        provider = await self.get_provider(provider_id)
        if provider.is_default:
            raise BadRequestError("默认 Provider 禁止删除，请先切换默认节点")
        await self._session.delete(provider)
        await self._session.flush()

    async def clone_provider(self, provider_id: str, *, user_id: str | None = None) -> LlmProvider:
        """Clone an LLM provider with a new key."""
        source = await self.get_provider(provider_id)
        new_key = f"{source.key}-copy"
        counter = 1
        while await self.get_provider_by_key(source.scope, source.scope_target, new_key):
            new_key = f"{source.key}-copy-{counter}"
            counter += 1

        now = datetime.now(UTC)
        provider = LlmProvider(
            name=f"{source.name} (副本)",
            key=new_key,
            scope=source.scope,
            scope_target=source.scope_target,
            priority=source.priority,
            provider_type=source.provider_type,
            config_json=dict(source.config_json),
            secret_json=dict(source.secret_json) if source.secret_json else None,
            description=source.description,
            is_default=False,
            is_enabled=source.is_enabled,
            created_at=now,
            updated_at=now,
        )
        self._session.add(provider)
        await self._session.flush()
        await self._session.refresh(provider)
        return provider

    async def set_default(self, provider_id: str) -> LlmProvider:
        """Set a provider as default for its scope/scope_target."""
        provider = await self.get_provider(provider_id)
        provider.is_default = True
        provider.updated_at = datetime.now(UTC)
        self._session.add(provider)
        await self._unset_other_defaults(provider)
        await self._session.flush()
        await self._session.refresh(provider)
        return provider

    async def _unset_other_defaults(self, provider: LlmProvider) -> None:
        """Unset default flag for other providers in same scope/scope_target."""
        result = await self._session.execute(
            select(LlmProvider).where(
                and_(
                    LlmProvider.id != provider.id,
                    LlmProvider.scope == provider.scope,
                    LlmProvider.scope_target == provider.scope_target,
                    LlmProvider.is_default == True,  # noqa: E712
                )
            )
        )
        for other in result.scalars().all():
            other.is_default = False
            other.updated_at = datetime.now(UTC)
            self._session.add(other)
        await self._session.flush()

    async def resolve_default_provider(
        self,
        *,
        project_id: str | None = None,
        user_id: str | None = None,
    ) -> LlmProvider | None:
        """Resolve the effective default provider across scopes.

        Precedence: user > project > global. Managed scope is not used here.
        """
        scopes: list[tuple[str, str | None]] = [
            ("global", None),
        ]
        if project_id:
            scopes.append(("project", project_id))
        if user_id:
            scopes.append(("user", user_id))

        for scope, target in reversed(scopes):
            result = await self._session.execute(
                select(LlmProvider)
                .where(
                    and_(
                        LlmProvider.scope == scope,
                        LlmProvider.scope_target == target,
                        LlmProvider.is_enabled == True,  # noqa: E712
                        LlmProvider.is_default == True,  # noqa: E712
                    )
                )
                .order_by(desc(LlmProvider.priority))
                .limit(1)
            )
            provider = result.scalar_one_or_none()
            if provider:
                return provider

        # Fallback to any enabled provider in scope precedence.
        for scope, target in reversed(scopes):
            result = await self._session.execute(
                select(LlmProvider)
                .where(
                    and_(
                        LlmProvider.scope == scope,
                        LlmProvider.scope_target == target,
                        LlmProvider.is_enabled == True,  # noqa: E712
                    )
                )
                .order_by(desc(LlmProvider.priority))
                .limit(1)
            )
            provider = result.scalar_one_or_none()
            if provider:
                return provider

        return None

    async def resolve_provider(
        self,
        *,
        provider_key: str | None = None,
        project_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Resolve the effective provider configuration across scopes.

        Precedence when ``provider_key`` is provided: managed > user > project >
        global for that key. Otherwise the default provider for each scope is used
        with the same precedence. Falls back to environment variables if no DB
        provider is found.

        Returns:
            Merged ``config_json`` + ``secret_json`` dictionary.
        """
        provider: LlmProvider | None = None

        if provider_key:
            scopes: list[tuple[str, str | None]] = [("global", None)]
            if project_id:
                scopes.append(("project", project_id))
            if user_id:
                scopes.append(("user", user_id))
            scopes.append(("managed", None))

            for scope, target in reversed(scopes):
                result = await self._session.execute(
                    select(LlmProvider)
                    .where(
                        and_(
                            LlmProvider.scope == scope,
                            LlmProvider.scope_target == target,
                            LlmProvider.key == provider_key,
                            LlmProvider.is_enabled == True,  # noqa: E712
                        )
                    )
                    .order_by(desc(LlmProvider.priority))
                    .limit(1)
                )
                provider = result.scalar_one_or_none()
                if provider:
                    break
        else:
            provider = await self.resolve_default_provider(project_id=project_id, user_id=user_id)

        if provider:
            return self.build_config(provider)
        return self.get_env_fallback_config()

    async def test_provider(self, provider_id: str) -> dict[str, Any]:
        """Test connectivity of an LLM provider."""
        import time

        try:
            provider = await self.get_provider(provider_id)
        except NotFoundError as exc:
            return {"success": False, "message": str(exc), "latency_ms": None}

        config = self.build_config(provider)

        start = time.perf_counter()
        try:
            llm = get_llm_provider_from_config(config)
            await llm.generate("ping", temperature=0.2)
            latency = int((time.perf_counter() - start) * 1000)
            return {"success": True, "message": "连接成功", "latency_ms": latency}
        except Exception as exc:  # noqa: BLE001
            latency = int((time.perf_counter() - start) * 1000)
            return {
                "success": False,
                "message": f"连接失败: {exc}",
                "latency_ms": latency,
            }

    def build_config(self, provider: LlmProvider) -> dict[str, Any]:
        """Build a merged config dict including secrets."""
        config = dict(provider.config_json)
        if provider.secret_json:
            config.update(provider.secret_json)
        config["provider"] = provider.provider_type
        return config

    def get_env_fallback_config(self) -> dict[str, Any]:
        """Return env-based fallback provider config."""
        provider = settings.GOVERNANCE_LLM_PROVIDER.lower()
        config: dict[str, Any] = {"provider": provider}
        if provider in {"kimi", "kimi-cli"}:
            config["provider"] = "kimi-cli"
            config["kimi_cli_path"] = settings.KIMI_CLI_PATH
            config["timeout"] = 120
        elif provider in {"openai", "kimi-api"}:
            config["provider"] = "openai" if provider == "openai" else "kimi-api"
            config["api_base"] = settings.OPENAI_API_BASE
            config["api_key"] = settings.OPENAI_API_KEY
            config["model"] = settings.OPENAI_MODEL
        return config
