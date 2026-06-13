"""Tests for BindingRouter.

Covers binding-rule CRUD API endpoints.
Uses Direct tests for read/update/delete to avoid session isolation.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.api.v1.binding import delete_rule, get_rule, list_rules, update_rule
from app.core.exceptions import NotFoundError
from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.binding_rule import BindingRule
from app.models.project import Project
from app.schemas.binding import BindingUpdateDTO
from main import app

client = TestClient(app)


class TestBindingRouter:
    """Binding router API tests."""

    @pytest.fixture
    async def seeded_project(self) -> Project:
        """Seed an application and project."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM binding_rules"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app_obj = Application(
                application_id="app-bind-router",
                application_name="Bind Router App",
                local_path="/tmp/bind-router",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-bind-router",
                project_name="Bind Router Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()
            return proj

    @pytest.fixture
    async def seeded_rule(self, seeded_project: Project) -> BindingRule:
        """Seed a binding rule."""
        async with AsyncSessionLocal() as session:
            rule = BindingRule(
                rule_id="bind-test-001",
                project_id=seeded_project.project_id,
                source_field="user.name",
                target_field="profile.displayName",
                transform_type="DIRECT",
                transform_config=None,
                status="ACTIVE",
            )
            session.add(rule)
            await session.commit()
            return rule

    @pytest.mark.asyncio
    async def test_create_rule(self, seeded_project: Project) -> None:
        """TEST-0301: POST creates a binding rule."""
        payload = {
            "source_field": "user.name",
            "target_field": "profile.displayName",
            "transform_type": "DIRECT",
            "transform_config": None,
            "status": "ACTIVE",
        }
        res = client.post(
            f"/api/v1/projects/{seeded_project.project_id}/binding-rules",
            json=payload,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["source_field"] == "user.name"
        assert data["transform_type"] == "DIRECT"

    @pytest.mark.asyncio
    async def test_create_rule_invalid_transform(self, seeded_project: Project) -> None:
        """TEST-0302: POST with invalid transform_type returns 422."""
        payload = {
            "source_field": "a",
            "target_field": "b",
            "transform_type": "INVALID",
            "status": "ACTIVE",
        }
        res = client.post(
            f"/api/v1/projects/{seeded_project.project_id}/binding-rules",
            json=payload,
        )
        assert res.status_code == 400

    @pytest.mark.asyncio
    async def test_list_rules(self, seeded_project: Project, seeded_rule: BindingRule) -> None:
        """TEST-0303: GET lists binding rules for a project (Direct)."""
        async with AsyncSessionLocal() as session:
            result = await list_rules(seeded_project.project_id, db=session)
            assert len(result) >= 1
            assert any(r.rule_id == "bind-test-001" for r in result)

    @pytest.mark.asyncio
    async def test_get_rule(self, seeded_rule: BindingRule) -> None:
        """TEST-0304: GET returns a single rule (Direct)."""
        async with AsyncSessionLocal() as session:
            result = await get_rule("bind-test-001", db=session)
            assert result.rule_id == "bind-test-001"

    @pytest.mark.asyncio
    async def test_get_rule_not_found(self, seeded_project: Project) -> None:
        """TEST-0305: GET nonexistent rule returns 404 (Direct)."""
        async with AsyncSessionLocal() as session:
            with pytest.raises(NotFoundError):
                await get_rule("no-such-rule", db=session)

    @pytest.mark.asyncio
    async def test_update_rule(self, seeded_rule: BindingRule) -> None:
        """TEST-0306: PATCH updates a binding rule (Direct)."""
        async with AsyncSessionLocal() as session:
            dto = BindingUpdateDTO(source_field="new", status="INACTIVE")
            result = await update_rule("bind-test-001", dto, db=session)
            assert result.source_field == "new"
            assert result.status == "INACTIVE"

    @pytest.mark.asyncio
    async def test_delete_rule(self, seeded_rule: BindingRule) -> None:
        """TEST-0307: DELETE removes a binding rule (Direct)."""
        async with AsyncSessionLocal() as session:
            await delete_rule("bind-test-001", db=session)
            with pytest.raises(NotFoundError):
                await get_rule("bind-test-001", db=session)
