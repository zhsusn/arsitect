"""Tests for StatusAggregator."""

from __future__ import annotations

from datetime import datetime

import pytest

from app.infrastructure.database.repositories.skill_execution_repo import (
    SkillExecutionRepository,
)
from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.execution_log import ExecutionLog
from app.models.project import Project
from app.models.skill_execution import SkillExecution
from app.services.artifact_service import ArtifactService
from app.services.status_aggregator import StatusAggregator


class TestStatusAggregator:
    """StatusAggregator tests."""

    @pytest.fixture
    async def seeded_execution(self) -> SkillExecution:
        """Seed project and a failed skill execution."""
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text

            await session.execute(text("DELETE FROM execution_logs"))
            await session.execute(text("DELETE FROM artifact_files"))
            await session.execute(text("DELETE FROM skill_executions"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app = Application(
                application_id="app-sa",
                application_name="SA App",
                local_path="/tmp/sa",
            )
            session.add(app)
            await session.flush()

            proj = Project(
                project_id="proj-sa",
                project_name="SA Project",
                application_id=app.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.flush()

            execution = SkillExecution(
                execution_id="exec-sa-1",
                project_id=proj.project_id,
                stage_id="stage-sa",
                skill_id="skill-sa",
                skill_name="test-skill",
                trigger_action="SINGLE_EXECUTE",
                current_phase="EXEC",
                phase_status="FAILED",
                overall_status="FAILED",
                created_at=datetime.utcnow(),
            )
            session.add(execution)
            await session.commit()
            return execution

    @pytest.mark.asyncio
    async def test_poll_execution_status_includes_artifact_paths(
        self, seeded_execution: SkillExecution
    ) -> None:
        """artifact_paths should include files linked to the execution."""
        async with AsyncSessionLocal() as session:
            svc = ArtifactService(session)
            art = await svc.create_artifact(
                project_id=seeded_execution.project_id,
                execution_id=seeded_execution.execution_id,
                file_name="output.md",
                file_path="/tmp/output.md",
                file_type="md",
                content="output",
            )

            aggregator = StatusAggregator(SkillExecutionRepository(session))
            status = await aggregator.poll_execution_status(seeded_execution.execution_id)

            assert status.execution_id == seeded_execution.execution_id
            assert status.overall_status == "FAILED"
            assert art.file_path in status.artifact_paths

    @pytest.mark.asyncio
    async def test_poll_execution_status_includes_error_summary(
        self, seeded_execution: SkillExecution
    ) -> None:
        """error_summary should surface the latest ERROR log."""
        async with AsyncSessionLocal() as session:
            log = ExecutionLog(
                log_id="log-sa-1",
                execution_id=seeded_execution.execution_id,
                log_anchor="anchor-1",
                level="ERROR",
                content="Something went wrong",
            )
            session.add(log)
            await session.commit()

            aggregator = StatusAggregator(SkillExecutionRepository(session))
            status = await aggregator.poll_execution_status(seeded_execution.execution_id)

            assert status.error_summary == "Something went wrong"

    @pytest.mark.asyncio
    async def test_poll_execution_status_not_found(self) -> None:
        """Querying a non-existent execution raises NotFoundError."""
        async with AsyncSessionLocal() as session:
            aggregator = StatusAggregator(SkillExecutionRepository(session))
            with pytest.raises(Exception):  # noqa: B017
                await aggregator.poll_execution_status("missing-id")
