"""SketchService — CRUD + generation orchestration for sketches.

V2: Primary generation path is now `generate_from_requirements()` which
reads module-requirements.md directly. The old `generate_from_stories()`
path is kept for backward compatibility.
"""

from __future__ import annotations

import json
import pathlib
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.application import Application
from app.models.project import Project
from app.models.sketch import Sketch
from app.models.user_story import UserStory
from app.services.page_spec_resolver import (
    flatten_specs_to_pages,
    resolve_project_specs,
)
from app.services.sketch_generator import (
    generate_sketch_from_module_specs,
    generate_sketch_from_stories,
)
from app.services.sketch_page_service import SketchPageService
from app.services.story_path_validator import validate_story_paths


class SketchService:
    """Handle sketch lifecycle and generation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session.

        Args:
            session: Async SQLAlchemy session.
        """
        self._session = session

    async def create_sketch(
        self,
        project_id: str,
        name: str,
        source_story_ids: str | None,
        status: str,
    ) -> Sketch:
        """Create a new sketch session."""
        if status not in {"DRAFT", "GENERATING", "GENERATED", "REVIEW_PENDING", "APPROVED", "REJECTED", "ARCHIVED"}:
            raise BadRequestError(detail="Invalid status value")

        sketch = Sketch(
            sketch_id=f"sketch-{uuid.uuid4()}",
            project_id=project_id,
            name=name,
            source_story_ids=source_story_ids,
            status=status,
        )
        self._session.add(sketch)
        await self._session.commit()
        await self._session.refresh(sketch)
        return sketch

    async def get_sketch(self, sketch_id: str) -> Sketch:
        """Fetch a sketch by ID."""
        result = await self._session.execute(
            select(Sketch).where(Sketch.sketch_id == sketch_id)
        )
        sketch = result.scalar_one_or_none()
        if sketch is None:
            raise NotFoundError(detail=f"Sketch '{sketch_id}' not found")
        return sketch

    async def list_sketches(self, project_id: str) -> list[Sketch]:
        """List sketches for a project."""
        result = await self._session.execute(
            select(Sketch)
            .where(Sketch.project_id == project_id)
            .order_by(Sketch.updated_at.desc())
        )
        return list(result.scalars().all())

    async def update_sketch(
        self, sketch_id: str, updates: dict[str, Any]
    ) -> Sketch:
        """Update an existing sketch."""
        sketch = await self.get_sketch(sketch_id)
        for key, value in updates.items():
            if value is not None and hasattr(sketch, key):
                setattr(sketch, key, value)
        await self._session.commit()
        await self._session.refresh(sketch)
        return sketch

    async def delete_sketch(self, sketch_id: str) -> None:
        """Delete a sketch and its pages."""
        sketch = await self.get_sketch(sketch_id)
        page_svc = SketchPageService(self._session)
        await page_svc.delete_by_project(sketch.project_id)
        await self._session.delete(sketch)
        await self._session.commit()

    # ------------------------------------------------------------------
    # NEW: Generate from detailed requirements (primary path)
    # ------------------------------------------------------------------

    async def generate_from_requirements(
        self,
        project_id: str,
        story_ids: list[str] | None = None,
    ) -> Sketch:
        """Generate sketch pages from detailed requirement documents.

        Args:
            project_id: Project identifier.
            story_ids: Optional list of story IDs for path validation.
                       If provided, validates story paths against nav graph.

        Returns:
            Created Sketch session with generated pages + validation report.
        """
        # Resolve project base path
        project = await self._session.get(Project, project_id)
        if project is None:
            raise BadRequestError(detail=f"Project '{project_id}' not found")

        app = await self._session.get(Application, project.application_id)
        base_path = pathlib.Path(app.local_path) if app and app.local_path else pathlib.Path(__file__).resolve().parents[3]

        # 1. Parse all module-requirements.md
        module_specs = resolve_project_specs(base_path)
        if not module_specs:
            raise BadRequestError(
                detail="No detailed requirement documents found in openspec/changes/*/detailed-requirements/"
            )

        # 2. Flatten to page dicts
        pages_data = flatten_specs_to_pages(module_specs)
        if not pages_data:
            raise BadRequestError(detail="No pages found in requirement documents")

        # 3. Create sketch session
        sketch = await self.create_sketch(
            project_id=project_id,
            name=f"草图-{len(pages_data)}个页面（来自详细需求）",
            source_story_ids=json.dumps(story_ids or [], ensure_ascii=False),
            status="GENERATING",
        )

        # 4. Generate SVG pages
        generated = generate_sketch_from_module_specs(pages_data)

        page_svc = SketchPageService(self._session)

        # Load existing pages for upsert (match by page_name within project)
        existing_pages = await page_svc.list_pages(project_id)
        existing_by_name: dict[str, Any] = {p.page_name: p for p in existing_pages}

        for idx, data in enumerate(generated):
            existing = existing_by_name.get(data["page_name"])
            if existing:
                # Update existing page
                await page_svc.update_page(
                    existing.page_id,
                    {
                        "page_type": data["page_type"],
                        "svg_content": data["svg_content"],
                        "fields_json": data["fields_json"],
                        "buttons_json": data["buttons_json"],
                        "nav_targets_json": data["nav_targets_json"],
                        "status": data["status"],
                        "sort_order": idx,
                        "source_module_id": data.get("source_module_id"),
                        "source_md_path": data.get("source_md_path"),
                    },
                )
            else:
                # Create new page
                await page_svc.create_page(
                    project_id=project_id,
                    story_id=None,  # Not tied to a single story anymore
                    page_name=data["page_name"],
                    page_type=data["page_type"],
                    svg_content=data["svg_content"],
                    fields_json=data["fields_json"],
                    buttons_json=data["buttons_json"],
                    nav_targets_json=data["nav_targets_json"],
                    status=data["status"],
                    sort_order=idx,
                    source_module_id=data.get("source_module_id"),
                    source_md_path=data.get("source_md_path"),
                )

        # 5. Path validation (if stories provided)
        validation_report: dict[str, Any] = {}
        if story_ids:
            stmt = select(UserStory).where(
                UserStory.project_id == project_id,
                UserStory.story_id.in_(story_ids),
            )
            result = await self._session.execute(stmt)
            stories = result.scalars().all()
            story_dicts = [
                {
                    "story_id": s.story_id,
                    "title": s.title,
                    "page_desc": s.page_desc or "",
                }
                for s in stories
            ]
            validation_report = validate_story_paths(module_specs, story_dicts)
            sketch.validation_report = json.dumps(validation_report, ensure_ascii=False)

        # 6. Update sketch metadata
        sketch.status = "GENERATED"
        sketch.page_count = len(generated)
        sketch.coverage_percent = validation_report.get("coverage_percent", 0)
        await self._session.commit()
        await self._session.refresh(sketch)
        return sketch

    # ------------------------------------------------------------------
    # LEGACY: Generate from user stories (backward compatibility)
    # ------------------------------------------------------------------

    async def generate_from_stories(
        self,
        project_id: str,
        story_ids: list[str] | None = None,
    ) -> Sketch:
        """Generate sketch pages from user stories.

        Args:
            project_id: Project identifier.
            story_ids: Optional list of story IDs. If None, uses all stories with page_desc.

        Returns:
            Created Sketch session with generated pages.
        """
        # Fetch target stories
        stmt = select(UserStory).where(
            UserStory.project_id == project_id,
            UserStory.page_desc.isnot(None),
        )
        if story_ids:
            stmt = stmt.where(UserStory.story_id.in_(story_ids))
        result = await self._session.execute(stmt)
        stories = result.scalars().all()

        if not stories:
            raise BadRequestError(
                detail="No user stories with page_desc found for generation"
            )

        # Create sketch session
        sketch = await self.create_sketch(
            project_id=project_id,
            name=f"草图-{len(stories)}个故事",
            source_story_ids=json.dumps([s.story_id for s in stories], ensure_ascii=False),
            status="GENERATING",
        )

        # Generate pages
        story_dicts = [
            {"title": s.title, "description": s.page_desc or s.description}
            for s in stories
        ]
        generated = generate_sketch_from_stories(story_dicts)

        page_svc = SketchPageService(self._session)
        for idx, data in enumerate(generated):
            await page_svc.create_page(
                project_id=project_id,
                story_id=stories[idx].story_id if idx < len(stories) else None,
                page_name=data["page_name"],
                page_type=data["page_type"],
                svg_content=data["svg_content"],
                fields_json=data["fields_json"],
                buttons_json=data["buttons_json"],
                nav_targets_json=data["nav_targets_json"],
                status=data["status"],
                sort_order=idx,
            )

        # Update sketch status
        sketch.status = "GENERATED"
        sketch.page_count = len(generated)
        await self._session.commit()
        await self._session.refresh(sketch)
        return sketch
