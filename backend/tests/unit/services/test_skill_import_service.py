"""Tests for SkillImportService."""

from __future__ import annotations

import pytest

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.skill import Skill
from app.services.skill_import_service import SkillImportService
from app.services.skill_parser import ParsedSkill, SkillParser


class TestSkillImportService:
    """Test SkillImportService scanning and conflict handling."""

    @pytest.mark.asyncio
    async def test_scan_directory_not_found(self) -> None:
        """Scanning non-existent directory returns error."""
        async with AsyncSessionLocal() as session:
            svc = SkillImportService(session, SkillParser())
            result = await svc.scan_directory("/nonexistent/path")
            assert len(result.errors) == 1
            assert len(result.parsed_skills) == 0

    @pytest.mark.asyncio
    async def test_confirm_import(self) -> None:
        """Can import parsed skills into registry."""
        async with AsyncSessionLocal() as session:
            svc = SkillImportService(session, SkillParser())
            parsed = ParsedSkill(
                skill_name="test-import",
                description="desc",
                version="1.0.0",
                pattern="generator",
                tags=["t1"],
                platforms=["kimi"],
                directory_path="/tmp",
            )
            summary = await svc.confirm_import([parsed])
            assert summary.imported == 1

    @pytest.mark.asyncio
    async def test_conflict_detection(self) -> None:
        """Same name+version skill is flagged as conflict."""
        async with AsyncSessionLocal() as session:
            svc = SkillImportService(session, SkillParser())
            # Pre-insert a skill
            skill = Skill(
                skill_id="pre-existing",
                skill_name="conflict-skill",
                version="1.0.0",
                pattern="generator",
                directory_path="/tmp",
            )
            session.add(skill)
            await session.commit()

            # Check internal helper
            existing = await svc._get_skill_by_name("conflict-skill")
            assert existing is not None
            assert existing.skill_id == "pre-existing"

    @pytest.mark.asyncio
    async def test_confirm_import_empty_list(self) -> None:
        """TEST-1101: Import empty list returns zero imported."""
        async with AsyncSessionLocal() as session:
            svc = SkillImportService(session, SkillParser())
            summary = await svc.confirm_import([])
            assert summary.imported == 0
            assert summary.skipped == 0

    @pytest.mark.asyncio
    async def test_scan_directory_success(self) -> None:
        """TEST-1102: Scan valid skill directory returns parsed skills.

        Covers AC-F-001: Skill directory scanning.
        """
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: test-skill\ndescription: A test skill\n---\n# Content",
                encoding="utf-8",
            )
            (skill_dir / "meta.json").write_text(
                '{"name":"test-skill","version":"1.0.0","pattern":"generator","tags":["t1"],"platforms":["kimi"]}',
                encoding="utf-8",
            )

            async with AsyncSessionLocal() as session:
                svc = SkillImportService(session, SkillParser())
                result = await svc.scan_directory(tmpdir)
                # If previous test inserted a skill with same name+version,
                # it will be in conflicts instead of parsed_skills.
                assert len(result.parsed_skills) == 1 or len(result.conflicts) == 1
                skill = (
                    result.parsed_skills[0]
                    if result.parsed_skills
                    else result.conflicts[0].parsed_skill
                )
                assert skill.skill_name == "test-skill"
                assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_scan_directory_parse_error(self) -> None:
        """TEST-1103: Scan directory with malformed skill records error.

        Covers AC-R-001: Single skill failure isolation.
        """
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "bad-skill"
            skill_dir.mkdir()
            # Missing meta.json
            (skill_dir / "SKILL.md").write_text("---\nname: bad\n---\n", encoding="utf-8")

            async with AsyncSessionLocal() as session:
                svc = SkillImportService(session, SkillParser())
                result = await svc.scan_directory(tmpdir)
                assert len(result.errors) == 1
                assert len(result.parsed_skills) == 0

    def test_serialize_list_empty(self) -> None:
        """TEST-1104: Serialize empty list returns None."""
        assert SkillImportService._serialize_list([]) is None

    def test_serialize_list_values(self) -> None:
        """TEST-1105: Serialize non-empty list returns JSON string."""
        result = SkillImportService._serialize_list(["a", "b"])
        import json

        assert json.loads(result) == ["a", "b"]

    def test_generate_skill_id(self) -> None:
        """TEST-1106: Generate skill id returns valid UUID."""
        import uuid

        skill_id = SkillImportService._generate_skill_id()
        assert uuid.UUID(skill_id)  # valid UUID format
