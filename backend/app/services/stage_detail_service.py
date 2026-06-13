"""Stage detail aggregation service."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.annotation import Annotation
from app.models.project_stage import ProjectStage


class StageDetailService:
    """Aggregate stage details: stage info, annotations, review status, gate, artifacts."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session

    async def get_stage_detail(self, stage_id: str) -> dict[str, Any] | None:
        """Return aggregated detail for a stage."""
        stage = await self._session.get(ProjectStage, stage_id)
        if stage is None:
            return None

        # Annotations
        ann_stmt = (
            select(Annotation)
            .where(Annotation.stage_id == stage_id)
            .order_by(Annotation.annotation_id.desc())
        )
        ann_result = await self._session.execute(ann_stmt)
        annotations = list(ann_result.scalars().all())

        # Review status derived from annotations
        review_status = "clean"
        pending = [a for a in annotations if a.status == "REVIEW_PENDING"]
        if pending:
            review_status = "pending_review"

        # Gate and artifacts are MVP placeholders until their tables are created
        return {
            "stage": stage,
            "annotations": annotations,
            "review_status": review_status,
            "gate": None,
            "artifacts": [],
        }
