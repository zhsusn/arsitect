"""Resolve skill identifiers to SKILL.md file paths."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.skill import Skill


class SkillResolver:
    """Resolve a skill ID or skill name to an absolute SKILL.md path."""

    def __init__(
        self,
        base_dir: str | Path | None = None,
        session: AsyncSession | None = None,
    ) -> None:
        """Initialize resolver.

        Args:
            base_dir: Base directory containing skill subdirectories. Defaults to
                the project-root ``.agents/skills`` directory.
            session: Optional async session for database lookups.
        """
        self._base_dir = Path(base_dir) if base_dir else settings.project_root / ".agents" / "skills"
        self._session = session

    async def resolve(self, skill_id: str) -> str:
        """Resolve ``skill_id`` to an absolute SKILL.md path.

        Resolution order:
        1. Database ``Skill.directory_path`` if a session is available.
        2. ``<base_dir>/<skill_id>/SKILL.md``.

        Args:
            skill_id: Skill identifier (usually the skill directory name).

        Returns:
            Absolute path to SKILL.md.

        Raises:
            FileNotFoundError: If no SKILL.md can be resolved.
        """
        if self._session is not None:
            db_path = await self._resolve_from_db(skill_id)
            if db_path is not None:
                return str(db_path)

        local_path = self._base_dir / skill_id / "SKILL.md"
        if local_path.exists():
            return str(local_path.resolve())

        raise FileNotFoundError(
            f"SKILL.md not found for skill '{skill_id}' under {self._base_dir}"
        )

    async def _resolve_from_db(self, skill_id: str) -> Path | None:
        """Look up the skill in the registry and return its SKILL.md path."""
        assert self._session is not None
        stmt = select(Skill).where(
            (Skill.skill_id == skill_id) | (Skill.skill_name == skill_id)
        )
        result = await self._session.execute(stmt)
        skill = result.scalar_one_or_none()
        if skill is None:
            return None
        directory = Path(skill.directory_path)
        skill_md = directory / "SKILL.md"
        if skill_md.exists():
            return skill_md.resolve()
        # If the stored directory does not contain SKILL.md, fall back to the
        # local skill directory using the skill name.
        local_path = self._base_dir / skill_id / "SKILL.md"
        if local_path.exists():
            return local_path.resolve()
        return None

    def resolve_sync(self, skill_id: str) -> str:
        """Synchronous version that only checks the local file system.

        Args:
            skill_id: Skill identifier.

        Returns:
            Absolute path to SKILL.md.

        Raises:
            FileNotFoundError: If SKILL.md is not found locally.
        """
        local_path = self._base_dir / skill_id / "SKILL.md"
        if local_path.exists():
            return str(local_path.resolve())
        raise FileNotFoundError(
            f"SKILL.md not found for skill '{skill_id}' under {self._base_dir}"
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable description for debugging."""
        return {
            "base_dir": str(self._base_dir),
            "has_session": self._session is not None,
        }
