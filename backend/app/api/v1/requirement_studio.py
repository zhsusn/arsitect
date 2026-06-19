"""Requirement Studio router — full implementation for UI restructuring."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.infrastructure.database.session import get_db
from app.models.artifact import ArtifactFile
from app.models.artifact_version import ArtifactVersion
from app.models.project import Project
from app.models.project_stage import ProjectStage
from app.models.stage_skill_binding import StageSkillBinding
from app.models.template_stage import TemplateStage
from app.schemas.requirement_studio import (
    ArtifactContentResponse,
    ArtifactEditRequest,
    ArtifactEditResponse,
    ArtifactsResponse,
    BaselineRequest,
    BaselineResponse,
    ChangeRequestRequest,
    ChangeRequestResponse,
    RequirementStudioStatusResponse,
    StageArtifactGroup,
    StageExecuteRequest,
    StageExecuteResponse,
    StageReviewRequest,
    StageReviewResponse,
    StageStatusItem,
    StageTasksResponse,
    StageTaskItem,
    StaleAnalysisResponse,
    StaleArtifactItem,
    StaleImpactItem,
)
from app.services.artifact_service import ArtifactService
from app.services.stage_orchestrator import StageOrchestrator

router = APIRouter(prefix="/requirement-studio", tags=["requirement-studio"])


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _map_stage_status(runtime_status: str) -> str:
    mapping = {
        "not_started": "not_started",
        "ready": "not_started",
        "in_progress": "in_progress",
        "review_pending": "review_pending",
        "gate_pending": "review_pending",
        "passed": "passed",
        "blocked": "in_progress",
        "skipped": "passed",
    }
    return mapping.get(runtime_status, "locked")


def _runtime_progress(runtime_status: str) -> int:
    mapping = {
        "not_started": 0,
        "ready": 0,
        "in_progress": 50,
        "review_pending": 80,
        "gate_pending": 90,
        "passed": 100,
        "blocked": 30,
        "skipped": 100,
    }
    return mapping.get(runtime_status, 0)


def _compute_hash(content: str) -> str:
    return hashlib.md5(content.encode("utf-8")).hexdigest()


# ------------------------------------------------------------------
# Status
# ------------------------------------------------------------------
@router.get("/{project_id}/status", response_model=RequirementStudioStatusResponse)
async def get_status(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> RequirementStudioStatusResponse:
    """Get requirement studio status with stage progression."""
    project = await db.get(Project, project_id)
    if project is None:
        raise NotFoundError(detail=f"Project '{project_id}' not found")

    stmt = (
        select(ProjectStage, TemplateStage)
        .join(
            TemplateStage,
            ProjectStage.stage_id == TemplateStage.business_stage_key,
            isouter=True,
        )
        .where(ProjectStage.project_id == project_id)
        .order_by(ProjectStage.order_index.asc())
    )
    result = await db.execute(stmt)
    stages = list(result.all())

    if not stages:
        raise NotFoundError(detail=f"No stages found for project '{project_id}'")

    # Determine current stage
    current_stage = None
    if project.current_stage_id:
        for ps, _ in stages:
            if ps.project_stage_id == project.current_stage_id:
                current_stage = ps
                break
    if current_stage is None:
        for ps, _ in stages:
            if not ps.skippable:
                current_stage = ps
                break
        if current_stage is None:
            current_stage = stages[0][0]

    current_order = current_stage.order_index

    stage_items = []
    for ps, ts in stages:
        if ps.order_index < current_order:
            status = "passed"
            progress = 100
            can_enter = True
        elif ps.project_stage_id == current_stage.project_stage_id:
            status = _map_stage_status(ps.runtime_status)
            progress = _runtime_progress(ps.runtime_status)
            can_enter = True
        else:
            status = "locked"
            progress = 0
            can_enter = False

        stage_items.append(
            StageStatusItem(
                stage_id=ps.stage_id,
                stage_name=ts.stage_name if ts else ps.stage_id,
                status=status,
                progress=progress,
                can_enter=can_enter,
            )
        )

    return RequirementStudioStatusResponse(
        project_id=project_id,
        current_stage=current_stage.stage_id,
        stages=stage_items,
    )


# ------------------------------------------------------------------
# Tasks
# ------------------------------------------------------------------
@router.get("/{project_id}/stage/{stage_id}/tasks", response_model=StageTasksResponse)
async def get_stage_tasks(
    project_id: str,
    stage_id: str,
    db: AsyncSession = Depends(get_db),
) -> StageTasksResponse:
    """Get tasks for a specific stage (derived from StageSkillBinding)."""
    stage_stmt = select(ProjectStage).where(
        ProjectStage.project_id == project_id,
        ProjectStage.stage_id == stage_id,
    )
    stage_result = await db.execute(stage_stmt)
    stage = stage_result.scalar_one_or_none()
    if stage is None:
        raise NotFoundError(detail=f"Stage '{stage_id}' not found for project '{project_id}'")

    binding_stmt = (
        select(StageSkillBinding)
        .where(StageSkillBinding.project_stage_id == stage.project_stage_id)
        .order_by(StageSkillBinding.execution_order.asc())
    )
    binding_result = await db.execute(binding_stmt)
    bindings = list(binding_result.scalars().all())

    # Fetch artifacts for this stage to map output artifacts
    art_stmt = select(ArtifactFile).where(
        ArtifactFile.project_id == project_id,
        ArtifactFile.stage_id == stage.project_stage_id,
    )
    art_result = await db.execute(art_stmt)
    artifacts = list(art_result.scalars().all())

    tasks = []
    for binding in bindings:
        artifact = next(
            (a for a in artifacts if a.skill_id == binding.skill_id),
            None,
        )
        tasks.append(
            StageTaskItem(
                task_id=binding.binding_id,
                task_name=binding.skill_id,
                task_type=binding.role,
                status="not_started",
                skill_id=binding.skill_id,
                output_artifact=artifact.file_name if artifact else None,
            )
        )

    return StageTasksResponse(stage_id=stage_id, tasks=tasks)


# ------------------------------------------------------------------
# Execute
# ------------------------------------------------------------------
@router.post(
    "/{project_id}/stage/{stage_id}/execute",
    response_model=StageExecuteResponse,
)
async def execute_stage(
    project_id: str,
    stage_id: str,
    dto: StageExecuteRequest,
    db: AsyncSession = Depends(get_db),
) -> StageExecuteResponse:
    """Trigger skill execution for a stage."""
    stage_stmt = select(ProjectStage).where(
        ProjectStage.project_id == project_id,
        ProjectStage.stage_id == stage_id,
    )
    stage_result = await db.execute(stage_stmt)
    stage = stage_result.scalar_one_or_none()
    if stage is None:
        raise NotFoundError(detail=f"Stage '{stage_id}' not found for project '{project_id}'")

    orchestrator = StageOrchestrator(session=db)
    result = await orchestrator.execute_stage(
        stage.project_stage_id,
        operator_id="api",
    )

    execution_ids = result.get("execution_ids", [])
    execution_id = execution_ids[0] if execution_ids else f"exec-{uuid.uuid4()}"
    return StageExecuteResponse(
        execution_id=execution_id,
        status=result.get("status", "NOT_STARTED"),
    )


# ------------------------------------------------------------------
# Review
# ------------------------------------------------------------------
@router.post(
    "/{project_id}/stage/{stage_id}/review",
    response_model=StageReviewResponse,
)
async def review_stage(
    project_id: str,
    stage_id: str,
    dto: StageReviewRequest,
    db: AsyncSession = Depends(get_db),
) -> StageReviewResponse:
    """Submit a review for a stage (pass or regenerate)."""
    stage_stmt = select(ProjectStage).where(
        ProjectStage.project_id == project_id,
        ProjectStage.stage_id == stage_id,
    )
    stage_result = await db.execute(stage_stmt)
    stage = stage_result.scalar_one_or_none()
    if stage is None:
        raise NotFoundError(detail=f"Stage '{stage_id}' not found for project '{project_id}'")

    if dto.action not in ("pass", "regenerate"):
        raise ValidationError(detail="action must be 'pass' or 'regenerate'")

    if dto.action == "pass":
        orchestrator = StageOrchestrator(session=db)
        result = await orchestrator.advance_stage(
            stage.project_stage_id,
            operator_id="api",
        )
        return StageReviewResponse(
            stage_id=stage_id,
            status=result.get("status", "passed"),
            next_stage_id=result.get("next_stage_id"),
        )

    # Regenerate: reset stage to ready so it can be re-executed
    stage.runtime_status = "ready"
    stage.execution_status = "NOT_STARTED"
    stage.started_at = None
    stage.completed_at = None
    db.add(stage)
    await db.commit()
    await db.refresh(stage)
    return StageReviewResponse(
        stage_id=stage_id,
        status="ready",
        next_stage_id=None,
    )


# ------------------------------------------------------------------
# Artifacts
# ------------------------------------------------------------------
@router.get("/{project_id}/artifacts", response_model=ArtifactsResponse)
async def get_artifacts(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> ArtifactsResponse:
    """Return artifacts grouped by stage."""
    art_stmt = (
        select(ArtifactFile)
        .where(ArtifactFile.project_id == project_id)
        .order_by(ArtifactFile.stage_id, ArtifactFile.created_at.desc())
    )
    art_result = await db.execute(art_stmt)
    artifacts = list(art_result.scalars().all())

    # Resolve stage names
    stage_ids = {a.stage_id for a in artifacts if a.stage_id}
    stage_names: dict[str, str] = {}
    if stage_ids:
        stage_stmt = (
            select(ProjectStage, TemplateStage)
            .join(
                TemplateStage,
                ProjectStage.stage_id == TemplateStage.business_stage_key,
                isouter=True,
            )
            .where(
                ProjectStage.project_id == project_id,
                ProjectStage.project_stage_id.in_(stage_ids),
            )
        )
        stage_result = await db.execute(stage_stmt)
        for ps, ts in stage_result.all():
            stage_names[ps.project_stage_id] = ts.stage_name if ts else ps.stage_id

    groups: dict[str, list] = {}
    for art in artifacts:
        sid = art.stage_id or "unknown"
        if sid not in groups:
            groups[sid] = []
        groups[sid].append(
            {
                "artifact_id": art.artifact_id,
                "file_name": art.file_name,
                "version": f"v{art.current_version}",
                "status": art.external_status,
            }
        )

    stage_items = [
        StageArtifactGroup(
            stage_id=sid,
            stage_name=stage_names.get(sid, sid),
            files=files,
        )
        for sid, files in groups.items()
    ]

    return ArtifactsResponse(artifacts=stage_items)


@router.get(
    "/{project_id}/artifacts/{artifact_id}",
    response_model=ArtifactContentResponse,
)
async def get_artifact_content(
    project_id: str,
    artifact_id: str,
    db: AsyncSession = Depends(get_db),
) -> ArtifactContentResponse:
    """Return artifact content and version history."""
    svc = ArtifactService(db)
    content, _total_lines, _content_hash = await svc.get_content(artifact_id)
    versions = await svc.list_versions(artifact_id)

    version_items = [
        {
            "version": f"v{v.version_number}",
            "created_at": v.created_at.isoformat() if v.created_at else "",
        }
        for v in versions
    ]

    return ArtifactContentResponse(
        content=content,
        versions=version_items,
    )


@router.post(
    "/{project_id}/artifacts/{artifact_id}/edit",
    response_model=ArtifactEditResponse,
)
async def edit_artifact(
    project_id: str,
    artifact_id: str,
    dto: ArtifactEditRequest,
    db: AsyncSession = Depends(get_db),
) -> ArtifactEditResponse:
    """Edit artifact content with external-change conflict detection."""
    svc = ArtifactService(db)
    artifact = await svc._repo.get_by_id(artifact_id)
    if artifact is None:
        raise NotFoundError(detail=f"Artifact '{artifact_id}' not found")

    # Read current disk content for conflict detection
    try:
        current_content = await svc._read_file(artifact.file_path)
    except OSError:
        current_content = ""

    current_hash = _compute_hash(current_content)
    has_conflict = (
        artifact.last_synced_hash is not None
        and artifact.last_synced_hash != current_hash
    )

    # Write new content
    await svc._write_file(artifact.file_path, dto.content)

    # Update artifact metadata
    new_hash = _compute_hash(dto.content)
    artifact.last_synced_hash = new_hash
    artifact.last_synced_at = datetime.now(UTC)
    artifact.current_version += 1
    artifact.file_size_bytes = len(dto.content.encode("utf-8"))
    artifact.external_status = "normal"
    await svc._repo.update(artifact)

    # Create version snapshot
    version = ArtifactVersion(
        artifact_id=artifact_id,
        version_number=artifact.current_version,
        operation_type="snapshot",
        content=dto.content,
    )
    await svc._version_repo.create_version(version)

    return ArtifactEditResponse(
        artifact_id=artifact_id,
        version=f"v{artifact.current_version}",
        has_conflict=has_conflict,
    )


# ------------------------------------------------------------------
# Governance
# ------------------------------------------------------------------
@router.post(
    "/{project_id}/governance/baseline",
    response_model=BaselineResponse,
)
async def create_baseline(
    project_id: str,
    dto: BaselineRequest,
    db: AsyncSession = Depends(get_db),
) -> BaselineResponse:
    """Create a baseline for selected artifacts."""
    for artifact_id in dto.artifact_ids:
        artifact = await db.get(ArtifactFile, artifact_id)
        if artifact is not None:
            artifact.external_status = "normal"
            db.add(artifact)
    await db.commit()

    baseline_id = f"BL-{uuid.uuid4().hex[:8].upper()}"
    return BaselineResponse(
        baseline_id=baseline_id,
        version="v1.0",
        created_at=datetime.now(UTC).isoformat(),
    )


@router.get(
    "/{project_id}/governance/stale-analysis",
    response_model=StaleAnalysisResponse,
)
async def get_stale_analysis(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> StaleAnalysisResponse:
    """Get stale artifacts with impact chains."""
    stmt = select(ArtifactFile).where(
        ArtifactFile.project_id == project_id,
        ArtifactFile.stale_flag == True,  # noqa: E712
    )
    result = await db.execute(stmt)
    artifacts = list(result.scalars().all())

    stale_items = []
    for art in artifacts:
        stale_items.append(
            StaleArtifactItem(
                artifact_id=art.artifact_id,
                artifact_name=art.file_name,
                version=f"v{art.current_version}",
                impact=[
                    StaleImpactItem(
                        type="downstream",
                        target="execution",
                        suggestion="Re-execute affected tasks",
                    )
                ],
            )
        )

    return StaleAnalysisResponse(stale_artifacts=stale_items)


@router.post(
    "/{project_id}/governance/change-request",
    response_model=ChangeRequestResponse,
)
async def create_change_request(
    project_id: str,
    dto: ChangeRequestRequest,
    db: AsyncSession = Depends(get_db),
) -> ChangeRequestResponse:
    """Create a change request for a target artifact."""
    artifact = await db.get(ArtifactFile, dto.target_artifact_id)
    if artifact is not None:
        artifact.stale_flag = True
        db.add(artifact)
        await db.commit()

    cr_id = f"CR-{uuid.uuid4().hex[:8].upper()}"
    return ChangeRequestResponse(
        change_request_id=cr_id,
        status="pending",
    )
