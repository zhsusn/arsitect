"""Stage-level execution status aggregation service."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.repositories.skill_execution_repo import (
    SkillExecutionRepository,
)
from app.models.project_stage import ProjectStage
from app.models.skill_execution import SkillExecution
from app.schemas.stage_execution_status import (
    LatestExecutionDTO,
    StageExecutionStatusDTO,
)
from app.services.status_aggregator import StatusAggregator


class StageExecutionStatusService:
    """Aggregate real-time execution status for a project stage."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session

    async def get_status(self, stage_id: str) -> StageExecutionStatusDTO | None:
        """Return aggregated execution status for a stage.

        Args:
            stage_id: Project stage ID.

        Returns:
            Status DTO or None if the stage does not exist.
        """
        stage = await self._session.get(ProjectStage, stage_id)
        if stage is None:
            return None

        stmt = (
            select(SkillExecution)
            .where(SkillExecution.stage_id == stage_id)
            .order_by(SkillExecution.created_at.desc())
        )
        result = await self._session.execute(stmt)
        executions = list(result.scalars().all())

        if not executions:
            return StageExecutionStatusDTO(
                stage_id=stage_id,
                runtime_status=stage.runtime_status,
                current_phase="NONE",
                overall_status="NOT_STARTED",
                progress_percent=0,
            )

        latest = executions[0]
        running = [
            e.execution_id
            for e in executions
            if e.overall_status in ("RUNNING", "NOT_STARTED")
        ]

        aggregator = StatusAggregator(SkillExecutionRepository(self._session))
        aggregated = await aggregator.poll_execution_status(latest.execution_id)

        return StageExecutionStatusDTO(
            stage_id=stage_id,
            runtime_status=stage.runtime_status,
            current_phase=aggregated.current_phase,
            overall_status=aggregated.overall_status,
            progress_percent=aggregated.stage_progress_percent,
            error_summary=aggregated.error_summary,
            artifact_paths=aggregated.artifact_paths,
            running_execution_ids=running,
            latest_execution=LatestExecutionDTO(
                execution_id=latest.execution_id,
                skill_name=latest.skill_name,
                overall_status=latest.overall_status,
                current_phase=latest.current_phase,
            ),
        )
