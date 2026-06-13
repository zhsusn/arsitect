"""Unit tests for Batch-05 advanced enterprise modules."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from app.advanced.history_viewer import HistoryViewer
from app.advanced.metrics_collector import MetricsCollector
from app.advanced.notification_manager import NotificationChannel, NotificationManager
from app.advanced.permission_manager import Permission, PermissionManager, Role
from app.common.event_bus import DomainEvent, EventBus
from app.models.application import Application
from app.models.project import Project
from app.models.skill_execution import SkillExecution


async def _seed_minimal_project(session, project_id: str) -> None:
    """Seed an application and project required by foreign keys."""
    app_obj = Application(
        application_id=f"app-{project_id}",
        application_name=f"App {project_id}",
        local_path="/tmp/test",
    )
    session.add(app_obj)
    await session.flush()

    project = Project(
        project_id=project_id,
        project_name=f"Project {project_id}",
        application_id=app_obj.application_id,
        template_level="Standard",
    )
    session.add(project)
    await session.flush()


async def _seed_execution(
    session,
    project_id: str,
    execution_id: str,
    skill_id: str,
    status: str,
    retry_count: int,
    phase: str = "NONE",
) -> None:
    """Seed a single skill execution for a project."""
    started = datetime.now(UTC) - timedelta(seconds=2)
    completed = datetime.now(UTC)
    execution = SkillExecution(
        execution_id=execution_id,
        project_id=project_id,
        stage_id="stage-1",
        skill_id=skill_id,
        skill_name="test-skill",
        current_phase=phase,
        overall_status=status,
        retry_count=retry_count,
        started_at=started,
        completed_at=completed,
    )
    session.add(execution)
    await session.flush()


class TestPermissionManager:
    """PermissionManager unit tests."""

    @pytest.mark.asyncio
    async def test_assign_role_and_check_permission(self, db_session) -> None:
        """Assigning a role should grant matching permissions."""
        await _seed_minimal_project(db_session, "proj-1")
        pm = PermissionManager(db_session)
        await pm.assign_role("proj-1", "user-1", Role.MEMBER)

        assert await pm.has_permission("user-1", "proj-1", Permission.PROJECT_READ)
        assert await pm.has_permission("user-1", "proj-1", Permission.SKILL_EXECUTE)
        assert not await pm.has_permission("user-1", "proj-1", Permission.GATE_BYPASS)

    @pytest.mark.asyncio
    async def test_owner_has_all_permissions(self, db_session) -> None:
        """OWNER role should imply every permission."""
        await _seed_minimal_project(db_session, "proj-1")
        pm = PermissionManager(db_session)
        await pm.assign_role("proj-1", "owner-1", Role.OWNER)

        for perm in Permission:
            assert await pm.has_permission("owner-1", "proj-1", perm)

    @pytest.mark.asyncio
    async def test_visitor_cannot_bypass_gate(self, db_session) -> None:
        """VISITOR should not be able to bypass gates."""
        await _seed_minimal_project(db_session, "proj-1")
        pm = PermissionManager(db_session)
        await pm.assign_role("proj-1", "visitor-1", Role.VISITOR)

        assert not await pm.can_bypass_gate("visitor-1", "proj-1")
        assert await pm.has_permission("visitor-1", "proj-1", Permission.PROJECT_READ)

    @pytest.mark.asyncio
    async def test_list_and_remove_member(self, db_session) -> None:
        """Listing members should reflect assignments and removals."""
        await _seed_minimal_project(db_session, "proj-1")
        pm = PermissionManager(db_session)
        await pm.assign_role("proj-1", "user-a", Role.ADMIN)
        await pm.assign_role("proj-1", "user-b", Role.MEMBER)

        members = await pm.list_members("proj-1")
        assert len(members) == 2
        assert {m.user_id for m in members} == {"user-a", "user-b"}

        await pm.remove_member("proj-1", "user-b")
        members = await pm.list_members("proj-1")
        assert len(members) == 1
        assert members[0].user_id == "user-a"


class TestMetricsCollector:
    """MetricsCollector unit tests."""

    @pytest.mark.asyncio
    async def test_get_skill_metrics(self, db_session) -> None:
        """Skill metrics should aggregate execution and retry counts."""
        await _seed_minimal_project(db_session, "proj-m1")
        await _seed_execution(db_session, "proj-m1", "exec-m1-1", "skill-1", "SUCCESS", 1)
        collector = MetricsCollector(db_session)

        metrics = await collector.get_skill_metrics("skill-1", "proj-m1")
        assert metrics is not None
        assert metrics.execution_count == 1
        assert metrics.success_count == 1
        assert metrics.fail_count == 0
        assert metrics.retry_count == 1
        assert metrics.total_duration_ms >= 0

    @pytest.mark.asyncio
    async def test_get_project_metrics(self, db_session) -> None:
        """Project metrics should summarize all executions."""
        await _seed_minimal_project(db_session, "proj-m2")
        await _seed_execution(db_session, "proj-m2", "exec-m2-1", "skill-1", "SUCCESS", 0)
        await _seed_execution(db_session, "proj-m2", "exec-m2-2", "skill-2", "FAILED", 2)
        collector = MetricsCollector(db_session)

        metrics = await collector.get_project_metrics("proj-m2")
        assert metrics["execution_count"] == 2
        assert metrics["success_count"] == 1
        assert metrics["fail_count"] == 1
        assert metrics["retry_count"] == 2
        assert metrics["success_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_list_application_metrics(self, db_session) -> None:
        """Application metrics should include every project."""
        await _seed_minimal_project(db_session, "proj-a1")
        await _seed_execution(db_session, "proj-a1", "exec-a1-1", "skill-1", "SUCCESS", 0)
        collector = MetricsCollector(db_session)

        metrics = await collector.list_application_metrics("app-proj-a1")
        assert len(metrics) == 1
        assert metrics[0]["project_id"] == "proj-a1"


class TestHistoryViewer:
    """HistoryViewer unit tests."""

    async def _seed_completed_project(self, session) -> str:
        """Seed an archived project with two skill executions."""
        await _seed_minimal_project(session, "proj-hv")
        project = await session.get(Project, "proj-hv")
        project.project_status = "Archived"
        await session.flush()

        base_time = datetime.now(UTC) - timedelta(minutes=10)
        for idx, (phase, status, retries) in enumerate(
            [
                ("PREP", "SUCCESS", 0),
                ("EXEC", "FAILED", 3),
            ]
        ):
            execution = SkillExecution(
                execution_id=f"exec-hv-{idx}",
                project_id="proj-hv",
                stage_id="stage-1",
                skill_id=f"skill-{idx}",
                skill_name=f"Skill {idx}",
                current_phase=phase,
                overall_status=status,
                retry_count=retries,
                started_at=base_time + timedelta(minutes=idx),
                completed_at=base_time + timedelta(minutes=idx + 1),
            )
            session.add(execution)
        await session.flush()
        return "proj-hv"

    @pytest.mark.asyncio
    async def test_get_project_timeline(self, db_session) -> None:
        """Timeline should group executions by phase and compute totals."""
        project_id = await self._seed_completed_project(db_session)
        viewer = HistoryViewer(db_session)

        timeline = await viewer.get_project_timeline(project_id)
        assert timeline is not None
        assert timeline.project_id == project_id
        assert len(timeline.skill_records) == 2
        assert timeline.total_duration_ms > 0

        phases = {s["name"]: s for s in timeline.stages}
        assert "PREP" in phases
        assert "EXEC" in phases
        assert phases["EXEC"]["success_rate"] == 0.0
        assert phases["PREP"]["success_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_get_rework_heatmap(self, db_session) -> None:
        """Heatmap should reflect retry counts per phase.skill."""
        project_id = await self._seed_completed_project(db_session)
        viewer = HistoryViewer(db_session)

        heatmap = await viewer.get_rework_heatmap(project_id)
        assert "EXEC.skill-1" in heatmap
        assert heatmap["EXEC.skill-1"]["retry_count"] == 3
        assert heatmap["EXEC.skill-1"]["intensity"] == 1.0

    @pytest.mark.asyncio
    async def test_list_completed_projects(self, db_session) -> None:
        """Only archived projects should appear in completed list."""
        await self._seed_completed_project(db_session)
        viewer = HistoryViewer(db_session)

        completed = await viewer.list_completed_projects()
        assert any(p["id"] == "proj-hv" for p in completed)

    @pytest.mark.asyncio
    async def test_get_application_summary(self, db_session) -> None:
        """Application summary should count projects."""
        await self._seed_completed_project(db_session)
        viewer = HistoryViewer(db_session)

        summary = await viewer.get_application_summary("app-proj-hv")
        assert summary["total_projects"] == 1
        assert summary["completed_projects"] == 1


class TestNotificationManager:
    """NotificationManager unit tests."""

    @pytest.fixture
    def event_bus(self):
        """Provide a fresh event bus for each test."""
        return EventBus()

    def test_send_and_get_unread(self, event_bus) -> None:
        """Sending a notification should make it available as unread."""
        manager = NotificationManager(event_bus)
        manager.send(
            type="test",
            title="Hello",
            message="World",
            project_id="proj-1",
            channels=[NotificationChannel.SSE],
        )

        unread = manager.get_notifications("proj-1", unread_only=True)
        assert len(unread) == 1
        assert unread[0].title == "Hello"

    def test_mark_read(self, event_bus) -> None:
        """Marking a notification read should remove it from unread list."""
        manager = NotificationManager(event_bus)
        notification = manager.send(
            type="test",
            title="Hello",
            message="World",
            project_id="proj-1",
            channels=[NotificationChannel.SSE],
        )

        assert manager.mark_read("proj-1", notification.id)
        assert len(manager.get_notifications("proj-1", unread_only=True)) == 0
        assert not manager.mark_read("proj-1", "missing-id")

    def test_mark_all_read(self, event_bus) -> None:
        """Mark all read should clear every unread notification."""
        manager = NotificationManager(event_bus)
        for idx in range(3):
            manager.send(
                type="test",
                title=f"Note {idx}",
                message="msg",
                project_id="proj-1",
                channels=[NotificationChannel.SSE],
            )

        assert manager.mark_all_read("proj-1") == 3
        assert len(manager.get_notifications("proj-1", unread_only=True)) == 0

    @pytest.mark.asyncio
    async def test_event_bus_subscribe_and_notify(self, event_bus) -> None:
        """Subscribing to gate.created should generate a notification."""
        await event_bus.start()
        try:
            manager = NotificationManager(event_bus)
            event_bus.publish(
                DomainEvent(
                    event_type="gate.created",
                    aggregate_id="proj-1",
                    payload={"skill_id": "skill-1"},
                )
            )
            await asyncio.sleep(0.05)

            notifications = manager.get_notifications("proj-1")
            assert len(notifications) == 1
            assert notifications[0].type == "gate"
        finally:
            await event_bus.stop()
