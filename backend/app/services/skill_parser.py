"""Skill file parser — handles Frontmatter and meta.json."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ParsedSkill:
    """Result of parsing a Skill directory."""

    skill_name: str
    description: str
    version: str
    pattern: str
    tags: list[str]
    platforms: list[str]
    directory_path: str
    parse_status: str = "PARSED"
    parse_error_reason: str | None = None


class SkillParser:
    """Parse SKILL.md Frontmatter and meta.json from a Skill directory."""

    FRONTMATTER_RE = re.compile(
        r"^---\s*\n(.*?)\n---\s*\n",
        re.DOTALL,
    )

    def parse_skill_directory(self, dir_path: str) -> ParsedSkill:
        """Parse a single Skill directory.

        Args:
            dir_path: Absolute path to the Skill directory.

        Returns:
            ParsedSkill with extracted metadata.

        Raises:
            ValueError: If required files are missing or malformed.
        """
        path = Path(dir_path)
        skill_md = path / "SKILL.md"
        meta_json = path / "meta.json"

        if not skill_md.exists():
            raise ValueError(f"SKILL.md not found in {dir_path}")
        if not meta_json.exists():
            raise ValueError(f"meta.json not found in {dir_path}")

        md_content = skill_md.read_text(encoding="utf-8")
        meta_content = meta_json.read_text(encoding="utf-8")

        frontmatter = self._extract_frontmatter(md_content)
        meta = self._validate_meta_json(meta_content)

        name = frontmatter.get("name", meta.get("name", ""))
        description = frontmatter.get("description", "")

        return ParsedSkill(
            skill_name=name,
            description=description,
            version=meta.get("version", "0.0.0"),
            pattern=meta.get("pattern", "tool-wrapper"),
            tags=meta.get("tags", []),
            platforms=meta.get("platforms", []),
            directory_path=str(path.resolve()),
        )

    def _extract_frontmatter(self, content: str) -> dict[str, Any]:
        """Extract YAML Frontmatter from SKILL.md content."""
        match = self.FRONTMATTER_RE.search(content)
        if not match:
            return {}
        try:
            return yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            return {}

    def _validate_meta_json(self, content: str) -> dict[str, Any]:
        """Parse and validate meta.json content."""
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError("meta.json must be a JSON object")
        required = {"name", "version", "pattern", "tags", "platforms"}
        missing = required - set(data.keys())
        if missing:
            raise ValueError(f"meta.json missing fields: {missing}")
        return data
