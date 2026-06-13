"""Tests for TemplateRepository and StageConfigService."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.template import Template
from app.models.template_stage import TemplateStage
from app.services.stage_config_service import StageConfigService


class TestTemplateRepository:
    """Test template queries."""

    @pytest.fixture
    async def seeded_templates(self) -> list[Template]:
        """Insert sample templates and stages."""
        async with AsyncSessionLocal() as session:
            # Clean up any previously committed data in shared memory db
            await session.execute(text("DELETE FROM template_stages"))
            await session.execute(text("DELETE FROM templates"))
            await session.commit()

            tpls = [
                Template(
                    template_id="Light",
                    template_name="轻量",
                    description="轻量模板",
                    stage_count=2,
                    estimated_skill_count=5,
                    applicable_complexity="low",
                ),
                Template(
                    template_id="Standard",
                    template_name="标准",
                    description="标准模板",
                    stage_count=3,
                    estimated_skill_count=10,
                    applicable_complexity="medium",
                ),
            ]
            session.add_all(tpls)
            await session.flush()

            stages = [
                TemplateStage(
                    stage_id="s1",
                    stage_name="需求",
                    order_index=1,
                    template_id="Light",
                ),
                TemplateStage(
                    stage_id="s2",
                    stage_name="编码",
                    order_index=2,
                    template_id="Light",
                ),
                TemplateStage(
                    stage_id="s3",
                    stage_name="设计",
                    order_index=1,
                    template_id="Standard",
                ),
            ]
            session.add_all(stages)
            await session.commit()
            return tpls

    @pytest.mark.asyncio
    async def test_list_templates(self, seeded_templates: list[Template]) -> None:
        """Can list all templates."""
        async with AsyncSessionLocal() as session:
            svc = StageConfigService(session)
            tpls = await svc.list_templates()
            assert len(tpls) >= 2
            ids = {t.template_id for t in tpls}
            assert "Light" in ids
            assert "Standard" in ids

    @pytest.mark.asyncio
    async def test_get_template_detail(self, seeded_templates: list[Template]) -> None:
        """Can get template with stages."""
        async with AsyncSessionLocal() as session:
            svc = StageConfigService(session)
            detail = await svc.get_template_detail("Light")
            assert detail["template"].template_id == "Light"
            assert len(detail["stages"]) == 2
            assert detail["stages"][0].order_index == 1
            assert detail["stages"][1].order_index == 2

    @pytest.mark.asyncio
    async def test_get_stage_sequence(self, seeded_templates: list[Template]) -> None:
        """Can get ordered stage sequence."""
        async with AsyncSessionLocal() as session:
            svc = StageConfigService(session)
            stages = await svc.get_stage_sequence("Standard")
            assert len(stages) == 1
            assert stages[0].stage_name == "设计"

    @pytest.mark.asyncio
    async def test_get_template_not_found(self) -> None:
        """Unknown template raises NotFoundError."""
        async with AsyncSessionLocal() as session:
            svc = StageConfigService(session)
            with pytest.raises(Exception, match="not found"):
                await svc.get_template_detail("Nonexistent")
