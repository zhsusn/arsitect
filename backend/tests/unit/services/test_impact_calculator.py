"""Tests for ImpactScopeCalculator."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.project_stage import ProjectStage
from app.models.template import Template
from app.models.template_stage import TemplateStage
from app.services.impact_scope_calculator import ImpactScopeCalculator


class TestImpactScopeCalculator:
    """Test template switch impact calculation."""

    @pytest.fixture
    async def seeded_data(self) -> str:
        """Insert templates, stages and project stages."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM project_stages"))
            await session.execute(text("DELETE FROM template_stages"))
            await session.execute(text("DELETE FROM templates"))
            await session.commit()

            tpl_old = Template(
                template_id="Light",
                template_name="旧模板",
                description="旧",
                stage_count=3,
                estimated_skill_count=5,
                applicable_complexity="low",
            )
            tpl_new = Template(
                template_id="Standard",
                template_name="新模板",
                description="新",
                stage_count=2,
                estimated_skill_count=4,
                applicable_complexity="low",
            )
            session.add_all([tpl_old, tpl_new])
            await session.flush()

            # Shared stage
            shared = TemplateStage(
                stage_id="shared-1",
                stage_name="共享阶段",
                order_index=1,
                template_id="Light",
                is_present_in="Light",
            )
            # Old-only stage
            old_only = TemplateStage(
                stage_id="old-only",
                stage_name="旧独有",
                order_index=2,
                template_id="Light",
                is_present_in="Light",
            )
            # New-only stage
            new_only = TemplateStage(
                stage_id="new-only",
                stage_name="新独有",
                order_index=1,
                template_id="Standard",
                is_present_in="Standard",
            )
            session.add_all([shared, old_only, new_only])
            await session.flush()

            project_id = "proj-impact"
            # Executed shared stage -> frozen
            ps_executed = ProjectStage(
                project_stage_id=str(uuid.uuid4()),
                project_id=project_id,
                stage_id="shared-1",
                order_index=1,
                status="EXECUTED",
            )
            # Defined old-only stage -> removed
            ps_defined = ProjectStage(
                project_stage_id=str(uuid.uuid4()),
                project_id=project_id,
                stage_id="old-only",
                order_index=2,
                status="DEFINED",
            )
            session.add_all([ps_executed, ps_defined])
            await session.commit()
            return project_id

    @pytest.mark.asyncio
    async def test_calculate_impact(self, seeded_data: str) -> None:
        """Impact calculation identifies frozen, removed and added stages."""
        async with AsyncSessionLocal() as session:
            calc = ImpactScopeCalculator(session)
            impact = await calc.calculate_impact(seeded_data, "Standard")

            assert impact["frozen_count"] == 1
            assert impact["removed_count"] == 1
            assert impact["added_count"] == 1
            assert impact["retained_count"] == 0

            frozen_ids = {s.stage_id for s in impact["frozen_stages"]}
            removed_ids = {s.stage_id for s in impact["removed_stages"]}
            added_ids = {s.stage_id for s in impact["added_stages"]}

            assert "shared-1" in frozen_ids
            assert "old-only" in removed_ids
            assert "new-only" in added_ids
