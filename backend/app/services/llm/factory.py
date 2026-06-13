"""Factory for creating configured LLM providers."""

from __future__ import annotations

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
