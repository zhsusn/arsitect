"""Unit tests for the AI CLI agent router.

These tests verify that the AI CLI routes free-form chat through the
configured LLM provider, which defaults to Kimi CLI in production.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cli_session import CliSession
from app.services.chat.agent_router import AgentRouter
from app.services.llm.base import LLMProvider


class SpyLLMProvider(LLMProvider):
    """Records chat messages and returns a deterministic response."""

    def __init__(self, response: str = "spy response") -> None:
        self._response = response
        self.chat_calls: list[list[dict[str, str]]] = []

    async def generate(self, prompt: str, *, temperature: float = 0.2) -> str:
        return self._response

    async def generate_stream(
        self,
        prompt: str,
        on_chunk: Any,
        *,
        temperature: float = 0.2,
    ) -> str:
        return self._response

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        on_chunk: Any,
        *,
        temperature: float = 0.2,
    ) -> str:
        self.chat_calls.append(messages)
        if on_chunk:
            result = on_chunk(self._response)
            if hasattr(result, "__await__"):
                await result
        return self._response


@pytest.fixture
def session() -> CliSession:
    """Return a minimal CLI session for agent router tests."""
    sess = MagicMock(spec=CliSession)
    sess.id = "session-1"
    sess.project_id = "proj-1"
    sess.task_mode = "free"
    sess.llm_provider = None
    sess.context_json = None
    return sess


@pytest.fixture
def router(db_session: AsyncSession) -> AgentRouter:
    """Return an AgentRouter bound to the test database session."""
    return AgentRouter(db_session)


@pytest.mark.asyncio
async def test_free_chat_uses_configured_kimi_cli_provider(
    router: AgentRouter,
    session: CliSession,
) -> None:
    """TEST-1730: Free chat delegates to the configured LLM provider.

    In production the default provider is ``kimi-cli``; this test ensures the
    router passes the conversation to :meth:`LLMProvider.chat_stream`.
    """
    spy = SpyLLMProvider(response="Kimi CLI reply")
    sent: list[dict[str, Any]] = []

    async def sender(msg: dict[str, Any]) -> None:
        sent.append(msg)

    with patch(
        "app.services.chat.agent_router.get_llm_provider_async",
        return_value=spy,
    ) as mock_factory:
        await router._run_free_chat(session, "hello", {}, sender)

    mock_factory.assert_awaited_once()
    assert mock_factory.call_args.kwargs.get("provider_key") is None
    assert len(spy.chat_calls) == 1
    messages = spy.chat_calls[0]
    assert any(m["role"] == "user" and m["content"] == "hello" for m in messages)

    types = [m.get("type") for m in sent]
    assert "text" in types
    assert "thinking" in types
    text_payloads = [
        m["payload"]["text"] for m in sent if m.get("type") == "text"
    ]
    assert "Kimi CLI reply" in text_payloads


@pytest.mark.asyncio
async def test_free_chat_respects_session_provider(
    router: AgentRouter,
    session: CliSession,
) -> None:
    """TEST-1731: Session-level provider overrides the default."""
    session.llm_provider = "openai"
    spy = SpyLLMProvider(response="OpenAI reply")
    sent: list[dict[str, Any]] = []

    async def sender(msg: dict[str, Any]) -> None:
        sent.append(msg)

    with patch(
        "app.services.chat.agent_router.get_llm_provider_async",
        return_value=spy,
    ) as mock_factory:
        await router._run_free_chat(session, "hello", {}, sender)

    mock_factory.assert_awaited_once()
    assert mock_factory.call_args.kwargs.get("provider_key") == "openai"


@pytest.mark.asyncio
async def test_free_chat_handles_llm_error(
    router: AgentRouter,
    session: CliSession,
) -> None:
    """TEST-1732: LLM failures are surfaced as error CLI responses."""
    failing_provider = SpyLLMProvider(response="")
    failing_provider.chat_stream = AsyncMock(side_effect=RuntimeError("kimi not found"))
    sent: list[dict[str, Any]] = []

    async def sender(msg: dict[str, Any]) -> None:
        sent.append(msg)

    with patch(
        "app.services.chat.agent_router.get_llm_provider_async",
        return_value=failing_provider,
    ):
        await router._run_free_chat(session, "hello", {}, sender)

    error_messages = [
        m.get("payload", {}).get("error", {}).get("message", "")
        for m in sent
        if m.get("type") == "error"
    ]
    assert any("kimi not found" in msg for msg in error_messages)
