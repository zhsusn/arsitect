"""Integration test 3: Advanced链路 — Complexity + C4 + Monitoring + Canvas."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.c4_baseline import C4Baseline
from app.models.operation_log import OperationLog
from app.models.project import Project


class TestSync3Advanced:
    """端到端验证高级功能链路。"""

    @pytest.fixture
    async def seeded_advanced_data(self):
        """Seed application, project, c4 baseline and operation log."""
        async with AsyncSessionLocal() as session:
            await session.execute(delete(OperationLog))
            await session.execute(delete(C4Baseline))
            await session.execute(delete(Project))
            await session.execute(delete(Application))
            await session.commit()

            app_obj = Application(
                application_id="app-sync3",
                application_name="Sync3App",
                local_path="/tmp/sync3",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-sync3",
                project_name="Sync3Proj",
                application_id=app_obj.application_id,
                template_level="Standard",
                project_status="Active",
                risk_level="Low",
            )
            session.add(proj)
            await session.flush()

            c4 = C4Baseline(
                baseline_id="c4-sync3",
                project_id=proj.project_id,
                version="1.0.0",
                dsl_content="system:\n  id: TestSystem\n  name: Test",
                dsl_hash="hash1",
                level="L1-L4",
                is_current=True,
            )
            session.add(c4)

            log = OperationLog(
                log_id="log-sync3",
                project_id=proj.project_id,
                action="CREATE_PROJECT",
                detail="Created by integration test",
            )
            session.add(log)
            await session.commit()
            session.expunge(app_obj)
            session.expunge(proj)
            session.expunge(c4)
            session.expunge(log)
            return app_obj, proj, c4, log

    @pytest.mark.asyncio
    async def test_full_advanced_flow(self, seeded_advanced_data, client: TestClient) -> None:
        """TEST-1498: C4 DSL → 监控看板 → 画布状态。"""
        app_obj, proj, c4, log = seeded_advanced_data

        # Complexity estimate
        res = client.post(
            f"/api/v1/projects/{proj.project_id}/size-estimates",
            json={
                "module_count": 5,
                "interface_count": 10,
                "page_count": 8,
                "tech_complexity": "Medium",
                "risk_level": "Low",
            },
        )
        assert res.status_code == 201

        # C4 DSL (unified YAML)
        res = client.get("/api/v1/c4/dsl/current", params={"project_id": proj.project_id})
        assert res.status_code == 200
        dsl_data = res.json()
        assert dsl_data["content"] == "system:\n  id: TestSystem\n  name: Test"
        assert dsl_data["format"] == "yaml"

        # Monitoring overview
        res = client.get("/api/v1/monitoring/overview")
        assert res.status_code == 200
        overview = res.json()
        assert "total_projects" in overview

        # Monitoring project stats
        res = client.get(f"/api/v1/monitoring/projects/{proj.project_id}/stats")
        assert res.status_code == 200
        stats = res.json()
        assert stats["execution_count"] >= 0

        # Canvas state save & get
        canvas_payload = {
            "nodes": [
                {
                    "id": "n1",
                    "type": "stage",
                    "position": {"x": 0, "y": 0},
                    "data": {"label": "Stage 1"},
                }
            ],
            "edges": [],
            "viewport": {"x": 0, "y": 0, "zoom": 1},
        }
        res = client.post(f"/api/v1/projects/{proj.project_id}/canvas/state", json=canvas_payload)
        assert res.status_code == 201
        canvas = res.json()
        assert canvas["project_id"] == proj.project_id

        res = client.get(f"/api/v1/projects/{proj.project_id}/canvas/state")
        assert res.status_code == 200
        canvas_get = res.json()
        assert len(canvas_get["nodes"]) == 1
