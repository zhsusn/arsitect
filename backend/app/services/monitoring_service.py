"""MonitoringService — 监控看板数据聚合."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gate_decision import GateDecision
from app.models.operation_log import OperationLog
from app.models.project import Project
from app.models.project_stage import ProjectStage
from app.models.skill_execution import SkillExecution


class MonitoringService:
    """Aggregate monitoring data for dashboard."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session.

        Args:
            session: Async SQLAlchemy session.
        """
        self._session = session

    async def get_overview(self) -> dict[str, int]:
        """Return global overview counts.

        Returns:
            Dict with total_projects, active_projects, risk_projects,
            pending_gates, total_executions.
        """
        total_projects_result = await self._session.execute(
            select(func.count()).select_from(Project)
        )
        total_projects = total_projects_result.scalar() or 0

        active_projects_result = await self._session.execute(
            select(func.count()).select_from(Project).where(Project.project_status == "Active")
        )
        active_projects = active_projects_result.scalar() or 0

        risk_projects_result = await self._session.execute(
            select(func.count()).select_from(Project).where(Project.risk_level.in_(["Medium", "High"]))
        )
        risk_projects = risk_projects_result.scalar() or 0

        pending_gates_result = await self._session.execute(
            select(func.count()).select_from(GateDecision).where(GateDecision.status == "pending")
        )
        pending_gates = pending_gates_result.scalar() or 0

        total_executions_result = await self._session.execute(
            select(func.count()).select_from(SkillExecution)
        )
        total_executions = total_executions_result.scalar() or 0

        return {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "risk_projects": risk_projects,
            "pending_gates": pending_gates,
            "total_executions": total_executions,
        }

    async def get_project_stats(self, project_id: str) -> dict[str, int]:
        """Return per-project monitoring stats.

        Args:
            project_id: Project identifier.

        Returns:
            Dict with stage_count, execution_count, gate_count, log_count.
        """
        stage_count_result = await self._session.execute(
            select(func.count())
            .select_from(ProjectStage)
            .where(ProjectStage.project_id == project_id)
        )
        stage_count = stage_count_result.scalar() or 0

        execution_count_result = await self._session.execute(
            select(func.count())
            .select_from(SkillExecution)
            .where(SkillExecution.project_id == project_id)
        )
        execution_count = execution_count_result.scalar() or 0

        gate_count_result = await self._session.execute(
            select(func.count())
            .select_from(GateDecision)
            .where(GateDecision.project_id == project_id)
        )
        gate_count = gate_count_result.scalar() or 0

        log_count_result = await self._session.execute(
            select(func.count())
            .select_from(OperationLog)
            .where(OperationLog.project_id == project_id)
        )
        log_count = log_count_result.scalar() or 0

        return {
            "stage_count": stage_count,
            "execution_count": execution_count,
            "gate_count": gate_count,
            "log_count": log_count,
        }

    async def list_operation_logs(
        self,
        project_id: str,
        *,
        action: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[OperationLog], int]:
        """List operation logs for a project with optional action filter.

        Args:
            project_id: Project identifier.
            action: Optional action filter.
            limit: Pagination limit.
            offset: Pagination offset.

        Returns:
            Tuple of (logs, total_count).
        """
        base_stmt = select(OperationLog).where(OperationLog.project_id == project_id)
        count_stmt = select(func.count()).select_from(OperationLog).where(OperationLog.project_id == project_id)

        if action:
            base_stmt = base_stmt.where(OperationLog.action == action)
            count_stmt = count_stmt.where(OperationLog.action == action)

        base_stmt = base_stmt.order_by(OperationLog.created_at.desc()).offset(offset).limit(limit)

        result = await self._session.execute(base_stmt)
        logs = list(result.scalars().all())

        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar() or 0

        return logs, total
