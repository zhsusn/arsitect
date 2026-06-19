"""Tests for WireframeRouter.

Covers wireframe CRUD API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.api.v1.wireframe import (
    delete_wireframe,
    get_wireframe,
    list_wireframes,
    update_wireframe,
)
from app.core.exceptions import NotFoundError
from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.project import Project
from app.models.wireframe import Wireframe
from app.schemas.wireframe import WireframeUpdateDTO
from main import app

client = TestClient(app)


class TestWireframeRouter:
    """Wireframe router API tests."""

    @pytest.fixture
    async def seeded_project(self) -> Project:
        """Seed an application and project."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM wireframes"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-wireframe-router",
                application_name="Wireframe Router App",
                local_path="/tmp/wireframe-router",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-wireframe-router",
                project_name="Wireframe Router Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()
            return proj

    @pytest.fixture
    async def seeded_wireframe(self, seeded_project: Project) -> Wireframe:
        """Seed a wireframe."""
        async with AsyncSessionLocal() as session:
            wf = Wireframe(
                wireframe_id="wireframe-test-001",
                project_id=seeded_project.project_id,
                name="Dashboard Wireframe",
                c4_baseline_version=None,
                status="DRAFT",
            )
            session.add(wf)
            await session.commit()
            return wf

    @pytest.mark.asyncio
    async def test_create_wireframe(self, seeded_project: Project) -> None:
        """TEST-0701: POST creates a wireframe."""
        payload = {
            "name": "Dashboard Wireframe",
            "status": "DRAFT",
        }
        res = client.post(
            f"/api/v1/projects/{seeded_project.project_id}/wireframes",
            json=payload,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Dashboard Wireframe"
        assert data["status"] == "DRAFT"

    @pytest.mark.asyncio
    async def test_create_wireframe_invalid_status(self, seeded_project: Project) -> None:
        """TEST-0702: POST with invalid status returns 422."""
        payload = {
            "name": "Test",
            "status": "INVALID",
        }
        res = client.post(
            f"/api/v1/projects/{seeded_project.project_id}/wireframes",
            json=payload,
        )
        assert res.status_code == 400

    @pytest.mark.asyncio
    async def test_list_wireframes(
        self, seeded_project: Project, seeded_wireframe: Wireframe
    ) -> None:
        """TEST-0703: GET lists wireframes (Direct)."""
        async with AsyncSessionLocal() as session:
            result = await list_wireframes(seeded_project.project_id, db=session)
            assert isinstance(result, list)
            assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_get_wireframe(self, seeded_wireframe: Wireframe) -> None:
        """TEST-0704: GET returns a single wireframe (Direct)."""
        async with AsyncSessionLocal() as session:
            result = await get_wireframe("wireframe-test-001", db=session)
            assert result.wireframe_id == "wireframe-test-001"

    @pytest.mark.asyncio
    async def test_get_wireframe_not_found(self, seeded_project: Project) -> None:
        """TEST-0705: GET nonexistent wireframe returns 404 (Direct)."""
        async with AsyncSessionLocal() as session:
            with pytest.raises(NotFoundError):
                await get_wireframe("no-such-wireframe", db=session)

    @pytest.mark.asyncio
    async def test_update_wireframe(self, seeded_wireframe: Wireframe) -> None:
        """TEST-0706: PATCH updates a wireframe (Direct)."""
        async with AsyncSessionLocal() as session:
            dto = WireframeUpdateDTO(name="NewName", status="ACTIVE")
            result = await update_wireframe("wireframe-test-001", dto, db=session)
            assert result.name == "NewName"
            assert result.status == "ACTIVE"

    @pytest.mark.asyncio
    async def test_delete_wireframe(self, seeded_wireframe: Wireframe) -> None:
        """TEST-0707: DELETE removes a wireframe (Direct)."""
        async with AsyncSessionLocal() as session:
            await delete_wireframe("wireframe-test-001", db=session)
            with pytest.raises(NotFoundError):
                await get_wireframe("wireframe-test-001", db=session)
