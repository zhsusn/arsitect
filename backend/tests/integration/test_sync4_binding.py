"""Integration test 4: Binding链路 — 完整 CRUD 端到端验证.

Covers FR-Binding-001 ~ FR-Binding-005:
- 创建绑定规则
- 列表查询
- 单条获取
- 部分更新
- 删除

Test-IDs: TEST-1501 ~ TEST-1505
Policy: default
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.binding_rule import BindingRule
from app.models.project import Project


class TestSync4Binding:
    """端到端验证 BindingRule CRUD 主链路."""

    @pytest.fixture
    async def seeded_project(self) -> Project:
        """Seed an application and project for binding tests."""
        async with AsyncSessionLocal() as session:
            await session.execute(delete(BindingRule))
            await session.execute(delete(Project))
            await session.execute(delete(Application))
            await session.commit()

            app_obj = Application(
                application_id="app-binding-int",
                application_name="Binding Integration App",
                local_path="/tmp/binding-int",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-binding-int",
                project_name="Binding Integration Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()
            session.expunge(proj)
            return proj

    # client fixture is provided by conftest.py with shared session override

    @pytest.mark.asyncio
    async def test_binding_full_crud_flow(self, seeded_project: Project, client: TestClient) -> None:
        """TEST-1501: BindingRule 完整 CRUD 端到端链路.

        Covers AC-F-001 / AC-F-002 / AC-F-003 / AC-F-004 / AC-F-005.
        """
        project_id = seeded_project.project_id

        # CREATE
        create_payload = {
            "source_field": "user.name",
            "target_field": "profile.displayName",
            "transform_type": "DIRECT",
            "transform_config": None,
            "status": "ACTIVE",
        }
        res = client.post(
            f"/api/v1/projects/{project_id}/binding-rules",
            json=create_payload,
        )
        assert res.status_code == 201
        created = res.json()
        rule_id = created["rule_id"]
        assert created["source_field"] == "user.name"
        assert created["transform_type"] == "DIRECT"

        # LIST
        res = client.get(f"/api/v1/projects/{project_id}/binding-rules")
        assert res.status_code == 200
        rules = res.json()
        assert isinstance(rules, list)
        assert any(r["rule_id"] == rule_id for r in rules)

        # GET
        res = client.get(f"/api/v1/binding-rules/{rule_id}")
        assert res.status_code == 200
        fetched = res.json()
        assert fetched["rule_id"] == rule_id
        assert fetched["source_field"] == "user.name"

        # UPDATE
        update_payload = {"source_field": "user.email", "status": "INACTIVE"}
        res = client.patch(
            f"/api/v1/binding-rules/{rule_id}",
            json=update_payload,
        )
        assert res.status_code == 200
        updated = res.json()
        assert updated["source_field"] == "user.email"
        assert updated["status"] == "INACTIVE"

        # DELETE
        res = client.delete(f"/api/v1/binding-rules/{rule_id}")
        assert res.status_code == 204

        # GET after delete → 404
        res = client.get(f"/api/v1/binding-rules/{rule_id}")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_binding_create_invalid_transform_type(self, seeded_project: Project, client: TestClient) -> None:
        """TEST-1502: 非法 transform_type 返回 400.

        Covers AC-V-001: 字段校验.
        """
        payload = {
            "source_field": "a",
            "target_field": "b",
            "transform_type": "INVALID_TYPE",
            "status": "ACTIVE",
        }
        res = client.post(
            f"/api/v1/projects/{seeded_project.project_id}/binding-rules",
            json=payload,
        )
        assert res.status_code == 400

    @pytest.mark.asyncio
    async def test_binding_list_empty_project(self, seeded_project: Project, client: TestClient) -> None:
        """TEST-1503: 空项目列表返回空数组.

        Covers edge case: 无绑定规则的项目.
        """
        res = client.get(f"/api/v1/projects/{seeded_project.project_id}/binding-rules")
        assert res.status_code == 200
        rules = res.json()
        assert rules == []
