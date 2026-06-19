"""Tests for WireframeService."""

from __future__ import annotations

import pytest

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.application import Application
from app.models.project import Project
from app.services.wireframe_service import WireframeService


class TestWireframeService:
    """WireframeService unit tests."""

    async def _seed_project(self, session, suffix: str = "1") -> Project:
        app = Application(
            application_id=f"app-wf-{suffix}",
            application_name=f"WfApp{suffix}",
            local_path=f"/tmp/wf{suffix}",
        )
        session.add(app)
        await session.flush()
        proj = Project(
            project_id=f"proj-wf-{suffix}",
            project_name=f"WfProj{suffix}",
            application_id=app.application_id,
            template_level="Standard",
        )
        session.add(proj)
        await session.flush()
        return proj

    @pytest.mark.asyncio
    async def test_create_wireframe(self, db_session) -> None:
        proj = await self._seed_project(db_session)
        svc = WireframeService(db_session)
        wf = await svc.create_wireframe(
            project_id=proj.project_id,
            name="Homepage",
            c4_baseline_version=None,
            status="DRAFT",
        )
        assert wf.name == "Homepage"
        assert wf.status == "DRAFT"

    @pytest.mark.asyncio
    async def test_create_wireframe_invalid_status(self, db_session) -> None:
        proj = await self._seed_project(db_session, suffix="bad")
        svc = WireframeService(db_session)
        with pytest.raises(BadRequestError):
            await svc.create_wireframe(
                project_id=proj.project_id,
                name="X",
                status="INVALID",
            )

    @pytest.mark.asyncio
    async def test_get_wireframe(self, db_session) -> None:
        proj = await self._seed_project(db_session, suffix="get")
        svc = WireframeService(db_session)
        created = await svc.create_wireframe(
            project_id=proj.project_id, name="Dash", status="ACTIVE"
        )
        fetched = await svc.get_wireframe(created.wireframe_id)
        assert fetched.wireframe_id == created.wireframe_id

    @pytest.mark.asyncio
    async def test_get_wireframe_not_found(self, db_session) -> None:
        svc = WireframeService(db_session)
        with pytest.raises(NotFoundError):
            await svc.get_wireframe("no-such-wf")

    @pytest.mark.asyncio
    async def test_list_wireframes(self, db_session) -> None:
        proj = await self._seed_project(db_session, suffix="list")
        svc = WireframeService(db_session)
        before = await svc.list_wireframes(proj.project_id)
        await svc.create_wireframe(project_id=proj.project_id, name="A", status="DRAFT")
        await svc.create_wireframe(project_id=proj.project_id, name="B", status="DRAFT")
        wfs = await svc.list_wireframes(proj.project_id)
        assert len(wfs) == len(before) + 2

    @pytest.mark.asyncio
    async def test_update_wireframe(self, db_session) -> None:
        proj = await self._seed_project(db_session, suffix="upd")
        svc = WireframeService(db_session)
        wf = await svc.create_wireframe(project_id=proj.project_id, name="Old", status="DRAFT")
        updated = await svc.update_wireframe(wf.wireframe_id, {"name": "New", "status": "ACTIVE"})
        assert updated.name == "New"
        assert updated.status == "ACTIVE"

    @pytest.mark.asyncio
    async def test_delete_wireframe(self, db_session) -> None:
        proj = await self._seed_project(db_session, suffix="del")
        svc = WireframeService(db_session)
        wf = await svc.create_wireframe(project_id=proj.project_id, name="ToDel", status="DRAFT")
        await svc.delete_wireframe(wf.wireframe_id)
        with pytest.raises(NotFoundError):
            await svc.get_wireframe(wf.wireframe_id)
