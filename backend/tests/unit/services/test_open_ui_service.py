"""Tests for OpenUIService."""

from __future__ import annotations

import pytest

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.application import Application
from app.models.project import Project
from app.services.open_ui_service import OpenUIService


class TestOpenUIService:
    """OpenUIService unit tests."""

    async def _seed_project(self, session, suffix: str = "1") -> Project:
        app = Application(
            application_id=f"app-oui-{suffix}",
            application_name=f"OuiApp{suffix}",
            local_path=f"/tmp/oui{suffix}",
        )
        session.add(app)
        await session.flush()
        proj = Project(
            project_id=f"proj-oui-{suffix}",
            project_name=f"OuiProj{suffix}",
            application_id=app.application_id,
            template_level="Standard",
        )
        session.add(proj)
        await session.flush()
        return proj

    @pytest.mark.asyncio
    async def test_create_spec(self, db_session) -> None:
        proj = await self._seed_project(db_session)
        svc = OpenUIService(db_session)
        spec = await svc.create_spec(
            project_id=proj.project_id,
            spec_name="Login Page",
            status="DRAFT",
        )
        assert spec.spec_name == "Login Page"
        assert spec.status == "DRAFT"
        assert spec.project_id == proj.project_id

    @pytest.mark.asyncio
    async def test_create_spec_invalid_status(self, db_session) -> None:
        proj = await self._seed_project(db_session, suffix="bad")
        svc = OpenUIService(db_session)
        with pytest.raises(BadRequestError):
            await svc.create_spec(
                project_id=proj.project_id,
                spec_name="X",
                status="UNKNOWN",
            )

    @pytest.mark.asyncio
    async def test_get_spec(self, db_session) -> None:
        proj = await self._seed_project(db_session, suffix="get")
        svc = OpenUIService(db_session)
        created = await svc.create_spec(
            project_id=proj.project_id,
            spec_name="Dashboard",
            status="GENERATED",
        )
        fetched = await svc.get_spec(created.spec_id)
        assert fetched.spec_id == created.spec_id

    @pytest.mark.asyncio
    async def test_get_spec_not_found(self, db_session) -> None:
        svc = OpenUIService(db_session)
        with pytest.raises(NotFoundError):
            await svc.get_spec("no-such-spec")

    @pytest.mark.asyncio
    async def test_list_specs(self, db_session) -> None:
        proj = await self._seed_project(db_session, suffix="list")
        svc = OpenUIService(db_session)
        before = await svc.list_specs(proj.project_id)
        await svc.create_spec(proj.project_id, "A", "DRAFT")
        await svc.create_spec(proj.project_id, "B", "DRAFT")
        specs = await svc.list_specs(proj.project_id)
        assert len(specs) == len(before) + 2

    @pytest.mark.asyncio
    async def test_update_spec(self, db_session) -> None:
        proj = await self._seed_project(db_session, suffix="upd")
        svc = OpenUIService(db_session)
        spec = await svc.create_spec(proj.project_id, "Old", "DRAFT")
        updated = await svc.update_spec(
            spec.spec_id, {"spec_name": "New", "status": "GENERATED"}
        )
        assert updated.spec_name == "New"
        assert updated.status == "GENERATED"

    @pytest.mark.asyncio
    async def test_delete_spec(self, db_session) -> None:
        proj = await self._seed_project(db_session, suffix="del")
        svc = OpenUIService(db_session)
        spec = await svc.create_spec(proj.project_id, "ToDel", "DRAFT")
        await svc.delete_spec(spec.spec_id)
        with pytest.raises(NotFoundError):
            await svc.get_spec(spec.spec_id)
