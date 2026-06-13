"""Integration test 6: OpenUI链路 - OpenUI Spec 完整 CRUD 端到端验证.

Covers FR-OpenUI-001 ~ FR-OpenUI-005:
- 创建 OpenUI spec
- 列表查询
- 单条获取
- 部分更新
- 删除

Test-IDs: TEST-1508 ~ TEST-1510
Policy: default
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.open_ui_spec import OpenUISpec
from app.models.project import Project


class TestSync6OpenUI:
    """端到端验证 OpenUISpec CRUD 主链路."""

    @pytest.fixture
    async def seeded_project(self) -> Project:
        """Seed an application and project for OpenUI tests."""
        async with AsyncSessionLocal() as session:
            await session.execute(delete(OpenUISpec))
            await session.execute(delete(Project))
            await session.execute(delete(Application))
            await session.commit()

            app_obj = Application(
                application_id="app-openui-int",
                application_name="OpenUI Integration App",
                local_path="/tmp/openui-int",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-openui-int",
                project_name="OpenUI Integration Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()
            session.expunge(proj)
            return proj

    @pytest.mark.asyncio
    async def test_openui_full_crud_flow(self, seeded_project: Project, client: TestClient) -> None:
        """TEST-1508: OpenUISpec 完整 CRUD 端到端链路.

        Covers AC-1.1 / AC-1.2: 原型规格创建与管理.
        """
        project_id = seeded_project.project_id

        # CREATE
        create_payload = {
            "spec_name": "Homepage",
            "dsl_json": '{"components": []}',
            "status": "DRAFT",
        }
        res = client.post(
            f"/api/v1/projects/{project_id}/open-ui-specs",
            json=create_payload,
        )
        assert res.status_code == 201
        created = res.json()
        spec_id = created["spec_id"]
        assert created["spec_name"] == "Homepage"
        assert created["status"] == "DRAFT"

        # LIST
        res = client.get(f"/api/v1/projects/{project_id}/open-ui-specs")
        assert res.status_code == 200
        specs = res.json()
        assert isinstance(specs, list)
        assert any(s["spec_id"] == spec_id for s in specs)

        # GET
        res = client.get(f"/api/v1/open-ui-specs/{spec_id}")
        assert res.status_code == 200
        fetched = res.json()
        assert fetched["spec_id"] == spec_id
        assert fetched["spec_name"] == "Homepage"

        # UPDATE
        update_payload = {"spec_name": "Dashboard", "status": "GENERATED"}
        res = client.patch(
            f"/api/v1/open-ui-specs/{spec_id}",
            json=update_payload,
        )
        assert res.status_code == 200
        updated = res.json()
        assert updated["spec_name"] == "Dashboard"
        assert updated["status"] == "GENERATED"

        # DELETE
        res = client.delete(f"/api/v1/open-ui-specs/{spec_id}")
        assert res.status_code == 204

        # GET after delete -> 404
        res = client.get(f"/api/v1/open-ui-specs/{spec_id}")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_openui_create_invalid_status(self, seeded_project: Project, client: TestClient) -> None:
        """TEST-1509: 非法 status 返回 400.

        Covers AC-3.1: 状态校验.
        """
        payload = {
            "spec_name": "Test",
            "dsl_json": "{}",
            "status": "INVALID",
        }
        res = client.post(
            f"/api/v1/projects/{seeded_project.project_id}/open-ui-specs",
            json=payload,
        )
        assert res.status_code == 400

    @pytest.mark.asyncio
    async def test_openui_list_empty(self, seeded_project: Project, client: TestClient) -> None:
        """TEST-1510: 空项目列表返回空数组.

        Covers edge case: 无 OpenUI spec.
        """
        res = client.get(f"/api/v1/projects/{seeded_project.project_id}/open-ui-specs")
        assert res.status_code == 200
        specs = res.json()
        assert specs == []
