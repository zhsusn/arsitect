"""Direct unit tests for templates router (no TestClient)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

from app.api.v1.templates import (
    confirm_template_deviation,
    get_stage_sequence,
    get_template,
    list_templates,
    preview_template_deviation,
)
from app.infrastructure.database.session import AsyncSessionLocal
from app.models.project_stage import ProjectStage
from app.models.template import Template
from app.models.template_stage import TemplateStage
from app.schemas.template import (
    TemplateDeviationConfirmDTO,
    TemplateDeviationPreviewRequestDTO,
)


class TestTemplatesRouterDirect:
    """Direct async tests for templates router endpoints."""

    @pytest.fixture
    async def seeded(self):
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
            yield session
            # cleanup
            await session.execute(text("DELETE FROM project_stages"))
            await session.execute(text("DELETE FROM template_stages"))
            await session.execute(text("DELETE FROM templates"))
            await session.commit()

    @pytest.mark.asyncio
    async def test_list_templates(self, seeded) -> None:
        result = await list_templates(db=seeded)
        assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_get_template(self, seeded) -> None:
        result = await get_template("Light", db=seeded)
        assert result.template.template_id == "Light"
        assert len(result.stages) == 2

    @pytest.mark.asyncio
    async def test_get_stage_sequence(self, seeded) -> None:
        ps = ProjectStage(
            project_stage_id=str(uuid.uuid4()),
            project_id="proj-seq",
            stage_id="s-req",
            order_index=1,
            status="DEFINED",
        )
        seeded.add(ps)
        await seeded.commit()

        result = await get_stage_sequence("proj-seq", db=seeded)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_preview_deviation(self, seeded) -> None:
        tpl = Template(
            template_id="Standard",
            template_name="标准",
            description="标准模板",
            stage_count=1,
            estimated_skill_count=3,
            applicable_complexity="medium",
        )
        seeded.add(tpl)
        await seeded.flush()

        stage = TemplateStage(
            stage_id="s-design",
            stage_name="设计",
            order_index=1,
            template_id="Standard",
        )
        seeded.add(stage)

        ps = ProjectStage(
            project_stage_id=str(uuid.uuid4()),
            project_id="proj-dev",
            stage_id="s-req",
            order_index=1,
            status="EXECUTED",
        )
        seeded.add(ps)
        await seeded.commit()

        result = await preview_template_deviation(
            "proj-dev",
            TemplateDeviationPreviewRequestDTO(new_template_id="Standard"),
            db=seeded,
        )
        assert result.frozen_count == 1
        assert result.added_count == 1

    @pytest.mark.asyncio
    async def test_confirm_deviation(self, seeded) -> None:
        tpl = Template(
            template_id="Deep",
            template_name="深度",
            description="深度模板",
            stage_count=1,
            estimated_skill_count=5,
            applicable_complexity="high",
        )
        seeded.add(tpl)
        await seeded.flush()

        stage = TemplateStage(
            stage_id="s-test",
            stage_name="测试",
            order_index=1,
            template_id="Deep",
            primary_skill_id="skill-test",
        )
        seeded.add(stage)

        ps = ProjectStage(
            project_stage_id=str(uuid.uuid4()),
            project_id="proj-confirm",
            stage_id="s-req",
            order_index=1,
            status="EXECUTED",
        )
        seeded.add(ps)
        await seeded.commit()

        result = await confirm_template_deviation(
            "proj-confirm",
            TemplateDeviationConfirmDTO(
                new_template_id="Deep", reason="测试偏离", risk_acknowledged=True
            ),
            db=seeded,
        )
        assert "frozen" in result
        assert "removed" in result
        assert "added" in result
