"""UserStoryService — CRUD for user stories."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.user_story import UserStory


class UserStoryService:
    """Handle user story lifecycle."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session.

        Args:
            session: Async SQLAlchemy session.
        """
        self._session = session

    async def create_story(
        self,
        project_id: str,
        title: str,
        description: str | None,
        acceptance_criteria: str | None,
        page_desc: str | None,
        priority: str,
        status: str,
    ) -> UserStory:
        """Create a new user story."""
        story = UserStory(
            story_id=f"us-{uuid.uuid4()}",
            project_id=project_id,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            page_desc=page_desc,
            priority=priority,
            status=status,
        )
        self._session.add(story)
        await self._session.flush()
        await self._session.commit()
        return story

    async def get_story(self, story_id: str) -> UserStory:
        """Fetch a user story by ID."""
        result = await self._session.execute(
            select(UserStory).where(UserStory.story_id == story_id)
        )
        story = result.scalar_one_or_none()
        if story is None:
            raise NotFoundError(detail=f"UserStory '{story_id}' not found")
        return story

    async def list_stories(self, project_id: str) -> list[UserStory]:
        """List user stories for a project."""
        result = await self._session.execute(
            select(UserStory)
            .where(UserStory.project_id == project_id)
            .order_by(UserStory.created_at.desc())
        )
        return list(result.scalars().all())

    async def find_by_title(self, project_id: str, title: str) -> UserStory | None:
        """Find a user story by title within a project."""
        result = await self._session.execute(
            select(UserStory)
            .where(UserStory.project_id == project_id)
            .where(UserStory.title == title)
        )
        return result.scalar_one_or_none()

    async def update_story(
        self, story_id: str, updates: dict[str, Any]
    ) -> UserStory:
        """Update an existing user story."""
        story = await self.get_story(story_id)
        for key, value in updates.items():
            if value is not None and hasattr(story, key):
                setattr(story, key, value)
        await self._session.flush()
        await self._session.commit()
        return story

    async def delete_story(self, story_id: str) -> None:
        """Delete a user story."""
        story = await self.get_story(story_id)
        await self._session.delete(story)
        await self._session.flush()
        await self._session.commit()
