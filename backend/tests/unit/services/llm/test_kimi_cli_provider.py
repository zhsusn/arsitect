"""Unit tests for the Kimi CLI LLM provider.

These tests verify that :class:`app.services.llm.kimi_cli.KimiCLIProvider`
spawns the ``kimi`` executable with the correct guard flags and handles
stdout/stderr/exit codes safely.
"""

from __future__ import annotations

import subprocess
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm.kimi_cli import KimiCLIProvider, _strip_surrogates


@pytest.fixture
def provider() -> KimiCLIProvider:
    """Return a KimiCLIProvider wired to a fake executable path."""
    return KimiCLIProvider(cli_path="/fake/kimi")


def _fake_process(stdout: bytes, stderr: bytes, returncode: int) -> MagicMock:
    """Return a minimal fake ``asyncio.subprocess.Process``."""
    proc = MagicMock()
    proc.stdin = MagicMock()
    proc.stdout = MagicMock()
    proc.stdout.read = AsyncMock(side_effect=[stdout, b""])
    proc.stderr = MagicMock()
    proc.stderr.read = AsyncMock(side_effect=[stderr, b""])
    proc.wait = AsyncMock()
    proc.returncode = returncode
    return proc


@pytest.mark.asyncio
async def test_generate_returns_stdout(provider: KimiCLIProvider) -> None:
    """TEST-1701: generate returns stripped stdout on success."""
    fake_proc = _fake_process(b"hello world\n", b"", 0)

    with patch(
        "app.services.llm.kimi_cli.asyncio.create_subprocess_exec",
        new=AsyncMock(return_value=fake_proc),
    ) as mock_exec:
        result = await provider.generate("prompt")

    assert result == "hello world"
    mock_exec.assert_awaited_once()
    cmd = mock_exec.await_args[0]
    assert cmd[0] == "/fake/kimi"
    assert "--quiet" in cmd
    assert "--max-steps-per-turn" in cmd
    assert cmd[cmd.index("--max-steps-per-turn") + 1] == "1"
    assert "-p" in cmd


@pytest.mark.asyncio
async def test_generate_stream_emits_chunks(provider: KimiCLIProvider) -> None:
    """TEST-1702: generate_stream invokes on_chunk for each stdout chunk."""
    fake_proc = _fake_process(b"chunk1chunk2", b"", 0)
    chunks: list[str] = []

    async def on_chunk(text: str) -> None:
        chunks.append(text)

    with patch(
        "app.services.llm.kimi_cli.asyncio.create_subprocess_exec",
        new=AsyncMock(return_value=fake_proc),
    ):
        result = await provider.generate_stream("prompt", on_chunk=on_chunk)

    assert result == "chunk1chunk2"
    assert chunks == ["chunk1chunk2"]


@pytest.mark.asyncio
async def test_generate_ignores_temperature(provider: KimiCLIProvider) -> None:
    """TEST-1703: temperature is ignored because Kimi CLI does not support it."""
    fake_proc = _fake_process(b"ok", b"", 0)

    with patch(
        "app.services.llm.kimi_cli.asyncio.create_subprocess_exec",
        new=AsyncMock(return_value=fake_proc),
    ) as mock_exec:
        await provider.generate("prompt", temperature=0.9)

    cmd = mock_exec.await_args[0]
    assert "0.9" not in cmd


@pytest.mark.asyncio
async def test_generate_injects_env_vars(provider: KimiCLIProvider) -> None:
    """TEST-1704: PYTHONIOENCODING and KIMI_CLI_NO_ANALYTICS are set."""
    fake_proc = _fake_process(b"ok", b"", 0)

    with patch(
        "app.services.llm.kimi_cli.asyncio.create_subprocess_exec",
        new=AsyncMock(return_value=fake_proc),
    ) as mock_exec:
        await provider.generate("prompt")

    kwargs = mock_exec.await_args[1]
    env = kwargs["env"]
    assert env["PYTHONIOENCODING"] == "utf-8"
    assert env["KIMI_CLI_NO_ANALYTICS"] == "1"


@pytest.mark.asyncio
async def test_generate_prefixed_with_tool_ban(provider: KimiCLIProvider) -> None:
    """TEST-1705: The prompt is prefixed with the tool-ban system instruction."""
    fake_proc = _fake_process(b"ok", b"", 0)

    with patch(
        "app.services.llm.kimi_cli.asyncio.create_subprocess_exec",
        new=AsyncMock(return_value=fake_proc),
    ) as mock_exec:
        await provider.generate("user prompt")

    cmd = mock_exec.await_args[0]
    prompt_arg = cmd[cmd.index("-p") + 1]
    assert "禁止调用任何工具" in prompt_arg
    assert "user prompt" in prompt_arg


@pytest.mark.asyncio
async def test_generate_nonzero_exit_with_output_returns_output(
    provider: KimiCLIProvider,
) -> None:
    """TEST-1706: Non-zero exit code with captured output is treated as success."""
    fake_proc = _fake_process(b"partial result", b"step limit", 1)

    with patch(
        "app.services.llm.kimi_cli.asyncio.create_subprocess_exec",
        new=AsyncMock(return_value=fake_proc),
    ):
        result = await provider.generate("prompt")

    assert result == "partial result"


@pytest.mark.asyncio
async def test_generate_nonzero_exit_without_output_raises(
    provider: KimiCLIProvider,
) -> None:
    """TEST-1707: Non-zero exit code with no output raises RuntimeError."""
    fake_proc = _fake_process(b"", b"fatal error", 1)

    with (
        patch(
            "app.services.llm.kimi_cli.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=fake_proc),
        ),
        pytest.raises(RuntimeError, match="Kimi CLI failed"),
    ):
        await provider.generate("prompt")


def test_strip_surrogates_removes_utf16_replacement() -> None:
    """TEST-1708: UTF-16 surrogate characters are stripped from text."""
    raw = "hello \ud800\udc00world"
    cleaned = _strip_surrogates(raw)
    assert "\ud800" not in cleaned
    assert cleaned == "hello world"


@pytest.mark.asyncio
async def test_generate_uses_settings_default_path(monkeypatch: Any) -> None:
    """TEST-1709: Provider falls back to settings.KIMI_CLI_PATH when no path is given."""
    monkeypatch.setattr("app.services.llm.kimi_cli.settings.KIMI_CLI_PATH", "kimi-from-settings")
    default_provider = KimiCLIProvider()
    fake_proc = _fake_process(b"ok", b"", 0)

    with patch(
        "app.services.llm.kimi_cli.asyncio.create_subprocess_exec",
        new=AsyncMock(return_value=fake_proc),
    ) as mock_exec:
        await default_provider.generate("prompt")

    cmd = mock_exec.await_args[0]
    assert cmd[0] == "kimi-from-settings"


@pytest.mark.asyncio
async def test_generate_stream_falls_back_on_not_implemented_error(
    provider: KimiCLIProvider,
) -> None:
    """TEST-1710: Falls back to threaded synchronous subprocess when the active
    event loop does not support asyncio subprocess transports."""
    chunks: list[str] = []

    async def on_chunk(text: str) -> None:
        chunks.append(text)

    with (
        patch(
            "app.services.llm.kimi_cli.asyncio.create_subprocess_exec",
            new=AsyncMock(side_effect=NotImplementedError()),
        ),
        patch(
            "app.services.llm.kimi_cli.subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="fallback result",
                stderr="",
            ),
        ) as mock_run,
    ):
        result = await provider.generate_stream("prompt", on_chunk=on_chunk)

    assert result == "fallback result"
    assert "".join(chunks) == "fallback result"
    mock_run.assert_called_once()
    kwargs = mock_run.call_args[1]
    assert kwargs["capture_output"] is True
    assert kwargs["env"]["PYTHONIOENCODING"] == "utf-8"
