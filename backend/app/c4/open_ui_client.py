"""OpenUIClient — prototype generation client with fallback wireframe."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from app.c4.baseline_store import C4BaselineStore
from app.c4.interface_contract_store import InterfaceContractStore
from app.common.fallback_manager import get_fallback_manager
from app.common.health_checker import get_health_checker
from app.services.open_ui_generator import build_fallback_wireframe


@dataclass
class OpenUIGenerationResult:
    """Result of OpenUI generation."""

    spec_id: str
    status: str  # GENERATED / FALLBACK / ERROR
    html_content: str | None
    page_count: int
    page_titles: list[str]
    prompt_text: str
    duration_ms: int
    error_message: str | None = None


class OpenUIClient:
    """OpenUI prototype service client.

    Responsibilities:
    1. Extract Container info from C4 DSL.
    2. Fetch interface contracts.
    3. Assemble structured prompt.
    4. Call OpenUI Docker HTTP API.
    5. Multi-page HTML split.
    6. Fallback wireframe when OpenUI is unavailable.
    """

    DEFAULT_BASE_URL = "http://localhost:3000"
    GENERATE_TIMEOUT = 15.0  # seconds

    def __init__(
        self,
        baseline_store: C4BaselineStore,
        contract_store: InterfaceContractStore,
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        self.baseline = baseline_store
        self.contracts = contract_store
        self.base_url = base_url.rstrip("/")

    # ============================================================
    # Health check
    # ============================================================
    async def check_health(self) -> dict[str, Any]:
        """Check OpenUI service availability via the global HealthChecker."""
        health_checker = get_health_checker()
        if not health_checker.has_results:
            await health_checker.refresh()
        is_available = health_checker.is_available("openui")
        fallback = get_fallback_manager().check_and_fallback("openui")
        return {
            "available": is_available,
            "fallback_message": fallback.message if fallback else None,
        }

    # ============================================================
    # Main generation flow
    # ============================================================
    async def generate_from_c4(
        self, project_id: str, spec_name: str = "prototype"
    ) -> OpenUIGenerationResult:
        """Generate prototype from C4 + interface contracts.

        Flow:
        1. Fetch C4 DSL (L2 Container).
        2. Fetch interface contracts.
        3. Assemble prompt.
        4. Check OpenUI health.
        5. Call OpenUI or fallback.
        6. Split pages.
        """
        start_time = datetime.utcnow()

        workspace = await self.baseline.read_current(project_id)
        if not workspace:
            return self._error_result("No C4 DSL found")

        import yaml

        try:
            dsl_data = yaml.safe_load(workspace.dsl_content)
        except yaml.YAMLError as exc:
            return self._error_result(f"Invalid C4 DSL YAML: {exc}")

        containers = dsl_data.get("workspace", {}).get("model", {}).get("containers", [])
        if not containers:
            return self._error_result("No containers found in C4 DSL")

        all_contracts = await self.contracts.list_by_project(project_id)
        contracts_by_container: dict[str, list[Any]] = {}
        for c in all_contracts:
            contracts_by_container.setdefault(c.container_id, []).append(c)

        prompt = self._assemble_prompt(containers, contracts_by_container)
        health = await self.check_health()
        get_fallback_manager().check_and_fallback("openui")

        if health["available"]:
            try:
                html_result = await self._call_openui(prompt)
                status = "GENERATED"
            except RuntimeError as exc:
                html_result = self._build_fallback_wireframe(containers, all_contracts)
                status = "FALLBACK"
                return self._error_result(str(exc))
        else:
            html_result = self._build_fallback_wireframe(containers, all_contracts)
            status = "FALLBACK"

        pages = self._split_pages(html_result)
        duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        return OpenUIGenerationResult(
            spec_id=f"openui-{hashlib.md5(prompt.encode()).hexdigest()[:8]}",
            status=status,
            html_content=html_result,
            page_count=len(pages),
            page_titles=[p.get("title", f"Page {i + 1}") for i, p in enumerate(pages)],
            prompt_text=prompt,
            duration_ms=duration,
        )

    # ============================================================
    # Prompt assembly
    # ============================================================
    def _assemble_prompt(
        self,
        containers: list[dict[str, Any]],
        contracts_by_container: dict[str, list[Any]],
    ) -> str:
        """Assemble OpenUI prompt."""
        lines = [
            "You are a UI generation assistant.",
            "Generate a complete, interactive single-page HTML prototype.",
            "",
            "System Overview:",
        ]

        for container in containers:
            cid = container["id"]
            cname = container.get("name", cid)
            tech = container.get("technology", "")
            desc = container.get("description", "")
            lines.append(f"- {cname} ({tech}): {desc}")

            container_contracts = contracts_by_container.get(cid, [])
            if container_contracts:
                lines.append("  Endpoints:")
                for c in container_contracts:
                    lines.append(f"  - {c.method} {c.endpoint_path}: {c.summary}")

        lines.extend(
            [
                "",
                "Requirements:",
                "- Use semantic HTML5, embedded CSS, and vanilla JS.",
                "- Include navigation, data tables or forms based on endpoints.",
                "- Support responsive layout.",
                "- Output a complete standalone HTML file.",
                "- Use Chinese UI labels where appropriate.",
                "- Split multiple pages with <!-- PAGE: PageName --> comments.",
            ]
        )

        return "\n".join(lines)

    # ============================================================
    # OpenUI HTTP call
    # ============================================================
    async def _call_openui(self, prompt: str) -> str:
        """Call OpenUI Docker service."""
        async with httpx.AsyncClient(timeout=self.GENERATE_TIMEOUT) as client:
            resp = await client.post(
                f"{self.base_url}/api/generate",
                json={"prompt": prompt, "format": "html"},
            )
            if resp.status_code != 200:
                raise RuntimeError(f"OpenUI returned {resp.status_code}")
            result = resp.json()
            html = result.get("html", "")
            return str(html) if html is not None else ""

    # ============================================================
    # Fallback wireframe
    # ============================================================
    def _build_fallback_wireframe(
        self,
        containers: list[dict[str, Any]],
        contracts: list[Any],
    ) -> str:
        """Generate static wireframe when OpenUI is unavailable.

        Delegates to the single shared fallback builder so the wireframe
        format stays consistent across all OpenUI consumers.
        """
        if len(containers) != 1:
            # The shared builder renders one container per page. For the
            # legacy multi-container input we fall back to the first
            # container's contracts to keep the output deterministic.
            container = containers[0] if containers else {"name": "Prototype"}
        else:
            container = containers[0]

        cid = container["id"]
        container_name = container.get("name", cid)
        container_contracts = [
            {
                "method_type": getattr(c, "method", "GET"),
                "endpoint_path": getattr(c, "endpoint_path", "/"),
                "operation_summary": getattr(c, "summary", ""),
            }
            for c in contracts
            if getattr(c, "container_id", cid) == cid
        ]
        return build_fallback_wireframe(container_name, container_contracts)

    # ============================================================
    # Page splitting
    # ============================================================
    def _split_pages(self, html_content: str) -> list[dict[str, str]]:
        """Split multi-page HTML by <!-- PAGE: PageName --> comments."""
        pattern = r"<!--\s*PAGE:\s*(.*?)\s*-->"
        splits = re.split(pattern, html_content)

        if len(splits) <= 1:
            return [{"title": "Main Page", "content": html_content}]

        pages = []
        for i in range(1, len(splits), 2):
            title = splits[i].strip()
            content = splits[i + 1] if i + 1 < len(splits) else ""
            pages.append({"title": title, "content": content})

        return pages

    def _error_result(self, message: str) -> OpenUIGenerationResult:
        return OpenUIGenerationResult(
            spec_id="",
            status="ERROR",
            html_content=None,
            page_count=0,
            page_titles=[],
            prompt_text="",
            duration_ms=0,
            error_message=message,
        )
