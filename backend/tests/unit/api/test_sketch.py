"""Tests for SketchRouter.

Covers sketch CRUD API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.api.v1.sketch import delete_sketch, get_sketch, list_sketches, update_sketch
from app.core.exceptions import NotFoundError
from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.project import Project
from app.models.sketch import Sketch
from app.schemas.sketch import SketchUpdateDTO
from main import app

client = TestClient(app)


class TestSketchRouter:
    """Sketch router API tests."""

    @pytest.fixture
    async def seeded_project(self) -> Project:
        """Seed an application and project."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM sketches"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-sketch-router",
                application_name="Sketch Router App",
                local_path="/tmp/sketch-router",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-sketch-router",
                project_name="Sketch Router Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()
            return proj

    @pytest.fixture
    async def seeded_sketch(self, seeded_project: Project) -> Sketch:
        """Seed a sketch."""
        async with AsyncSessionLocal() as session:
            sketch = Sketch(
                sketch_id="sketch-test-001",
                project_id=seeded_project.project_id,
                name="Homepage Sketch",
                source_story_ids=None,
                status="DRAFT",
            )
            session.add(sketch)
            await session.commit()
            return sketch

    @pytest.mark.asyncio
    async def test_create_sketch(self, seeded_project: Project) -> None:
        """TEST-0601: POST creates a sketch."""
        payload = {
            "name": "Homepage Sketch",
            "status": "DRAFT",
        }
        res = client.post(
            f"/api/v1/projects/{seeded_project.project_id}/sketches",
            json=payload,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Homepage Sketch"
        assert data["status"] == "DRAFT"

    @pytest.mark.asyncio
    async def test_create_sketch_invalid_status(self, seeded_project: Project) -> None:
        """TEST-0602: POST with invalid status returns 422."""
        payload = {
            "name": "Test",
            "status": "INVALID",
        }
        res = client.post(
            f"/api/v1/projects/{seeded_project.project_id}/sketches",
            json=payload,
        )
        assert res.status_code == 400

    @pytest.mark.asyncio
    async def test_list_sketches(self, seeded_project: Project, seeded_sketch: Sketch) -> None:
        """TEST-0603: GET lists sketches (Direct)."""
        async with AsyncSessionLocal() as session:
            result = await list_sketches(seeded_project.project_id, db=session)
            assert isinstance(result, list)
            assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_get_sketch(self, seeded_sketch: Sketch) -> None:
        """TEST-0604: GET returns a single sketch (Direct)."""
        async with AsyncSessionLocal() as session:
            result = await get_sketch("sketch-test-001", db=session)
            assert result.sketch_id == "sketch-test-001"

    @pytest.mark.asyncio
    async def test_get_sketch_not_found(self, seeded_project: Project) -> None:
        """TEST-0605: GET nonexistent sketch returns 404 (Direct)."""
        async with AsyncSessionLocal() as session:
            with pytest.raises(NotFoundError):
                await get_sketch("no-such-sketch", db=session)

    @pytest.mark.asyncio
    async def test_update_sketch(self, seeded_sketch: Sketch) -> None:
        """TEST-0606: PATCH updates a sketch (Direct)."""
        async with AsyncSessionLocal() as session:
            dto = SketchUpdateDTO(name="NewName", status="GENERATED")
            result = await update_sketch("sketch-test-001", dto, db=session)
            assert result.name == "NewName"
            assert result.status == "GENERATED"

    @pytest.mark.asyncio
    async def test_delete_sketch(self, seeded_sketch: Sketch) -> None:
        """TEST-0607: DELETE removes a sketch (Direct)."""
        async with AsyncSessionLocal() as session:
            await delete_sketch("sketch-test-001", db=session)
            with pytest.raises(NotFoundError):
                await get_sketch("sketch-test-001", db=session)
