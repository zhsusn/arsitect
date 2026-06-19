"""Tests for Complexity router."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.project import Project
from main import app

client = TestClient(app)


class TestCreateSizeEstimate:
    """Tests POST /projects/{id}/size-estimates."""

    @pytest.fixture
    async def seeded_proj(self) -> Project:
        async with AsyncSessionLocal() as session:
            unique = str(uuid.uuid4())[:8]
            app_obj = Application(
                application_id="app-cx-api-1",
                application_name=f"Test App CX1 {unique}",
                local_path="/tmp",
            )
            session.add(app_obj)
            await session.flush()
            proj = Project(
                project_id="proj-cx-api-1",
                project_name="Complexity Test",
                application_id="app-cx-api-1",
                template_level="Standard",
                project_status="Draft",
            )
            session.add(proj)
            await session.flush()
            await session.commit()
            return proj

    def test_success(self, seeded_proj: Project) -> None:
        resp = client.post(
            "/api/v1/projects/proj-cx-api-1/size-estimates",
            json={
                "module_count": 5,
                "interface_count": 10,
                "page_count": 3,
                "tech_complexity": "Medium",
                "risk_level": "Low",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["project_id"] == "proj-cx-api-1"
        assert data["complexity_level"] in ("Trivial", "Light", "Standard", "Deep")

    def test_project_not_found(self) -> None:
        resp = client.post(
            "/api/v1/projects/no-such/size-estimates",
            json={
                "module_count": 1,
                "interface_count": 0,
                "page_count": 0,
                "tech_complexity": "Low",
                "risk_level": "Low",
            },
        )
        assert resp.status_code == 404

    def test_validation_error(self) -> None:
        resp = client.post(
            "/api/v1/projects/proj-cx-api-1/size-estimates",
            json={
                "module_count": 0,
                "interface_count": 0,
                "page_count": 0,
                "tech_complexity": "Low",
                "risk_level": "Low",
            },
        )
        assert resp.status_code == 422


class TestListSizeEstimates:
    """Tests GET /projects/{id}/size-estimates."""

    @pytest.fixture
    async def seeded_proj2(self) -> Project:
        async with AsyncSessionLocal() as session:
            unique = str(uuid.uuid4())[:8]
            app_obj = Application(
                application_id="app-cx-api-2",
                application_name=f"Test App CX2 {unique}",
                local_path="/tmp",
            )
            session.add(app_obj)
            await session.flush()
            proj = Project(
                project_id="proj-cx-api-2",
                project_name="List Test",
                application_id="app-cx-api-2",
                template_level="Standard",
                project_status="Draft",
            )
            session.add(proj)
            await session.flush()
            await session.commit()
            return proj

    def test_success(self, seeded_proj2: Project) -> None:
        client.post(
            "/api/v1/projects/proj-cx-api-2/size-estimates",
            json={
                "module_count": 3,
                "interface_count": 0,
                "page_count": 0,
                "tech_complexity": "Low",
                "risk_level": "Low",
            },
        )

        resp = client.get("/api/v1/projects/proj-cx-api-2/size-estimates")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1


class TestGetTemplateRecommendation:
    """Tests GET /complexity/templates/{level}."""

    def test_success(self) -> None:
        resp = client.get("/api/v1/complexity/templates/Standard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["level"] == "Standard"
        assert data["stage_count"] > 0

    def test_invalid_level(self) -> None:
        resp = client.get("/api/v1/complexity/templates/Unknown")
        assert resp.status_code == 422
