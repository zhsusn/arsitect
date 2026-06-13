"""Tests for SkillParser."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.skill_parser import ParsedSkill, SkillParser


class TestSkillParser:
    """Test SkillParser with real Skill files."""

    @pytest.fixture
    def parser(self) -> SkillParser:
        """Return a SkillParser instance."""
        return SkillParser()

    def test_parse_existing_skill(self, parser: SkillParser) -> None:
        """Can parse an existing Skill from .agents/skills/."""
        skill_dir = Path(".agents/skills/brainstorming")
        if not skill_dir.exists():
            pytest.skip("brainstorming skill not found")

        result = parser.parse_skill_directory(str(skill_dir))
        assert isinstance(result, ParsedSkill)
        assert result.skill_name == "brainstorming"
        assert result.version == "2.2.0"
        assert result.pattern == "inversion"
        assert "sdlc" in result.tags
        assert "kimi" in result.platforms
        assert result.parse_status == "PARSED"

    def test_extract_frontmatter(self, parser: SkillParser) -> None:
        """Frontmatter extraction works correctly."""
        content = "---\nname: test-skill\ndescription: A test skill\n---\n\n# Heading"
        fm = parser._extract_frontmatter(content)
        assert fm["name"] == "test-skill"
        assert fm["description"] == "A test skill"

    def test_extract_frontmatter_missing(self, parser: SkillParser) -> None:
        """Missing frontmatter returns empty dict."""
        fm = parser._extract_frontmatter("# No frontmatter")
        assert fm == {}

    def test_validate_meta_json(self, parser: SkillParser) -> None:
        """Valid meta.json parses correctly."""
        raw = json.dumps({
            "name": "test",
            "version": "1.0.0",
            "pattern": "generator",
            "tags": ["a"],
            "platforms": ["kimi"],
        })
        meta = parser._validate_meta_json(raw)
        assert meta["name"] == "test"

    def test_validate_meta_json_missing_field(self, parser: SkillParser) -> None:
        """Missing required fields raise ValueError."""
        raw = json.dumps({"name": "test"})
        with pytest.raises(ValueError):
            parser._validate_meta_json(raw)

    def test_parse_missing_files(self, parser: SkillParser) -> None:
        """Missing SKILL.md raises ValueError."""
        with pytest.raises(ValueError):
            parser.parse_skill_directory("/nonexistent/path")

    def test_parse_skills_directory_coverage(self, parser: SkillParser) -> None:
        """Parse ≥ 90% of existing Skill files successfully."""
        skills_root = Path(".agents/skills")
        if not skills_root.exists():
            pytest.skip(".agents/skills not found")

        skill_dirs = [d for d in skills_root.iterdir() if d.is_dir()]
        if not skill_dirs:
            pytest.skip("No skill directories found")

        success = 0
        for skill_dir in skill_dirs:
            try:
                result = parser.parse_skill_directory(str(skill_dir))
                if result.parse_status == "PARSED":
                    success += 1
            except Exception:
                pass

        coverage = success / len(skill_dirs)
        assert coverage >= 0.9, f"Parsed {coverage:.0%} of {len(skill_dirs)} skills"

    def test_extract_frontmatter_malformed_yaml(self, parser: SkillParser) -> None:
        """TEST-1201: Malformed YAML frontmatter returns empty dict.

        Covers AC-F-003: Frontmatter parse error handling.
        """
        content = "---\nname: [unclosed\n---\n# Heading"
        fm = parser._extract_frontmatter(content)
        assert fm == {}

    def test_validate_meta_json_not_dict(self, parser: SkillParser) -> None:
        """TEST-1202: meta.json that is not a dict raises ValueError.

        Covers AC-F-004: Meta JSON validation.
        """
        raw = json.dumps("just a string")
        with pytest.raises(ValueError):
            parser._validate_meta_json(raw)

    def test_parse_skill_directory_meta_missing(self, parser: SkillParser) -> None:
        """TEST-1203: Directory with SKILL.md but no meta.json raises ValueError.

        Covers EX-004: Missing meta.json handling.
        """
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "partial-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: partial\n---\n", encoding="utf-8"
            )
            with pytest.raises(ValueError):
                parser.parse_skill_directory(str(skill_dir))

    def test_parse_skill_directory_frontmatter_fallback(self, parser: SkillParser) -> None:
        """TEST-1204: Falls back to meta.json name when frontmatter lacks name.

        Covers front/meta fallback logic.
        """
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "fallback-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\ndescription: no name here\n---\n", encoding="utf-8"
            )
            (skill_dir / "meta.json").write_text(
                json.dumps({
                    "name": "fallback-name",
                    "version": "1.0.0",
                    "pattern": "generator",
                    "tags": ["t1"],
                    "platforms": ["kimi"],
                }),
                encoding="utf-8",
            )
            result = parser.parse_skill_directory(str(skill_dir))
            assert result.skill_name == "fallback-name"
            assert result.parse_status == "PARSED"
