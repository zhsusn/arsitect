"""Tests for ProjectRepository."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.infrastructure.database.repositories.project_repo import ProjectRepository
from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.project import Project


class TestProjectRepository:
    """ProjectRepository tests."""

    @pytest.fixture
    async def seeded_app_and_project(self) -> tuple[Application, Project]:
        """Seed an application and a project."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM size_estimates"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app = Application(
                application_id="app-proj",
                application_name="Proj App",
                local_path="/tmp/proj",
            )
            session.add(app)
            await session.flush()

            proj = Project(
                project_id="proj-001",
                project_name="Test Project",
                application_id="app-proj",
                template_level="Standard",
                project_status="Draft",
            )
            session.add(proj)
            await session.commit()
            return app, proj

    @pytest.mark.asyncio
    async def test_create_and_get(
        self, seeded_app_and_project: tuple[Application, Project]
    ) -> None:
        """Can create and retrieve a project."""
        app, _ = seeded_app_and_project
        async with AsyncSessionLocal() as session:
            repo = ProjectRepository(session)
            proj = Project(
                project_id="proj-new",
                project_name="New Project",
                application_id=app.application_id,
                template_level="Light",
            )
            created = await repo.create(proj)
            assert created.project_id == "proj-new"

            fetched = await repo.get_by_id("proj-new")
            assert fetched is not None
            assert fetched.project_name == "New Project"

    @pytest.mark.asyncio
    async def test_list_by_application(
        self, seeded_app_and_project: tuple[Application, Project]
    ) -> None:
        """Can list projects by application."""
        app, _ = seeded_app_and_project
        async with AsyncSessionLocal() as session:
            repo = ProjectRepository(session)
            items, total = await repo.list_by_application(app.application_id)
            assert total >= 1
            assert any(p.project_id == "proj-001" for p in items)

    @pytest.mark.asyncio
    async def test_update(self, seeded_app_and_project: tuple[Application, Project]) -> None:
        """Can update a project."""
        _, proj = seeded_app_and_project
        async with AsyncSessionLocal() as session:
            repo = ProjectRepository(session)
            proj.project_name = "Updated Name"
            updated = await repo.update(proj)
            assert updated.project_name == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete(self, seeded_app_and_project: tuple[Application, Project]) -> None:
        """Can delete a project."""
        _, proj = seeded_app_and_project
        async with AsyncSessionLocal() as session:
            repo = ProjectRepository(session)
            ok = await repo.delete(proj.project_id)
            assert ok is True
            assert await repo.get_by_id(proj.project_id) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self) -> None:
        """Deleting nonexistent project returns False."""
        async with AsyncSessionLocal() as session:
            repo = ProjectRepository(session)
            ok = await repo.delete("does-not-exist")
            assert ok is False

    @pytest.mark.asyncio
    async def test_exists_by_name(
        self, seeded_app_and_project: tuple[Application, Project]
    ) -> None:
        """Name existence check works."""
        app, _ = seeded_app_and_project
        async with AsyncSessionLocal() as session:
            repo = ProjectRepository(session)
            assert await repo.exists_by_name(app.application_id, "Test Project") is True
            assert await repo.exists_by_name(app.application_id, "No Such Project") is False

    @pytest.mark.asyncio
    async def test_archive_activate_cancel(
        self, seeded_app_and_project: tuple[Application, Project]
    ) -> None:
        """State transitions update status correctly."""
        _, proj = seeded_app_and_project
        async with AsyncSessionLocal() as session:
            repo = ProjectRepository(session)

            # Archive
            proj.project_status = "Archived"
            await repo.update(proj)
            fetched = await repo.get_by_id(proj.project_id)
            assert fetched is not None
            assert fetched.project_status == "Archived"

            # Activate
            fetched.project_status = "Active"
            await repo.update(fetched)
            fetched2 = await repo.get_by_id(proj.project_id)
            assert fetched2 is not None
            assert fetched2.project_status == "Active"

            # Cancel
            fetched2.project_status = "Cancelled"
            await repo.update(fetched2)
            fetched3 = await repo.get_by_id(proj.project_id)
            assert fetched3 is not None
            assert fetched3.project_status == "Cancelled"
