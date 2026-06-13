"""Tests for Template, TemplateStage and ProjectStage models."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.project_stage import ProjectStage
from app.models.template import Template
from app.models.template_stage import TemplateStage


class TestTemplateModel:
    """Test Template ORM model."""

    @pytest.mark.asyncio
    async def test_create_template(self) -> None:
        """Can create a valid template."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM template_stages"))
            await session.execute(text("DELETE FROM templates"))
            await session.commit()

            tpl = Template(
                template_id="Standard",
                template_name="标准模板",
                description="适用于大多数项目",
                stage_count=12,
                estimated_skill_count=30,
                applicable_complexity="medium",
            )
            session.add(tpl)
            await session.commit()

            fetched = await session.get(Template, "Standard")
            assert fetched is not None
            assert fetched.template_name == "标准模板"

    @pytest.mark.asyncio
    async def test_template_id_enum_constraint(self) -> None:
        """Invalid template_id raises IntegrityError."""
        async with AsyncSessionLocal() as session:
            tpl = Template(
                template_id="Invalid",
                template_name="无效模板",
                description="x",
                stage_count=1,
                estimated_skill_count=1,
                applicable_complexity="low",
            )
            session.add(tpl)
            with pytest.raises(IntegrityError):
                await session.commit()


class TestTemplateStageModel:
    """Test TemplateStage ORM model."""

    @pytest.mark.asyncio
    async def test_create_stage(self) -> None:
        """Can create a stage linked to a template."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM template_stages"))
            await session.execute(text("DELETE FROM templates"))
            await session.commit()

            tpl = Template(
                template_id="Light",
                template_name="轻量模板",
                description="小型项目",
                stage_count=6,
                estimated_skill_count=12,
                applicable_complexity="low",
            )
            session.add(tpl)
            await session.flush()

            stage = TemplateStage(
                stage_id=str(uuid.uuid4()),
                stage_name="需求分析",
                order_index=1,
                template_id="Light",
                skippable=False,
            )
            session.add(stage)
            await session.commit()

            result = await session.execute(
                select(TemplateStage).where(TemplateStage.template_id == "Light")
            )
            assert result.scalar_one() is not None


class TestProjectStageModel:
    """Test ProjectStage ORM model."""

    @pytest.mark.asyncio
    async def test_create_project_stage(self) -> None:
        """Can create a project stage."""
        async with AsyncSessionLocal() as session:
            ps = ProjectStage(
                project_stage_id=str(uuid.uuid4()),
                project_id="proj-001",
                stage_id="stage-001",
                order_index=1,
                status="DEFINED",
            )
            session.add(ps)
            await session.commit()

            fetched = await session.get(ProjectStage, ps.project_stage_id)
            assert fetched is not None
            assert fetched.status == "DEFINED"

    @pytest.mark.asyncio
    async def test_status_enum_constraint(self) -> None:
        """Invalid status raises IntegrityError."""
        async with AsyncSessionLocal() as session:
            ps = ProjectStage(
                project_stage_id=str(uuid.uuid4()),
                project_id="proj-002",
                stage_id="stage-002",
                order_index=1,
                status="INVALID_STATUS",
            )
            session.add(ps)
            with pytest.raises(IntegrityError):
                await session.commit()
