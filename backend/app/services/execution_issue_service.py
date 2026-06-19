"""Execution issue business logic service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.infrastructure.database.repositories.execution_issue_repo import ExecutionIssueRepository
from app.models.execution_issue import ExecutionIssue


class ExecutionIssueService:
    """Orchestrates execution issue CRUD and feedback."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session
        self._repo = ExecutionIssueRepository(session)

    async def get_issues(self, project_id: str) -> list[ExecutionIssue]:
        """Get all execution issues for a project."""
        return await self._repo.get_by_project(project_id)

    async def get_issue_by_id(self, issue_id: str) -> ExecutionIssue:
        """Get a single execution issue by ID."""
        issue = await self._repo.get_by_id(issue_id)
        if issue is None:
            raise NotFoundError(detail=f"Issue '{issue_id}' not found")
        return issue

    async def create_issue(
        self,
        project_id: str,
        task_id: str | None,
        issue_type: str,
        error_log: str | None = None,
        related_artifacts: list[str] | None = None,
        suggested_action: str | None = None,
        target_artifact_id: str | None = None,
        change_request_id: str | None = None,
    ) -> ExecutionIssue:
        """Create a new execution issue."""
        valid_types = {"compile_error", "test_failure", "arch_mismatch", "interface_mismatch", "other"}
        if issue_type not in valid_types:
            raise ValidationError(detail=f"Invalid issue type '{issue_type}'")

        issue = ExecutionIssue(
            issue_id=str(uuid.uuid4()),
            project_id=project_id,
            task_id=task_id,
            issue_type=issue_type,
            error_log=error_log,
            related_artifacts=related_artifacts,
            suggested_action=suggested_action,
            target_artifact_id=target_artifact_id,
            change_request_id=change_request_id,
            status="open",
        )
        return await self._repo.create(issue)

    async def feedback_to_architecture(
        self,
        issue_id: str,
        feedback: bool = True,
        target_artifact_id: str | None = None,
        change_description: str | None = None,
    ) -> ExecutionIssue:
        """Mark issue as feedback to architecture and optionally create a change request."""
        issue = await self.get_issue_by_id(issue_id)
        issue.feedback_to_architecture = feedback
        if feedback and target_artifact_id:
            issue.target_artifact_id = target_artifact_id
            issue.change_request_id = f"CR-{uuid.uuid4().hex[:8].upper()}"
        issue.updated_at = datetime.now(UTC)
        return await self._repo.update(issue)
