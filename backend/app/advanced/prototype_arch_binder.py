"""PrototypeArchBinder — prototype/architecture interface gap detection."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.c4.baseline_store import C4BaselineStore
from app.c4.interface_contract_store import InterfaceContractStore
from app.models.interface_contract import InterfaceContract
from app.models.open_ui_page import OpenUIPage
from app.models.open_ui_spec import OpenUISpec
from app.models.wireframe_page import WireframePage


@dataclass
class ExtractedAnchor:
    """Interface anchor extracted from a prototype page."""

    name: str
    path: str | None
    method: str = "GET"
    params: dict[str, Any] | None = None
    source_page: str = ""
    source_type: str = "wireframe"


@dataclass
class InterfaceGap:
    """Gap between prototype and interface contract."""

    contract_id: str
    endpoint_path: str
    method: str
    gap_type: str
    suggestion: str
    source_page: str = ""
    source_type: str = ""


@dataclass
class DiffResult:
    """Result of comparing anchors against contracts."""

    anchor: ExtractedAnchor
    contract: InterfaceContract | None
    result_type: str = ""
    param_diff: dict[str, Any] | None = None


class PrototypeArchBinder:
    """Prototype-architecture binder.

    Responsibilities:
    1. Extract interface anchors from wireframe/OpenUI pages.
    2. Compare anchors against C4 interface contracts.
    3. Detect gaps (missing in prototype or missing in contract).
    4. Write gaps back to C4 DSL or create InterfaceContract records.
    """

    _PATH_RE = re.compile(r"(/api/[a-zA-Z0-9_\-/]+|/v\d+/[a-zA-Z0-9_\-/]+)")
    _METHOD_RE = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\b")

    def __init__(
        self,
        session: AsyncSession,
        baseline_store: C4BaselineStore,
        contract_store: InterfaceContractStore,
    ) -> None:
        """Initialize with stores."""
        self._session = session
        self.baseline = baseline_store
        self.contracts = contract_store

    async def detect_gaps(self, project_id: str) -> list[InterfaceGap]:
        """Detect gaps by scanning project prototype pages."""
        proto_interfaces = await self._extract_proto_interfaces(project_id)
        return await self.detect_gaps_from_interfaces(project_id, proto_interfaces)

    async def detect_gaps_from_interfaces(
        self,
        project_id: str,
        proto_interfaces: list[dict[str, Any]],
    ) -> list[InterfaceGap]:
        """Detect gaps given externally-discovered prototype interfaces."""
        contract_interfaces = await self.contracts.list_by_project(project_id)
        contract_set = {(c.endpoint_path, (c.method or "GET").upper()) for c in contract_interfaces}
        proto_set = {(p.get("path", ""), p.get("method", "GET").upper()) for p in proto_interfaces}

        gaps: list[InterfaceGap] = []
        for c in contract_interfaces:
            method = (c.method or "GET").upper()
            if (c.endpoint_path, method) not in proto_set:
                gaps.append(
                    InterfaceGap(
                        contract_id=c.contract_id,
                        endpoint_path=c.endpoint_path or "",
                        method=method,
                        gap_type="missing_in_proto",
                        suggestion=f"Implement {method} {c.endpoint_path} in prototype",
                    )
                )

        for p in proto_interfaces:
            path = p.get("path", "")
            method = p.get("method", "GET").upper()
            if (path, method) not in contract_set:
                gaps.append(
                    InterfaceGap(
                        contract_id="",
                        endpoint_path=path,
                        method=method,
                        gap_type="missing_in_contract",
                        suggestion=f"Add {method} {path} to interface contract",
                        source_page=p.get("source_page", ""),
                        source_type=p.get("source_type", ""),
                    )
                )
        return gaps

    async def sync_to_dsl(self, project_id: str, gaps: list[InterfaceGap]) -> bool:
        """Write missing-in-contract gaps back to C4 DSL."""
        baseline = await self.baseline.read_current(project_id)
        if baseline is None:
            return False

        try:
            dsl_data = yaml.safe_load(baseline.dsl_content or "") or {}
        except yaml.YAMLError:
            return False

        model = dsl_data.setdefault("workspace", {}).setdefault("model", {})
        interfaces = model.setdefault("interfaces", [])

        existing_ids = {i.get("id") for i in interfaces if isinstance(i, dict)}
        for gap in gaps:
            if gap.gap_type != "missing_in_contract":
                continue
            safe_path = gap.endpoint_path.replace("/", "_").strip("_")
            iface_id = f"{gap.method}_{safe_path}"
            if iface_id in existing_ids:
                continue
            interfaces.append(
                {
                    "id": iface_id,
                    "method": gap.method,
                    "path": gap.endpoint_path,
                }
            )
            existing_ids.add(iface_id)

        # Persist via baseline store if it supports write; otherwise update
        # the baseline record directly.
        new_dsl = yaml.dump(dsl_data, allow_unicode=True)
        if hasattr(self.baseline, "write_current"):
            await self.baseline.write_current(project_id, new_dsl)
        else:
            from app.models.c4_baseline import C4Baseline

            result = await self._session.execute(
                select(C4Baseline)
                .where(C4Baseline.project_id == project_id)
                .where(C4Baseline.is_current == True)  # noqa: E712
            )
            current = result.scalar_one_or_none()
            if current:
                current.dsl_content = new_dsl
                await self._session.flush()
        return True

    async def apply_writeback(
        self, project_id: str, gaps: list[InterfaceGap]
    ) -> list[dict[str, Any]]:
        """Create InterfaceContract records for missing-in-contract gaps."""
        created: list[dict[str, Any]] = []
        for gap in gaps:
            if gap.gap_type != "missing_in_contract":
                continue
            contract = InterfaceContract(
                contract_id=f"ic-{uuid.uuid4()}",
                project_id=project_id,
                container_id="prototype_gap",
                endpoint_path=gap.endpoint_path or "/",
                method_type=gap.method.upper(),
                request_schema="{}",
                response_schema="{}",
            )
            self._session.add(contract)
            created.append(
                {
                    "contract_id": contract.contract_id,
                    "path": contract.endpoint_path,
                    "method": contract.method_type,
                }
            )
        await self._session.flush()
        return created

    async def _extract_proto_interfaces(self, project_id: str) -> list[dict[str, Any]]:
        """Extract prototype interface anchors from pages."""
        wf_pages = list(
            (
                await self._session.execute(
                    select(WireframePage).where(WireframePage.project_id == project_id)
                )
            )
            .scalars()
            .all()
        )
        ou_specs = list(
            (
                await self._session.execute(
                    select(OpenUISpec).where(OpenUISpec.project_id == project_id)
                )
            )
            .scalars()
            .all()
        )
        ou_pages: list[OpenUIPage] = []
        for spec in ou_specs:
            pages = list(
                (
                    await self._session.execute(
                        select(OpenUIPage).where(OpenUIPage.spec_id == spec.spec_id)
                    )
                )
                .scalars()
                .all()
            )
            ou_pages.extend(pages)

        contracts = list(
            (
                await self._session.execute(
                    select(InterfaceContract).where(InterfaceContract.project_id == project_id)
                )
            )
            .scalars()
            .all()
        )

        wf_anchors = self._extract_wireframe_anchors(wf_pages)
        ou_anchors = self._extract_openui_anchors(ou_pages)
        all_anchors = wf_anchors + ou_anchors

        diffs = self._compare_anchors(all_anchors, contracts)
        interfaces: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for d in diffs:
            key = (d.anchor.path or "", d.anchor.method.upper())
            if not key[0] or key in seen:
                continue
            seen.add(key)
            interfaces.append(
                {
                    "path": d.anchor.path,
                    "method": d.anchor.method.upper(),
                    "source_page": d.anchor.source_page,
                    "source_type": d.anchor.source_type,
                }
            )
        return interfaces

    @classmethod
    def _extract_wireframe_anchors(cls, pages: list[WireframePage]) -> list[ExtractedAnchor]:
        """Extract anchors from wireframe page layout_json."""
        anchors: list[ExtractedAnchor] = []
        for page in pages:
            page_label = page.page_name or f"page-{page.page_id}"
            if not page.layout_json:
                continue
            try:
                layout = json.loads(page.layout_json)
                for zone in layout if isinstance(layout, list) else [layout]:
                    if not isinstance(zone, dict):
                        continue
                    for el in zone.get("elements", []):
                        if not isinstance(el, dict):
                            continue
                        action = el.get("action") or el.get("href")
                        if action and isinstance(action, str) and action.startswith("/"):
                            anchors.append(
                                ExtractedAnchor(
                                    name=el.get("label", action),
                                    path=action,
                                    method=el.get("method", "POST"),
                                    params=el.get("fields", {}),
                                    source_page=page_label,
                                    source_type="wireframe",
                                )
                            )
            except (json.JSONDecodeError, TypeError):
                pass
        return anchors

    @classmethod
    def _extract_openui_anchors(cls, pages: list[OpenUIPage]) -> list[ExtractedAnchor]:
        """Extract anchors from OpenUI HTML pages."""
        anchors: list[ExtractedAnchor] = []
        for page in pages:
            page_label = page.page_title or f"openui-{page.page_id}"
            html = page.html_content or ""
            if not html:
                continue

            for m in re.finditer(r"<!--\s*api:\s*([^|]+)\|([^|]+)\|([^\s]+)\s*-->", html):
                anchors.append(
                    ExtractedAnchor(
                        name=m.group(1).strip(),
                        path=m.group(3).strip(),
                        method=m.group(2).strip().upper(),
                        source_page=page_label,
                        source_type="openui",
                    )
                )

            for m in re.finditer(r'<form[^>]*action=["\']([^"\']+)["\'][^>]*>', html, re.I):
                path = m.group(1)
                if path.startswith("/"):
                    method_match = re.search(r'method=["\']([a-zA-Z]+)["\']', m.group(0), re.I)
                    method = method_match.group(1).upper() if method_match else "POST"
                    anchors.append(
                        ExtractedAnchor(
                            name=f"form-{path}",
                            path=path,
                            method=method,
                            source_page=page_label,
                            source_type="openui",
                        )
                    )

            for m in cls._PATH_RE.finditer(html):
                path = m.group(0).rstrip("-/")
                if any(a.path == path and a.source_page == page_label for a in anchors):
                    continue
                method = "GET"
                ctx = html[max(0, m.start() - 30) : m.end() + 30]
                mm = cls._METHOD_RE.search(ctx)
                if mm:
                    method = mm.group(1)
                anchors.append(
                    ExtractedAnchor(
                        name=f"fetch-{path}",
                        path=path,
                        method=method,
                        source_page=page_label,
                        source_type="openui",
                    )
                )
        return anchors

    @classmethod
    def _compare_anchors(
        cls,
        anchors: list[ExtractedAnchor],
        contracts: list[InterfaceContract],
    ) -> list[DiffResult]:
        """Compare extracted anchors against C4 contracts."""
        contract_map: dict[str, InterfaceContract] = {}
        for c in contracts:
            key = f"{(c.method_type or 'GET').upper()} {c.endpoint_path or ''}".lower().strip()
            if key:
                contract_map[key] = c

        results: list[DiffResult] = []
        matched_keys: set[str] = set()

        for anchor in anchors:
            key = f"{anchor.method.upper()} {anchor.path or ''}".lower().strip()
            contract = contract_map.get(key)
            if contract:
                matched_keys.add(key)
                param_diff = cls._param_diff(anchor, contract)
                results.append(
                    DiffResult(
                        anchor=anchor,
                        contract=contract,
                        result_type="diff" if param_diff else "matched",
                        param_diff=param_diff,
                    )
                )
                continue

            fuzzy: InterfaceContract | None = None
            fuzzy_key: str | None = None
            for k, c2 in contract_map.items():
                if (anchor.path or "").lower() == (c2.endpoint_path or "").lower():
                    fuzzy = c2
                    fuzzy_key = k
                    break
            if fuzzy and fuzzy_key:
                matched_keys.add(fuzzy_key)
                param_diff = cls._param_diff(anchor, fuzzy)
                results.append(
                    DiffResult(
                        anchor=anchor,
                        contract=fuzzy,
                        result_type="diff" if param_diff else "matched",
                        param_diff=param_diff,
                    )
                )
            else:
                results.append(
                    DiffResult(
                        anchor=anchor,
                        contract=None,
                        result_type="gap",
                    )
                )

        for key, contract in contract_map.items():
            if key in matched_keys:
                continue
            results.append(
                DiffResult(
                    anchor=ExtractedAnchor(
                        name=contract.endpoint_path or key,
                        path=contract.endpoint_path,
                        method=contract.method_type or "GET",
                        source_page="c4-contract",
                        source_type="wireframe",
                    ),
                    contract=contract,
                    result_type="redundant",
                )
            )
        return results

    @staticmethod
    def _param_diff(anchor: ExtractedAnchor, contract: InterfaceContract) -> dict[str, Any] | None:
        """Compare parameters between anchor and contract."""
        try:
            c_params: dict[str, Any] = (
                json.loads(contract.request_schema or "{}") if contract.request_schema else {}
            )
        except (json.JSONDecodeError, TypeError):
            c_params = {}
        a_params = anchor.params or {}
        if not c_params and not a_params:
            return None
        c_keys = set(c_params.keys()) if isinstance(c_params, dict) else set()
        a_keys = set(a_params.keys()) if isinstance(a_params, dict) else set()
        if c_keys == a_keys:
            return None
        return {
            "anchor_keys": list(a_keys),
            "contract_keys": list(c_keys),
            "missing_in_anchor": list(c_keys - a_keys),
            "missing_in_contract": list(a_keys - c_keys),
        }
