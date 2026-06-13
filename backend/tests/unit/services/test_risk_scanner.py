"""Tests for RiskScannerService."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.models.project import Project
from app.services.risk_scanner_service import RiskScannerService


class TestRiskScannerService:
    """RiskScannerService tests."""

    @pytest.mark.asyncio
    async def test_detect_timebox_overdue(self) -> None:
        """Detects inactive project overdue risk."""
        svc = RiskScannerService(None)  # type: ignore[arg-type]
        proj = Project(
            project_id="p1",
            project_name="Overdue",
            application_id="a1",
            template_level="Standard",
            last_activity_at=datetime(2020, 1, 1, tzinfo=UTC),
        )
        alerts = await svc.scan_project(proj)
        assert any(a.alert_type == "TIMEBOX_OVERDUE" for a in alerts)

    @pytest.mark.asyncio
    async def test_detect_stage_blocked(self) -> None:
        """Detects active project without current stage."""
        svc = RiskScannerService(None)  # type: ignore[arg-type]
        proj = Project(
            project_id="p2",
            project_name="Blocked",
            application_id="a1",
            template_level="Standard",
            project_status="Active",
            current_stage=None,
        )
        alerts = await svc.scan_project(proj)
        assert any(a.alert_type == "STAGE_BLOCKED" for a in alerts)

    @pytest.mark.asyncio
    async def test_detect_stale_artifact(self) -> None:
        """Detects active project with zero progress."""
        svc = RiskScannerService(None)  # type: ignore[arg-type]
        proj = Project(
            project_id="p3",
            project_name="Stale",
            application_id="a1",
            template_level="Standard",
            project_status="Active",
            progress_percent=0,
        )
        alerts = await svc.scan_project(proj)
        assert any(a.alert_type == "STALE_ARTIFACT" for a in alerts)

    @pytest.mark.asyncio
    async def test_no_alerts_for_healthy(self) -> None:
        """Healthy project has no alerts."""
        svc = RiskScannerService(None)  # type: ignore[arg-type]
        proj = Project(
            project_id="p4",
            project_name="Healthy",
            application_id="a1",
            template_level="Standard",
            project_status="Active",
            progress_percent=50,
            current_stage="Coding",
            last_activity_at=datetime.now(UTC),
        )
        alerts = await svc.scan_project(proj)
        assert len(alerts) == 0

    @pytest.mark.asyncio
    async def test_scan_application(self) -> None:
        """Aggregates alerts across multiple projects."""
        svc = RiskScannerService(None)  # type: ignore[arg-type]
        projects = [
            Project(
                project_id="p5",
                project_name="A",
                application_id="a1",
                template_level="Standard",
                project_status="Active",
                progress_percent=0,
                current_stage="Coding",
            ),
            Project(
                project_id="p6",
                project_name="B",
                application_id="a1",
                template_level="Light",
                project_status="Active",
                progress_percent=0,
                current_stage=None,
            ),
        ]
        alerts = await svc.scan_application(projects)
        assert len(alerts) == 3  # A: STALE_ARTIFACT, B: STAGE_BLOCKED + STALE_ARTIFACT
