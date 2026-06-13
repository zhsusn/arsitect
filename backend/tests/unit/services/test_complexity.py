"""Tests for ComplexityService."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.core.exceptions import NotFoundError, ValidationError
from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.project import Project
from app.services.complexity_service import ComplexityService


class TestCalculateScores:
    """Unit tests for the static scoring algorithm."""

    def test_trivial_project(self) -> None:
        result = ComplexityService.calculate_scores(
            module_count=1,
            interface_count=0,
            page_count=0,
            tech_complexity="Low",
            risk_level="Low",
        )
        assert result["complexity_level"] == "Trivial"
        assert result["optimistic_score"] <= result["expected_score"]
        assert result["expected_score"] <= result["conservative_score"]

    def test_deep_project(self) -> None:
        result = ComplexityService.calculate_scores(
            module_count=50,
            interface_count=100,
            page_count=50,
            tech_complexity="High",
            risk_level="High",
        )
        assert result["complexity_level"] == "Deep"

    def test_light_project(self) -> None:
        result = ComplexityService.calculate_scores(
            module_count=5,
            interface_count=8,
            page_count=8,
            tech_complexity="Medium",
            risk_level="Medium",
        )
        assert result["complexity_level"] == "Light"

    def test_standard_project(self) -> None:
        result = ComplexityService.calculate_scores(
            module_count=10,
            interface_count=12,
            page_count=15,
            tech_complexity="Medium",
            risk_level="Medium",
        )
        assert result["complexity_level"] == "Standard"


class TestCreateSizeEstimate:
    """Tests for create_size_estimate."""

    @pytest.fixture
    async def seeded_proj(self) -> Project:
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM size_estimates"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app = Application(application_id="app-cx-1", application_name="Test App CX1", local_path="/tmp")
            session.add(app)
            proj = Project(
                project_id="proj-cx-1",
                project_name="Test",
                application_id="app-cx-1",
                template_level="Standard",
                project_status="Draft",
            )
            session.add(proj)
            await session.commit()
            return proj

    @pytest.mark.asyncio
    async def test_success(self, seeded_proj: Project) -> None:
        async with AsyncSessionLocal() as session:
            svc = ComplexityService(session)
            est = await svc.create_size_estimate(
                project_id=seeded_proj.project_id,
                module_count=5,
                interface_count=10,
                page_count=3,
                tech_complexity="Medium",
                risk_level="Low",
            )
            assert est.project_id == seeded_proj.project_id
            assert est.complexity_level in ("Trivial", "Light", "Standard", "Deep")
            assert est.optimistic_score is not None

    @pytest.mark.asyncio
    async def test_project_not_found(self) -> None:
        async with AsyncSessionLocal() as session:
            svc = ComplexityService(session)
            with pytest.raises(NotFoundError):
                await svc.create_size_estimate(
                    project_id="no-such",
                    module_count=1,
                    interface_count=0,
                    page_count=0,
                    tech_complexity="Low",
                    risk_level="Low",
                )


class TestListSizeEstimates:
    """Tests for list_size_estimates."""

    @pytest.fixture
    async def seeded_proj2(self) -> Project:
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM size_estimates"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app = Application(application_id="app-cx-2", application_name="Test App CX2", local_path="/tmp")
            session.add(app)
            proj = Project(
                project_id="proj-cx-2",
                project_name="Test",
                application_id="app-cx-2",
                template_level="Standard",
                project_status="Draft",
            )
            session.add(proj)
            await session.commit()
            return proj

    @pytest.mark.asyncio
    async def test_returns_estimates(self, seeded_proj2: Project) -> None:
        async with AsyncSessionLocal() as session:
            svc = ComplexityService(session)
            await svc.create_size_estimate(
                project_id=seeded_proj2.project_id,
                module_count=3,
                interface_count=0,
                page_count=0,
                tech_complexity="Low",
                risk_level="Low",
            )
        async with AsyncSessionLocal() as session:
            svc = ComplexityService(session)
            items = await svc.list_size_estimates(seeded_proj2.project_id)
            assert len(items) == 1


class TestTemplateRecommendation:
    """Tests for get_template_recommendation."""

    def test_valid_levels(self) -> None:
        for level in ("Trivial", "Light", "Standard", "Deep"):
            rec = ComplexityService.get_template_recommendation(level)
            assert rec["level"] == level
            assert rec["stage_count"] > 0

    def test_invalid_level(self) -> None:
        with pytest.raises(ValidationError):
            ComplexityService.get_template_recommendation("Unknown")
