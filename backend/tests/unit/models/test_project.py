"""Tests for Project and SizeEstimate models."""

from __future__ import annotations

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.project import Project
from app.models.size_estimate import SizeEstimate


class TestProjectModel:
    """Project model tests."""

    @pytest.mark.asyncio
    async def test_create_project(self) -> None:
        """Can create a valid project."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM size_estimates"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app = Application(
                application_id="app-001",
                application_name="Test App",
                local_path="/tmp/test",
            )
            session.add(app)
            await session.flush()

            proj = Project(
                project_id="proj-001",
                project_name="Test Project",
                project_description="A test project",
                project_status="Draft",
                application_id="app-001",
                template_level="Standard",
                progress_percent=10,
                risk_level="Low",
            )
            session.add(proj)
            await session.commit()

            result = await session.execute(
                select(Project).where(Project.project_id == "proj-001")
            )
            fetched = result.scalar_one()
            assert fetched.project_name == "Test Project"
            assert fetched.project_status == "Draft"
            assert fetched.progress_percent == 10

    @pytest.mark.asyncio
    async def test_status_enum_constraint(self) -> None:
        """Invalid project_status is rejected."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM size_estimates"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app = Application(
                application_id="app-002",
                application_name="Test App 2",
                local_path="/tmp/test2",
            )
            session.add(app)
            await session.flush()

            proj = Project(
                project_id="proj-002",
                project_name="Bad Status",
                application_id="app-002",
                template_level="Light",
                project_status="Invalid",
            )
            session.add(proj)
            with pytest.raises(IntegrityError):
                await session.commit()
            await session.rollback()

    @pytest.mark.asyncio
    async def test_template_level_constraint(self) -> None:
        """Invalid template_level is rejected."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM size_estimates"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app = Application(
                application_id="app-003",
                application_name="Test App 3",
                local_path="/tmp/test3",
            )
            session.add(app)
            await session.flush()

            proj = Project(
                project_id="proj-003",
                project_name="Bad Level",
                application_id="app-003",
                template_level="Custom",
            )
            session.add(proj)
            with pytest.raises(IntegrityError):
                await session.commit()
            await session.rollback()

    @pytest.mark.asyncio
    async def test_progress_range_constraint(self) -> None:
        """Progress outside 0-100 is rejected."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM size_estimates"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app = Application(
                application_id="app-004",
                application_name="Test App 4",
                local_path="/tmp/test4",
            )
            session.add(app)
            await session.flush()

            proj = Project(
                project_id="proj-004",
                project_name="Bad Progress",
                application_id="app-004",
                template_level="Trivial",
                progress_percent=150,
            )
            session.add(proj)
            with pytest.raises(IntegrityError):
                await session.commit()
            await session.rollback()


class TestSizeEstimateModel:
    """SizeEstimate model tests."""

    @pytest.mark.asyncio
    async def test_create_estimate(self) -> None:
        """Can create a valid size estimate."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM size_estimates"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app = Application(
                application_id="app-est",
                application_name="Est App",
                local_path="/tmp/est",
            )
            session.add(app)
            await session.flush()

            proj = Project(
                project_id="proj-est",
                project_name="Est Project",
                application_id="app-est",
                template_level="Standard",
            )
            session.add(proj)
            await session.flush()

            est = SizeEstimate(
                estimate_id="est-001",
                project_id="proj-est",
                module_count=5,
                interface_count=10,
                page_count=3,
                tech_complexity="Medium",
                risk_level="Low",
                optimistic_score=20,
                expected_score=35,
                conservative_score=50,
                complexity_level="Light",
            )
            session.add(est)
            await session.commit()

            result = await session.execute(
                select(SizeEstimate).where(SizeEstimate.estimate_id == "est-001")
            )
            fetched = result.scalar_one()
            assert fetched.module_count == 5
            assert fetched.complexity_level == "Light"

    @pytest.mark.asyncio
    async def test_module_count_range(self) -> None:
        """Module count outside 1-50 is rejected."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM size_estimates"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app = Application(
                application_id="app-est2",
                application_name="Est App 2",
                local_path="/tmp/est2",
            )
            session.add(app)
            await session.flush()

            proj = Project(
                project_id="proj-est2",
                project_name="Est Project 2",
                application_id="app-est2",
                template_level="Standard",
            )
            session.add(proj)
            await session.flush()

            est = SizeEstimate(
                estimate_id="est-002",
                project_id="proj-est2",
                module_count=0,
                tech_complexity="Low",
                risk_level="Low",
            )
            session.add(est)
            with pytest.raises(IntegrityError):
                await session.commit()
            await session.rollback()

    @pytest.mark.asyncio
    async def test_tech_complexity_constraint(self) -> None:
        """Invalid tech_complexity is rejected."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM size_estimates"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app = Application(
                application_id="app-est3",
                application_name="Est App 3",
                local_path="/tmp/est3",
            )
            session.add(app)
            await session.flush()

            proj = Project(
                project_id="proj-est3",
                project_name="Est Project 3",
                application_id="app-est3",
                template_level="Standard",
            )
            session.add(proj)
            await session.flush()

            est = SizeEstimate(
                estimate_id="est-003",
                project_id="proj-est3",
                module_count=1,
                tech_complexity="VeryHigh",
                risk_level="Low",
            )
            session.add(est)
            with pytest.raises(IntegrityError):
                await session.commit()
            await session.rollback()
