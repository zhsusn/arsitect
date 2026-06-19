"""Integration test 8: Wireframe链路 - Wireframe 完整 CRUD 端到端验证.

Covers FR-Wireframe-001 ~ FR-Wireframe-005:
- 创建 Wireframe
- 列表查询
- 单条获取
- 部分更新
- 删除

Test-IDs: TEST-1514 ~ TEST-1516
Policy: default
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.project import Project
from app.models.wireframe import Wireframe


class TestSync8Wireframe:
    """端到端验证 Wireframe CRUD 主链路."""

    @pytest.fixture
    async def seeded_project(self) -> Project:
        """Seed an application and project for wireframe tests."""
        async with AsyncSessionLocal() as session:
            await session.execute(delete(Wireframe))
            await session.execute(delete(Project))
            await session.execute(delete(Application))
            await session.commit()

            app_obj = Application(
                application_id="app-wireframe-int",
                application_name="Wireframe Integration App",
                local_path="/tmp/wireframe-int",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-wireframe-int",
                project_name="Wireframe Integration Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()
            session.expunge(proj)
            return proj

    @pytest.mark.asyncio
    async def test_wireframe_full_crud_flow(
        self, seeded_project: Project, client: TestClient
    ) -> None:
        """TEST-1514: Wireframe 完整 CRUD 端到端链路.

        Covers US-016: 线框图查看与管理.
        """
        project_id = seeded_project.project_id

        # CREATE
        create_payload = {
            "name": "Dashboard Wireframe",
            "nodes": '[{"id":"n1"}]',
            "edges": '[{"id":"e1"}]',
            "status": "DRAFT",
        }
        res = client.post(
            f"/api/v1/projects/{project_id}/wireframes",
            json=create_payload,
        )
        assert res.status_code == 201
        created = res.json()
        wireframe_id = created["wireframe_id"]
        assert created["name"] == "Dashboard Wireframe"
        assert created["status"] == "DRAFT"

        # LIST
        res = client.get(f"/api/v1/projects/{project_id}/wireframes")
        assert res.status_code == 200
        wireframes = res.json()
        assert isinstance(wireframes, list)
        assert any(w["wireframe_id"] == wireframe_id for w in wireframes)

        # GET
        res = client.get(f"/api/v1/wireframes/{wireframe_id}")
        assert res.status_code == 200
        fetched = res.json()
        assert fetched["wireframe_id"] == wireframe_id
        assert fetched["name"] == "Dashboard Wireframe"

        # UPDATE
        update_payload = {"name": "Settings Wireframe", "status": "ACTIVE"}
        res = client.patch(
            f"/api/v1/wireframes/{wireframe_id}",
            json=update_payload,
        )
        assert res.status_code == 200
        updated = res.json()
        assert updated["name"] == "Settings Wireframe"
        assert updated["status"] == "ACTIVE"

        # DELETE
        res = client.delete(f"/api/v1/wireframes/{wireframe_id}")
        assert res.status_code == 204

        # GET after delete -> 404
        res = client.get(f"/api/v1/wireframes/{wireframe_id}")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_wireframe_create_invalid_status(
        self, seeded_project: Project, client: TestClient
    ) -> None:
        """TEST-1515: 非法 status 返回 400.

        Covers AC-V-001: 字段校验.
        """
        payload = {
            "name": "Test",
            "nodes": "[]",
            "edges": "[]",
            "status": "INVALID",
        }
        res = client.post(
            f"/api/v1/projects/{seeded_project.project_id}/wireframes",
            json=payload,
        )
        assert res.status_code == 400

    @pytest.mark.asyncio
    async def test_wireframe_list_empty(self, seeded_project: Project, client: TestClient) -> None:
        """TEST-1516: 空项目列表返回空数组.

        Covers edge case: 无 wireframe.
        """
        res = client.get(f"/api/v1/projects/{seeded_project.project_id}/wireframes")
        assert res.status_code == 200
        wireframes = res.json()
        assert wireframes == []
