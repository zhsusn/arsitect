"""Tests for TemplateRouter."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.project_stage import ProjectStage
from app.models.template import Template
from app.models.template_stage import TemplateStage
from main import app

client = TestClient(app)


class TestTemplateRouter:
    """Test template endpoints."""

    @pytest.fixture
    async def seeded(self) -> None:
        """Seed templates and stages."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM project_stages"))
            await session.execute(text("DELETE FROM template_stages"))
            await session.execute(text("DELETE FROM templates"))
            await session.commit()

            tpl = Template(
                template_id="Light",
                template_name="轻量",
                description="轻量模板",
                stage_count=2,
                estimated_skill_count=5,
                applicable_complexity="low",
            )
            session.add(tpl)
            await session.flush()

            stages = [
                TemplateStage(
                    stage_id="s-req",
                    stage_name="需求",
                    order_index=1,
                    template_id="Light",
                ),
                TemplateStage(
                    stage_id="s-code",
                    stage_name="编码",
                    order_index=2,
                    template_id="Light",
                ),
            ]
            session.add_all(stages)
            await session.commit()

    @pytest.mark.asyncio
    async def test_list_templates(self, seeded: None) -> None:
        """GET /templates returns template list."""
        response = client.get("/api/v1/templates")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(t["template_id"] == "Light" for t in data)

    @pytest.mark.asyncio
    async def test_get_template(self, seeded: None) -> None:
        """GET /templates/{level} returns template detail."""
        response = client.get("/api/v1/templates/Light")
        assert response.status_code == 200
        data = response.json()
        assert data["template"]["template_id"] == "Light"
        assert len(data["stages"]) == 2

    @pytest.mark.asyncio
    async def test_get_stage_sequence(self, seeded: None) -> None:
        """GET /projects/{id}/stage-sequence returns stages."""
        async with AsyncSessionLocal() as session:
            ps = ProjectStage(
                project_stage_id=str(uuid.uuid4()),
                project_id="proj-tpl",
                stage_id="s-req",
                order_index=1,
                status="DEFINED",
            )
            session.add(ps)
            await session.commit()

        response = client.get("/api/v1/templates/projects/proj-tpl/stage-sequence")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["project_id"] == "proj-tpl"

    @pytest.mark.asyncio
    async def test_preview_deviation(self, seeded: None) -> None:
        """POST /projects/{id}/template-deviation/preview returns impact."""
        async with AsyncSessionLocal() as session:
            # Add Standard template and a unique stage
            tpl = Template(
                template_id="Standard",
                template_name="标准",
                description="标准模板",
                stage_count=1,
                estimated_skill_count=3,
                applicable_complexity="medium",
            )
            session.add(tpl)
            await session.flush()

            stage = TemplateStage(
                stage_id="s-design",
                stage_name="设计",
                order_index=1,
                template_id="Standard",
            )
            session.add(stage)

            ps = ProjectStage(
                project_stage_id=str(uuid.uuid4()),
                project_id="proj-dev",
                stage_id="s-req",
                order_index=1,
                status="EXECUTED",
            )
            session.add(ps)
            await session.commit()

        response = client.post(
            "/api/v1/templates/projects/proj-dev/template-deviation/preview",
            json={"new_template_id": "Standard"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["frozen_count"] == 1
        assert data["added_count"] == 1

    @pytest.mark.asyncio
    async def test_confirm_deviation(self, seeded: None) -> None:
        """POST /projects/{id}/template-deviation applies switch."""
        async with AsyncSessionLocal() as session:
            tpl = Template(
                template_id="Deep",
                template_name="深度",
                description="深度模板",
                stage_count=1,
                estimated_skill_count=5,
                applicable_complexity="high",
            )
            session.add(tpl)
            await session.flush()

            stage = TemplateStage(
                stage_id="s-test",
                stage_name="测试",
                order_index=1,
                template_id="Deep",
                primary_skill_id="skill-test",
            )
            session.add(stage)

            ps = ProjectStage(
                project_stage_id=str(uuid.uuid4()),
                project_id="proj-confirm",
                stage_id="s-req",
                order_index=1,
                status="EXECUTED",
            )
            session.add(ps)
            await session.commit()

        response = client.post(
            "/api/v1/templates/projects/proj-confirm/template-deviation",
            json={"new_template_id": "Deep", "reason": "测试偏离", "risk_acknowledged": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert "frozen" in data
        assert "removed" in data
        assert "added" in data
