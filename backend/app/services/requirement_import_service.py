"""Service to import user stories from OpenSpec requirement artifacts."""

from __future__ import annotations

import pathlib
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError
from app.models.application import Application
from app.models.project import Project
from app.services.user_story_service import UserStoryService

# Regex patterns for parsing module-requirements.md
_MODULE_NAME_RE = re.compile(
    r"[\*\-]?\s*\*\*模块名称\*\*\s*[:：]\s*(.+?)(?:\s*$|\s+\*\*)",
    re.MULTILINE,
)
_USER_STORY_RE = re.compile(
    r"[\*\-]?\s*\*\*关联用户故事\*\*\s*[:：]\s*(.+?)(?:\s*$|\s+\*\*)",
    re.MULTILINE,
)
_PRIORITY_RE = re.compile(
    r"[\*\-]?\s*\*\*优先级\*\*\s*[:：]\s*(P\d)",
    re.MULTILINE,
)
_AC_TABLE_RE = re.compile(
    r"###\s*1\.\d+\s*验收标准.*?\n\n\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|\n\|:?[-:]+:?\|[^|]+\|[^|]+\|[^|]+\|\n(.*?)(?=\n##|\Z)",
    re.DOTALL,
)
_PAGE_LIST_RE = re.compile(
    r"###\s*2\.1\s*页面清单.*?\n\n\|[^|]+\|[^|]+\|[^|]+\|\n\|:?[-:]+:?\|[^|]+\|[^|]+\|\n(.*?)(?=\n##|\Z)",
    re.DOTALL,
)


def _parse_ac_criteria(ac_block: str) -> str:
    """Extract Given-When-Then lines from acceptance criteria table block."""
    lines: list[str] = []
    for row in ac_block.strip().split("\n"):
        row = row.strip()
        if not row or row.startswith("|") and "---" in row:
            continue
        cells = [c.strip() for c in row.split("|") if c.strip()]
        if len(cells) >= 3:
            # cells: [ID, Type, Description, Score]
            desc = cells[2]
            if desc and not desc.startswith("-"):
                lines.append(f"- {desc}")
    return "\n".join(lines)


def _parse_page_desc(page_block: str) -> str:
    """Extract page descriptions from page list table block."""
    lines: list[str] = []
    for row in page_block.strip().split("\n"):
        row = row.strip()
        if not row or row.startswith("|") and "---" in row:
            continue
        cells = [c.strip() for c in row.split("|") if c.strip()]
        if len(cells) >= 2:
            page_name = cells[0]
            page_desc = cells[1] if len(cells) > 1 else ""
            if page_name and not page_name.startswith("-"):
                lines.append(f"- {page_name}：{page_desc}")
    return "\n".join(lines)


def _extract_user_story_from_md(content: str) -> dict[str, Any] | None:
    """Parse a single module-requirements.md and return user story fields."""
    # Try to get module name
    module_name_match = _MODULE_NAME_RE.search(content)
    module_name = module_name_match.group(1).strip() if module_name_match else ""

    # Try to get associated user story line
    us_match = _USER_STORY_RE.search(content)
    us_line = us_match.group(1).strip() if us_match else ""

    # Derive title: prefer user story ID+name, fallback to module name
    title = us_line if us_line else module_name
    if not title:
        # Fallback: first H1 heading
        h1_match = re.search(r"^#\s+(.+?)$", content, re.MULTILINE)
        title = h1_match.group(1).strip() if h1_match else "未命名用户故事"

    # Priority mapping
    priority_match = _PRIORITY_RE.search(content)
    raw_priority = priority_match.group(1) if priority_match else "P1"
    # Map module-level priority to story priority
    priority = raw_priority if raw_priority in ("P0", "P1", "P2", "P3") else "P1"

    # Acceptance criteria from AC table
    ac_match = _AC_TABLE_RE.search(content)
    acceptance_criteria = ""
    if ac_match:
        acceptance_criteria = _parse_ac_criteria(ac_match.group(1))

    # Page description from page list
    page_match = _PAGE_LIST_RE.search(content)
    page_desc = ""
    if page_match:
        page_desc = _parse_page_desc(page_match.group(1))

    return {
        "title": title,
        "description": module_name,
        "acceptance_criteria": acceptance_criteria or None,
        "page_desc": page_desc or None,
        "priority": priority,
        "status": "DRAFT",
    }


class RequirementImportService:
    """Import user stories from OpenSpec detailed requirement artifacts."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session."""
        self._session = session
        self._story_svc = UserStoryService(session)

    async def import_user_stories(self, project_id: str) -> dict[str, Any]:
        """Scan openspec artifacts and import user stories for a project."""
        # Fetch project and its application
        project = await self._session.get(Project, project_id)
        if project is None:
            raise BadRequestError(detail=f"Project '{project_id}' not found")

        app = await self._session.get(Application, project.application_id)
        if app is None or not app.local_path:
            raise BadRequestError(
                detail="Project has no associated application or local path"
            )

        # Search openspec detailed requirements
        search_pattern = "openspec/changes/*/detailed-requirements/**/module-requirements.md"
        candidates: list[pathlib.Path] = []

        base_path = pathlib.Path(app.local_path)
        if base_path.exists():
            candidates = list(base_path.glob(search_pattern))

        # Fallback 1: if no openspec in app path, try current workspace (self-hosted mode)
        if not candidates:
            workspace_path = pathlib.Path(__file__).resolve().parents[3]
            candidates = list(workspace_path.glob(search_pattern))

        # Fallback 2: try project root (where this repo is checked out)
        if not candidates:
            project_root = pathlib.Path(__file__).resolve().parents[2]
            candidates = list(project_root.glob(search_pattern))

        if not candidates:
            raise BadRequestError(
                detail="No detailed requirement documents found in openspec/changes/*/detailed-requirements/"
            )

        imported: list[dict[str, Any]] = []
        skipped = 0

        # De-duplicate by title within this import
        seen_titles: set[str] = set()

        for md_path in candidates:
            try:
                content = md_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = md_path.read_text(encoding="gbk")
            except Exception:
                skipped += 1
                continue

            story_data = _extract_user_story_from_md(content)
            if not story_data:
                skipped += 1
                continue

            # Deduplicate
            if story_data["title"] in seen_titles:
                skipped += 1
                continue
            seen_titles.add(story_data["title"])

            # Check if already exists in DB (by title for this project)
            existing = await self._story_svc.find_by_title(project_id, story_data["title"])
            if existing:
                skipped += 1
                continue

            story = await self._story_svc.create_story(
                project_id=project_id,
                title=story_data["title"],
                description=story_data["description"],
                acceptance_criteria=story_data["acceptance_criteria"],
                page_desc=story_data["page_desc"],
                priority=story_data["priority"],
                status=story_data["status"],
            )
            imported.append(
                {
                    "story_id": story.story_id,
                    "title": story.title,
                }
            )

        await self._session.commit()

        return {
            "imported_count": len(imported),
            "skipped_count": skipped,
            "stories": imported,
        }
