"""Skill import service — scanning and conflict handling."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill
from app.services.skill_parser import ParsedSkill, SkillParser


@dataclass
class SkillConflictItem:
    """A single conflict with existing skill info."""

    parsed_skill: ParsedSkill
    existing_skill: Skill | None = None


@dataclass
class SkillScanResult:
    """Result of scanning a directory for Skills."""

    parsed_skills: list[ParsedSkill] = field(default_factory=list)
    conflicts: list[SkillConflictItem] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class SkillImportSummary:
    """Summary after confirming import decisions."""

    imported: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class ConflictResolution:
    """Resolution decision for a single conflict."""

    skill_name: str
    action: str  # overwrite | skip | rename
    new_name: str | None = None


class SkillImportService:
    """Orchestrates Skill scanning, parsing, and conflict resolution."""

    def __init__(
        self,
        session: AsyncSession,
        parser: SkillParser,
    ) -> None:
        """Initialize with session and parser."""
        self._session = session
        self._parser = parser

    async def scan_directory(
        self,
        directory_path: str,
    ) -> SkillScanResult:
        """Scan a directory for Skill folders and parse them.

        Returns parsed skills, conflicts (same name already
        registered), and parse errors.
        """
        result = SkillScanResult()
        root = Path(directory_path)

        # Fallback to project root if relative path not found under cwd
        if not root.exists() and not root.is_absolute():
            project_root = Path(__file__).resolve().parents[3]
            root = project_root / directory_path

        if not root.exists():
            result.errors.append(f"Directory not found: {directory_path}")
            return result

        skill_dirs = [d for d in root.iterdir() if d.is_dir()]
        for skill_dir in skill_dirs:
            try:
                parsed = self._parser.parse_skill_directory(str(skill_dir))
            except Exception as exc:
                result.errors.append(f"{skill_dir.name}: {exc}")
                continue

            # Check for existing skill with same name
            existing = await self._get_skill_by_name(parsed.skill_name)
            if existing:
                result.conflicts.append(
                    SkillConflictItem(parsed_skill=parsed, existing_skill=existing)
                )
            else:
                result.parsed_skills.append(parsed)

        return result

    async def confirm_import(
        self,
        skills_to_import: list[ParsedSkill],
        resolutions: list[ConflictResolution] | None = None,
    ) -> SkillImportSummary:
        """Persist skills to the registry with conflict resolutions."""
        summary = SkillImportSummary()
        resolution_map = {r.skill_name: r for r in (resolutions or [])}

        all_skills = list(skills_to_import)

        for parsed in all_skills:
            resolution = resolution_map.get(parsed.skill_name)
            if resolution:
                if resolution.action == "skip":
                    summary.skipped += 1
                    continue
                elif resolution.action == "rename" and resolution.new_name:
                    parsed = self._rename_skill(parsed, resolution.new_name)
                elif resolution.action == "overwrite":
                    existing = await self._get_skill_by_name(parsed.skill_name)
                    if existing:
                        await self._session.delete(existing)

            try:
                skill = Skill(
                    skill_id=self._generate_skill_id(),
                    skill_name=parsed.skill_name,
                    version=parsed.version,
                    pattern=parsed.pattern,
                    tags=self._serialize_list(parsed.tags),
                    platforms=self._serialize_list(parsed.platforms),
                    description=parsed.description,
                    directory_path=parsed.directory_path,
                    parse_status=parsed.parse_status,
                    parse_error_reason=parsed.parse_error_reason,
                )
                self._session.add(skill)
                summary.imported += 1
            except Exception as exc:
                summary.errors.append(f"{parsed.skill_name}: {exc}")
                summary.skipped += 1

        await self._session.commit()
        return summary

    async def _get_skill_by_name(
        self,
        skill_name: str,
    ) -> Skill | None:
        """Check if a skill with the same name exists."""
        stmt = select(Skill).where(Skill.skill_name == skill_name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _rename_skill(parsed: ParsedSkill, new_name: str) -> ParsedSkill:
        """Return a new ParsedSkill with renamed skill_name."""
        return ParsedSkill(
            skill_name=new_name,
            description=parsed.description,
            version=parsed.version,
            pattern=parsed.pattern,
            tags=parsed.tags,
            platforms=parsed.platforms,
            directory_path=parsed.directory_path,
            parse_status=parsed.parse_status,
            parse_error_reason=parsed.parse_error_reason,
        )

    @staticmethod
    def _generate_skill_id() -> str:
        """Generate a UUID v4 string."""
        import uuid

        return str(uuid.uuid4())

    @staticmethod
    def _serialize_list(items: list[str]) -> str | None:
        """Serialize a list to JSON string or None if empty."""
        import json

        if not items:
            return None
        return json.dumps(items)
