"""Tests for PostStage.

Covers DR-008 Skill Executor — Post stage artifact validation.
"""

from __future__ import annotations

import os
import tempfile

import pytest

from app.services.pocketflow.post_stage import PostStage


class TestPostStage:
    """PostStage unit tests."""

    @pytest.fixture
    def post_stage(self) -> PostStage:
        return PostStage()

    @pytest.fixture
    def work_dir(self) -> str:
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.mark.asyncio
    async def test_finalize_all_valid(self, post_stage: PostStage, work_dir: str) -> None:
        """TEST-0901: All artifacts valid — success.

        Covers AC-F-003: Artifact validation pass.
        """
        # Create valid artifacts
        for name in ("doc.md", "config.yaml", "data.json"):
            path = os.path.join(work_dir, name)
            with open(path, "w") as f:
                f.write("# test")

        result = await post_stage.finalize(
            expected_artifacts=["doc.md", "config.yaml", "data.json"],
            work_dir=work_dir,
        )
        assert result.success is True
        assert result.report.valid_count == 3
        assert result.report.missing_count == 0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_finalize_missing_artifact(self, post_stage: PostStage, work_dir: str) -> None:
        """TEST-0902: Missing artifact — failure.

        Covers AC-F-003: Artifact missing detection.
        """
        result = await post_stage.finalize(
            expected_artifacts=["missing.md"],
            work_dir=work_dir,
        )
        assert result.success is False
        assert result.report.missing_count == 1
        assert result.report.valid_count == 0
        assert "1 artifacts missing" in result.error

    @pytest.mark.asyncio
    async def test_finalize_oversized_artifact(self, post_stage: PostStage, work_dir: str) -> None:
        """TEST-0903: Artifact > 10MB generates warning.

        Covers edge case: oversized artifact handling.
        """
        large_file = os.path.join(work_dir, "large.md")
        # Write 11MB
        with open(large_file, "wb") as f:
            f.write(b"x" * (11 * 1024 * 1024))

        result = await post_stage.finalize(
            expected_artifacts=["large.md"],
            work_dir=work_dir,
        )
        assert result.success is True
        assert result.report.missing_count == 0
        assert len(result.report.warnings) == 1
        assert result.report.warnings[0]["warning_type"] == "OVERSIZED"

    @pytest.mark.asyncio
    async def test_finalize_invalid_format(self, post_stage: PostStage, work_dir: str) -> None:
        """TEST-0904: Unsupported file format generates warning and invalid count.

        Covers AC-F-003: Format validation.
        """
        bad_file = os.path.join(work_dir, "script.py")
        with open(bad_file, "w") as f:
            f.write("print('hello')")

        result = await post_stage.finalize(
            expected_artifacts=["script.py"],
            work_dir=work_dir,
        )
        assert result.success is True
        assert result.report.invalid_count == 1
        assert result.report.valid_count == 0
        assert len(result.report.warnings) == 1
        assert result.report.warnings[0]["warning_type"] == "FORMAT_INVALID"

    @pytest.mark.asyncio
    async def test_finalize_mixed_artifacts(self, post_stage: PostStage, work_dir: str) -> None:
        """TEST-0905: Mix of valid, missing, and invalid artifacts.

        Covers comprehensive artifact validation.
        """
        # Valid
        with open(os.path.join(work_dir, "valid.md"), "w") as f:
            f.write("# valid")
        # Invalid format
        with open(os.path.join(work_dir, "bad.exe"), "wb") as f:
            f.write(b"\x00")

        result = await post_stage.finalize(
            expected_artifacts=["valid.md", "missing.yml", "bad.exe"],
            work_dir=work_dir,
        )
        assert result.success is False
        assert result.report.valid_count == 1
        assert result.report.missing_count == 1
        assert result.report.invalid_count == 1
        assert len(result.report.warnings) == 2

    @pytest.mark.asyncio
    async def test_finalize_empty_list(self, post_stage: PostStage, work_dir: str) -> None:
        """TEST-0906: Empty expected artifacts list succeeds.

        Covers edge case: no artifacts required.
        """
        result = await post_stage.finalize(
            expected_artifacts=[],
            work_dir=work_dir,
        )
        assert result.success is True
        assert result.report.valid_count == 0
        assert result.report.missing_count == 0
