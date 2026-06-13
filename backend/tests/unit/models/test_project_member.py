"""Tests for ProjectMember model."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models.application import Application
from app.models.project import Project
from app.models.project_member import ProjectMember


class TestProjectMember:
    """ProjectMember ORM tests."""

    async def _seed_project(self, db_session, suffix: str = "1"):
        """Helper to create an application + project."""
        app = Application(
            application_id=f"app-mem-{suffix}",
            application_name=f"MemApp{suffix}",
            local_path=f"/tmp/mem{suffix}",
        )
        db_session.add(app)
        await db_session.flush()
        proj = Project(
            project_id=f"proj-mem-{suffix}",
            project_name=f"MemProj{suffix}",
            application_id=app.application_id,
            template_level="Standard",
        )
        db_session.add(proj)
        await db_session.flush()
        return proj

    @pytest.mark.asyncio
    async def test_create_project_member(self, db_session) -> None:
        """Should persist project member with default role."""
        proj = await self._seed_project(db_session)
        member = ProjectMember(
            member_id="mem-001",
            project_id=proj.project_id,
            user_id="user-001",
            role="owner",
        )
        db_session.add(member)
        await db_session.flush()

        result = await db_session.execute(
            select(ProjectMember).where(ProjectMember.member_id == "mem-001")
        )
        found = result.scalar_one()
        assert found.user_id == "user-001"
        assert found.role == "owner"
        assert found.joined_at is not None

    @pytest.mark.asyncio
    async def test_default_role(self, db_session) -> None:
        """Default role should be 'member'."""
        proj = await self._seed_project(db_session, suffix="2")
        member = ProjectMember(
            member_id="mem-002",
            project_id=proj.project_id,
            user_id="user-002",
        )
        db_session.add(member)
        await db_session.flush()

        result = await db_session.execute(
            select(ProjectMember).where(ProjectMember.member_id == "mem-002")
        )
        found = result.scalar_one()
        assert found.role == "member"
