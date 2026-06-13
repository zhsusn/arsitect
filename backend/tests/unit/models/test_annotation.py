"""Tests for Annotation model."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.annotation import Annotation


@pytest.mark.asyncio
async def test_annotation_crud() -> None:
    """Can create and fetch an annotation."""
    async with AsyncSessionLocal() as session:
        from app.models.project_stage import ProjectStage

        stage = ProjectStage(
            project_stage_id="stage-001",
            project_id="proj-001",
            stage_id="s-001",
            order_index=1,
            status="DEFINED",
        )
        session.add(stage)
        await session.flush()

        ann = Annotation(
            annotation_id="ann-001",
            stage_id="stage-001",
            author="tester",
            content="Review comment",
            annotation_type="review",
            status="REVIEW_PENDING",
        )
        session.add(ann)
        await session.commit()

        result = await session.execute(
            select(Annotation).where(Annotation.annotation_id == "ann-001")
        )
        fetched = result.scalar_one()
        assert fetched.content == "Review comment"
        assert fetched.status == "REVIEW_PENDING"
