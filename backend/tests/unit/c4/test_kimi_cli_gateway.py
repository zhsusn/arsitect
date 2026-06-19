"""Unit tests for the governance auto-fix Kimi CLI gateway."""

from __future__ import annotations

import subprocess
from typing import Any
from unittest.mock import patch

import pytest

from app.c4.governance_fix.llm_gateway import KimiCLIGateway, _strip_surrogates


@pytest.fixture
def gateway() -> KimiCLIGateway:
    """Return a KimiCLIGateway wired to a fake executable path."""
    return KimiCLIGateway(cli_path="/fake/kimi")


def _completed(stdout: str, stderr: str, returncode: int) -> subprocess.CompletedProcess[str]:
    """Build a ``subprocess.CompletedProcess`` for tests."""
    return subprocess.CompletedProcess(
        args=["kimi"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


@pytest.mark.asyncio
async def test_generate_returns_stdout(gateway: KimiCLIGateway) -> None:
    """TEST-1713: generate returns stripped stdout on success."""
    with patch("app.c4.governance_fix.llm_gateway.subprocess.run") as mock_run:
        mock_run.return_value = _completed("hello world\n", "", 0)
        result = await gateway.generate("prompt")

    assert result == "hello world"
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "/fake/kimi"
    assert "--quiet" in cmd
    assert "--max-steps-per-turn" in cmd
    assert cmd[cmd.index("--max-steps-per-turn") + 1] == "1"
    assert "-p" in cmd


@pytest.mark.asyncio
async def test_generate_stream_emits_chunks(gateway: KimiCLIGateway) -> None:
    """TEST-1714: generate_stream emits command prefix and result chunks."""
    chunks: list[str] = []

    async def on_chunk(text: str) -> None:
        chunks.append(text)

    with patch("app.c4.governance_fix.llm_gateway.subprocess.run") as mock_run:
        mock_run.return_value = _completed("result", "", 0)
        result = await gateway.generate_stream("prompt", on_chunk=on_chunk)

    assert result == "result"
    assert any("执行命令" in chunk for chunk in chunks)
    assert "result" in chunks


@pytest.mark.asyncio
async def test_generate_injects_env_vars(gateway: KimiCLIGateway) -> None:
    """TEST-1715: PYTHONIOENCODING and KIMI_CLI_NO_ANALYTICS are set."""
    with patch("app.c4.governance_fix.llm_gateway.subprocess.run") as mock_run:
        mock_run.return_value = _completed("ok", "", 0)
        await gateway.generate("prompt")

    kwargs = mock_run.call_args[1]
    env = kwargs["env"]
    assert env["PYTHONIOENCODING"] == "utf-8"
    assert env["KIMI_CLI_NO_ANALYTICS"] == "1"


@pytest.mark.asyncio
async def test_generate_prefixed_with_tool_ban(gateway: KimiCLIGateway) -> None:
    """TEST-1716: The prompt is prefixed with the tool-ban system instruction."""
    with patch("app.c4.governance_fix.llm_gateway.subprocess.run") as mock_run:
        mock_run.return_value = _completed("ok", "", 0)
        await gateway.generate("user prompt")

    cmd = mock_run.call_args[0][0]
    prompt_arg = cmd[cmd.index("-p") + 1]
    assert "禁止调用任何工具" in prompt_arg
    assert "user prompt" in prompt_arg


@pytest.mark.asyncio
async def test_generate_timeout_raises(gateway: KimiCLIGateway) -> None:
    """TEST-1717: A subprocess timeout is converted to a RuntimeError."""
    with patch("app.c4.governance_fix.llm_gateway.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="kimi", timeout=120)
        with pytest.raises(RuntimeError, match="Kimi CLI timed out"):
            await gateway.generate("prompt")


@pytest.mark.asyncio
async def test_generate_nonzero_exit_with_output_returns_output(
    gateway: KimiCLIGateway,
) -> None:
    """TEST-1718: Non-zero exit code with captured output is treated as success."""
    with patch("app.c4.governance_fix.llm_gateway.subprocess.run") as mock_run:
        mock_run.return_value = _completed("partial result", "step limit", 1)
        result = await gateway.generate("prompt")

    assert result == "partial result"


@pytest.mark.asyncio
async def test_generate_nonzero_exit_without_output_raises(
    gateway: KimiCLIGateway,
) -> None:
    """TEST-1719: Non-zero exit code with no output raises RuntimeError."""
    with patch("app.c4.governance_fix.llm_gateway.subprocess.run") as mock_run:
        mock_run.return_value = _completed("", "fatal error", 1)
        with pytest.raises(RuntimeError, match="Kimi CLI failed"):
            await gateway.generate("prompt")


def test_strip_surrogates_removes_utf16_replacement() -> None:
    """TEST-1720: UTF-16 surrogate characters are stripped from text."""
    raw = "hello \ud800\udc00world"
    cleaned = _strip_surrogates(raw)
    assert "\ud800" not in cleaned
    assert cleaned == "hello world"


@pytest.mark.asyncio
async def test_generate_json_parses_markdown_fence(gateway: KimiCLIGateway) -> None:
    """TEST-1721: generate_json strips markdown fences before parsing JSON."""
    with patch("app.c4.governance_fix.llm_gateway.subprocess.run") as mock_run:
        mock_run.return_value = _completed('```json\n{"a": 1}\n```', "", 0)
        result = await gateway.generate_json("prompt")

    assert result == {"a": 1}


@pytest.mark.asyncio
async def test_generate_json_invalid_raises(gateway: KimiCLIGateway) -> None:
    """TEST-1722: Invalid JSON response raises ValueError."""
    with patch("app.c4.governance_fix.llm_gateway.subprocess.run") as mock_run:
        mock_run.return_value = _completed("not json", "", 0)
        with pytest.raises(ValueError, match="LLM response is not valid JSON"):
            await gateway.generate_json("prompt")


@pytest.mark.asyncio
async def test_generate_uses_settings_default_path(monkeypatch: Any) -> None:
    """TEST-1723: Gateway falls back to settings.KIMI_CLI_PATH when no path is given."""
    monkeypatch.setattr(
        "app.c4.governance_fix.llm_gateway.settings.KIMI_CLI_PATH", "kimi-from-settings"
    )
    default_gateway = KimiCLIGateway()

    with patch("app.c4.governance_fix.llm_gateway.subprocess.run") as mock_run:
        mock_run.return_value = _completed("ok", "", 0)
        await default_gateway.generate("prompt")

    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "kimi-from-settings"
