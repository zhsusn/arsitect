"""Tests for StageDetailService."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.annotation import Annotation
from app.models.project_stage import ProjectStage
from app.services.stage_detail_service import StageDetailService


class TestStageDetailService:
    """StageDetailService tests."""

    @pytest.fixture
    async def clean_db(self):
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM annotations"))
            await session.execute(text("DELETE FROM project_stages"))
            await session.commit()

            stage = ProjectStage(
                project_stage_id="stage-sd",
                project_id="proj-sd",
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
    async def test_get_stage_detail(self, clean_db) -> None:
        svc = StageDetailService(clean_db)
        detail = await svc.get_stage_detail("stage-sd")
        assert detail is not None
        assert detail["stage"].project_stage_id == "stage-sd"
        assert detail["review_status"] == "clean"
        assert detail["annotations"] == []

    @pytest.mark.asyncio
    async def test_get_stage_detail_with_pending_review(self, clean_db) -> None:
        clean_db.add(
            Annotation(
                annotation_id="ann-sd",
                stage_id="stage-sd",
                author="reviewer",
                content="Issue",
                status="REVIEW_PENDING",
            )
        )
        await clean_db.commit()

        svc = StageDetailService(clean_db)
        detail = await svc.get_stage_detail("stage-sd")
        assert detail["review_status"] == "pending_review"
        assert len(detail["annotations"]) == 1

    @pytest.mark.asyncio
    async def test_get_stage_detail_not_found(self, clean_db) -> None:
        svc = StageDetailService(clean_db)
        detail = await svc.get_stage_detail("no-such-stage")
        assert detail is None
