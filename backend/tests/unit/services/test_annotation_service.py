"""Tests for AnnotationService."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.infrastructure.database.session import AsyncSessionLocal
from app.services.annotation_service import AnnotationService


class TestAnnotationService:
    """AnnotationService tests."""

    @pytest.fixture
    async def clean_db(self):
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM annotations"))
            await session.execute(text("DELETE FROM project_stages"))
            await session.commit()

            from app.models.project_stage import ProjectStage

            stage = ProjectStage(
                project_stage_id="stage-001",
                project_id="proj-001",
                stage_id="s-001",
                order_index=1,
                status="DEFINED",
            )
            session.add(stage)
            await session.commit()
            yield session
            await session.execute(text("DELETE FROM annotations"))
            await session.execute(text("DELETE FROM project_stages"))
            await session.commit()

    @pytest.mark.asyncio
    async def test_create_and_list(self, clean_db) -> None:
        svc = AnnotationService(clean_db)
        ann = await svc.create(
            annotation_id="ann-001",
            stage_id="stage-001",
            author="alice",
            content="First comment",
        )
        assert ann.annotation_id == "ann-001"

        items = await svc.list_by_stage("stage-001")
        assert len(items) == 1
        assert items[0].content == "First comment"

    @pytest.mark.asyncio
    async def test_update(self, clean_db) -> None:
        svc = AnnotationService(clean_db)
        await svc.create(
            annotation_id="ann-002",
            stage_id="stage-001",
            author="alice",
            content="Old",
        )
        updated = await svc.update("ann-002", "New")
        assert updated is not None
        assert updated.content == "New"

    @pytest.mark.asyncio
    async def test_delete(self, clean_db) -> None:
        svc = AnnotationService(clean_db)
        await svc.create(
            annotation_id="ann-003",
            stage_id="stage-001",
            author="alice",
            content="To delete",
        )
        assert await svc.delete("ann-003") is True
        assert await svc.delete("ann-003") is False

    @pytest.mark.asyncio
    async def test_has_unread_reviews(self, clean_db) -> None:
        svc = AnnotationService(clean_db)
        await svc.create(
            annotation_id="ann-004",
            stage_id="stage-001",
            author="reviewer",
            content="Issue found",
            status="REVIEW_PENDING",
        )
        assert await svc.has_unread_reviews("stage-001") is True
        await svc.mark_viewed("stage-001")
        assert await svc.has_unread_reviews("stage-001") is False
