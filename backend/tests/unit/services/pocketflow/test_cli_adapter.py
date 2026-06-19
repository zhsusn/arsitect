"""Tests for CLI adapters."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.pocketflow.cli_adapter import (
    CLIExecutionResult,
    ExecutionStatus,
    KimiCLIAdapter,
    MockCLIAdapter,
)


class TestKimiCLIAdapter:
    """Tests for KimiCLIAdapter."""

    @pytest.fixture
    def adapter(self) -> KimiCLIAdapter:
        """Create a KimiCLIAdapter with a fixed executable path."""
        return KimiCLIAdapter(kimi_cli_path="/usr/bin/kimi")

    def test_build_command_without_inputs(self, adapter: KimiCLIAdapter) -> None:
        """Command contains kimi run and the skill path."""
        cmd = adapter.build_command("/skills/brainstorming/SKILL.md")
        assert cmd == ["/usr/bin/kimi", "run", "/skills/brainstorming/SKILL.md"]

    def test_build_command_with_inputs(self, adapter: KimiCLIAdapter) -> None:
        """Command appends --input key=value for each input."""
        cmd = adapter.build_command(
            "/skills/brainstorming/SKILL.md",
            {"project_id": "proj-1", "topic": "new feature"},
        )
        assert cmd[0] == "/usr/bin/kimi"
        assert cmd[1] == "run"
        assert cmd[2] == "/skills/brainstorming/SKILL.md"
        assert "--input" in cmd
        assert "project_id=proj-1" in cmd
        assert "topic=new feature" in cmd

    @pytest.mark.asyncio
    async def test_execute_success(self, adapter: KimiCLIAdapter) -> None:
        """Successful subprocess execution returns SUCCESS status."""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"ok output", b""))

        with patch(
            "app.services.pocketflow.cli_adapter.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=mock_process),
        ) as mock_create:
            result = await adapter.execute(
                "/skills/brainstorming/SKILL.md",
                {"project_id": "proj-1"},
            )

        assert result.status == ExecutionStatus.SUCCESS
        assert result.exit_code == 0
        assert result.stdout == "ok output"
        assert result.stderr == ""
        assert result.skill_id == "SKILL"
        assert result.duration_ms >= 0

        mock_create.assert_awaited_once()
        _, call_kwargs = mock_create.call_args
        assert call_kwargs["stdout"] is not None
        assert call_kwargs["stderr"] is not None
        assert call_kwargs["env"]["PYTHONUNBUFFERED"] == "1"

    @pytest.mark.asyncio
    async def test_execute_failure(self, adapter: KimiCLIAdapter) -> None:
        """Non-zero exit code returns ERROR status."""
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b"", b"error msg"))

        with patch(
            "app.services.pocketflow.cli_adapter.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=mock_process),
        ):
            result = await adapter.execute("/skills/brainstorming/SKILL.md")

        assert result.status == ExecutionStatus.ERROR
        assert result.exit_code == 1
        assert result.stderr == "error msg"

    @pytest.mark.asyncio
    async def test_execute_timeout_kills_process(self, adapter: KimiCLIAdapter) -> None:
        """Timeout leads to KILLED status and process termination."""
        mock_process = MagicMock()
        mock_process.communicate = AsyncMock(side_effect=TimeoutError)
        mock_process.wait = AsyncMock(return_value=0)

        with patch(
            "app.services.pocketflow.cli_adapter.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=mock_process),
        ):
            result = await adapter.execute(
                "/skills/brainstorming/SKILL.md",
                timeout=0.01,
                kill_timeout=0.01,
            )

        assert result.status == ExecutionStatus.KILLED
        assert result.exit_code == -1
        assert "timed out" in result.stderr.lower()
        mock_process.terminate.assert_called_once()


class TestMockCLIAdapter:
    """Tests for MockCLIAdapter."""

    @pytest.mark.asyncio
    async def test_default_success_result(self) -> None:
        """Default result is successful."""
        adapter = MockCLIAdapter()
        result = await adapter.execute("/skills/brainstorming/SKILL.md")

        assert result.status == ExecutionStatus.SUCCESS
        assert result.exit_code == 0
        assert result.stdout == "mock stdout"

    @pytest.mark.asyncio
    async def test_per_skill_results(self) -> None:
        """Per-skill results take precedence."""
        error_result = CLIExecutionResult(
            skill_id="fail",
            status=ExecutionStatus.ERROR,
            exit_code=1,
            stdout="",
            stderr="boom",
            duration_ms=5,
        )
        adapter = MockCLIAdapter(results={"/skills/fail/SKILL.md": error_result})

        success = await adapter.execute("/skills/ok/SKILL.md")
        assert success.status == ExecutionStatus.SUCCESS

        failure = await adapter.execute("/skills/fail/SKILL.md")
        assert failure.status == ExecutionStatus.ERROR
        assert failure.stderr == "boom"

    @pytest.mark.asyncio
    async def test_default_override(self) -> None:
        """Default result can be overridden for all skills."""
        default = CLIExecutionResult(
            skill_id="x",
            status=ExecutionStatus.TIMEOUT,
            exit_code=0,
            stdout="",
            stderr="timeout",
            duration_ms=100,
        )
        adapter = MockCLIAdapter(result=default)
        result = await adapter.execute("/skills/any/SKILL.md")
        assert result.status == ExecutionStatus.TIMEOUT
