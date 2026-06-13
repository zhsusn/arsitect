"""UserStory router — CRUD for user stories."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db
from app.schemas.user_story import (
    UserStoryCreateDTO,
    UserStoryImportResultDTO,
    UserStoryResponseDTO,
    UserStoryUpdateDTO,
)
from app.services.requirement_import_service import RequirementImportService
from app.services.user_story_service import UserStoryService

router = APIRouter(tags=["user-stories"])


@router.post(
    "/projects/{project_id}/user-stories",
    response_model=UserStoryResponseDTO,
    status_code=201,
)
async def create_user_story(
    project_id: str,
    dto: UserStoryCreateDTO,
    db: AsyncSession = Depends(get_db),
) -> UserStoryResponseDTO:
    """Create a new user story for a project."""
    svc = UserStoryService(db)
    story = await svc.create_story(
        project_id=project_id,
        title=dto.title,
        description=dto.description,
        acceptance_criteria=dto.acceptance_criteria,
        page_desc=dto.page_desc,
        priority=dto.priority,
        status=dto.status,
    )
    return UserStoryResponseDTO(
        story_id=story.story_id,
        project_id=story.project_id,
        title=story.title,
        description=story.description,
        acceptance_criteria=story.acceptance_criteria,
        page_desc=story.page_desc,
        priority=story.priority,
        status=story.status,
        created_at=story.created_at,
        updated_at=story.updated_at,
    )


@router.get(
    "/projects/{project_id}/user-stories",
    response_model=list[UserStoryResponseDTO],
)
async def list_user_stories(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[UserStoryResponseDTO]:
    """List user stories for a project."""
    svc = UserStoryService(db)
    stories = await svc.list_stories(project_id)
    return [
        UserStoryResponseDTO(
            story_id=s.story_id,
            project_id=s.project_id,
            title=s.title,
            description=s.description,
            acceptance_criteria=s.acceptance_criteria,
            page_desc=s.page_desc,
            priority=s.priority,
            status=s.status,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in stories
    ]


@router.get(
    "/user-stories/{story_id}",
    response_model=UserStoryResponseDTO,
)
async def get_user_story(
    story_id: str,
    db: AsyncSession = Depends(get_db),
) -> UserStoryResponseDTO:
    """Get a single user story by ID."""
    svc = UserStoryService(db)
    story = await svc.get_story(story_id)
    return UserStoryResponseDTO(
        story_id=story.story_id,
        project_id=story.project_id,
        title=story.title,
        description=story.description,
        acceptance_criteria=story.acceptance_criteria,
        page_desc=story.page_desc,
        priority=story.priority,
        status=story.status,
        created_at=story.created_at,
        updated_at=story.updated_at,
    )


@router.patch(
    "/user-stories/{story_id}",
    response_model=UserStoryResponseDTO,
)
async def update_user_story(
    story_id: str,
    dto: UserStoryUpdateDTO,
    db: AsyncSession = Depends(get_db),
) -> UserStoryResponseDTO:
    """Update a user story."""
    svc = UserStoryService(db)
    story = await svc.update_story(story_id, dto.model_dump(exclude_unset=True))
    return UserStoryResponseDTO(
        story_id=story.story_id,
        project_id=story.project_id,
        title=story.title,
        description=story.description,
        acceptance_criteria=story.acceptance_criteria,
        page_desc=story.page_desc,
        priority=story.priority,
        status=story.status,
        created_at=story.created_at,
        updated_at=story.updated_at,
    )


@router.post(
    "/projects/{project_id}/user-stories/import-from-requirements",
    response_model=UserStoryImportResultDTO,
    status_code=201,
)
async def import_user_stories_from_requirements(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> UserStoryImportResultDTO:
    """Import user stories from OpenSpec detailed requirement artifacts."""
    svc = RequirementImportService(db)
    result = await svc.import_user_stories(project_id)
    return UserStoryImportResultDTO(
        imported_count=result["imported_count"],
        skipped_count=result["skipped_count"],
        stories=result["stories"],
    )


@router.delete(
    "/user-stories/{story_id}",
    status_code=204,
    response_model=None,
)
async def delete_user_story(
    story_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a user story."""
    svc = UserStoryService(db)
    await svc.delete_story(story_id)
