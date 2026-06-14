"""Unit tests for the governance LLM gateway factory."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.c4.governance_fix.llm_gateway import (
    KimiCLIGateway,
    NoOpLLMGateway,
    OpenAILLMGateway,
    get_llm_gateway,
)


@pytest.mark.parametrize(
    ("provider", "expected_class"),
    [
        ("kimi", KimiCLIGateway),
        ("KIMI", KimiCLIGateway),
        ("openai", OpenAILLMGateway),
        ("OPENAI", OpenAILLMGateway),
        ("none", NoOpLLMGateway),
        ("disabled", NoOpLLMGateway),
    ],
)
def test_get_llm_gateway_resolves_providers(provider: str, expected_class: type) -> None:
    """TEST-1724: Factory resolves provider names case-insensitively."""
    with patch("app.c4.governance_fix.llm_gateway.settings.GOVERNANCE_LLM_PROVIDER", provider):
        result = get_llm_gateway()

    assert isinstance(result, expected_class)


def test_get_llm_gateway_defaults_to_kimi() -> None:
    """TEST-1725: Factory defaults to Kimi CLI when settings is 'kimi'."""
    with patch("app.c4.governance_fix.llm_gateway.settings.GOVERNANCE_LLM_PROVIDER", "kimi"):
        result = get_llm_gateway()

    assert isinstance(result, KimiCLIGateway)
