"""Annotation service — CRUD and red-dot (unread) logic."""

from __future__ import annotations

from datetime import UTC

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.annotation import Annotation


class AnnotationService:
    """Business logic for stage annotations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session

    async def list_by_stage(self, stage_id: str) -> list[Annotation]:
        """List annotations for a stage, newest first."""
        stmt = (
            select(Annotation)
            .where(Annotation.stage_id == stage_id)
            .order_by(Annotation.annotation_id.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        *,
        annotation_id: str,
        stage_id: str,
        author: str,
        content: str,
        annotation_type: str = "comment",
        status: str = "REVIEW_PENDING",
    ) -> Annotation:
        """Create a new annotation."""
        ann = Annotation(
            annotation_id=annotation_id,
            stage_id=stage_id,
            author=author,
            content=content,
            annotation_type=annotation_type,
            status=status,
        )
        self._session.add(ann)
        await self._session.commit()
        await self._session.refresh(ann)
        return ann

    async def update(
        self,
        annotation_id: str,
        content: str,
    ) -> Annotation | None:
        """Update annotation content."""
        ann = await self._session.get(Annotation, annotation_id)
        if ann is None:
            return None
        ann.content = content
        await self._session.commit()
        await self._session.refresh(ann)
        return ann

    async def delete(self, annotation_id: str) -> bool:
        """Delete an annotation."""
        ann = await self._session.get(Annotation, annotation_id)
        if ann is None:
            return False
        await self._session.delete(ann)
        await self._session.commit()
        return True

    async def has_unread_reviews(self, stage_id: str) -> bool:
        """Red-dot logic: True if REVIEW_PENDING and not yet viewed."""
        stmt = (
            select(func.count())
            .select_from(Annotation)
            .where(
                Annotation.stage_id == stage_id,
                Annotation.status == "REVIEW_PENDING",
                Annotation.viewed_at.is_(None),
            )
        )
        count = await self._session.scalar(stmt) or 0
        return count > 0

    async def mark_viewed(self, stage_id: str) -> None:
        """Mark all pending annotations for a stage as viewed."""
        from datetime import datetime

        stmt = select(Annotation).where(
            Annotation.stage_id == stage_id,
            Annotation.status == "REVIEW_PENDING",
            Annotation.viewed_at.is_(None),
        )
        result = await self._session.execute(stmt)
        for ann in result.scalars().all():
            ann.viewed_at = datetime.now(UTC).isoformat()
        await self._session.commit()
