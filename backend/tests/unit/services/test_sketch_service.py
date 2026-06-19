"""Tests for SketchService."""

from __future__ import annotations

import pytest

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.application import Application
from app.models.project import Project
from app.services.sketch_service import SketchService


class TestSketchService:
    """SketchService unit tests."""

    async def _seed_project(self, session, suffix: str = "1") -> Project:
        app = Application(
            application_id=f"app-sketch-{suffix}",
            application_name=f"SketchApp{suffix}",
            local_path=f"/tmp/sketch{suffix}",
        )
        session.add(app)
        await session.flush()
        proj = Project(
            project_id=f"proj-sketch-{suffix}",
            project_name=f"SketchProj{suffix}",
            application_id=app.application_id,
            template_level="Standard",
        )
        session.add(proj)
        await session.flush()
        return proj

    @pytest.mark.asyncio
    async def test_create_sketch(self, db_session) -> None:
        proj = await self._seed_project(db_session)
        svc = SketchService(db_session)
        sketch = await svc.create_sketch(
            project_id=proj.project_id,
            name="Landing Page Sketch",
            source_story_ids=None,
            status="DRAFT",
        )
        assert sketch.name == "Landing Page Sketch"
        assert sketch.status == "DRAFT"

    @pytest.mark.asyncio
    async def test_create_sketch_invalid_status(self, db_session) -> None:
        proj = await self._seed_project(db_session, suffix="bad")
        svc = SketchService(db_session)
        with pytest.raises(BadRequestError):
            await svc.create_sketch(
                project_id=proj.project_id,
                name="X",
                source_story_ids=None,
                status="WRONG",
            )

    @pytest.mark.asyncio
    async def test_get_sketch(self, db_session) -> None:
        proj = await self._seed_project(db_session, suffix="get")
        svc = SketchService(db_session)
        created = await svc.create_sketch(proj.project_id, "A", None, "GENERATED")
        fetched = await svc.get_sketch(created.sketch_id)
        assert fetched.sketch_id == created.sketch_id

    @pytest.mark.asyncio
    async def test_get_sketch_not_found(self, db_session) -> None:
        svc = SketchService(db_session)
        with pytest.raises(NotFoundError):
            await svc.get_sketch("no-such-sketch")

    @pytest.mark.asyncio
    async def test_list_sketches(self, db_session) -> None:
        proj = await self._seed_project(db_session, suffix="list")
        svc = SketchService(db_session)
        await svc.create_sketch(proj.project_id, "A", None, "DRAFT")
        await svc.create_sketch(proj.project_id, "B", None, "DRAFT")
        sketches = await svc.list_sketches(proj.project_id)
        assert len(sketches) == 2

    @pytest.mark.asyncio
    async def test_update_sketch(self, db_session) -> None:
        proj = await self._seed_project(db_session, suffix="upd")
        svc = SketchService(db_session)
        sketch = await svc.create_sketch(proj.project_id, "Old", None, "DRAFT")
        updated = await svc.update_sketch(
            sketch.sketch_id,
            {"name": "New", "status": "GENERATED"},
        )
        assert updated.name == "New"
        assert updated.status == "GENERATED"

    @pytest.mark.asyncio
    async def test_delete_sketch(self, db_session) -> None:
        proj = await self._seed_project(db_session, suffix="del")
        svc = SketchService(db_session)
        sketch = await svc.create_sketch(proj.project_id, "ToDel", None, "DRAFT")
        await svc.delete_sketch(sketch.sketch_id)
        with pytest.raises(NotFoundError):
            await svc.get_sketch(sketch.sketch_id)
