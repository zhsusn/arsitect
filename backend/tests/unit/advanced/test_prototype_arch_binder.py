"""Tests for PrototypeArchBinder — prototype/architecture interface gap detection."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import pytest

from app.advanced.prototype_arch_binder import (
    ExtractedAnchor,
    InterfaceGap,
    PrototypeArchBinder,
)
from app.c4.baseline_store import C4BaselineStore as BaselineStore
from app.c4.interface_contract_store import InterfaceContractStore
from app.models.application import Application
from app.models.c4_baseline import C4Baseline
from app.models.interface_contract import InterfaceContract
from app.models.open_ui_page import OpenUIPage
from app.models.open_ui_spec import OpenUISpec
from app.models.project import Project
from app.models.wireframe import Wireframe
from app.models.wireframe_page import WireframePage


@dataclass
class _ProjectSeed:
    """Holds seeded IDs for a test project."""

    project_id: str
    wireframe_id: str
    spec_id: str


class TestPrototypeArchBinder:
    """PrototypeArchBinder unit tests."""

    async def _seed_project(
        self,
        db_session,
        project_id: str,
    ) -> _ProjectSeed:
        """Seed application, project, wireframe, openui spec and baseline."""
        app_obj = Application(
            application_id=f"app-{project_id}",
            application_name=f"App {project_id}",
            local_path="/tmp/test",
        )
        db_session.add(app_obj)
        await db_session.flush()

        project = Project(
            project_id=project_id,
            project_name=f"Project {project_id}",
            application_id=app_obj.application_id,
            template_level="Standard",
        )
        db_session.add(project)
        await db_session.flush()

        wireframe = Wireframe(
            wireframe_id=f"wf-{project_id}",
            project_id=project_id,
            name="Test Wireframe",
        )
        db_session.add(wireframe)

        spec = OpenUISpec(
            spec_id=f"spec-{project_id}",
            project_id=project_id,
            spec_name="Test Spec",
        )
        db_session.add(spec)

        baseline = C4Baseline(
            project_id=project_id,
            version="1.0.0",
            dsl_content="workspace:\n  model:\n    containers: []",
            dsl_hash="hash",
            level="L1-L4",
            is_current=True,
        )
        db_session.add(baseline)
        await db_session.flush()

        return _ProjectSeed(
            project_id=project_id,
            wireframe_id=wireframe.wireframe_id,
            spec_id=spec.spec_id,
        )

    async def _seed_contract(
        self,
        db_session,
        project_id: str,
        path: str,
        method: str,
    ) -> InterfaceContract:
        """Seed an interface contract record."""
        contract = InterfaceContract(
            contract_id=f"ic-{uuid.uuid4()}",
            project_id=project_id,
            container_id="c1",
            endpoint_path=path,
            method_type=method,
            operation_summary="summary",
            request_schema='{"id": "string"}',
            response_schema="{}",
            status="DRAFT",
        )
        db_session.add(contract)
        await db_session.flush()
        return contract

    @pytest.mark.asyncio
    async def test_detect_gaps_from_interfaces_missing_in_proto(self, db_session) -> None:
        """Contracts without prototype anchors should yield missing_in_proto gaps."""
        seed = await self._seed_project(db_session, "proj-gap1")
        await self._seed_contract(db_session, seed.project_id, "/api/orders", "GET")

        binder = PrototypeArchBinder(
            session=db_session,
            baseline_store=BaselineStore(db_session),
            contract_store=InterfaceContractStore(db_session),
        )
        gaps = await binder.detect_gaps_from_interfaces(seed.project_id, [])

        assert len(gaps) == 1
        assert gaps[0].gap_type == "missing_in_proto"
        assert gaps[0].endpoint_path == "/api/orders"

    @pytest.mark.asyncio
    async def test_detect_gaps_from_interfaces_missing_in_contract(self, db_session) -> None:
        """Prototype anchors without contracts should yield missing_in_contract gaps."""
        seed = await self._seed_project(db_session, "proj-gap2")

        binder = PrototypeArchBinder(
            session=db_session,
            baseline_store=BaselineStore(db_session),
            contract_store=InterfaceContractStore(db_session),
        )
        proto = [
            {
                "path": "/api/users",
                "method": "POST",
                "source_page": "users",
                "source_type": "wireframe",
            }
        ]
        gaps = await binder.detect_gaps_from_interfaces(seed.project_id, proto)

        assert len(gaps) == 1
        assert gaps[0].gap_type == "missing_in_contract"
        assert gaps[0].endpoint_path == "/api/users"

    @pytest.mark.asyncio
    async def test_detect_gaps_from_interfaces_aligned(self, db_session) -> None:
        """Matching contract and prototype should produce no gaps."""
        seed = await self._seed_project(db_session, "proj-gap3")
        await self._seed_contract(db_session, seed.project_id, "/api/items", "GET")

        binder = PrototypeArchBinder(
            session=db_session,
            baseline_store=BaselineStore(db_session),
            contract_store=InterfaceContractStore(db_session),
        )
        proto = [{"path": "/api/items", "method": "GET"}]
        gaps = await binder.detect_gaps_from_interfaces(seed.project_id, proto)

        assert gaps == []

    @pytest.mark.asyncio
    async def test_apply_writeback_creates_contracts(self, db_session) -> None:
        """apply_writeback should persist InterfaceContract records."""
        seed = await self._seed_project(db_session, "proj-wb")
        gaps = [
            InterfaceGap(
                contract_id="",
                endpoint_path="/api/pay",
                method="POST",
                gap_type="missing_in_contract",
                suggestion="add",
            )
        ]

        binder = PrototypeArchBinder(
            session=db_session,
            baseline_store=BaselineStore(db_session),
            contract_store=InterfaceContractStore(db_session),
        )
        created = await binder.apply_writeback(seed.project_id, gaps)

        assert len(created) == 1
        assert created[0]["path"] == "/api/pay"
        assert created[0]["method"] == "POST"

    @pytest.mark.asyncio
    async def test_sync_to_dsl_updates_baseline(self, db_session) -> None:
        """sync_to_dsl should write missing-in-contract gaps into C4 DSL."""
        seed = await self._seed_project(db_session, "proj-sync")
        gaps = [
            InterfaceGap(
                contract_id="",
                endpoint_path="/api/ship",
                method="GET",
                gap_type="missing_in_contract",
                suggestion="add",
            )
        ]

        binder = PrototypeArchBinder(
            session=db_session,
            baseline_store=BaselineStore(db_session),
            contract_store=InterfaceContractStore(db_session),
        )
        ok = await binder.sync_to_dsl(seed.project_id, gaps)

        assert ok is True
        updated = await binder.baseline.read_current(seed.project_id)
        assert updated is not None
        assert "GET_api_ship" in updated.dsl_content

    @pytest.mark.asyncio
    async def test_sync_to_dsl_without_baseline(self, db_session) -> None:
        """sync_to_dsl should return False when no baseline exists."""
        seed = await self._seed_project(db_session, "proj-nobase")
        # Remove baseline
        # Easier: delete by project_id via execute
        from sqlalchemy import delete

        await db_session.execute(delete(C4Baseline).where(C4Baseline.project_id == seed.project_id))
        await db_session.flush()

        binder = PrototypeArchBinder(
            session=db_session,
            baseline_store=BaselineStore(db_session),
            contract_store=InterfaceContractStore(db_session),
        )
        gaps = [
            InterfaceGap(
                contract_id="",
                endpoint_path="/api/x",
                method="GET",
                gap_type="missing_in_contract",
                suggestion="add",
            )
        ]
        ok = await binder.sync_to_dsl(seed.project_id, gaps)
        assert ok is False

    def test_extract_wireframe_anchors(self) -> None:
        """Wireframe layout JSON with action/href should produce anchors."""
        page = WireframePage(
            page_id="wp-1",
            wireframe_id="wf-1",
            project_id="proj-1",
            page_name="Orders",
            layout_json='[{"elements": [{"label": "List", "action": "/api/orders", "method": "GET"}]}]',
        )
        anchors = PrototypeArchBinder._extract_wireframe_anchors([page])
        assert len(anchors) == 1
        assert anchors[0].path == "/api/orders"
        assert anchors[0].method == "GET"
        assert anchors[0].source_page == "Orders"

    def test_extract_wireframe_anchors_invalid_json(self) -> None:
        """Invalid layout JSON should be ignored without raising."""
        page = WireframePage(
            page_id="wp-1",
            wireframe_id="wf-1",
            project_id="proj-1",
            page_name="Bad",
            layout_json="not json",
        )
        assert PrototypeArchBinder._extract_wireframe_anchors([page]) == []

    def test_extract_openui_anchors(self) -> None:
        """OpenUI HTML with api comments/forms/paths should produce anchors."""
        page = OpenUIPage(
            page_id="op-1",
            spec_id="spec-1",
            project_id="proj-1",
            page_title="Checkout",
            html_content="""
<!-- api: Pay|POST|/api/pay -->
<form action="/api/checkout" method="POST">
  <button>Go</button>
</form>
<script>fetch('/api/status')</script>
""",
        )
        anchors = PrototypeArchBinder._extract_openui_anchors([page])
        paths = {a.path for a in anchors}
        assert paths == {"/api/pay", "/api/checkout", "/api/status"}

    def test_compare_anchors_matched_and_gap(self) -> None:
        """Compare should tag matched anchors, gaps and redundant contracts."""
        anchor = ExtractedAnchor(
            name="orders",
            path="/api/orders",
            method="GET",
        )
        contract = InterfaceContract(
            contract_id="ic-1",
            project_id="proj-1",
            container_id="c1",
            endpoint_path="/api/orders",
            method_type="GET",
        )
        diffs = PrototypeArchBinder._compare_anchors([anchor], [contract])
        types = {d.result_type for d in diffs}
        assert "matched" in types

    def test_param_diff_equal_params(self) -> None:
        """Equal params should return None."""
        anchor = ExtractedAnchor(name="a", path="/x", params={"id": "string"})
        contract = InterfaceContract(
            contract_id="ic-1",
            project_id="proj-1",
            container_id="c1",
            endpoint_path="/x",
            method_type="GET",
            request_schema='{"id": "string"}',
        )
        assert PrototypeArchBinder._param_diff(anchor, contract) is None

    def test_param_diff_different_params(self) -> None:
        """Different params should report missing keys."""
        anchor = ExtractedAnchor(name="a", path="/x", params={"id": "string"})
        contract = InterfaceContract(
            contract_id="ic-1",
            project_id="proj-1",
            container_id="c1",
            endpoint_path="/x",
            method_type="GET",
            request_schema='{"id": "string", "name": "string"}',
        )
        diff = PrototypeArchBinder._param_diff(anchor, contract)
        assert diff is not None
        assert "name" in diff["missing_in_anchor"]
