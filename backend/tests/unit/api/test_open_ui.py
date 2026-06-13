"""Tests for OpenUIRouter.

Covers OpenUI spec CRUD API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.api.v1.open_ui import delete_spec, get_spec, list_specs, update_spec
from app.core.exceptions import NotFoundError
from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.open_ui_spec import OpenUISpec
from app.models.project import Project
from app.schemas.open_ui import OpenUIUpdateDTO
from main import app

client = TestClient(app)


class TestOpenUIRouter:
    """OpenUI router API tests."""

    @pytest.fixture
    async def seeded_project(self) -> Project:
        """Seed an application and project."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM open_ui_specs"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-openui-router",
                application_name="OpenUI Router App",
                local_path="/tmp/openui-router",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-openui-router",
                project_name="OpenUI Router Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()
            return proj

    @pytest.fixture
    async def seeded_spec(self, seeded_project: Project) -> OpenUISpec:
        """Seed an OpenUI spec."""
        async with AsyncSessionLocal() as session:
            spec = OpenUISpec(
                spec_id="openui-test-001",
                project_id=seeded_project.project_id,
                spec_name="Homepage",
                status="DRAFT",
            )
            session.add(spec)
            await session.commit()
            return spec

    @pytest.mark.asyncio
    async def test_create_spec(self, seeded_project: Project) -> None:
        """TEST-0501: POST creates an OpenUI spec."""
        payload = {
            "spec_name": "Homepage",
            "status": "DRAFT",
        }
        res = client.post(
            f"/api/v1/projects/{seeded_project.project_id}/open-ui-specs",
            json=payload,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["spec_name"] == "Homepage"
        assert data["status"] == "DRAFT"

    @pytest.mark.asyncio
    async def test_create_spec_invalid_status(self, seeded_project: Project) -> None:
        """TEST-0502: POST with invalid status returns 422."""
        payload = {
            "spec_name": "Homepage",
            "status": "INVALID",
        }
        res = client.post(
            f"/api/v1/projects/{seeded_project.project_id}/open-ui-specs",
            json=payload,
        )
        assert res.status_code == 400

    @pytest.mark.asyncio
    async def test_list_specs(self, seeded_project: Project, seeded_spec: OpenUISpec) -> None:
        """TEST-0503: GET lists OpenUI specs (Direct)."""
        async with AsyncSessionLocal() as session:
            result = await list_specs(seeded_project.project_id, db=session)
            assert isinstance(result, list)
            assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_get_spec(self, seeded_spec: OpenUISpec) -> None:
        """TEST-0504: GET returns a single spec (Direct)."""
        async with AsyncSessionLocal() as session:
            result = await get_spec("openui-test-001", db=session)
            assert result.spec_id == "openui-test-001"

    @pytest.mark.asyncio
    async def test_get_spec_not_found(self, seeded_project: Project) -> None:
        """TEST-0505: GET nonexistent spec returns 404 (Direct)."""
        async with AsyncSessionLocal() as session:
            with pytest.raises(NotFoundError):
                await get_spec("no-such-spec", db=session)

    @pytest.mark.asyncio
    async def test_update_spec(self, seeded_spec: OpenUISpec) -> None:
        """TEST-0506: PATCH updates an OpenUI spec (Direct)."""
        async with AsyncSessionLocal() as session:
            dto = OpenUIUpdateDTO(spec_name="NewName", status="GENERATED")
            result = await update_spec("openui-test-001", dto, db=session)
            assert result.spec_name == "NewName"
            assert result.status == "GENERATED"

    @pytest.mark.asyncio
    async def test_delete_spec(self, seeded_spec: OpenUISpec) -> None:
        """TEST-0507: DELETE removes an OpenUI spec (Direct)."""
        async with AsyncSessionLocal() as session:
            await delete_spec("openui-test-001", db=session)
            with pytest.raises(NotFoundError):
                await get_spec("openui-test-001", db=session)
