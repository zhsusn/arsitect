"""Integration test 7: Sketch链路 - Sketch 完整 CRUD 端到端验证.

Covers FR-Sketch-001 ~ FR-Sketch-005:
- 创建 Sketch
- 列表查询
- 单条获取
- 部分更新
- 删除

Test-IDs: TEST-1511 ~ TEST-1513
Policy: default
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.project import Project
from app.models.sketch import Sketch


class TestSync7Sketch:
    """端到端验证 Sketch CRUD 主链路."""

    @pytest.fixture
    async def seeded_project(self) -> Project:
        """Seed an application and project for sketch tests."""
        async with AsyncSessionLocal() as session:
            await session.execute(delete(Sketch))
            await session.execute(delete(Project))
            await session.execute(delete(Application))
            await session.commit()

            app_obj = Application(
                application_id="app-sketch-int",
                application_name="Sketch Integration App",
                local_path="/tmp/sketch-int",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-sketch-int",
                project_name="Sketch Integration Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()
            session.expunge(proj)
            return proj

    @pytest.mark.asyncio
    async def test_sketch_full_crud_flow(self, seeded_project: Project, client: TestClient) -> None:
        """TEST-1511: Sketch 完整 CRUD 端到端链路.

        Covers US-016: 草图查看与管理.
        """
        project_id = seeded_project.project_id

        # CREATE
        create_payload = {
            "name": "Homepage Sketch",
            "status": "DRAFT",
        }
        res = client.post(
            f"/api/v1/projects/{project_id}/sketches",
            json=create_payload,
        )
        assert res.status_code == 201
        created = res.json()
        sketch_id = created["sketch_id"]
        assert created["name"] == "Homepage Sketch"
        assert created["status"] == "DRAFT"

        # LIST
        res = client.get(f"/api/v1/projects/{project_id}/sketches")
        assert res.status_code == 200
        sketches = res.json()
        assert isinstance(sketches, list)
        assert any(s["sketch_id"] == sketch_id for s in sketches)

        # GET
        res = client.get(f"/api/v1/sketches/{sketch_id}")
        assert res.status_code == 200
        fetched = res.json()
        assert fetched["sketch_id"] == sketch_id
        assert fetched["name"] == "Homepage Sketch"

        # UPDATE
        update_payload = {"name": "Dashboard Sketch", "status": "APPROVED"}
        res = client.patch(
            f"/api/v1/sketches/{sketch_id}",
            json=update_payload,
        )
        assert res.status_code == 200
        updated = res.json()
        assert updated["name"] == "Dashboard Sketch"
        assert updated["status"] == "APPROVED"

        # DELETE
        res = client.delete(f"/api/v1/sketches/{sketch_id}")
        assert res.status_code == 204

        # GET after delete -> 404
        res = client.get(f"/api/v1/sketches/{sketch_id}")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_sketch_create_invalid_status(
        self, seeded_project: Project, client: TestClient
    ) -> None:
        """TEST-1512: 非法 status 返回 400.

        Covers AC-V-001: 字段校验.
        """
        payload = {
            "name": "Test",
            "status": "INVALID",
        }
        res = client.post(
            f"/api/v1/projects/{seeded_project.project_id}/sketches",
            json=payload,
        )
        assert res.status_code == 400

    @pytest.mark.asyncio
    async def test_sketch_list_empty(self, seeded_project: Project, client: TestClient) -> None:
        """TEST-1513: 空项目列表返回空数组.

        Covers edge case: 无 sketch.
        """
        res = client.get(f"/api/v1/projects/{seeded_project.project_id}/sketches")
        assert res.status_code == 200
        sketches = res.json()
        assert sketches == []
