"""Unit tests for AIGateway."""

from __future__ import annotations

import pytest

from app.services.ai_gateway import AIGateway


class TestAIGateway:
    """AIGateway prompt and mock generation tests."""

    async def test_get_prompt(self) -> None:
        """TEST-1526: get_prompt renders a registered template."""
        gateway = AIGateway(api_key="test-key")
        prompt = gateway.get_prompt("bug_analysis", {"error_input": "ValueError"})

        assert "ValueError" in prompt
        assert "root cause" in prompt

    async def test_get_prompt_unknown(self) -> None:
        """TEST-1527: get_prompt raises KeyError for unregistered templates."""
        gateway = AIGateway(api_key="test-key")
        with pytest.raises(KeyError):
            gateway.get_prompt("unknown_prompt", {})

    async def test_generate_stream(self) -> None:
        """TEST-1528: generate yields multiple mock chunks."""
        gateway = AIGateway(api_key="test-key")
        chunks = [
            chunk async for chunk in gateway.generate("fix_plan", {"root_cause": "bad config"})
        ]

        assert len(chunks) == 4
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert "fix_plan" in "".join(chunks)

    async def test_generate_non_stream(self) -> None:
        """TEST-1529: generate_non_stream returns the joined mock response."""
        gateway = AIGateway(api_key="test-key")
        response = await gateway.generate_non_stream(
            "arch_governance",
            {"issue_type": "circular", "project_path": "/tmp/proj"},
        )

        assert isinstance(response, str)
        assert "arch_governance" in response

    async def test_api_key_from_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """TEST-1530: AIGateway falls back to the KIMI_API_KEY environment variable."""
        monkeypatch.setenv("KIMI_API_KEY", "env-key")
        gateway = AIGateway()

        assert gateway._api_key == "env-key"
