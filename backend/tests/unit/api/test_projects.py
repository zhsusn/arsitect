"""Tests for ProjectRouter."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.project import Project
from app.models.project_stage import ProjectStage
from app.models.stage_skill_binding import StageSkillBinding
from main import app

client = TestClient(app)


class TestProjectRouter:
    """ProjectRouter integration tests."""

    @pytest.fixture
    async def seeded_app(self) -> Application:
        """Seed an application."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM size_estimates"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app = Application(
                application_id="app-router",
                application_name="Router App",
                local_path="/tmp/router",
            )
            session.add(app)
            await session.commit()
            return app

    @pytest.mark.asyncio
    async def test_list_projects(self, seeded_app: Application) -> None:
        """GET /applications/{id}/projects returns paginated projects."""
        async with AsyncSessionLocal() as session:
            proj = Project(
                project_id="proj-r1",
                project_name="Router Project",
                application_id=seeded_app.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()

        res = client.get(f"/api/v1/applications/{seeded_app.application_id}/projects")
        assert res.status_code == 200
        data = res.json()
        assert "data" in data
        assert len(data["data"]) >= 1
        assert any(p["project_id"] == "proj-r1" for p in data["data"])

    @pytest.mark.asyncio
    async def test_create_project(self, seeded_app: Application) -> None:
        """POST creates a project."""
        payload = {
            "project_id": "proj-r2",
            "project_name": "New Router Project",
            "template_level": "Light",
        }
        res = client.post(
            f"/api/v1/applications/{seeded_app.application_id}/projects",
            json=payload,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["project_name"] == "New Router Project"
        assert data["project_status"] == "Draft"

    @pytest.mark.asyncio
    async def test_create_duplicate_returns_409(self, seeded_app: Application) -> None:
        """Duplicate name returns 409."""
        async with AsyncSessionLocal() as session:
            proj = Project(
                project_id="proj-r3",
                project_name="Dup Router",
                application_id=seeded_app.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()

        payload = {
            "project_name": "Dup Router",
            "template_level": "Light",
        }
        res = client.post(
            f"/api/v1/applications/{seeded_app.application_id}/projects",
            json=payload,
        )
        assert res.status_code == 409

    @pytest.mark.asyncio
    async def test_get_project(self, seeded_app: Application) -> None:
        """GET /projects/{id} returns project details."""
        async with AsyncSessionLocal() as session:
            proj = Project(
                project_id="proj-r4",
                project_name="Get Project",
                application_id=seeded_app.application_id,
                template_level="Deep",
            )
            session.add(proj)
            await session.commit()

        res = client.get("/api/v1/projects/proj-r4")
        assert res.status_code == 200
        data = res.json()
        assert data["project_name"] == "Get Project"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, seeded_app: Application) -> None:
        """GET unknown project returns 404."""
        res = client.get("/api/v1/projects/no-such-proj")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_update_project(self, seeded_app: Application) -> None:
        """PATCH updates project info."""
        async with AsyncSessionLocal() as session:
            proj = Project(
                project_id="proj-r5",
                project_name="Before",
                application_id=seeded_app.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()

        res = client.patch(
            "/api/v1/projects/proj-r5",
            json={"project_name": "After", "project_description": "Updated"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["project_name"] == "After"
        assert data["project_description"] == "Updated"

    @pytest.mark.asyncio
    async def test_archive_project(self, seeded_app: Application) -> None:
        """POST /archive archives an Active project."""
        async with AsyncSessionLocal() as session:
            proj = Project(
                project_id="proj-r6",
                project_name="Archive Me",
                application_id=seeded_app.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()

        client.post("/api/v1/projects/proj-r6/activate")
        res = client.post("/api/v1/projects/proj-r6/archive")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "archived"

    @pytest.mark.asyncio
    async def test_activate_project(self, seeded_app: Application) -> None:
        """POST /activate changes status to Active."""
        async with AsyncSessionLocal() as session:
            proj = Project(
                project_id="proj-r7",
                project_name="Activate Me",
                application_id=seeded_app.application_id,
                template_level="Standard",
                project_status="Draft",
            )
            session.add(proj)
            await session.commit()

        res = client.post("/api/v1/projects/proj-r7/activate")
        assert res.status_code == 200
        data = res.json()
        assert data["project_status"] == "Active"

    @pytest.mark.asyncio
    async def test_cancel_zero_progress(self, seeded_app: Application) -> None:
        """POST /cancel cancels zero-progress project."""
        async with AsyncSessionLocal() as session:
            proj = Project(
                project_id="proj-r8",
                project_name="Cancel Me",
                application_id=seeded_app.application_id,
                template_level="Standard",
                progress_percent=0,
            )
            session.add(proj)
            await session.commit()

        res = client.post("/api/v1/projects/proj-r8/cancel")
        assert res.status_code == 200
        data = res.json()
        assert data["project_status"] == "Cancelled"

    @pytest.mark.asyncio
    async def test_cancel_active_project(self, seeded_app: Application) -> None:
        """POST /cancel cancels an Active project."""
        async with AsyncSessionLocal() as session:
            proj = Project(
                project_id="proj-r9",
                project_name="Cancel Active",
                application_id=seeded_app.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()

        client.post("/api/v1/projects/proj-r9/activate")
        res = client.post("/api/v1/projects/proj-r9/cancel")
        assert res.status_code == 200
        data = res.json()
        assert data["project_status"] == "Cancelled"

    @pytest.fixture
    async def seeded_project_with_stages(
        self, seeded_app: Application
    ) -> str:
        """Seed a project with three stages and bindings."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM stage_rollback_logs"))
            await session.execute(text("DELETE FROM stage_skill_bindings"))
            await session.execute(text("DELETE FROM project_stages"))
            await session.execute(text("DELETE FROM project_path_config"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app = Application(
                application_id="app-rollback-router",
                application_name="Rollback Router App",
                local_path="/tmp/rollback-router",
            )
            session.add(app)
            await session.flush()

            proj = Project(
                project_id="proj-rollback-router",
                project_name="Rollback Router Project",
                application_id=app.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.flush()

            for idx, (ps_id, sk_id) in enumerate(
                [("ps-rr-1", "skill-rr-1"), ("ps-rr-2", "skill-rr-2")],
                start=1,
            ):
                stage = ProjectStage(
                    project_stage_id=ps_id,
                    project_id=proj.project_id,
                    stage_id=f"ts-rr-{idx}",
                    order_index=idx,
                    status="DEFINED",
                    primary_skill_id=sk_id,
                    runtime_status="not_started",
                    is_gate_required=False,
                )
                session.add(stage)
                await session.flush()
                session.add(
                    StageSkillBinding(
                        binding_id=f"b-rr-{idx}",
                        project_stage_id=ps_id,
                        skill_id=sk_id,
                        role="primary",
                        execution_order=0,
                    )
                )
            await session.commit()
            return proj.project_id

    @pytest.mark.asyncio
    async def test_rollback_project_stage_endpoint(
        self, seeded_project_with_stages: str
    ) -> None:
        """POST rollback resets downstream stage and returns summary."""
        res = client.post(
            f"/api/v1/projects/{seeded_project_with_stages}/stages/ps-rr-2/rollback",
            json={"target_stage_id": "ps-rr-1", "reason": "回退测试"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["project_id"] == seeded_project_with_stages
        assert data["target_stage_id"] == "ps-rr-1"
        assert "ps-rr-2" in data["reset_stage_ids"]
        assert data["stale_artifact_ids"] == []
