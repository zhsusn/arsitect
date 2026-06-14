"""Unit tests for the generic LLM provider factory."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.services.llm.factory import get_llm_provider
from app.services.llm.kimi_cli import KimiCLIProvider
from app.services.llm.noop import NoOpProvider
from app.services.llm.openai import OpenAIProvider


@pytest.mark.parametrize(
    ("provider", "expected_class"),
    [
        ("kimi", KimiCLIProvider),
        ("kimi-cli", KimiCLIProvider),
        ("openai", OpenAIProvider),
        ("kimi-api", OpenAIProvider),
        ("unknown", NoOpProvider),
    ],
)
def test_get_llm_provider_resolves_aliases(provider: str, expected_class: type) -> None:
    """TEST-1710: Factory resolves provider aliases to the correct implementation."""
    with patch("app.services.llm.factory.settings.GOVERNANCE_LLM_PROVIDER", provider):
        result = get_llm_provider()

    assert isinstance(result, expected_class)


def test_get_llm_provider_uses_settings_default() -> None:
    """TEST-1711: Factory uses the configured default provider when none is given."""
    with patch("app.services.llm.factory.settings.GOVERNANCE_LLM_PROVIDER", "kimi"):
        result = get_llm_provider()

    assert isinstance(result, KimiCLIProvider)


def test_get_llm_provider_explicit_overrides_settings() -> None:
    """TEST-1712: Explicit provider argument overrides settings default."""
    with patch("app.services.llm.factory.settings.GOVERNANCE_LLM_PROVIDER", "openai"):
        result = get_llm_provider("kimi-cli")

    assert isinstance(result, KimiCLIProvider)
