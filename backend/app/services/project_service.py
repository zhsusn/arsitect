"""Project business logic service with dual-track state machine."""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.event_bus import DomainEvent, EventBus, get_event_bus
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.governance.project_governance import ProjectGovernance
from app.infrastructure.database.repositories.project_repo import ProjectRepository
from app.models.artifact import ArtifactFile
from app.models.operation_log import OperationLog
from app.models.project import Project
from app.models.project_path_config import ProjectPathConfig
from app.models.project_stage import ProjectStage
from app.models.size_estimate import SizeEstimate
from app.models.stage_skill_binding import StageSkillBinding
from app.models.template import Template
from app.models.template_stage import TemplateStage
from app.services.stage_orchestrator import StageOrchestrator


class ProjectService:
    """Orchestrates project CRUD and state transitions."""

    def __init__(
        self,
        session: AsyncSession,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize with an async session."""
        self._session = session
        self._repo = ProjectRepository(session)
        self._governance = ProjectGovernance(session)
        self._event_bus = event_bus or get_event_bus()

    async def create_project(
        self,
        *,
        project_id: str,
        project_name: str,
        application_id: str,
        template_level: str,
        project_description: str | None = None,
    ) -> Project:
        """Create a new project with duplicate name check and stage instances."""
        exists = await self._repo.exists_by_name(application_id, project_name)
        if exists:
            raise ConflictError(
                detail=f"Project '{project_name}' already exists in this application"
            )
        created_id = await self._governance.create(
            name=project_name,
            description=project_description or "",
            application_id=application_id,
            template_level=template_level,
        )
        # If caller supplied a specific project_id, replace the generated one.
        if project_id and created_id != project_id:
            proj = await self._repo.get_by_id(created_id)
            if proj is not None:
                proj.project_id = project_id
                await self._session.commit()
                await self._session.refresh(proj)

        proj = await self._repo.get_by_id(project_id or created_id)
        if proj is None:
            raise NotFoundError(detail="Project creation failed")

        await self._initialize_project_stages(proj)
        await self._session.flush()
        await self._initialize_stage_skill_bindings(proj)
        await self._initialize_project_path_config(proj)
        await self._session.commit()
        await self._session.refresh(proj)
        return proj

    async def _initialize_project_stages(self, project: Project) -> None:
        """Create ProjectStage records from the project's template stages."""
        stmt = (
            select(TemplateStage)
            .where(TemplateStage.template_id == project.template_level)
            .order_by(TemplateStage.order_index)
        )
        result = await self._session.execute(stmt)
        template_stages = list(result.scalars().all())
        if not template_stages:
            return

        for ts in template_stages:
            self._session.add(
                ProjectStage(
                    project_stage_id=str(uuid.uuid4()),
                    project_id=project.project_id,
                    stage_id=ts.business_stage_key,
                    order_index=ts.order_index,
                    status="DEFINED",
                    primary_skill_id=ts.primary_skill_id,
                    auxiliary_skill_ids=ts.auxiliary_skill_ids,
                    skippable=ts.skippable,
                    merge_group_id=ts.merge_group_id,
                    is_gate_required=ts.is_gate_required,
                    auto_advance=ts.auto_advance,
                    execution_strategy=project.execution_strategy,
                )
            )

    async def _initialize_stage_skill_bindings(self, project: Project) -> None:
        """Create skill binding snapshots for each project stage."""
        stmt = select(ProjectStage).where(ProjectStage.project_id == project.project_id)
        result = await self._session.execute(stmt)
        stages = list(result.scalars().all())

        for stage in stages:
            if stage.primary_skill_id:
                self._session.add(
                    StageSkillBinding(
                        binding_id=str(uuid.uuid4()),
                        project_stage_id=stage.project_stage_id,
                        skill_id=stage.primary_skill_id,
                        role="primary",
                        execution_order=0,
                        is_optional=False,
                    )
                )
            auxiliary = []
            if stage.auxiliary_skill_ids:
                try:
                    auxiliary = json.loads(stage.auxiliary_skill_ids)
                except json.JSONDecodeError:
                    auxiliary = []
            for idx, skill_id in enumerate(auxiliary, start=1):
                self._session.add(
                    StageSkillBinding(
                        binding_id=str(uuid.uuid4()),
                        project_stage_id=stage.project_stage_id,
                        skill_id=skill_id,
                        role="auxiliary",
                        execution_order=idx,
                        is_optional=False,
                    )
                )

    async def _initialize_project_path_config(self, project: Project) -> None:
        """Persist the complexity route decision for the project."""
        template_record = await self._session.get(Template, project.template_level)
        if template_record is None:
            return

        # Inherit execution strategy and merge policy from template.
        project.execution_strategy = template_record.default_execution_strategy
        project.merge_policy_json = template_record.merge_policy_json

        from sqlalchemy import select

        existing_result = await self._session.execute(
            select(ProjectPathConfig).where(
                ProjectPathConfig.project_id == project.project_id
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing is None:
            self._session.add(
                ProjectPathConfig(
                    config_id=str(uuid.uuid4()),
                    project_id=project.project_id,
                    template_level=project.template_level,
                    execution_strategy=project.execution_strategy,
                    merge_policy_json=project.merge_policy_json
                    or json.dumps({"groups": []}),
                )
            )

    async def get_project(self, project_id: str) -> Project:
        """Fetch a project by ID."""
        proj = await self._repo.get_by_id(project_id)
        if proj is None:
            raise NotFoundError(detail=f"Project '{project_id}' not found")
        return proj

    async def list_projects(
        self,
        application_id: str,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Project], int]:
        """List projects by application."""
        return await self._repo.list_by_application(application_id, page=page, page_size=page_size)

    async def update_project(
        self,
        project_id: str,
        *,
        project_name: str | None = None,
        project_description: str | None = None,
    ) -> Project:
        """Update project info."""
        proj = await self.get_project(project_id)
        if project_name is not None:
            if project_name != proj.project_name:
                exists = await self._repo.exists_by_name(proj.application_id, project_name)
                if exists:
                    raise ConflictError(detail=f"Project name '{project_name}' already exists")
            proj.project_name = project_name
        if project_description is not None:
            proj.project_description = project_description
        return await self._repo.update(proj)

    async def update_execution_strategy(
        self,
        project_id: str,
        *,
        execution_strategy: str,
        reason: str | None = None,
    ) -> dict[str, object]:
        """Update project execution strategy and cascade to pending stages."""
        valid_strategies = {"full_auto", "semi_auto", "full_manual"}
        if execution_strategy not in valid_strategies:
            raise ValidationError(
                detail=f"Invalid execution_strategy '{execution_strategy}'"
            )

        proj = await self.get_project(project_id)
        old_strategy = proj.execution_strategy
        proj.execution_strategy = execution_strategy
        self._session.add(proj)

        path_config_result = await self._session.execute(
            select(ProjectPathConfig).where(
                ProjectPathConfig.project_id == project_id
            )
        )
        path_config = path_config_result.scalar_one_or_none()
        if path_config is not None:
            path_config.execution_strategy = execution_strategy
            self._session.add(path_config)

        stmt = select(ProjectStage).where(
            ProjectStage.project_id == project_id,
            ProjectStage.runtime_status.in_(
                {"not_started", "ready", "blocked"}
            ),
        )
        result = await self._session.execute(stmt)
        updated_stage_ids: list[str] = []
        for stage in result.scalars().all():
            stage.execution_strategy = execution_strategy
            self._session.add(stage)
            updated_stage_ids.append(stage.project_stage_id)

        self._session.add(
            OperationLog(
                log_id=str(uuid.uuid4()),
                project_id=project_id,
                action="EXECUTION_STRATEGY_CHANGED",
                operator_id="system",
                target_type="project",
                target_id=project_id,
                detail=json.dumps(
                    {
                        "old_strategy": old_strategy,
                        "new_strategy": execution_strategy,
                        "reason": reason,
                        "updated_stage_count": len(updated_stage_ids),
                    },
                    ensure_ascii=False,
                ),
            )
        )
        await self._session.commit()
        await self._session.refresh(proj)

        self._event_bus.publish(
            DomainEvent(
                event_type="project.strategy_changed",
                aggregate_id=project_id,
                payload={
                    "project_id": project_id,
                    "execution_strategy": proj.execution_strategy,
                },
            )
        )
        self._broadcast_sse(
            project_id,
            "project.strategy_changed",
            {
                "project_id": project_id,
                "execution_strategy": proj.execution_strategy,
            },
        )

        return {
            "project_id": project_id,
            "execution_strategy": proj.execution_strategy,
            "updated_stage_ids": updated_stage_ids,
        }

    def _broadcast_sse(
        self,
        project_id: str,
        message_type: str,
        payload: dict[str, Any],
    ) -> None:
        """Broadcast an event to connected SSE clients if available."""
        try:
            from app.api.v1.advanced import _get_notification_manager

            manager = _get_notification_manager()
            manager.broadcast(project_id, message_type, payload)
        except Exception:
            pass

    async def archive_project(self, project_id: str) -> Project:
        """Archive a project."""
        await self._governance.archive(project_id)
        proj = await self.get_project(project_id)
        return proj

    async def activate_project(self, project_id: str) -> Project:
        """Activate (confirm) a project from Draft.

        Also freezes all project stages to lock the template configuration and
        initializes the first stage to READY (auto-start for full_auto strategy).
        """
        proj = await self.get_project(project_id)
        await self._governance.activate(project_id, complexity_route=proj.template_level)

        # Freeze all stages
        stmt = select(ProjectStage).where(ProjectStage.project_id == project_id)
        result = await self._session.execute(stmt)
        stages = list(result.scalars().all())
        for stage in stages:
            if not stage.is_frozen:
                stage.is_frozen = True
                if stage.status not in ("EXECUTED", "FROZEN", "ARCHIVED", "REMOVED"):
                    stage.status = "FROZEN"
                self._session.add(stage)
        await self._session.flush()

        # Initialize first non-skipped stage to READY
        first_stage = next((s for s in stages if not s.skippable), None)
        if first_stage is not None and first_stage.runtime_status == "not_started":
            first_stage.runtime_status = "ready"
            proj.current_stage_id = first_stage.project_stage_id
            self._session.add(first_stage)
            self._session.add(proj)
            await self._session.flush()

            if proj.execution_strategy == "full_auto":
                await self._session.commit()
                orchestrator = StageOrchestrator(session=self._session)
                await orchestrator.execute_stage(first_stage.project_stage_id)
                return await self.get_project(project_id)

        await self._session.commit()
        return await self.get_project(project_id)

    async def cancel_project(self, project_id: str) -> Project:
        """Cancel a project (Draft or Active -> Cancelled).

        Delegates state transition to ProjectGovernance.
        """
        proj = await self.get_project(project_id)
        if proj.project_status == "Cancelled":
            raise ConflictError(detail="Project is already cancelled")
        await self._governance.cancel(project_id)
        return await self.get_project(project_id)

    async def get_project_overview(self, project_id: str) -> dict[str, object]:
        """Get aggregated project overview for detail drawer."""
        proj = await self.get_project(project_id)

        # Size estimate
        size_estimate = None
        if proj.size_estimate_id:
            estimate = await self._session.get(SizeEstimate, proj.size_estimate_id)
            if estimate:
                size_estimate = {
                    "estimate_id": estimate.estimate_id,
                    "module_count": estimate.module_count,
                    "interface_count": estimate.interface_count,
                    "page_count": estimate.page_count,
                    "tech_complexity": estimate.tech_complexity,
                    "risk_level": estimate.risk_level,
                    "optimistic_score": estimate.optimistic_score,
                    "expected_score": estimate.expected_score,
                    "conservative_score": estimate.conservative_score,
                    "complexity_level": estimate.complexity_level,
                }

        # Stages
        stages = await self.list_project_stages(project_id)

        # Artifacts (latest 50)
        art_stmt = (
            select(ArtifactFile)
            .where(ArtifactFile.project_id == project_id)
            .order_by(ArtifactFile.created_at.desc())
            .limit(50)
        )
        art_result = await self._session.execute(art_stmt)
        artifacts = [
            {
                "artifact_id": a.artifact_id,
                "file_name": a.file_name,
                "file_type": a.file_type,
                "stage_id": a.stage_id,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in art_result.scalars().all()
        ]

        # Operation logs (latest 20)
        logs = await self.list_operation_logs(project_id, limit=20)

        return {
            "project": proj,
            "size_estimate": size_estimate,
            "stages": stages,
            "artifacts": artifacts,
            "operation_logs": logs,
        }

    async def list_project_stages(self, project_id: str) -> list[dict[str, object]]:
        """List stage progress for a project."""
        stmt = (
            select(ProjectStage, TemplateStage)
            .join(
                TemplateStage,
                ProjectStage.stage_id == TemplateStage.business_stage_key,
                isouter=True,
            )
            .where(ProjectStage.project_id == project_id)
            .order_by(ProjectStage.order_index)
        )
        result = await self._session.execute(stmt)
        stages = []
        runtime_progress_map = {
            "not_started": 0,
            "ready": 0,
            "in_progress": 50,
            "review_pending": 80,
            "gate_pending": 90,
            "passed": 100,
            "blocked": 30,
            "skipped": 100,
        }
        execution_progress_map = {
            "NOT_STARTED": 0,
            "IN_PROGRESS": 50,
            "COMPLETED": 100,
            "BLOCKED": 25,
        }
        for ps, ts in result.all():
            runtime_progress = runtime_progress_map.get(ps.runtime_status, 0)
            execution_progress = execution_progress_map.get(ps.execution_status, 0)
            stages.append(
                {
                    "stage_id": ps.project_stage_id,
                    "stage_name": ts.stage_name if ts else ps.stage_id,
                    "order_index": ps.order_index,
                    "status": ps.status,
                    "runtime_status": ps.runtime_status,
                    "execution_status": ps.execution_status,
                    "progress_percent": max(runtime_progress, execution_progress),
                    "planned_days": None,
                    "elapsed_days": None,
                    "skippable": ps.skippable,
                }
            )
        return stages

    async def list_operation_logs(
        self, project_id: str, *, limit: int = 20
    ) -> list[dict[str, object]]:
        """List recent operation logs for a project."""
        stmt = (
            select(OperationLog)
            .where(OperationLog.project_id == project_id)
            .order_by(OperationLog.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [
            {
                "log_id": log.log_id,
                "action": log.action,
                "operator_id": log.operator_id,
                "target_type": log.target_type,
                "detail": log.detail,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in result.scalars().all()
        ]

    async def cleanup_expired_drafts(self) -> int:
        """Cancel draft projects older than the governance TTL."""
        return await self._governance.cleanup_expired_drafts()

    async def bind_size_estimate(self, project_id: str, estimate_id: str | None) -> Project:
        """Bind or unbind a size estimate to/from a project."""
        proj = await self.get_project(project_id)
        if estimate_id is not None:
            estimate = await self._session.get(SizeEstimate, estimate_id)
            if estimate is None:
                raise NotFoundError(detail=f"Size estimate '{estimate_id}' not found")
        proj.size_estimate_id = estimate_id
        return await self._repo.update(proj)
