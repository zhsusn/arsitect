"""Tests for PocketFlowEngine (Batch-02 design doc implementation)."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from app.common.project_context import ProjectContext
from app.engine.pocketflow_engine import (
    ExecutionResult,
    ExecutionStatus,
    HTTPAdapter,
    KimiCLIAdapter,
    PocketFlowEngine,
    SkillConfig,
)


class TestKimiCLIAdapter:
    """KimiCLIAdapter unit tests."""

    def test_build_command(self) -> None:
        """Command includes skill path and inputs."""
        adapter = KimiCLIAdapter()
        cmd = adapter.build_command("skill.py", {"input": "/path/to/input.md"})
        assert cmd == ["kimi", "run", "skill.py", "--input", "input=/path/to/input.md"]

    def test_build_command_multiple_inputs(self) -> None:
        """Multiple inputs are all appended."""
        adapter = KimiCLIAdapter()
        cmd = adapter.build_command("skill.py", {"a": "1", "b": "2"})
        assert "--input" in cmd
        assert "a=1" in cmd
        assert "b=2" in cmd

    @pytest.mark.asyncio
    async def test_execute_success(self, monkeypatch) -> None:
        """Successful execution returns SUCCESS status."""
        adapter = KimiCLIAdapter()
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"stdout", b"stderr"))

        monkeypatch.setattr(
            asyncio,
            "create_subprocess_exec",
            AsyncMock(return_value=mock_process),
        )

        result = await adapter.execute("test_skill.md", {})
        assert result.status == ExecutionStatus.SUCCESS
        assert result.exit_code == 0
        assert result.stdout == "stdout"
        assert result.stderr == "stderr"

    @pytest.mark.asyncio
    async def test_execute_timeout_sigkill(self, monkeypatch) -> None:
        """Timeout triggers SIGTERM then SIGKILL."""
        adapter = KimiCLIAdapter()
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(
            side_effect=asyncio.TimeoutError
        )
        # First wait after terminate times out, then kill succeeds
        mock_process.wait = AsyncMock(
            side_effect=[asyncio.TimeoutError, None]
        )

        monkeypatch.setattr(
            asyncio,
            "create_subprocess_exec",
            AsyncMock(return_value=mock_process),
        )

        result = await adapter.execute("test.md", {}, timeout=0.1, kill_timeout=0.1)
        assert result.status == ExecutionStatus.KILLED
        assert result.exit_code == -1
        assert "SIGKILL" in result.stderr or "timed out" in result.stderr
        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()


class TestHTTPAdapter:
    """HTTPAdapter unit tests."""

    @pytest.mark.asyncio
    async def test_execute_success(self, monkeypatch) -> None:
        """HTTP 200 returns SUCCESS."""
        adapter = HTTPAdapter(endpoint="http://test/api")

        class FakeResponse:
            status_code = 200
            text = '{"ok": true}'

        monkeypatch.setattr(
            "httpx.AsyncClient.post",
            AsyncMock(return_value=FakeResponse()),
        )

        result = await adapter.execute("skill.md", {})
        assert result.status == ExecutionStatus.SUCCESS
        assert result.exit_code == 200
        assert result.stdout == '{"ok": true}'

    @pytest.mark.asyncio
    async def test_execute_timeout(self, monkeypatch) -> None:
        """HTTP timeout returns TIMEOUT status."""
        adapter = HTTPAdapter(endpoint="http://test/api")

        import httpx

        monkeypatch.setattr(
            "httpx.AsyncClient.post",
            AsyncMock(side_effect=httpx.TimeoutException("timeout")),
        )

        result = await adapter.execute("skill.md", {}, timeout=0.1)
        assert result.status == ExecutionStatus.TIMEOUT
        assert "timed out" in result.stderr


class TestPocketFlowEngine:
    """PocketFlowEngine three-phase tests."""

    @pytest.fixture
    def engine(self) -> PocketFlowEngine:
        """Engine with mock CLI adapter."""
        adapter = AsyncMock()
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = ProjectContext("test-proj", base_dir=tmpdir)
            ctx.artifacts_dir.mkdir(parents=True, exist_ok=True)
            yield PocketFlowEngine(adapter, ctx)

    @pytest.mark.asyncio
    async def test_prep_missing_input(self, engine: PocketFlowEngine) -> None:
        """PREP fails when input artifact is missing."""
        skill = SkillConfig(
            skill_id="test",
            name="Test",
            file_path="skill.md",
            inputs=["nonexistent.md"],
            outputs=["out.md"],
        )
        with pytest.raises(FileNotFoundError):
            await engine._prep_phase(skill)

    @pytest.mark.asyncio
    async def test_prep_success(self, engine: PocketFlowEngine) -> None:
        """PREP succeeds when inputs exist and computes hashes."""
        skill = SkillConfig(
            skill_id="test",
            name="Test",
            file_path="skill.md",
            inputs=["in.md"],
            outputs=["out.md"],
        )
        (engine.ctx.artifacts_dir / "in.md").write_text("hello")

        prep = await engine._prep_phase(skill)
        assert "input_hashes" in prep
        assert "in.md" in prep["input_hashes"]
        assert prep["input_paths"]["in.md"].endswith("in.md")

    @pytest.mark.asyncio
    async def test_exec_writes_log(self, engine: PocketFlowEngine) -> None:
        """EXEC writes log file to disk."""
        engine.cli.execute = AsyncMock(
            return_value=ExecutionResult(
                skill_id="test",
                status=ExecutionStatus.SUCCESS,
                exit_code=0,
                stdout="ok",
                stderr="",
                output_artifacts=[],
                log_path="",
                duration_ms=100,
            )
        )

        skill = SkillConfig(
            skill_id="test",
            name="Test",
            file_path="skill.md",
            inputs=[],
            outputs=[],
        )
        prep = {"input_hashes": {}, "input_paths": {}, "work_dir": str(engine.ctx.artifacts_dir)}
        result = await engine._exec_phase(skill, prep)

        assert result.status == ExecutionStatus.SUCCESS
        assert result.log_path != ""
        assert Path(result.log_path).exists()

    @pytest.mark.asyncio
    async def test_post_collects_outputs(self, engine: PocketFlowEngine) -> None:
        """POST collects existing output artifacts."""
        skill = SkillConfig(
            skill_id="test",
            name="Test",
            file_path="skill.md",
            inputs=[],
            outputs=["out.md", "missing.md"],
        )
        (engine.ctx.artifacts_dir / "out.md").write_text("output")

        exec_result = ExecutionResult(
            skill_id="test",
            status=ExecutionStatus.SUCCESS,
            exit_code=0,
            stdout="",
            stderr="",
            output_artifacts=[],
            log_path="",
            duration_ms=50,
        )
        result = await engine._post_phase(skill, exec_result)
        assert "out.md" in result.output_artifacts
        assert "missing.md" not in result.output_artifacts

    @pytest.mark.asyncio
    async def test_full_pipeline(self, engine: PocketFlowEngine) -> None:
        """Full Prep → Exec → Post pipeline."""
        (engine.ctx.artifacts_dir / "in.md").write_text("input")
        engine.cli.execute = AsyncMock(
            return_value=ExecutionResult(
                skill_id="test",
                status=ExecutionStatus.SUCCESS,
                exit_code=0,
                stdout="ok",
                stderr="",
                output_artifacts=[],
                log_path="",
                duration_ms=100,
            )
        )

        skill = SkillConfig(
            skill_id="test",
            name="Test",
            file_path="skill.md",
            inputs=["in.md"],
            outputs=["out.md"],
        )
        (engine.ctx.artifacts_dir / "out.md").write_text("output")

        result = await engine.execute(skill)
        assert result.status == ExecutionStatus.SUCCESS
        assert result.log_path != ""
