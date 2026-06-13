"""Project business logic service with dual-track state machine."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.governance.project_governance import ProjectGovernance
from app.infrastructure.database.repositories.project_repo import ProjectRepository
from app.models.artifact import ArtifactFile
from app.models.operation_log import OperationLog
from app.models.project import Project
from app.models.project_stage import ProjectStage
from app.models.size_estimate import SizeEstimate
from app.models.template_stage import TemplateStage


class ProjectService:
    """Orchestrates project CRUD and state transitions."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session
        self._repo = ProjectRepository(session)
        self._governance = ProjectGovernance(session)

    async def create_project(
        self,
        *,
        project_id: str,
        project_name: str,
        application_id: str,
        template_level: str,
        project_description: str | None = None,
    ) -> Project:
        """Create a new project with duplicate name check."""
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
                return proj
        proj = await self._repo.get_by_id(created_id)
        if proj is None:
            raise NotFoundError(detail="Project creation failed")
        await self._session.commit()
        await self._session.refresh(proj)
        return proj

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
        return await self._repo.list_by_application(
            application_id, page=page, page_size=page_size
        )

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
                exists = await self._repo.exists_by_name(
                    proj.application_id, project_name
                )
                if exists:
                    raise ConflictError(
                        detail=f"Project name '{project_name}' already exists"
                    )
            proj.project_name = project_name
        if project_description is not None:
            proj.project_description = project_description
        return await self._repo.update(proj)

    async def archive_project(self, project_id: str) -> Project:
        """Archive a project."""
        await self._governance.archive(project_id)
        proj = await self.get_project(project_id)
        return proj

    async def activate_project(self, project_id: str) -> Project:
        """Activate (confirm) a project from Draft.

        Also freezes all project stages to lock the template configuration.
        """
        proj = await self.get_project(project_id)
        await self._governance.activate(
            project_id, complexity_route=proj.template_level
        )

        # Freeze all stages
        stmt = select(ProjectStage).where(ProjectStage.project_id == project_id)
        result = await self._session.execute(stmt)
        for stage in result.scalars().all():
            if not stage.is_frozen:
                stage.is_frozen = True
                if stage.status not in ("EXECUTED", "FROZEN", "ARCHIVED", "REMOVED"):
                    stage.status = "FROZEN"
                self._session.add(stage)
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
                ProjectStage.stage_id == TemplateStage.stage_id,
                isouter=True,
            )
            .where(ProjectStage.project_id == project_id)
            .order_by(ProjectStage.order_index)
        )
        result = await self._session.execute(stmt)
        stages = []
        for ps, ts in result.all():
            # Derive progress from execution_status
            progress_map = {
                "NOT_STARTED": 0,
                "IN_PROGRESS": 50,
                "COMPLETED": 100,
                "BLOCKED": 25,
            }
            stages.append(
                {
                    "stage_id": ps.project_stage_id,
                    "stage_name": ts.stage_name if ts else ps.stage_id,
                    "order_index": ps.order_index,
                    "status": ps.status,
                    "execution_status": ps.execution_status,
                    "progress_percent": progress_map.get(ps.execution_status, 0),
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

    async def bind_size_estimate(
        self, project_id: str, estimate_id: str | None
    ) -> Project:
        """Bind or unbind a size estimate to/from a project."""
        proj = await self.get_project(project_id)
        if estimate_id is not None:
            estimate = await self._session.get(SizeEstimate, estimate_id)
            if estimate is None:
                raise NotFoundError(
                    detail=f"Size estimate '{estimate_id}' not found"
                )
        proj.size_estimate_id = estimate_id
        return await self._repo.update(proj)
