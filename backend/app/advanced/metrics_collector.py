"""MetricsCollector — skill execution metrics aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.skill_execution import SkillExecution


@dataclass
class SkillMetrics:
    """Aggregated metrics for a skill in a project."""

    skill_id: str
    project_id: str
    execution_count: int
    total_duration_ms: int
    avg_duration_ms: float
    success_count: int
    fail_count: int
    retry_count: int
    avg_gate_wait_ms: int


class MetricsCollector:
    """Metrics collector.

    Responsibilities:
    1. Aggregate skill execution metrics.
    2. Compute gate wait times.
    3. Provide data for HistoryViewer and monitoring dashboards.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session."""
        self._session = session

    async def get_skill_metrics(
        self, skill_id: str, project_id: str
    ) -> SkillMetrics | None:
        """Return aggregated metrics for a skill in a project."""
        result = await self._session.execute(
            select(
                func.count().label("execution_count"),
                func.sum(SkillExecution.retry_count).label("retry_count"),
            )
            .where(SkillExecution.skill_id == skill_id)
            .where(SkillExecution.project_id == project_id)
        )
        row = result.mappings().one_or_none()
        if row is None or row["execution_count"] == 0:
            return None

        success_result = await self._session.execute(
            select(func.count())
            .where(SkillExecution.skill_id == skill_id)
            .where(SkillExecution.project_id == project_id)
            .where(SkillExecution.overall_status == "SUCCESS")
        )
        success_count = success_result.scalar() or 0

        fail_result = await self._session.execute(
            select(func.count())
            .where(SkillExecution.skill_id == skill_id)
            .where(SkillExecution.project_id == project_id)
            .where(SkillExecution.overall_status == "FAILED")
        )
        fail_count = fail_result.scalar() or 0

        records = list(
            (
                await self._session.execute(
                    select(SkillExecution)
                    .where(SkillExecution.skill_id == skill_id)
                    .where(SkillExecution.project_id == project_id)
                )
            )
            .scalars()
            .all()
        )
        total_duration = 0
        for r in records:
            if r.started_at and r.completed_at:
                total_duration += int(
                    (r.completed_at - r.started_at).total_seconds() * 1000
                )

        count = row["execution_count"] or 0
        return SkillMetrics(
            skill_id=skill_id,
            project_id=project_id,
            execution_count=count,
            total_duration_ms=total_duration,
            avg_duration_ms=(total_duration / count if count else 0),
            success_count=success_count,
            fail_count=fail_count,
            retry_count=row["retry_count"] or 0,
            avg_gate_wait_ms=await self._avg_gate_wait(project_id),
        )

    async def get_project_metrics(
        self, project_id: str
    ) -> dict[str, Any]:
        """Return aggregated metrics for a project."""
        result = await self._session.execute(
            select(
                func.count().label("execution_count"),
                func.sum(SkillExecution.retry_count).label("retry_count"),
            )
            .where(SkillExecution.project_id == project_id)
        )
        row = result.mappings().one_or_none()

        success_result = await self._session.execute(
            select(func.count())
            .where(SkillExecution.project_id == project_id)
            .where(SkillExecution.overall_status == "SUCCESS")
        )
        success_count = success_result.scalar() or 0

        fail_result = await self._session.execute(
            select(func.count())
            .where(SkillExecution.project_id == project_id)
            .where(SkillExecution.overall_status == "FAILED")
        )
        fail_count = fail_result.scalar() or 0

        count = row["execution_count"] if row else 0
        retry_count = row["retry_count"] if row else 0

        return {
            "project_id": project_id,
            "execution_count": count or 0,
            "success_count": success_count,
            "fail_count": fail_count,
            "retry_count": retry_count or 0,
            "success_rate": (
                success_count / count if count else 0
            ),
        }

    async def list_application_metrics(
        self, application_id: str
    ) -> list[dict[str, Any]]:
        """Return per-project metrics for an application."""
        result = await self._session.execute(
            select(Project.project_id)
            .where(Project.application_id == application_id)
        )
        project_ids = list(result.scalars().all())
        return [await self.get_project_metrics(pid) for pid in project_ids]

    async def _avg_gate_wait(self, project_id: str) -> int:
        """Compute average gate wait time in milliseconds (placeholder).

        TODO: GateDecision currently lacks an ``approved_at`` timestamp, so a
        real average cannot be calculated. Return 0 until the schema is
        extended.
        """
        # Avoid querying unsummable datetime columns; simply return the placeholder.
        return 0
