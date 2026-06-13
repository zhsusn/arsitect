"""Tests for ArchValidationSession model."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models.application import Application
from app.models.arch_validation_session import ArchValidationSession
from app.models.project import Project


class TestArchValidationSession:
    """ArchValidationSession ORM tests."""

    async def _seed_project(self, session, suffix: str = "1") -> Project:
        app = Application(
            application_id=f"app-arch-{suffix}",
            application_name=f"ArchApp{suffix}",
            local_path=f"/tmp/arch{suffix}",
        )
        session.add(app)
        await session.flush()
        proj = Project(
            project_id=f"proj-arch-{suffix}",
            project_name=f"ArchProj{suffix}",
            application_id=app.application_id,
            template_level="Standard",
        )
        session.add(proj)
        await session.flush()
        return proj

    @pytest.mark.asyncio
    async def test_create_session(self, db_session) -> None:
        """Should persist arch validation session."""
        proj = await self._seed_project(db_session)
        sess = ArchValidationSession(
            session_id="sess-001",
            project_id=proj.project_id,
            level="L1",
            baseline_dsl="graph TD\n  A --> B",
            current_dsl="graph TD\n  A --> B\n  A --> C",
            status="COMPLETED",
        )
        db_session.add(sess)
        await db_session.flush()

        result = await db_session.execute(
            select(ArchValidationSession).where(ArchValidationSession.session_id == "sess-001")
        )
        found = result.scalar_one()
        assert found.level == "L1"
        assert found.status == "COMPLETED"
        assert found.created_at is not None
