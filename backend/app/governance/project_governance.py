"""Project governance — state machine, CRUD and lifecycle rules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectState

# Map design-time enum values (lowercase) to existing DB title-case strings.
_STATE_TO_DB: dict[ProjectState, str] = {
    ProjectState.DRAFT: "Draft",
    ProjectState.ACTIVE: "Active",
    ProjectState.ARCHIVED: "Archived",
    ProjectState.CANCELLED: "Cancelled",
}
_DB_TO_STATE: dict[str, ProjectState] = {v: k for k, v in _STATE_TO_DB.items()}


@dataclass
class ProjectDTO:
    """Lightweight project data transfer object."""

    id: str
    name: str
    state: str
    complexity_route: str | None
    created_at: datetime
    module_count: int = 0


class ProjectGovernance:
    """Project governance.

    Responsibilities:
    1. Project CRUD.
    2. State transition control (Draft/Active/Archived/Cancelled).
    3. Automatic cleanup of expired Draft projects.
    4. Complexity route management.
    """

    # Draft auto-cleanup TTL.
    DRAFT_TTL_DAYS = 7

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with an async database session."""
        self.db = db

    async def create(
        self,
        name: str,
        description: str = "",
        *,
        application_id: str,
        template_level: str = "Standard",
    ) -> str:
        """Create a new project (initial state is DRAFT).

        Args:
            name: Project name.
            description: Optional project description.
            application_id: Required application identifier.
            template_level: Template level, defaults to Standard.

        Returns:
            The newly created project ID.
        """
        project = Project(
            project_name=name,
            project_description=description,
            project_status=_STATE_TO_DB[ProjectState.DRAFT],
            application_id=application_id,
            template_level=template_level,
            risk_level="None",
            progress_percent=0,
        )
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return str(project.project_id)

    async def get(self, project_id: str) -> ProjectDTO | None:
        """Fetch a project by ID."""
        project = await self._get_entity(project_id)
        return self._to_dto(project)

    async def list(
        self,
        state: ProjectState | None = None,
        application_id: str | None = None,
    ) -> list[ProjectDTO]:
        """List projects, optionally filtered by state and application."""
        query = select(Project)
        if state is not None:
            query = query.where(Project.project_status == _STATE_TO_DB[state])
        if application_id is not None:
            query = query.where(Project.application_id == application_id)
        result = await self.db.execute(query.order_by(Project.created_at.desc()))
        return [self._to_dto(p) for p in result.scalars().all()]

    # ============================================================
    # State transitions
    # ============================================================
    async def activate(self, project_id: str, complexity_route: str) -> bool:
        """Draft -> Active (formal project confirmation)."""
        project = await self._get_entity(project_id)
        self._require_state(project, ProjectState.DRAFT)
        project.project_status = _STATE_TO_DB[ProjectState.ACTIVE]
        # Persist the chosen complexity route as the project's template level.
        project.template_level = self._normalize_template_level(complexity_route)
        await self.db.flush()
        return True

    async def archive(self, project_id: str) -> bool:
        """Active -> Archived."""
        project = await self._get_entity(project_id)
        self._require_state(project, ProjectState.ACTIVE)
        project.project_status = _STATE_TO_DB[ProjectState.ARCHIVED]
        await self.db.flush()
        return True

    async def cancel(self, project_id: str) -> bool:
        """Draft/Active -> Cancelled."""
        project = await self._get_entity(project_id)
        current = self._current_state(project)
        if current in (ProjectState.ARCHIVED, ProjectState.CANCELLED):
            raise ValueError(f"Cannot cancel: state is {current.value}")
        project.project_status = _STATE_TO_DB[ProjectState.CANCELLED]
        await self.db.flush()
        return True

    # ============================================================
    # Draft auto-cleanup
    # ============================================================
    async def cleanup_expired_drafts(self) -> int:
        """Cancel Draft projects older than DRAFT_TTL_DAYS."""
        cutoff = datetime.now(UTC) - timedelta(days=self.DRAFT_TTL_DAYS)
        result = await self.db.execute(
            select(Project).where(
                Project.project_status == _STATE_TO_DB[ProjectState.DRAFT],
                Project.created_at < cutoff,
            )
        )
        expired = result.scalars().all()
        for project in expired:
            project.project_status = _STATE_TO_DB[ProjectState.CANCELLED]
        await self.db.flush()
        return len(expired)

    # ============================================================
    # Helpers
    # ============================================================
    async def _get_entity(self, project_id: str) -> Project:
        result = await self.db.execute(
            select(Project).where(Project.project_id == project_id)
        )
        project = result.scalar_one_or_none()
        if project is None:
            raise ValueError(f"Project not found: {project_id}")
        return project

    @staticmethod
    def _current_state(project: Project) -> ProjectState:
        status = project.project_status
        state = _DB_TO_STATE.get(status)
        if state is None:
            raise ValueError(f"Unknown project status: {status}")
        return state

    @staticmethod
    def _require_state(project: Project, expected: ProjectState) -> None:
        current = ProjectGovernance._current_state(project)
        if current != expected:
            raise ValueError(
                f"Expected state {expected.value}, current state is {current.value}"
            )

    @staticmethod
    def _normalize_template_level(route: str) -> str:
        """Normalize complexity route / template level to title-case DB values."""
        mapping = {
            "trivial": "Trivial",
            "light": "Light",
            "standard": "Standard",
            "deep": "Deep",
            "Trivial": "Trivial",
            "Light": "Light",
            "Standard": "Standard",
            "Deep": "Deep",
        }
        normalized = mapping.get(route)
        if normalized is None:
            raise ValueError(f"Invalid complexity route: {route}")
        return normalized

    @staticmethod
    def _to_dto(project: Project) -> ProjectDTO:
        state = ProjectGovernance._current_state(project)
        return ProjectDTO(
            id=str(project.project_id),
            name=project.project_name,
            state=state.value,
            complexity_route=project.template_level,
            created_at=project.created_at,
            module_count=0,
        )
