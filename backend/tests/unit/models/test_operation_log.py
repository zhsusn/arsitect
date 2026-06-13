"""Tests for OperationLog model."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models.application import Application
from app.models.operation_log import OperationLog
from app.models.project import Project


class TestOperationLog:
    """OperationLog ORM tests."""

    @pytest.mark.asyncio
    async def test_create_operation_log(self, db_session) -> None:
        """Should persist operation log with all fields."""
        app = Application(application_id="app-log-1", application_name="LogApp", local_path="/tmp/log")
        db_session.add(app)
        await db_session.flush()
        proj = Project(
            project_id="proj-log-1",
            project_name="LogProj",
            application_id=app.application_id,
            template_level="Standard",
        )
        db_session.add(proj)
        await db_session.flush()

        log = OperationLog(
            log_id="log-001",
            project_id=proj.project_id,
            operator_id="user-001",
            action="CREATE_PROJECT",
            target_type="Project",
            target_id=proj.project_id,
            detail="Created by test",
        )
        db_session.add(log)
        await db_session.flush()

        result = await db_session.execute(
            select(OperationLog).where(OperationLog.log_id == "log-001")
        )
        found = result.scalar_one()
        assert found.action == "CREATE_PROJECT"
        assert found.target_type == "Project"
        assert found.detail == "Created by test"
        assert found.created_at is not None
