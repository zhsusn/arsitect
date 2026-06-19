"""OpenUIService — CRUD + generation orchestration for OpenUI specs."""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.c4.baseline_store import C4BaselineStore
from app.c4.dsl_manager import C4DSLManager
from app.c4.renderer import C4Renderer
from app.common.fallback_manager import get_fallback_manager
from app.common.health_checker import get_health_checker
from app.core.exceptions import BadRequestError, NotFoundError
from app.models.interface_contract import InterfaceContract
from app.models.open_ui_spec import OpenUISpec
from app.services.open_ui_generator import (
    OpenUIServiceUnavailableError,
    assemble_prompt,
    build_fallback_wireframe,
    generate_html,
    split_pages,
)
from app.services.open_ui_page_service import OpenUIPageService


class OpenUIService:
    """Handle OpenUI spec lifecycle and generation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session."""
        self._session = session

    async def create_spec(
        self,
        project_id: str,
        spec_name: str,
        status: str,
    ) -> OpenUISpec:
        """Create a new OpenUI spec session."""
        if status not in {"DRAFT", "GENERATING", "GENERATED", "RENDERING", "FALLBACK", "ARCHIVED"}:
            raise BadRequestError(detail="Invalid status value")

        spec = OpenUISpec(
            spec_id=f"openui-{uuid.uuid4()}",
            project_id=project_id,
            spec_name=spec_name,
            service_status="UNKNOWN",
            status=status,
        )
        self._session.add(spec)
        await self._session.flush()
        return spec

    async def get_spec(self, spec_id: str) -> OpenUISpec:
        """Fetch a spec by ID."""
        result = await self._session.execute(
            select(OpenUISpec).where(OpenUISpec.spec_id == spec_id)
        )
        spec = result.scalar_one_or_none()
        if spec is None:
            raise NotFoundError(detail=f"OpenUI spec '{spec_id}' not found")
        return spec

    async def list_specs(self, project_id: str) -> list[OpenUISpec]:
        """List specs for a project."""
        result = await self._session.execute(
            select(OpenUISpec)
            .where(OpenUISpec.project_id == project_id)
            .order_by(OpenUISpec.updated_at.desc())
        )
        return list(result.scalars().all())

    async def update_spec(self, spec_id: str, updates: dict[str, Any]) -> OpenUISpec:
        """Update an existing spec."""
        spec = await self.get_spec(spec_id)
        for key, value in updates.items():
            if value is not None and hasattr(spec, key):
                setattr(spec, key, value)
        await self._session.flush()
        return spec

    async def delete_spec(self, spec_id: str) -> None:
        """Delete a spec and its pages."""
        spec = await self.get_spec(spec_id)
        page_svc = OpenUIPageService(self._session)
        await page_svc.delete_by_spec(spec_id)
        await self._session.delete(spec)
        await self._session.flush()

    async def check_health(self, spec_id: str | None = None) -> dict[str, Any]:
        """Check OpenUI service health status via the global HealthChecker."""
        health_checker = get_health_checker()
        # Ensure at least one synchronous check has run if not monitoring.
        if not health_checker.has_results:
            await health_checker.refresh()
        is_available = health_checker.is_available("openui")
        status = "AVAILABLE" if is_available else "UNAVAILABLE"
        if spec_id:
            spec = await self.get_spec(spec_id)
            spec.service_status = status
            await self._session.flush()
        fallback = get_fallback_manager().check_and_fallback("openui")
        return {
            "status": status,
            "available": is_available,
            "fallback_message": fallback.message if fallback else None,
        }

    async def generate_from_c4(
        self,
        project_id: str,
    ) -> OpenUISpec:
        """Generate OpenUI prototype from C4 Container + interface contracts.

        Args:
            project_id: Project identifier.

        Returns:
            Created OpenUISpec session with generated pages.
        """
        # Fetch C4 DSL (L2 Container)
        baseline_store = C4BaselineStore(self._session)
        dsl_manager = C4DSLManager(baseline_store)
        renderer = C4Renderer(dsl_manager)
        mermaid_output = await renderer.render(project_id, "L2")
        dsl_text = mermaid_output.mermaid_code

        if not dsl_text or dsl_text == "graph TD\n  A[No C4 DSL found]":
            raise BadRequestError(
                detail="No C4 DSL (L2 Container) found. Please generate or upload C4 DSL first."
            )

        # Fetch interface contracts
        contract_result = await self._session.execute(
            select(InterfaceContract)
            .where(InterfaceContract.project_id == project_id)
            .order_by(InterfaceContract.endpoint_path.asc())
        )
        contracts = contract_result.scalars().all()

        # Parse C4 nodes for Container names (simple heuristic)
        containers = self._extract_containers(dsl_text)
        if not containers:
            containers = [{"id": "default", "name": dsl_text[:20], "desc": ""}]

        # Create spec session
        spec = await self.create_spec(
            project_id=project_id,
            spec_name=f"OpenUI-{containers[0]['name']}",
            status="GENERATING",
        )

        # Check service health via global HealthChecker / FallbackManager
        health = await self.check_health(spec.spec_id)
        is_available = health["available"]

        page_svc = OpenUIPageService(self._session)
        total_pages = 0
        page_titles: list[str] = []

        for _idx, container in enumerate(containers):
            # Filter contracts by container (MVP: use all contracts for all containers)
            container_contracts = [
                {
                    "method_type": c.method_type,
                    "endpoint_path": c.endpoint_path,
                    "operation_summary": c.operation_summary or "",
                }
                for c in contracts
            ]

            prompt = assemble_prompt(
                container_name=container["name"],
                container_desc=container.get("desc", f"{container['name']} module"),
                endpoints=container_contracts,
            )
            spec.prompt_text = prompt
            await self._session.flush()

            if is_available:
                try:
                    result = await generate_html(prompt)
                    html = result["html_content"]
                    spec.generation_duration_ms = result.get("generation_duration_ms")
                    spec.content_hash = result.get("content_hash")
                    spec.status = "GENERATED"
                except OpenUIServiceUnavailableError:
                    is_available = False
                    html = build_fallback_wireframe(container["name"], container_contracts)
                    spec.status = "FALLBACK"
                    spec.service_status = "UNAVAILABLE"
            else:
                html = build_fallback_wireframe(container["name"], container_contracts)
                spec.status = "FALLBACK"

            # Split and store pages
            split = split_pages(html)
            for pidx, page in enumerate(split):
                await page_svc.create_page(
                    spec_id=spec.spec_id,
                    project_id=project_id,
                    container_id=container["id"],
                    page_title=page["title"],
                    html_content=page["html_segment"],
                    page_index=total_pages + pidx,
                    status="GENERATED" if is_available else "ERROR",
                )
                page_titles.append(page["title"])

            total_pages += len(split)

        spec.page_count = total_pages
        spec.page_titles_json = json.dumps(page_titles, ensure_ascii=False)
        if spec.status != "FALLBACK":
            spec.status = "GENERATED"
        await self._session.flush()
        return spec

    @staticmethod
    def _extract_containers(dsl_text: str) -> list[dict[str, str]]:
        """Extract container nodes from Mermaid DSL text.

        Simple regex-based extraction for MVP.
        """
        import re as _re

        containers: list[dict[str, str]] = []
        seen: set[str] = set()
        for m in _re.finditer(r"^\s*([a-zA-Z0-9_]+)\s*\[(.*?)\]", dsl_text, _re.MULTILINE):
            nid = m.group(1).strip()
            label = m.group(2).strip()
            if nid not in seen:
                seen.add(nid)
                containers.append({"id": nid, "name": label, "desc": label})
        return containers
