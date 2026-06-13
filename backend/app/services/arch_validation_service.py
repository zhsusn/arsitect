"""ArchValidationService — 架构验证与漂移检测."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.c4.baseline_store import C4BaselineStore
from app.c4.dsl_manager import C4DSLManager
from app.c4.renderer import C4Renderer
from app.models.arch_validation_session import ArchValidationSession


class ArchValidationService:
    """Validate architecture DSL against baseline and detect drift."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session.

        Args:
            session: Async SQLAlchemy session.
        """
        self._session = session

    async def trigger_validation(
        self, project_id: str, level: str
    ) -> ArchValidationSession:
        """Trigger a new validation session for a project/level.

        Args:
            project_id: Project identifier.
            level: C4 level (L1-L4).

        Returns:
            Created validation session.
        """
        # Fetch current DSL
        current_dsl = ""
        baseline_store = C4BaselineStore(self._session)
        baseline = await baseline_store.read_current(project_id)

        if baseline:
            if level != "ALL":
                dsl_manager = C4DSLManager(baseline_store)
                workspace = await dsl_manager.read_workspace(project_id)
                if workspace:
                    renderer = C4Renderer(dsl_manager)
                    if level == "L1":
                        current_dsl = renderer._render_l1(workspace).mermaid_code
                    elif level == "L2":
                        current_dsl = renderer._render_l2(workspace).mermaid_code
                    elif level == "L3":
                        current_dsl = renderer._render_l3(workspace).mermaid_code
                    else:
                        current_dsl = renderer._render_l2(workspace).mermaid_code
            else:
                current_dsl = baseline.dsl_content

        # Find or create baseline
        baseline_result = await self._session.execute(
            select(ArchValidationSession)
            .where(
                ArchValidationSession.project_id == project_id,
                ArchValidationSession.level == level,
            )
            .order_by(ArchValidationSession.created_at.desc())
        )
        last_session = baseline_result.scalar_one_or_none()
        baseline_dsl = last_session.baseline_dsl if last_session else current_dsl

        diff_summary = self._diff_dsl(baseline_dsl, current_dsl)
        status = "DRIFT_DETECTED" if diff_summary else "NO_DRIFT"

        session = ArchValidationSession(
            project_id=project_id,
            level=level,
            baseline_dsl=baseline_dsl,
            current_dsl=current_dsl,
            diff_summary=diff_summary,
            status=status,
            completed_at=datetime.now(UTC),
        )
        self._session.add(session)
        await self._session.flush()
        await self._session.commit()
        return session

    async def get_diffs(self, project_id: str) -> list[ArchValidationSession]:
        """Get all validation diffs for a project.

        Args:
            project_id: Project identifier.

        Returns:
            List of validation sessions ordered by created_at desc.
        """
        result = await self._session.execute(
            select(ArchValidationSession)
            .where(ArchValidationSession.project_id == project_id)
            .order_by(ArchValidationSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_baseline(self, project_id: str, level: str) -> ArchValidationSession:
        """Update baseline to current DSL.

        Args:
            project_id: Project identifier.
            level: C4 level (L1-L4).

        Returns:
            Created baseline session.
        """
        current_dsl = ""
        baseline_store = C4BaselineStore(self._session)
        baseline = await baseline_store.read_current(project_id)

        if baseline:
            if level != "ALL":
                dsl_manager = C4DSLManager(baseline_store)
                workspace = await dsl_manager.read_workspace(project_id)
                if workspace:
                    renderer = C4Renderer(dsl_manager)
                    if level == "L1":
                        current_dsl = renderer._render_l1(workspace).mermaid_code
                    elif level == "L2":
                        current_dsl = renderer._render_l2(workspace).mermaid_code
                    elif level == "L3":
                        current_dsl = renderer._render_l3(workspace).mermaid_code
                    else:
                        current_dsl = renderer._render_l2(workspace).mermaid_code
            else:
                current_dsl = baseline.dsl_content

        session = ArchValidationSession(
            project_id=project_id,
            level=level,
            baseline_dsl=current_dsl,
            current_dsl=current_dsl,
            diff_summary=None,
            status="BASELINE_UPDATED",
            completed_at=datetime.now(UTC),
        )
        self._session.add(session)
        await self._session.flush()
        await self._session.commit()
        return session

    @staticmethod
    def _diff_dsl(baseline: str, current: str) -> str | None:
        """Simple line-based diff summary.

        Args:
            baseline: Baseline DSL text.
            current: Current DSL text.

        Returns:
            Diff summary string or None if identical.
        """
        if baseline == current:
            return None
        base_lines = baseline.splitlines()
        curr_lines = current.splitlines()
        added = sum(1 for line in curr_lines if line not in base_lines)
        removed = sum(1 for line in base_lines if line not in curr_lines)
        return f"+{added}/-{removed} lines changed"
