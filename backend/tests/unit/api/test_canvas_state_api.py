"""Tests for CanvasStateRouter."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.canvas_state import CanvasState
from app.models.project import Project
from main import app

client = TestClient(app)


class TestCanvasStateRouter:
    """Canvas state API tests."""

    async def _seed_project(self, session, suffix: str = "1") -> Project:
        """Helper to create an application + project."""
        app_obj = Application(
            application_id=f"app-csapi-{suffix}",
            application_name=f"CsApiApp{suffix}",
            local_path=f"/tmp/csapi{suffix}",
        )
        session.add(app_obj)
        await session.flush()
        proj = Project(
            project_id=f"proj-csapi-{suffix}",
            project_name=f"CsApiProj{suffix}",
            application_id=app_obj.application_id,
            template_level="Standard",
            project_status="Active",
            risk_level="Low",
        )
        session.add(proj)
        await session.flush()
        return proj

    @pytest.mark.asyncio
    async def test_get_canvas_state_not_found(self) -> None:
        """GET returns 404 when canvas state does not exist."""
        res = client.get("/api/v1/projects/proj-missing/canvas/state")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_save_and_get_canvas_state(self) -> None:
        """POST creates canvas state; GET returns it."""
        async with AsyncSessionLocal() as session:
            proj = await self._seed_project(session, suffix="crud")
            await session.commit()

        payload = {
            "nodes": [
                {"id": "n1", "type": "stage", "position": {"x": 0, "y": 0}, "data": {"label": "Stage 1", "status": "DEFINED"}}
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2"}
            ],
            "viewport": {"x": 10, "y": 20, "zoom": 1.2},
        }

        res = client.post(f"/api/v1/projects/{proj.project_id}/canvas/state", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["project_id"] == proj.project_id
        assert len(data["nodes"]) == 1
        assert data["nodes"][0]["id"] == "n1"
        assert data["edges"][0]["source"] == "n1"
        assert data["viewport"]["zoom"] == 1.2

        res2 = client.get(f"/api/v1/projects/{proj.project_id}/canvas/state")
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["project_id"] == proj.project_id
        assert data2["nodes"][0]["data"]["status"] == "DEFINED"

    @pytest.mark.asyncio
    async def test_update_canvas_state(self) -> None:
        """POST updates existing canvas state."""
        async with AsyncSessionLocal() as session:
            proj = await self._seed_project(session, suffix="update")
            cs = CanvasState(
                canvas_state_id="cs-upd",
                project_id=proj.project_id,
                nodes="[]",
                edges="[]",
                viewport='{"x":0,"y":0,"zoom":1}',
            )
            session.add(cs)
            await session.commit()

        payload = {
            "nodes": [
                {"id": "n2", "position": {"x": 100, "y": 200}, "data": {"label": "Updated"}}
            ],
            "edges": [],
            "viewport": {"x": 50, "y": 50, "zoom": 0.8},
        }

        res = client.post(f"/api/v1/projects/{proj.project_id}/canvas/state", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert len(data["nodes"]) == 1
        assert data["nodes"][0]["data"]["label"] == "Updated"
        assert data["viewport"]["zoom"] == 0.8
