"""Risk scanner service for project health monitoring."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


@dataclass
class RiskAlert:
    """A single risk alert."""

    alert_type: str
    severity: str  # Low, Medium, High
    message: str
    project_id: str | None = None
    stage_id: str | None = None


class RiskScannerService:
    """Scan projects for risks: timebox overdue, stage blocking, stale artifacts."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session

    async def scan_project(self, project: Project) -> list[RiskAlert]:
        """Scan a single project for risks."""
        alerts: list[RiskAlert] = []

        # Timebox overdue risk
        if project.last_activity_at is not None:
            days_inactive = (datetime.now(UTC) - project.last_activity_at).days
            if days_inactive > 7:
                alerts.append(
                    RiskAlert(
                        alert_type="TIMEBOX_OVERDUE",
                        severity="High" if days_inactive > 14 else "Medium",
                        message=f"Project inactive for {days_inactive} days",
                        project_id=project.project_id,
                    )
                )

        # Stage blocking risk (simplified: no current_stage for too long)
        if project.current_stage is None and project.project_status == "Active":
            alerts.append(
                RiskAlert(
                    alert_type="STAGE_BLOCKED",
                    severity="Medium",
                    message="No current stage assigned for active project",
                    project_id=project.project_id,
                )
            )

        # Stale artifact risk (progress stuck)
        if project.progress_percent == 0 and project.project_status == "Active":
            alerts.append(
                RiskAlert(
                    alert_type="STALE_ARTIFACT",
                    severity="Low",
                    message="Active project with zero progress",
                    project_id=project.project_id,
                )
            )

        return alerts

    async def scan_application(self, projects: list[Project]) -> list[RiskAlert]:
        """Scan multiple projects and return aggregated alerts."""
        all_alerts: list[RiskAlert] = []
        for proj in projects:
            alerts = await self.scan_project(proj)
            all_alerts.extend(alerts)
        return all_alerts
