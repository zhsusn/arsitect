"""Tests for ReworkEvent model."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models.application import Application
from app.models.project import Project
from app.models.rework_event import ReworkEvent


class TestReworkEvent:
    """ReworkEvent ORM tests."""

    async def _seed_project(self, session, suffix: str = "1") -> Project:
        app = Application(
            application_id=f"app-rework-{suffix}",
            application_name=f"ReworkApp{suffix}",
            local_path=f"/tmp/rework{suffix}",
        )
        session.add(app)
        await session.flush()
        proj = Project(
            project_id=f"proj-rework-{suffix}",
            project_name=f"ReworkProj{suffix}",
            application_id=app.application_id,
            template_level="Standard",
        )
        session.add(proj)
        await session.flush()
        return proj

    @pytest.mark.asyncio
    async def test_create_rework_event(self, db_session) -> None:
        """Should persist rework event."""
        proj = await self._seed_project(db_session)
        event = ReworkEvent(
            event_id="evt-001",
            project_id=proj.project_id,
            stage_id="stage-001",
            event_type="DESIGN_CHANGE",
            reason="Requirement updated",
        )
        db_session.add(event)
        await db_session.flush()

        result = await db_session.execute(
            select(ReworkEvent).where(ReworkEvent.event_id == "evt-001")
        )
        found = result.scalar_one()
        assert found.event_type == "DESIGN_CHANGE"
        assert found.reason == "Requirement updated"
        assert found.created_at is not None
