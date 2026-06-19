"""Tests for StageConfigService.

Covers DR-009 Template Engine detailed requirements.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.core.exceptions import NotFoundError
from app.infrastructure.database.session import AsyncSessionLocal
from app.models.template import Template
from app.models.template_stage import TemplateStage
from app.services.stage_config_service import StageConfigService


class TestStageConfigService:
    """StageConfigService unit tests."""

    @pytest.fixture
    async def seeded_template(self) -> Template:
        """Seed a template with stages."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM template_stages"))
            await session.execute(text("DELETE FROM templates"))
            await session.commit()

            tpl = Template(
                template_id="Standard",
                template_name="Standard SDLC",
                description="Full lifecycle template",
                stage_count=3,
                estimated_skill_count=12,
                applicable_complexity="Standard",
            )
            session.add(tpl)
            await session.flush()

            stages = [
                TemplateStage(
                    stage_id="stage-001",
                    template_id="Standard",
                    stage_name="Requirement Analysis",
                    order_index=1,
                    primary_skill_id="skill-req",
                ),
                TemplateStage(
                    stage_id="stage-002",
                    template_id="Standard",
                    stage_name="High Level Design",
                    order_index=2,
                    primary_skill_id="skill-hld",
                ),
                TemplateStage(
                    stage_id="stage-003",
                    template_id="Standard",
                    stage_name="Implementation",
                    order_index=3,
                    primary_skill_id="skill-impl",
                ),
            ]
            for s in stages:
                session.add(s)
            await session.commit()
            return tpl

    @pytest.mark.asyncio
    async def test_list_templates(self, seeded_template: Template) -> None:
        """TEST-0201: List all predefined templates.

        Covers AC-01: Template selection list.
        """
        async with AsyncSessionLocal() as session:
            svc = StageConfigService(session)
            templates = await svc.list_templates()
            assert len(templates) >= 1
            assert any(t.template_id == "Standard" for t in templates)

    @pytest.mark.asyncio
    async def test_get_template_detail_found(self, seeded_template: Template) -> None:
        """TEST-0202: Get template detail with ordered stage sequence.

        Covers AC-04: Stage definition display.
        """
        async with AsyncSessionLocal() as session:
            svc = StageConfigService(session)
            detail = await svc.get_template_detail("Standard")
            assert detail["template"].template_id == "Standard"
            assert len(detail["stages"]) == 3
            assert detail["stages"][0].stage_name == "Requirement Analysis"
            assert detail["stages"][1].order_index == 2

    @pytest.mark.asyncio
    async def test_get_template_detail_not_found(self) -> None:
        """TEST-0203: Get nonexistent template raises NotFoundError.

        Covers edge case: missing template.
        """
        async with AsyncSessionLocal() as session:
            svc = StageConfigService(session)
            with pytest.raises(NotFoundError):
                await svc.get_template_detail("NonExistent")

    @pytest.mark.asyncio
    async def test_get_stage_sequence_found(self, seeded_template: Template) -> None:
        """TEST-0204: Get ordered stage list for a template.

        Covers AC-04: Stage sequence retrieval.
        """
        async with AsyncSessionLocal() as session:
            svc = StageConfigService(session)
            stages = await svc.get_stage_sequence("Standard")
            assert len(stages) == 3
            assert stages[0].order_index < stages[1].order_index

    @pytest.mark.asyncio
    async def test_get_stage_sequence_not_found(self) -> None:
        """TEST-0205: Get stage sequence for nonexistent template raises NotFoundError.

        Covers edge case: missing template.
        """
        async with AsyncSessionLocal() as session:
            svc = StageConfigService(session)
            with pytest.raises(NotFoundError):
                await svc.get_stage_sequence("Missing")

    @pytest.mark.asyncio
    async def test_stage_ordering(self, seeded_template: Template) -> None:
        """TEST-0206: Stage sequence is ordered by order_index.

        Covers AC-04: Ordered stage list.
        """
        async with AsyncSessionLocal() as session:
            svc = StageConfigService(session)
            stages = await svc.get_stage_sequence("Standard")
            order_indices = [s.order_index for s in stages]
            assert order_indices == sorted(order_indices)

    @pytest.mark.asyncio
    async def test_update_execution_strategy(self, seeded_template: Template) -> None:
        """Template default execution strategy can be updated."""
        async with AsyncSessionLocal() as session:
            svc = StageConfigService(session)
            updated = await svc.update_execution_strategy("Standard", "full_auto")
            assert updated.default_execution_strategy == "full_auto"
            refreshed = await svc.get_template_detail("Standard")
            assert refreshed["template"].default_execution_strategy == "full_auto"

    @pytest.mark.asyncio
    async def test_update_execution_strategy_invalid(self) -> None:
        """Invalid execution strategy raises ValidationError."""
        from app.core.exceptions import ValidationError

        async with AsyncSessionLocal() as session:
            svc = StageConfigService(session)
            with pytest.raises(ValidationError):
                await svc.update_execution_strategy("Standard", "invalid")
