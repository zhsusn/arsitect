"""Tests for ExecStage HTTP invocation layer."""

from __future__ import annotations

import httpx
import pytest

from app.services.pocketflow.exec_stage import ExecStage


class FakeResponse:
    """Fake httpx response for testing."""

    def __init__(self, text: str, status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "error",
                request=None,
                response=self,
            )


class FakeAsyncClient:
    """Fake httpx AsyncClient."""

    def __init__(self, response: FakeResponse | Exception, timeout: int = 60) -> None:
        self._response = response
        self.timeout = timeout

    async def post(self, url: str, json: dict | None = None) -> FakeResponse:
        if isinstance(self._response, Exception):
            raise self._response
        return self._response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


@pytest.mark.asyncio
async def test_execute_success(monkeypatch) -> None:
    """Happy path returns success result."""
    fake = FakeAsyncClient(FakeResponse('{"ok": true}', 200))
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **kwargs: fake
    )

    stage = ExecStage()
    result = await stage.execute("http://ai.local/run", {"prompt": "hello"})
    assert result.success is True
    assert result.output == '{"ok": true}'
    assert result.duration_ms >= 0


@pytest.mark.asyncio
async def test_execute_timeout(monkeypatch) -> None:
    """Timeout returns failed result with error message."""
    fake = FakeAsyncClient(httpx.TimeoutException("timed out"))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: fake)

    stage = ExecStage()
    result = await stage.execute("http://ai.local/run", {})
    assert result.success is False
    assert "timed out" in result.error
    assert result.duration_ms >= 0


@pytest.mark.asyncio
async def test_execute_http_error(monkeypatch) -> None:
    """HTTP error returns failed result with status code."""
    fake = FakeAsyncClient(FakeResponse("bad request", 400))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: fake)

    stage = ExecStage()
    result = await stage.execute("http://ai.local/run", {})
    assert result.success is False
    assert "400" in result.error


@pytest.mark.asyncio
async def test_execute_generic_exception(monkeypatch) -> None:
    """Generic exception returns failed result with message."""
    fake = FakeAsyncClient(ValueError("something went wrong"))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: fake)

    stage = ExecStage()
    result = await stage.execute("http://ai.local/run", {})
    assert result.success is False
    assert "something went wrong" in result.error
