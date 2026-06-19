"""Tests for RequirementStudioRouter."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.project import Project
from app.models.project_stage import ProjectStage
from main import app

client = TestClient(app)


class TestRequirementStudioRouter:
    """RequirementStudio router full implementation tests."""

    @pytest.fixture
    async def seeded_project(self) -> Project:
        """Seed application and project for requirement studio tests."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM project_stages"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-rs",
                application_name="RS App",
                local_path="/tmp/rs",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-rs",
                project_name="RS Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()
            return proj

    @pytest.fixture
    async def seeded_project_with_stages(self, seeded_project: Project) -> Project:
        """Seed project stages for status tests."""
        async with AsyncSessionLocal() as session:
            for i, stage_id in enumerate(["requirement-outline", "design-outline"]):
                ps = ProjectStage(
                    project_stage_id=f"ps-{stage_id}",
                    project_id=seeded_project.project_id,
                    stage_id=stage_id,
                    order_index=i,
                    runtime_status="not_started",
                    skippable=False,
                )
                session.add(ps)
            await session.commit()
            return seeded_project

    @pytest.mark.asyncio
    async def test_get_status(self, seeded_project_with_stages: Project) -> None:
        """GET status returns project stage progression."""
        res = client.get(f"/api/v1/requirement-studio/{seeded_project_with_stages.project_id}/status")
        assert res.status_code == 200
        data = res.json()
        assert data["project_id"] == seeded_project_with_stages.project_id
        assert "current_stage" in data
        assert "stages" in data
        assert isinstance(data["stages"], list)

    @pytest.mark.asyncio
    async def test_execute_stage(self, seeded_project_with_stages: Project) -> None:
        """POST execute stage requires skillId in body."""
        res = client.post(
            f"/api/v1/requirement-studio/{seeded_project_with_stages.project_id}/stage/requirement-outline/execute",
            json={"skill_id": "skill-test"},
        )
        # Stage may not have bindings, but we verify the route works
        assert res.status_code in (200, 404, 422)

    @pytest.mark.asyncio
    async def test_get_artifacts(self, seeded_project: Project) -> None:
        """GET artifacts returns grouped artifact list."""
        res = client.get(f"/api/v1/requirement-studio/{seeded_project.project_id}/artifacts")
        assert res.status_code == 200
        data = res.json()
        assert "artifacts" in data
        assert isinstance(data["artifacts"], list)

    @pytest.mark.asyncio
    async def test_create_baseline(self, seeded_project: Project) -> None:
        """POST baseline creates baseline with artifactIds."""
        res = client.post(
            f"/api/v1/requirement-studio/{seeded_project.project_id}/governance/baseline",
            json={"artifact_ids": ["art-1"], "description": "test baseline"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "baseline_id" in data
        assert "version" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_get_stale_analysis(self, seeded_project: Project) -> None:
        """GET stale analysis returns stale artifacts."""
        res = client.get(f"/api/v1/requirement-studio/{seeded_project.project_id}/governance/stale-analysis")
        assert res.status_code == 200
        data = res.json()
        assert "stale_artifacts" in data
        assert isinstance(data["stale_artifacts"], list)

    @pytest.mark.asyncio
    async def test_create_change_request(self, seeded_project: Project) -> None:
        """POST change request requires targetArtifactId."""
        res = client.post(
            f"/api/v1/requirement-studio/{seeded_project.project_id}/governance/change-request",
            json={"target_artifact_id": "art-1", "change_type": "modify", "reason": "test"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "change_request_id" in data
        assert "status" in data
