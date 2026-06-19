"""Tests for BindingService."""

from __future__ import annotations

import pytest

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.application import Application
from app.models.project import Project
from app.services.binding_service import BindingService


class TestBindingService:
    """BindingService unit tests."""

    async def _seed_project(self, session, suffix: str = "1") -> Project:
        app = Application(
            application_id=f"app-bind-{suffix}",
            application_name=f"BindApp{suffix}",
            local_path=f"/tmp/bind{suffix}",
        )
        session.add(app)
        await session.flush()
        proj = Project(
            project_id=f"proj-bind-{suffix}",
            project_name=f"BindProj{suffix}",
            application_id=app.application_id,
            template_level="Standard",
        )
        session.add(proj)
        await session.flush()
        return proj

    @pytest.mark.asyncio
    async def test_create_rule(self, db_session) -> None:
        proj = await self._seed_project(db_session)
        svc = BindingService(db_session)
        rule = await svc.create_rule(
            project_id=proj.project_id,
            source_field="user.name",
            target_field="profile.displayName",
            transform_type="DIRECT",
            transform_config=None,
            status="ACTIVE",
        )
        assert rule.source_field == "user.name"
        assert rule.transform_type == "DIRECT"

    @pytest.mark.asyncio
    async def test_create_rule_invalid_transform(self, db_session) -> None:
        proj = await self._seed_project(db_session, suffix="bad")
        svc = BindingService(db_session)
        with pytest.raises(BadRequestError):
            await svc.create_rule(
                project_id=proj.project_id,
                source_field="a",
                target_field="b",
                transform_type="INVALID",
                transform_config=None,
                status="ACTIVE",
            )

    @pytest.mark.asyncio
    async def test_get_rule(self, db_session) -> None:
        proj = await self._seed_project(db_session, suffix="get")
        svc = BindingService(db_session)
        created = await svc.create_rule(proj.project_id, "a", "b", "MAP", '{"k":"v"}', "ACTIVE")
        fetched = await svc.get_rule(created.rule_id)
        assert fetched.rule_id == created.rule_id

    @pytest.mark.asyncio
    async def test_get_rule_not_found(self, db_session) -> None:
        svc = BindingService(db_session)
        with pytest.raises(NotFoundError):
            await svc.get_rule("no-such-rule")

    @pytest.mark.asyncio
    async def test_list_rules(self, db_session) -> None:
        proj = await self._seed_project(db_session, suffix="list")
        svc = BindingService(db_session)
        await svc.create_rule(proj.project_id, "a", "b", "DIRECT", None, "ACTIVE")
        await svc.create_rule(proj.project_id, "c", "d", "FORMAT", None, "ACTIVE")
        rules = await svc.list_rules(proj.project_id)
        assert len(rules) == 2

    @pytest.mark.asyncio
    async def test_update_rule(self, db_session) -> None:
        proj = await self._seed_project(db_session, suffix="upd")
        svc = BindingService(db_session)
        rule = await svc.create_rule(proj.project_id, "old", "old", "DIRECT", None, "ACTIVE")
        updated = await svc.update_rule(
            rule.rule_id,
            {"source_field": "new", "status": "INACTIVE"},
        )
        assert updated.source_field == "new"
        assert updated.status == "INACTIVE"

    @pytest.mark.asyncio
    async def test_delete_rule(self, db_session) -> None:
        proj = await self._seed_project(db_session, suffix="del")
        svc = BindingService(db_session)
        rule = await svc.create_rule(proj.project_id, "x", "y", "DIRECT", None, "ACTIVE")
        await svc.delete_rule(rule.rule_id)
        with pytest.raises(NotFoundError):
            await svc.get_rule(rule.rule_id)
