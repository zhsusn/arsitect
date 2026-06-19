"""Execution router — tasks and issues."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.infrastructure.database.session import get_db
from app.schemas.execution_issue import (
    IssueCreateDTO,
    IssueFeedbackDTO,
    IssueFeedbackToArchitectureRequestDTO,
    IssueFeedbackToArchitectureResponseDTO,
    IssueResponseDTO,
)
from app.schemas.execution_task import (
    MarkBugRequestDTO,
    MarkBugResponseDTO,
    TaskAutoGenerateRequestDTO,
    TaskAutoGenerateResponseDTO,
    TaskCreateDTO,
    TaskResponseDTO,
    TaskUpdateDTO,
)
from app.services.execution_issue_service import ExecutionIssueService
from app.services.task_center_service import TaskCenterService

router = APIRouter(prefix="/execution", tags=["execution"])


# ------------------------------------------------------------------
# Tasks
# ------------------------------------------------------------------
@router.get("/{project_id}/tasks", response_model=list[TaskResponseDTO])
async def get_tasks(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[TaskResponseDTO]:
    """Get all execution tasks for a project."""
    svc = TaskCenterService(db)
    tasks = await svc.get_tasks(project_id)
    return [TaskResponseDTO.model_validate(t) for t in tasks]


@router.get("/{project_id}/tasks/{task_id}", response_model=TaskResponseDTO)
async def get_task(
    project_id: str,
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> TaskResponseDTO:
    """Get a single execution task."""
    svc = TaskCenterService(db)
    task = await svc.get_task_by_id(task_id)
    return TaskResponseDTO.model_validate(task)


@router.post(
    "/{project_id}/tasks",
    response_model=TaskResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    project_id: str,
    dto: TaskCreateDTO,
    db: AsyncSession = Depends(get_db),
) -> TaskResponseDTO:
    """Create a new execution task."""
    svc = TaskCenterService(db)
    task = await svc.create_task(
        project_id=project_id,
        name=dto.name,
        type=dto.type,
        input_artifacts=dto.input_artifacts,
        assigned_skill_id=dto.assigned_skill_id,
        parent_module=dto.parent_module,
        output_artifact_path=dto.output_artifact_path,
    )
    return TaskResponseDTO.model_validate(task)


@router.post(
    "/{project_id}/tasks/auto-generate",
    response_model=TaskAutoGenerateResponseDTO,
)
async def auto_generate_tasks(
    project_id: str,
    dto: TaskAutoGenerateRequestDTO,
    db: AsyncSession = Depends(get_db),
) -> TaskAutoGenerateResponseDTO:
    """Auto-generate tasks from design artifacts."""
    svc = TaskCenterService(db)
    tasks = await svc.auto_generate_tasks(project_id, dto.design_artifact_ids)
    return TaskAutoGenerateResponseDTO(
        tasks=[TaskResponseDTO.model_validate(t) for t in tasks]
    )


@router.patch("/{project_id}/tasks/{task_id}", response_model=TaskResponseDTO)
async def update_task_status(
    project_id: str,
    task_id: str,
    dto: TaskUpdateDTO,
    db: AsyncSession = Depends(get_db),
) -> TaskResponseDTO:
    """Update task status."""
    svc = TaskCenterService(db)
    task = await svc.update_task_status(
        task_id,
        status=dto.status or "pending",
        output_artifact_path=dto.output_artifact_path,
    )
    return TaskResponseDTO.model_validate(task)


@router.post("/{project_id}/tasks/{task_id}/execute", response_model=TaskResponseDTO)
async def execute_task(
    project_id: str,
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> TaskResponseDTO:
    """Execute a task."""
    svc = TaskCenterService(db)
    task = await svc.execute_task(task_id)
    return TaskResponseDTO.model_validate(task)


@router.post("/{project_id}/tasks/{task_id}/retry", response_model=TaskResponseDTO)
async def retry_task(
    project_id: str,
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> TaskResponseDTO:
    """Retry a failed task."""
    svc = TaskCenterService(db)
    task = await svc.retry_task(task_id)
    return TaskResponseDTO.model_validate(task)


@router.post(
    "/{project_id}/tasks/{task_id}/mark-bug",
    response_model=MarkBugResponseDTO,
)
async def mark_bug(
    project_id: str,
    task_id: str,
    dto: MarkBugRequestDTO,
    db: AsyncSession = Depends(get_db),
) -> MarkBugResponseDTO:
    """Mark a failed task as a bug and create an issue."""
    svc = TaskCenterService(db)
    task, issue = await svc.mark_as_bug(task_id, dto.error_log, dto.issue_type)
    return MarkBugResponseDTO(
        task_id=task.task_id,
        issue_id=issue.issue_id,
    )


# ------------------------------------------------------------------
# Issues
# ------------------------------------------------------------------
@router.get("/{project_id}/issues", response_model=list[IssueResponseDTO])
async def get_issues(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[IssueResponseDTO]:
    """Get all execution issues for a project."""
    svc = ExecutionIssueService(db)
    issues = await svc.get_issues(project_id)
    return [IssueResponseDTO.model_validate(i) for i in issues]


@router.post(
    "/{project_id}/issues",
    response_model=IssueResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_issue(
    project_id: str,
    dto: IssueCreateDTO,
    db: AsyncSession = Depends(get_db),
) -> IssueResponseDTO:
    """Create a new execution issue."""
    svc = ExecutionIssueService(db)
    issue = await svc.create_issue(
        project_id=project_id,
        task_id=dto.task_id,
        issue_type=dto.issue_type,
        error_log=dto.error_log,
        related_artifacts=dto.related_artifacts,
        suggested_action=dto.suggested_action,
        target_artifact_id=dto.target_artifact_id,
        change_request_id=dto.change_request_id,
    )
    return IssueResponseDTO.model_validate(issue)


@router.patch(
    "/{project_id}/issues/{issue_id}/feedback",
    response_model=IssueResponseDTO,
)
async def feedback_to_architecture(
    project_id: str,
    issue_id: str,
    dto: IssueFeedbackDTO,
    db: AsyncSession = Depends(get_db),
) -> IssueResponseDTO:
    """Provide feedback to architecture for an issue."""
    svc = ExecutionIssueService(db)
    issue = await svc.feedback_to_architecture(issue_id, dto.feedback_to_architecture)
    return IssueResponseDTO.model_validate(issue)


@router.post(
    "/{project_id}/issues/{issue_id}/feedback-to-architecture",
    response_model=IssueFeedbackToArchitectureResponseDTO,
)
async def feedback_to_architecture_post(
    project_id: str,
    issue_id: str,
    dto: IssueFeedbackToArchitectureRequestDTO,
    db: AsyncSession = Depends(get_db),
) -> IssueFeedbackToArchitectureResponseDTO:
    """Feedback an issue to architecture and create a change request."""
    svc = ExecutionIssueService(db)
    issue = await svc.feedback_to_architecture(
        issue_id,
        target_artifact_id=dto.target_artifact_id,
        change_description=dto.change_description,
    )
    return IssueFeedbackToArchitectureResponseDTO(
        issue_id=issue.issue_id,
        change_request_id=issue.change_request_id or "",
        status=issue.status,
    )
