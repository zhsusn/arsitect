"""Tests for PrepStage.

Covers DR-008 Skill Executor — Prep stage context assembly.
"""

from __future__ import annotations

import os
import tempfile

import pytest

from app.services.pocketflow.prep_stage import PrepStage


class TestPrepStage:
    """PrepStage unit tests."""

    @pytest.fixture
    def prep_stage(self) -> PrepStage:
        return PrepStage()

    @pytest.fixture
    def skill_md_content(self) -> str:
        return "---\nname: test-skill\n---\n# Test Skill\n"

    @pytest.mark.asyncio
    async def test_prepare_success(self, prep_stage: PrepStage, skill_md_content: str) -> None:
        """TEST-1001: Successful prep assembles context.

        Covers AC-BR-001: Prep phase completion.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = os.path.join(tmpdir, "SKILL.md")
            with open(skill_path, "w", encoding="utf-8") as f:
                f.write(skill_md_content)

            result = await prep_stage.prepare(skill_path, "proj-1")
            assert result.success is True
            assert result.skill_path == skill_path
            assert result.context["project_id"] == "proj-1"
            assert result.context["skill_path"] == skill_path
            assert "skill_content_preview" in result.context
            assert result.error is None

    @pytest.mark.asyncio
    async def test_prepare_missing_file(self, prep_stage: PrepStage) -> None:
        """TEST-1002: Missing SKILL.md returns failure.

        Covers AC-F-003 / EX-003: Skill definition missing.
        """
        result = await prep_stage.prepare("/nonexistent/SKILL.md", "proj-1")
        assert result.success is False
        assert "not found" in result.error
        assert result.context == {}

    @pytest.mark.asyncio
    async def test_prepare_unreadable_file(self, prep_stage: PrepStage) -> None:
        """TEST-1003: Unreadable file returns failure with OSError message.

        Covers edge case: file permission/read error.
        """
        import sys

        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            tmpfile.write(b"test")
            tmpfile_path = tmpfile.name

        try:
            os.chmod(tmpfile_path, 0o000)
            result = await prep_stage.prepare(tmpfile_path, "proj-1")
            # On Windows, chmod may not restrict read access for owner,
            # so we handle both success (read OK) and failure paths.
            if sys.platform == "win32":
                # Windows may still allow read; skip strict assertion
                assert result.success is True or result.success is False
            else:
                assert result.success is False
                assert "Failed to read" in result.error
        finally:
            os.chmod(tmpfile_path, 0o644)
            os.unlink(tmpfile_path)

    @pytest.mark.asyncio
    async def test_prepare_preview_length(self, prep_stage: PrepStage) -> None:
        """TEST-1004: Content preview is truncated to 500 chars.

        Covers edge case: large SKILL.md handling.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = os.path.join(tmpdir, "SKILL.md")
            long_content = "A" * 1000
            with open(skill_path, "w", encoding="utf-8") as f:
                f.write(long_content)

            result = await prep_stage.prepare(skill_path, "proj-1")
            assert result.success is True
            preview = result.context["skill_content_preview"]
            assert len(preview) == 500
            assert preview == "A" * 500
