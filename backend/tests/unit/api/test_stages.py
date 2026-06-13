"""Tests for StageRouter."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.annotation import Annotation
from app.models.project_stage import ProjectStage
from main import app

client = TestClient(app)


class TestStageRouter:
    """Stage router tests."""

    @pytest.fixture
    async def seeded_stage(self):
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM annotations"))
            await session.execute(text("DELETE FROM project_stages"))
            await session.commit()

            stage = ProjectStage(
                project_stage_id="stage-api",
                project_id="proj-api",
                stage_id="s-001",
                order_index=1,
                status="DEFINED",
            )
            session.add(stage)
            await session.commit()
            yield stage
            await session.execute(text("DELETE FROM annotations"))
            await session.execute(text("DELETE FROM project_stages"))
            await session.commit()

    @pytest.mark.asyncio
    async def test_get_stage_detail(self, seeded_stage) -> None:
        res = client.get(f"/api/v1/stages/{seeded_stage.project_stage_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["project_stage_id"] == seeded_stage.project_stage_id

    def test_get_stage_detail_not_found(self) -> None:
        res = client.get("/api/v1/stages/no-such-stage")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_list_annotations(self, seeded_stage) -> None:
        async with AsyncSessionLocal() as session:
            session.add(
                Annotation(
                    annotation_id="ann-api",
                    stage_id=seeded_stage.project_stage_id,
                    author="alice",
                    content="Note",
                )
            )
            await session.commit()

        res = client.get(f"/api/v1/stages/{seeded_stage.project_stage_id}/annotations")
        assert res.status_code == 200
        data = res.json()
        assert data["total_count"] == 1

    @pytest.mark.asyncio
    async def test_create_annotation(self, seeded_stage) -> None:
        payload = {
            "annotation_id": "ann-create",
            "author": "bob",
            "content": "New note",
        }
        res = client.post(
            f"/api/v1/stages/{seeded_stage.project_stage_id}/annotations",
            json=payload,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["content"] == "New note"

    @pytest.mark.asyncio
    async def test_update_annotation(self, seeded_stage) -> None:
        async with AsyncSessionLocal() as session:
            session.add(
                Annotation(
                    annotation_id="ann-upd",
                    stage_id=seeded_stage.project_stage_id,
                    author="alice",
                    content="Old",
                )
            )
            await session.commit()

        res = client.put(
            f"/api/v1/stages/{seeded_stage.project_stage_id}/annotations/ann-upd",
            json={"content": "Updated"},
        )
        assert res.status_code == 200
        assert res.json()["content"] == "Updated"

    @pytest.mark.asyncio
    async def test_delete_annotation(self, seeded_stage) -> None:
        async with AsyncSessionLocal() as session:
            session.add(
                Annotation(
                    annotation_id="ann-del",
                    stage_id=seeded_stage.project_stage_id,
                    author="alice",
                    content="Delete me",
                )
            )
            await session.commit()

        res = client.delete(
            f"/api/v1/stages/{seeded_stage.project_stage_id}/annotations/ann-del"
        )
        assert res.status_code == 204
