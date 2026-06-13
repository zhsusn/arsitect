"""Tests for InterfaceContractStore."""

from __future__ import annotations

import pytest

from app.c4.interface_contract_store import (
    ContractStatus,
    InterfaceContract,
    InterfaceContractStore,
)
from app.models.application import Application
from app.models.project import Project


class TestInterfaceContractStore:
    """InterfaceContractStore unit tests."""

    async def _seed_project(self, session, suffix: str = "1") -> Project:
        app = Application(
            application_id=f"app-ic-{suffix}",
            application_name=f"IcApp{suffix}",
            local_path=f"/tmp/ic{suffix}",
        )
        session.add(app)
        await session.flush()
        proj = Project(
            project_id=f"proj-ic-{suffix}",
            project_name=f"IcProj{suffix}",
            application_id=app.application_id,
            template_level="Standard",
        )
        session.add(proj)
        await session.flush()
        return proj

    @pytest.mark.asyncio
    async def test_create_and_get(self, db_session) -> None:
        """Create contract and retrieve by ID."""
        proj = await self._seed_project(db_session)
        store = InterfaceContractStore(db_session)

        contract = InterfaceContract(
            contract_id="",
            project_id=proj.project_id,
            container_id="WebApp",
            endpoint_path="/api/users",
            method="GET",
            summary="List users",
        )
        cid = await store.create(contract)
        assert cid

        fetched = await store.get(cid)
        assert fetched is not None
        assert fetched.endpoint_path == "/api/users"
        assert fetched.method == "GET"
        assert fetched.status == ContractStatus.DRAFT.value

    @pytest.mark.asyncio
    async def test_list_by_container(self, db_session) -> None:
        """List contracts filtered by container."""
        proj = await self._seed_project(db_session)
        store = InterfaceContractStore(db_session)

        await store.create(
            InterfaceContract(
                contract_id="",
                project_id=proj.project_id,
                container_id="WebApp",
                endpoint_path="/api/users",
                method="GET",
            )
        )
        await store.create(
            InterfaceContract(
                contract_id="",
                project_id=proj.project_id,
                container_id="WebApp",
                endpoint_path="/api/orders",
                method="POST",
            )
        )
        await store.create(
            InterfaceContract(
                contract_id="",
                project_id=proj.project_id,
                container_id="MobileApp",
                endpoint_path="/api/push",
                method="POST",
            )
        )

        web_contracts = await store.list_by_container(proj.project_id, "WebApp")
        assert len(web_contracts) == 2

    @pytest.mark.asyncio
    async def test_list_by_project_excludes_deprecated(self, db_session) -> None:
        """list_by_project excludes DEPRECATED."""
        proj = await self._seed_project(db_session)
        store = InterfaceContractStore(db_session)

        cid1 = await store.create(
            InterfaceContract(
                contract_id="",
                project_id=proj.project_id,
                container_id="C1",
                endpoint_path="/a",
                method="GET",
            )
        )
        cid2 = await store.create(
            InterfaceContract(
                contract_id="",
                project_id=proj.project_id,
                container_id="C2",
                endpoint_path="/b",
                method="GET",
            )
        )
        await store.deprecate(cid2)

        active = await store.list_by_project(proj.project_id)
        assert len(active) == 1
        assert active[0].contract_id == cid1

    @pytest.mark.asyncio
    async def test_state_machine(self, db_session) -> None:
        """Test freeze / gap / deprecate transitions."""
        proj = await self._seed_project(db_session)
        store = InterfaceContractStore(db_session)

        cid = await store.create(
            InterfaceContract(
                contract_id="",
                project_id=proj.project_id,
                container_id="C1",
                endpoint_path="/x",
                method="GET",
            )
        )

        await store.freeze(cid)
        frozen = await store.get(cid)
        assert frozen is not None
        assert frozen.status == ContractStatus.FROZEN.value

        await store.mark_gap(cid)
        gap = await store.get(cid)
        assert gap is not None
        assert gap.status == ContractStatus.GAP.value

        await store.deprecate(cid)
        dep = await store.get(cid)
        assert dep is not None
        assert dep.status == ContractStatus.DEPRECATED.value

    @pytest.mark.asyncio
    async def test_update_schema(self, db_session) -> None:
        """Update request/response schema."""
        proj = await self._seed_project(db_session)
        store = InterfaceContractStore(db_session)

        cid = await store.create(
            InterfaceContract(
                contract_id="",
                project_id=proj.project_id,
                container_id="C1",
                endpoint_path="/x",
                method="GET",
            )
        )

        await store.update_schema(
            cid,
            request_schema={"properties": {"name": {"type": "string"}}},
            response_schema={"properties": {"id": {"type": "integer"}}},
        )

        updated = await store.get(cid)
        assert updated is not None
        assert updated.request_schema is not None
        assert "name" in updated.request_schema["properties"]
        assert "id" in updated.response_schema["properties"]

    @pytest.mark.asyncio
    async def test_export_for_openui(self, db_session) -> None:
        """Export contracts as OpenUI prompt text."""
        proj = await self._seed_project(db_session)
        store = InterfaceContractStore(db_session)

        await store.create(
            InterfaceContract(
                contract_id="",
                project_id=proj.project_id,
                container_id="C1",
                endpoint_path="/api/users",
                method="GET",
                summary="List users",
            )
        )

        text = await store.export_for_openui(proj.project_id)
        assert "Available Endpoints:" in text
        assert "GET /api/users" in text
