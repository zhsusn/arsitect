"""Advanced enterprise router — Batch-05 endpoints."""

from __future__ import annotations

import contextlib
import os
import tempfile
from typing import Any

from fastapi import APIRouter, Depends, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.advanced import (
    DriftDetector,
    HistoryViewer,
    ImportExportManager,
    InterfaceGap,
    MetricsCollector,
    NotificationManager,
    Permission,
    PermissionManager,
    PrototypeArchBinder,
    Role,
    SearchEngine,
)
from app.c4.baseline_store import C4BaselineStore
from app.c4.interface_contract_store import InterfaceContractStore
from app.common.event_bus import get_event_bus
from app.docforge.fragment_registry import FragmentRegistry
from app.infrastructure.database.session import get_db
from app.schemas.advanced import (
    AssignRoleDTO,
    CompletedProjectDTO,
    DriftReportDTO,
    DriftRequestDTO,
    GapWritebackResultDTO,
    HeatmapCellDTO,
    HistorySummaryDTO,
    InterfaceGapDTO,
    NotificationDTO,
    PermissionCheckDTO,
    ProjectMemberDTO,
    ProjectMetricsDTO,
    ProjectTimelineDTO,
    ProtoInterfaceDTO,
    SearchResultDTO,
    SkillMetricsDTO,
    TimelineStageDTO,
)

router = APIRouter(prefix="/advanced", tags=["advanced"])


# Shared notification manager so all routes/requests see the same in-memory state.
_notification_manager: NotificationManager | None = None


def _get_notification_manager() -> NotificationManager:
    """Return the singleton NotificationManager for this process."""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager(get_event_bus())
    return _notification_manager


# ---------------------------------------------------------------------------
# HistoryViewer
# ---------------------------------------------------------------------------
@router.get(
    "/history/{project_id}/timeline",
    response_model=ProjectTimelineDTO,
)
async def get_timeline(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProjectTimelineDTO:
    """Get project execution timeline."""
    viewer = HistoryViewer(db)
    timeline = await viewer.get_project_timeline(project_id)
    if timeline is None:
        return ProjectTimelineDTO(
            project_id=project_id,
            project_name="",
            stages=[],
            total_duration_ms=0,
        )
    return ProjectTimelineDTO(
        project_id=timeline.project_id,
        project_name=timeline.project_name,
        stages=[
            TimelineStageDTO(
                name=s["name"],
                skill_count=s["skill_count"],
                total_duration_ms=s["total_duration_ms"],
                avg_duration_ms=s["avg_duration_ms"],
                success_rate=s["success_rate"],
                start=s["start"],
                end=s["end"],
            )
            for s in timeline.stages
        ],
        total_duration_ms=timeline.total_duration_ms,
    )


@router.get(
    "/history/{project_id}/heatmap",
    response_model=dict[str, HeatmapCellDTO],
)
async def get_heatmap(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, HeatmapCellDTO]:
    """Get rework heatmap for a project."""
    viewer = HistoryViewer(db)
    heatmap = await viewer.get_rework_heatmap(project_id)
    return {key: HeatmapCellDTO(**value) for key, value in heatmap.items()}


@router.get(
    "/history/completed",
    response_model=list[CompletedProjectDTO],
)
async def list_completed_projects(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> list[CompletedProjectDTO]:
    """List completed/archived projects."""
    viewer = HistoryViewer(db)
    projects = await viewer.list_completed_projects(limit=limit)
    return [CompletedProjectDTO(**p) for p in projects]


@router.get(
    "/applications/{application_id}/history/summary",
    response_model=HistorySummaryDTO,
)
async def get_application_summary(
    application_id: str,
    db: AsyncSession = Depends(get_db),
) -> HistorySummaryDTO:
    """Get application-level history summary."""
    viewer = HistoryViewer(db)
    data = await viewer.get_application_summary(application_id)
    return HistorySummaryDTO(**data)


# ---------------------------------------------------------------------------
# PermissionManager
# ---------------------------------------------------------------------------
@router.post(
    "/projects/{project_id}/members",
    response_model=ProjectMemberDTO,
    status_code=201,
)
async def assign_role(
    project_id: str,
    dto: AssignRoleDTO,
    db: AsyncSession = Depends(get_db),
) -> ProjectMemberDTO:
    """Assign a role to a project member."""
    pm = PermissionManager(db)
    member = await pm.assign_role(project_id, dto.user_id, Role(dto.role))
    return ProjectMemberDTO(
        user_id=member.user_id,
        project_id=member.project_id,
        role=member.role,
    )


@router.get(
    "/projects/{project_id}/members",
    response_model=list[ProjectMemberDTO],
)
async def list_members(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[ProjectMemberDTO]:
    """List project members."""
    pm = PermissionManager(db)
    members = await pm.list_members(project_id)
    return [
        ProjectMemberDTO(
            user_id=m.user_id,
            project_id=m.project_id,
            role=m.role,
        )
        for m in members
    ]


@router.delete(
    "/projects/{project_id}/members/{user_id}",
    status_code=204,
    response_model=None,
)
async def remove_member(
    project_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a member from a project."""
    pm = PermissionManager(db)
    await pm.remove_member(project_id, user_id)


@router.get(
    "/projects/{project_id}/permissions/check",
    response_model=PermissionCheckDTO,
)
async def check_permission(
    project_id: str,
    user_id: str,
    permission: str,
    db: AsyncSession = Depends(get_db),
) -> PermissionCheckDTO:
    """Check whether a user has a permission."""
    pm = PermissionManager(db)
    allowed = await pm.has_permission(project_id, user_id, Permission(permission))
    return PermissionCheckDTO(
        user_id=user_id,
        permission=permission,
        allowed=allowed,
    )


# ---------------------------------------------------------------------------
# PrototypeArchBinder
# ---------------------------------------------------------------------------
@router.post(
    "/projects/{project_id}/gaps",
    response_model=list[InterfaceGapDTO],
)
async def detect_gaps(
    project_id: str,
    dto: list[ProtoInterfaceDTO] | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[InterfaceGapDTO]:
    """Detect interface gaps between prototype and C4 contracts."""
    binder = PrototypeArchBinder(
        session=db,
        baseline_store=C4BaselineStore(db),
        contract_store=InterfaceContractStore(db),
    )
    if dto is None:
        gaps = await binder.detect_gaps(project_id)
    else:
        interfaces = [m.model_dump() for m in dto]
        gaps = await binder.detect_gaps_from_interfaces(project_id, interfaces)
    return [
        InterfaceGapDTO(
            contract_id=g.contract_id,
            endpoint_path=g.endpoint_path,
            method=g.method,
            gap_type=g.gap_type,
            suggestion=g.suggestion,
            source_page=g.source_page or None,
            source_type=g.source_type or None,
        )
        for g in gaps
    ]


@router.post(
    "/projects/{project_id}/gaps/writeback",
    response_model=GapWritebackResultDTO,
)
async def writeback_gaps(
    project_id: str,
    dto: list[InterfaceGapDTO],
    db: AsyncSession = Depends(get_db),
) -> GapWritebackResultDTO:
    """Create InterfaceContract records for missing-in-contract gaps."""
    binder = PrototypeArchBinder(
        session=db,
        baseline_store=C4BaselineStore(db),
        contract_store=InterfaceContractStore(db),
    )
    gaps = [
        InterfaceGap(
            contract_id=g.contract_id,
            endpoint_path=g.endpoint_path,
            method=g.method,
            gap_type=g.gap_type,
            suggestion=g.suggestion,
            source_page=g.source_page or "",
            source_type=g.source_type or "",
        )
        for g in dto
    ]
    created = await binder.apply_writeback(project_id, gaps)
    return GapWritebackResultDTO(
        created_count=len(created),
        contracts=created,
    )


@router.post(
    "/projects/{project_id}/gaps/sync-to-dsl",
    response_model=dict[str, Any],
)
async def sync_gaps_to_dsl(
    project_id: str,
    dto: list[InterfaceGapDTO],
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Write missing-in-contract gaps back to C4 DSL."""
    binder = PrototypeArchBinder(
        session=db,
        baseline_store=C4BaselineStore(db),
        contract_store=InterfaceContractStore(db),
    )
    gaps = [
        InterfaceGap(
            contract_id=g.contract_id,
            endpoint_path=g.endpoint_path,
            method=g.method,
            gap_type=g.gap_type,
            suggestion=g.suggestion,
            source_page=g.source_page or "",
            source_type=g.source_type or "",
        )
        for g in dto
    ]
    ok = await binder.sync_to_dsl(project_id, gaps)
    return {"success": ok}


# ---------------------------------------------------------------------------
# DriftDetector
# ---------------------------------------------------------------------------
@router.post(
    "/projects/{project_id}/drift",
    response_model=DriftReportDTO,
)
async def detect_drift(
    project_id: str,
    dto: DriftRequestDTO,
    db: AsyncSession = Depends(get_db),
) -> DriftReportDTO:
    """Detect architecture drift between DSL and code directory."""
    detector = DriftDetector(C4BaselineStore(db))
    report = await detector.detect(project_id, dto.code_dir)
    return DriftReportDTO(
        project_id=report.project_id,
        checked_at=report.checked_at,
        additions=report.additions,
        deletions=report.deletions,
        modifications=report.modifications,
    )


# ---------------------------------------------------------------------------
# MetricsCollector
# ---------------------------------------------------------------------------
@router.get(
    "/projects/{project_id}/metrics",
    response_model=ProjectMetricsDTO,
)
async def get_project_metrics(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProjectMetricsDTO:
    """Get aggregated metrics for a project."""
    collector = MetricsCollector(db)
    data = await collector.get_project_metrics(project_id)
    return ProjectMetricsDTO(**data)


@router.get(
    "/projects/{project_id}/skills/{skill_id}/metrics",
    response_model=SkillMetricsDTO,
)
async def get_skill_metrics(
    project_id: str,
    skill_id: str,
    db: AsyncSession = Depends(get_db),
) -> SkillMetricsDTO:
    """Get metrics for a skill in a project."""
    collector = MetricsCollector(db)
    metrics = await collector.get_skill_metrics(skill_id, project_id)
    if metrics is None:
        return SkillMetricsDTO(
            skill_id=skill_id,
            project_id=project_id,
            execution_count=0,
            total_duration_ms=0,
            avg_duration_ms=0.0,
            success_count=0,
            fail_count=0,
            retry_count=0,
            avg_gate_wait_ms=0,
        )
    return SkillMetricsDTO(
        skill_id=metrics.skill_id,
        project_id=metrics.project_id,
        execution_count=metrics.execution_count,
        total_duration_ms=metrics.total_duration_ms,
        avg_duration_ms=metrics.avg_duration_ms,
        success_count=metrics.success_count,
        fail_count=metrics.fail_count,
        retry_count=metrics.retry_count,
        avg_gate_wait_ms=metrics.avg_gate_wait_ms,
    )


# ---------------------------------------------------------------------------
# SearchEngine
# ---------------------------------------------------------------------------
@router.get(
    "/search",
    response_model=list[SearchResultDTO],
)
async def global_search(
    project_id: str,
    q: str,
    type: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[SearchResultDTO]:
    """Global search across artifacts, C4 nodes and fragments."""
    engine = SearchEngine(
        fragment_registry=FragmentRegistry(db),
        baseline_store=C4BaselineStore(db),
    )
    filters = {"type": type} if type else {}
    results = await engine.search(project_id, q, filters)
    return [
        SearchResultDTO(
            type=r.type,
            id=r.id,
            title=r.title,
            preview=r.preview,
            path=r.path,
            score=r.score,
        )
        for r in results
    ]


# ---------------------------------------------------------------------------
# NotificationManager
# ---------------------------------------------------------------------------
@router.get(
    "/projects/{project_id}/notifications",
    response_model=list[NotificationDTO],
)
async def get_notifications(
    project_id: str,
    unread_only: bool = False,
) -> list[NotificationDTO]:
    """List notifications for a project."""
    manager = _get_notification_manager()
    notifications = manager.get_notifications(project_id, unread_only)
    return [
        NotificationDTO(
            id=n.id,
            type=n.type,
            title=n.title,
            message=n.message,
            project_id=n.project_id,
            channels=n.channels,
            created_at=n.created_at,
            read=n.read,
        )
        for n in notifications
    ]


@router.post(
    "/projects/{project_id}/notifications/{notif_id}/read",
    response_model=dict[str, bool],
)
async def mark_notification_read(
    project_id: str,
    notif_id: str,
) -> dict[str, bool]:
    """Mark a notification as read."""
    manager = _get_notification_manager()
    ok = manager.mark_read(project_id, notif_id)
    return {"success": ok}


@router.get("/events/{project_id}")
async def events_stream(
    project_id: str,
    request: Request,
) -> Any:
    """SSE event stream for a project."""
    manager = _get_notification_manager()
    return await manager.connect_sse(project_id, request)


# ---------------------------------------------------------------------------
# ImportExportManager
# ---------------------------------------------------------------------------
@router.post(
    "/projects/{project_id}/export",
    response_model=dict[str, str],
)
async def export_project(
    project_id: str,
    output_dir: str = "./exports",
) -> dict[str, str]:
    """Export a project to .arsitect archive."""
    manager = ImportExportManager()
    path = await manager.export_project(project_id, output_dir)
    return {"path": path}


@router.post(
    "/projects/import",
    response_model=dict[str, str],
)
async def import_project(
    file: UploadFile,
    target_project_id: str | None = None,
) -> dict[str, str]:
    """Import a project from .arsitect archive."""
    manager = ImportExportManager()
    suffix = ".arsitect"
    if file.filename:
        suffix = os.path.splitext(os.path.basename(file.filename))[1] or suffix

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        import_path = tmp.name

    try:
        project_id = await manager.import_project(import_path, target_project_id)
    finally:
        with contextlib.suppress(FileNotFoundError, PermissionError):
            os.remove(import_path)
    return {"project_id": project_id}
