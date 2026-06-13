"""Tests for ArchValidationService."""

from __future__ import annotations

import pytest

from app.models.application import Application
from app.models.c4_baseline import C4Baseline
from app.models.project import Project
from app.services.arch_validation_service import ArchValidationService


class TestArchValidationService:
    """ArchValidationService unit tests."""

    async def _seed_project(self, session, suffix: str = "1") -> Project:
        app = Application(
            application_id=f"app-av-{suffix}",
            application_name=f"AvApp{suffix}",
            local_path=f"/tmp/av{suffix}",
        )
        session.add(app)
        await session.flush()
        proj = Project(
            project_id=f"proj-av-{suffix}",
            project_name=f"AvProj{suffix}",
            application_id=app.application_id,
            template_level="Standard",
        )
        session.add(proj)
        await session.flush()
        return proj

    @pytest.mark.asyncio
    async def test_trigger_validation_no_dsl(self, db_session) -> None:
        """Validation with no DSL should report no drift."""
        proj = await self._seed_project(db_session)
        svc = ArchValidationService(db_session)
        session = await svc.trigger_validation(proj.project_id, "ALL")
        assert session.status == "NO_DRIFT"
        assert session.diff_summary is None

    @pytest.mark.asyncio
    async def test_trigger_validation_with_dsl(self, db_session) -> None:
        """Validation with changed DSL should detect drift."""
        proj = await self._seed_project(db_session, suffix="dsl")
        baseline = C4Baseline(
            baseline_id="c4-av-dsl",
            project_id=proj.project_id,
            version="1.0.0",
            dsl_content="graph TD\n  A --> B",
            dsl_hash="hash1",
            level="L1-L4",
            is_current=True,
        )
        db_session.add(baseline)
        await db_session.flush()

        # First trigger establishes baseline
        svc = ArchValidationService(db_session)
        first = await svc.trigger_validation(proj.project_id, "ALL")
        assert first.status == "NO_DRIFT"

        # Change DSL
        baseline.dsl_content = "graph TD\n  A --> B\n  A --> C"
        baseline.dsl_hash = "hash2"
        await db_session.flush()

        # Second trigger detects drift
        second = await svc.trigger_validation(proj.project_id, "ALL")
        assert second.status == "DRIFT_DETECTED"
        assert second.diff_summary is not None

    @pytest.mark.asyncio
    async def test_update_baseline(self, db_session) -> None:
        """Baseline update should store current DSL."""
        proj = await self._seed_project(db_session, suffix="base")
        baseline = C4Baseline(
            baseline_id="c4-av-base",
            project_id=proj.project_id,
            version="1.0.0",
            dsl_content="graph TD\n  X --> Y",
            dsl_hash="hash1",
            level="L1-L4",
            is_current=True,
        )
        db_session.add(baseline)
        await db_session.flush()

        svc = ArchValidationService(db_session)
        session = await svc.update_baseline(proj.project_id, "ALL")
        assert session.status == "BASELINE_UPDATED"
        assert session.baseline_dsl == "graph TD\n  X --> Y"

    @pytest.mark.asyncio
    async def test_get_diffs(self, db_session) -> None:
        """Should return list of validation sessions."""
        proj = await self._seed_project(db_session, suffix="diffs")
        svc = ArchValidationService(db_session)
        await svc.trigger_validation(proj.project_id, "ALL")
        diffs = await svc.get_diffs(proj.project_id)
        assert len(diffs) == 1
