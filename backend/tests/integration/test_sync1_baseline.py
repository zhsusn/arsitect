"""Integration test 1: P0 baseline链路 — App + Projects + Skills + Templates."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.project import Project
from app.models.skill import Skill


class TestSync1Baseline:
    """端到端验证 P0 基础链路。"""

    @pytest.fixture
    async def seeded_baseline_data(self):
        """Seed application, project and skill for baseline tests."""
        async with AsyncSessionLocal() as session:
            await session.execute(delete(Skill))
            await session.execute(delete(Project))
            await session.execute(delete(Application))
            await session.commit()

            app_obj = Application(
                application_id="app-sync1",
                application_name="Sync1App",
                local_path="/tmp/sync1",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-sync1",
                project_name="Sync1Proj",
                application_id=app_obj.application_id,
                template_level="Standard",
                project_status="Active",
                risk_level="Low",
            )
            session.add(proj)
            await session.flush()

            skill = Skill(
                skill_id="skill-sync1",
                skill_name="sync-skill",
                version="1.0.0",
                pattern="generator",
                directory_path="/tmp/skills/sync-skill",
                description="Test skill",
            )
            session.add(skill)
            await session.commit()
            session.expunge(app_obj)
            session.expunge(proj)
            session.expunge(skill)
            return app_obj, proj, skill

    @pytest.mark.asyncio
    async def test_full_baseline_flow(self, seeded_baseline_data, client: TestClient) -> None:
        """TEST-1500: 创建 Application → Project → Skill → 列表查询。"""
        app_obj, proj, skill = seeded_baseline_data

        # List applications
        res = client.get("/api/v1/applications")
        assert res.status_code == 200
        apps = res.json()["data"]
        assert any(a["application_id"] == "app-sync1" for a in apps)

        # List projects
        res = client.get(f"/api/v1/applications/{app_obj.application_id}/projects")
        assert res.status_code == 200
        projects = res.json()["data"]
        assert any(p["project_id"] == "proj-sync1" for p in projects)

        # List skills
        res = client.get("/api/v1/skills")
        assert res.status_code == 200
        skills = res.json()["data"]
        assert any(s["skill_id"] == "skill-sync1" for s in skills)

        # List templates
        res = client.get("/api/v1/templates")
        assert res.status_code == 200
        templates = res.json()
        assert isinstance(templates, list)
