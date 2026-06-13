"""Prep stage: context assembly."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PrepResult:
    """Result of prep stage."""

    success: bool
    skill_path: str
    context: dict[str, str]
    error: str | None = None


class PrepStage:
    """Assemble execution context by reading SKILL.md and project info."""

    async def prepare(
        self,
        skill_path: str,
        project_id: str,
    ) -> PrepResult:
        """Prepare execution context.

        Args:
            skill_path: Absolute path to SKILL.md.
            project_id: Project identifier.

        Returns:
            PrepResult with assembled context.
        """
        path = Path(skill_path)
        if not path.exists():
            return PrepResult(
                success=False,
                skill_path=skill_path,
                context={},
                error=f"SKILL.md not found at {skill_path}",
            )

        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            return PrepResult(
                success=False,
                skill_path=skill_path,
                context={},
                error=f"Failed to read SKILL.md: {exc}",
            )

        context = {
            "skill_path": skill_path,
            "project_id": project_id,
            "skill_content_preview": content[:500],
        }
        return PrepResult(
            success=True,
            skill_path=skill_path,
            context=context,
        )
