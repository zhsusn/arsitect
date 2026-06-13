"""WireframeService — CRUD + generation orchestration for wireframes."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.c4.baseline_store import C4BaselineStore
from app.c4.dsl_manager import C4DSLManager
from app.c4.renderer import C4Renderer
from app.core.exceptions import BadRequestError, NotFoundError
from app.models.wireframe import Wireframe
from app.services.wireframe_generator import generate_wireframe_from_c4
from app.services.wireframe_nav_link_service import WireframeNavLinkService
from app.services.wireframe_page_service import WireframePageService


class WireframeService:
    """Handle wireframe lifecycle and generation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session."""
        self._session = session

    async def create_wireframe(
        self,
        project_id: str,
        name: str,
        status: str,
        c4_baseline_version: str | None = None,
    ) -> Wireframe:
        """Create a new wireframe session."""
        if status not in {"DRAFT", "ACTIVE", "ARCHIVED"}:
            raise BadRequestError(detail="Invalid status value")

        wf = Wireframe(
            wireframe_id=f"wf-{uuid.uuid4()}",
            project_id=project_id,
            name=name,
            pipeline_stage="idle",
            status=status,
        )
        self._session.add(wf)
        await self._session.flush()
        return wf

    async def get_wireframe(self, wireframe_id: str) -> Wireframe:
        """Fetch a wireframe by ID."""
        result = await self._session.execute(
            select(Wireframe).where(Wireframe.wireframe_id == wireframe_id)
        )
        wf = result.scalar_one_or_none()
        if wf is None:
            raise NotFoundError(detail=f"Wireframe '{wireframe_id}' not found")
        return wf

    async def list_wireframes(self, project_id: str) -> list[Wireframe]:
        """List wireframes for a project."""
        result = await self._session.execute(
            select(Wireframe)
            .where(Wireframe.project_id == project_id)
            .order_by(Wireframe.updated_at.desc())
        )
        return list(result.scalars().all())

    async def update_wireframe(
        self, wireframe_id: str, updates: dict[str, Any]
    ) -> Wireframe:
        """Update an existing wireframe."""
        wf = await self.get_wireframe(wireframe_id)
        for key, value in updates.items():
            if value is not None and hasattr(wf, key):
                setattr(wf, key, value)
        await self._session.flush()
        return wf

    async def delete_wireframe(self, wireframe_id: str) -> None:
        """Delete a wireframe and its pages/links."""
        wf = await self.get_wireframe(wireframe_id)
        page_svc = WireframePageService(self._session)
        link_svc = WireframeNavLinkService(self._session)
        await page_svc.delete_by_wireframe(wireframe_id)
        await link_svc.delete_by_wireframe(wireframe_id)
        await self._session.delete(wf)
        await self._session.flush()

    async def generate_from_c4(
        self,
        project_id: str,
    ) -> Wireframe:
        """Generate wireframe pages from C4 DSL.

        Args:
            project_id: Project identifier.

        Returns:
            Created Wireframe session with generated pages and nav links.
        """
        # Fetch C4 DSL (L2)
        baseline_store = C4BaselineStore(self._session)
        dsl_manager = C4DSLManager(baseline_store)
        renderer = C4Renderer(dsl_manager)
        mermaid_output = await renderer.render(project_id, "L2")
        dsl_text = mermaid_output.mermaid_code

        if not dsl_text or dsl_text == "graph TD\n  A[No C4 DSL found]":
            raise BadRequestError(
                detail="No C4 DSL (L2 Container) found for this project. Please generate or upload C4 DSL first."
            )

        # Create wireframe session
        wf = await self.create_wireframe(
            project_id=project_id,
            name="线框图-L2",
            status="DRAFT",
        )
        wf.pipeline_stage = "domain_mapping"
        await self._session.flush()

        # Run generator pipeline
        output = generate_wireframe_from_c4(dsl_text)
        pages_data = output["pages"]
        nav_data = output["nav_links"]
        summary = output["summary"]

        # Persist pages
        page_svc = WireframePageService(self._session)
        entity_to_page_id: dict[str, str] = {}
        for idx, p in enumerate(pages_data):
            page = await page_svc.create_page(
                wireframe_id=wf.wireframe_id,
                project_id=project_id,
                entity_id=p["entity_id"],
                entity_name=p["entity_name"],
                page_name=p["entity_name"],
                page_type=p["page_type"],
                confidence=p["confidence"],
                mapping_source=p["mapping_source"],
                svg_content=p["svg_content"],
                layout_json=p["layout_json"],
                status="PUBLISHED" if p["mapping_source"] != "uncertain" else "MAPPED_UNCERTAIN",
                sort_order=idx,
            )
            entity_to_page_id[p["entity_id"]] = page.page_id

        # Persist nav links
        link_svc = WireframeNavLinkService(self._session)
        for link in nav_data:
            src_page = entity_to_page_id.get(link["source_entity_id"])
            tgt_page = entity_to_page_id.get(link["target_entity_id"])
            if src_page and tgt_page:
                await link_svc.create_link(
                    wireframe_id=wf.wireframe_id,
                    project_id=project_id,
                    source_page_id=src_page,
                    target_page_id=tgt_page,
                    interface_refs_json=None,
                    relation_strength=link["relation_strength"],
                    interface_count=link["interface_count"],
                )

        # Update wireframe summary
        wf.pipeline_stage = "completed"
        wf.page_count = summary["total_pages"]
        wf.avg_confidence = int(summary["avg_confidence"])
        await self._session.flush()
        return wf
