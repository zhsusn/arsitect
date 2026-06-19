"""HistoryViewer — completed project timeline and rework heatmap."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.skill_execution import SkillExecution


@dataclass
class ExecutionRecord:
    """Single skill execution record for history display."""

    skill_id: str
    skill_name: str
    phase: str
    status: str
    duration_ms: int
    started_at: datetime | None
    completed_at: datetime | None
    retry_count: int


@dataclass
class ProjectTimeline:
    """Aggregated timeline for a completed project."""

    project_id: str
    project_name: str
    stages: list[dict[str, Any]]
    total_duration_ms: int
    skill_records: list[ExecutionRecord]


class HistoryViewer:
    """History viewer.

    Responsibilities:
    1. Query execution history for completed/archived projects.
    2. Aggregate stage duration and success rate.
    3. Compute rework heatmap from retry counts.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session."""
        self._session = session

    async def get_project_timeline(self, project_id: str) -> ProjectTimeline | None:
        """Return project timeline with stage aggregates."""
        project = await self._session.get(Project, project_id)
        if project is None:
            return None

        result = await self._session.execute(
            select(SkillExecution)
            .where(SkillExecution.project_id == project_id)
            .order_by(SkillExecution.started_at)
        )
        records = [
            ExecutionRecord(
                skill_id=r.skill_id,
                skill_name=r.skill_name,
                phase=r.current_phase or "NONE",
                status=self._normalize_status(r.overall_status),
                duration_ms=self._duration_ms(r),
                started_at=r.started_at,
                completed_at=r.completed_at,
                retry_count=r.retry_count,
            )
            for r in result.scalars().all()
        ]

        stages = self._group_by_phase(records)
        total_duration = sum(r.duration_ms for r in records)

        return ProjectTimeline(
            project_id=project_id,
            project_name=project.project_name,
            stages=stages,
            total_duration_ms=total_duration,
            skill_records=records,
        )

    async def get_rework_heatmap(self, project_id: str) -> dict[str, dict[str, Any]]:
        """Return rework heatmap keyed by phase.skill_id."""
        timeline = await self.get_project_timeline(project_id)
        if timeline is None:
            return {}

        heatmap: dict[str, dict[str, Any]] = {}
        for record in timeline.skill_records:
            key = f"{record.phase}.{record.skill_id}"
            heatmap[key] = {
                "skill_id": record.skill_id,
                "skill_name": record.skill_name,
                "phase": record.phase,
                "retry_count": record.retry_count,
                "intensity": min(record.retry_count / 3, 1.0),
            }
        return heatmap

    async def list_completed_projects(self, limit: int = 20) -> list[dict[str, Any]]:
        """List archived/completed projects."""
        result = await self._session.execute(
            select(Project)
            .where(Project.project_status == "Archived")
            .order_by(Project.updated_at.desc())
            .limit(limit)
        )
        return [
            {
                "id": p.project_id,
                "name": p.project_name,
                "completed_at": (p.updated_at.isoformat() if p.updated_at else None),
            }
            for p in result.scalars().all()
        ]

    async def get_application_summary(self, application_id: str) -> dict[str, int]:
        """Return summary stats for an application."""
        total_result = await self._session.execute(
            select(func.count())
            .select_from(Project)
            .where(Project.application_id == application_id)
        )
        total_projects = total_result.scalar() or 0

        completed_result = await self._session.execute(
            select(func.count())
            .select_from(Project)
            .where(
                Project.application_id == application_id,
                Project.project_status == "Archived",
            )
        )
        completed_projects = completed_result.scalar() or 0

        from app.models.rework_event import ReworkEvent

        rework_result = await self._session.execute(
            select(func.count())
            .select_from(ReworkEvent)
            .join(Project, ReworkEvent.project_id == Project.project_id)
            .where(Project.application_id == application_id)
        )
        rework_count = rework_result.scalar() or 0

        return {
            "total_projects": total_projects,
            "completed_projects": completed_projects,
            "rework_count": rework_count,
        }

    @staticmethod
    def _group_by_phase(
        records: list[ExecutionRecord],
    ) -> list[dict[str, Any]]:
        """Group execution records by phase and aggregate."""
        phases: defaultdict[str, list[ExecutionRecord]] = defaultdict(list)
        for r in records:
            phases[r.phase].append(r)

        result = []
        for phase_name, phase_records in sorted(phases.items()):
            durations = [r.duration_ms for r in phase_records]
            total = sum(durations)
            result.append(
                {
                    "name": phase_name,
                    "skill_count": len(phase_records),
                    "total_duration_ms": total,
                    "avg_duration_ms": (total / len(durations) if durations else 0),
                    "success_rate": (
                        len([r for r in phase_records if r.status == "completed"])
                        / len(phase_records)
                        if phase_records
                        else 0
                    ),
                    "start": min(
                        (r.started_at for r in phase_records if r.started_at),
                        default=None,
                    ),
                    "end": max(
                        (r.completed_at for r in phase_records if r.completed_at),
                        default=None,
                    ),
                }
            )
        return result

    @staticmethod
    def _normalize_status(status: str | None) -> str:
        """Normalize overall_status to history viewer status."""
        if status in ("SUCCESS", "COMPLETED"):
            return "completed"
        if status == "FAILED":
            return "failed"
        return status.lower() if status else "unknown"

    @staticmethod
    def _duration_ms(record: SkillExecution) -> int:
        """Calculate duration in milliseconds."""
        if record.started_at and record.completed_at:
            delta = record.completed_at - record.started_at
            return int(delta.total_seconds() * 1000)
        return 0
