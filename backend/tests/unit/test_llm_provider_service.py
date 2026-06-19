"""Unit tests for LlmProviderService."""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError
from app.schemas.llm_provider import LlmProviderCreate
from app.services.llm_provider_service import LlmProviderService


def _provider_dto(**kwargs: Any) -> LlmProviderCreate:
    """Build a provider DTO with sensible defaults."""
    defaults: dict[str, Any] = {
        "scope": "global",
        "provider_type": "kimi-cli",
        "config_json": {},
    }
    defaults.update(kwargs)
    return LlmProviderCreate(**defaults)


class TestLlmProviderService:
    """LlmProviderService CRUD and resolution tests."""

    async def test_create_and_get_provider(self, db_session: AsyncSession) -> None:
        """TEST-1800: create and retrieve a provider."""
        svc = LlmProviderService(db_session)
        provider = await svc.create_provider(
            _provider_dto(
                name="Kimi CLI",
                key="kimi-default",
                config_json={"kimi_cli_path": "kimi"},
            )
        )
        assert provider.id
        assert provider.key == "kimi-default"

        fetched = await svc.get_provider(provider.id)
        assert fetched.name == "Kimi CLI"

    async def test_duplicate_key_raises(self, db_session: AsyncSession) -> None:
        """TEST-1801: duplicate composite key is rejected."""
        svc = LlmProviderService(db_session)
        dto = _provider_dto(name="Dup", key="dup")
        await svc.create_provider(dto)
        with pytest.raises(ValueError):
            await svc.create_provider(dto)

    async def test_set_default_unmarks_others(self, db_session: AsyncSession) -> None:
        """TEST-1802: setting default unmarks other providers in same scope."""
        svc = LlmProviderService(db_session)
        first = await svc.create_provider(
            _provider_dto(name="First", key="first", is_default=True)
        )
        second = await svc.create_provider(
            _provider_dto(name="Second", key="second")
        )
        await svc.set_default(second.id)

        refreshed_first = await svc.get_provider(first.id)
        refreshed_second = await svc.get_provider(second.id)
        assert refreshed_first.is_default is False
        assert refreshed_second.is_default is True

    async def test_resolve_provider_by_key(self, db_session: AsyncSession) -> None:
        """TEST-1803: resolve merges config and secrets for a keyed provider."""
        svc = LlmProviderService(db_session)
        await svc.create_provider(
            _provider_dto(
                name="Project OpenAI",
                key="openai-proj",
                scope="project",
                scope_target="proj-1",
                provider_type="openai",
                config_json={
                    "api_base": "https://api.example.com/v1",
                    "model": "gpt-4o",
                },
                api_key="sk-proj",
                priority=10,
            )
        )
        config = await svc.resolve_provider(
            provider_key="openai-proj", project_id="proj-1"
        )
        assert config["provider"] == "openai"
        assert config["api_key"] == "sk-proj"

    async def test_resolve_provider_env_fallback(
        self, db_session: AsyncSession
    ) -> None:
        """TEST-1804: resolution falls back to env vars when no DB provider."""
        svc = LlmProviderService(db_session)
        config = await svc.resolve_provider(provider_key="missing")
        assert "provider" in config

    async def test_clone_provider(self, db_session: AsyncSession) -> None:
        """TEST-1805: clone creates a new provider with a copy suffix."""
        svc = LlmProviderService(db_session)
        source = await svc.create_provider(
            _provider_dto(name="Source", key="source")
        )
        cloned = await svc.clone_provider(source.id)
        assert cloned.key == "source-copy"
        assert cloned.name == "Source (副本)"

    async def test_delete_default_forbidden(self, db_session: AsyncSession) -> None:
        """TEST-1806: deleting the default provider is forbidden."""
        svc = LlmProviderService(db_session)
        provider = await svc.create_provider(
            _provider_dto(name="Default", key="default", is_default=True)
        )
        with pytest.raises(BadRequestError):
            await svc.delete_provider(provider.id)
