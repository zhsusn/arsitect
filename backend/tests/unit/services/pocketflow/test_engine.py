"""Tests for PocketFlowEngine."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from app.services.pocketflow.engine import PocketFlowEngine
from app.services.pocketflow.exec_stage import ExecResult


class TestPocketFlowEngine:
    """PocketFlowEngine tests."""

    @pytest.fixture
    def engine(self) -> PocketFlowEngine:
        """Create a fresh engine."""
        return PocketFlowEngine()

    @pytest.mark.asyncio
    async def test_prep_exec_post_sequence(self, engine: PocketFlowEngine) -> None:
        """prep → exec → post runs in sequence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text("# Test Skill")

            engine._exec.execute = AsyncMock(
                return_value=ExecResult(success=True, output="ok", duration_ms=100)
            )
            result = await engine.execute(
                skill_path=str(skill_path),
                project_id="proj-1",
                work_dir=tmpdir,
                expected_artifacts=[],
            )

            assert result.final_status == "PASSED"
            assert "prep" in result.phase_results
            assert "exec" in result.phase_results
            assert "post" in result.phase_results
            assert result.phase_results["prep"].status == "PASSED"
            assert result.phase_results["exec"].status == "PASSED"
            assert result.phase_results["post"].status == "PASSED"

    @pytest.mark.asyncio
    async def test_prep_fails_stops_pipeline(self, engine: PocketFlowEngine) -> None:
        """If prep fails, exec and post are not run."""
        result = await engine.execute(
            skill_path="/nonexistent/SKILL.md",
            project_id="proj-1",
            work_dir="/tmp",
            expected_artifacts=[],
        )
        assert result.final_status == "FAILED"
        assert result.phase_results["prep"].status == "FAILED"
        assert "exec" not in result.phase_results
        assert "post" not in result.phase_results

    @pytest.mark.asyncio
    async def test_exec_timeout(self, engine: PocketFlowEngine) -> None:
        """Exec timeout marks exec as FAILED."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text("# Test Skill")

            engine._exec.execute = AsyncMock(
                return_value=ExecResult(
                    success=False, output="", duration_ms=60000, error="Request timed out after 60s"
                )
            )
            result = await engine.execute(
                skill_path=str(skill_path),
                project_id="proj-1",
                work_dir=tmpdir,
                expected_artifacts=[],
            )

            assert result.final_status == "FAILED"
            assert result.phase_results["prep"].status == "PASSED"
            assert result.phase_results["exec"].status == "FAILED"
            assert "post" not in result.phase_results

    @pytest.mark.asyncio
    async def test_post_missing_artifact(self, engine: PocketFlowEngine) -> None:
        """Missing required artifact fails post stage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / "SKILL.md"
            skill_path.write_text("# Test Skill")

            engine._exec.execute = AsyncMock(
                return_value=ExecResult(success=True, output="ok", duration_ms=100)
            )
            result = await engine.execute(
                skill_path=str(skill_path),
                project_id="proj-1",
                work_dir=tmpdir,
                expected_artifacts=["missing.md"],
            )

            assert result.final_status == "FAILED"
            assert result.phase_results["post"].status == "FAILED"
            assert len(result.missing_artifacts) == 1
