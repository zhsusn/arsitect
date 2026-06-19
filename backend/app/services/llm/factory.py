"""Factory for creating configured LLM providers."""

from __future__ import annotations

from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

from .base import LLMProvider
from .kimi_cli import KimiCLIProvider
from .noop import NoOpProvider
from .openai import OpenAIProvider

DEFAULT_PROVIDER: str = "kimi-cli"


def get_llm_provider(provider: str | None = None) -> LLMProvider:
    """Return the configured LLM provider.

    Args:
        provider: Provider identifier. Defaults to
            ``settings.GOVERNANCE_LLM_PROVIDER`` for backwards compatibility,
            falling back to ``kimi-cli``.

    Returns:
        An initialized LLM provider.
    """
    resolved = (provider or settings.GOVERNANCE_LLM_PROVIDER).lower()
    if resolved in {"kimi", "kimi-cli"}:
        return KimiCLIProvider()
    if resolved in {"openai", "kimi-api"}:
        return OpenAIProvider()
    return NoOpProvider()


def get_llm_provider_from_config(config: dict[str, Any]) -> LLMProvider:
    """Build an LLM provider from a config node payload.

    Args:
        config: Merged config_json + secret_json from a provider node.

    Returns:
        An initialized LLM provider.
    """
    provider = str(config.get("provider", "kimi-cli")).lower()
    if provider in {"kimi", "kimi-cli"}:
        return KimiCLIProvider(cli_path=str(config.get("kimi_cli_path", "kimi")))
    if provider in {"openai", "kimi-api"}:
        return OpenAIProvider(
            api_base=cast(str | None, config.get("api_base") or None),
            api_key=cast(str | None, config.get("api_key") or None),
            model=str(config.get("model", "gpt-4o-mini")),
        )
    return NoOpProvider()


async def get_llm_provider_async(
    db: AsyncSession,
    *,
    provider_key: str | None = None,
    project_id: str | None = None,
    user_id: str | None = None,
) -> LLMProvider:
    """Return an LLM provider resolved dynamically from dedicated LLM tables.

    Args:
        db: AsyncSession.
        provider_key: Optional specific provider key to use.
        project_id: Optional project scope for resolution.
        user_id: Optional user scope for resolution.

    Returns:
        An initialized LLM provider.
    """
    from app.services.llm_provider_service import LlmProviderService

    svc = LlmProviderService(db)
    config = await svc.resolve_provider(
        provider_key=provider_key,
        project_id=project_id,
        user_id=user_id,
    )
    return get_llm_provider_from_config(config)
