"""Tests for ProjectService."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.core.exceptions import ConflictError
from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.services.project_service import ProjectService


class TestProjectService:
    """ProjectService tests."""

    @pytest.fixture
    async def seeded_app(self) -> Application:
        """Seed an application."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM size_estimates"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            app = Application(
                application_id="app-svc",
                application_name="Svc App",
                local_path="/tmp/svc",
            )
            session.add(app)
            await session.commit()
            return app

    @pytest.mark.asyncio
    async def test_create_project(self, seeded_app: Application) -> None:
        """Can create a project."""
        async with AsyncSessionLocal() as session:
            svc = ProjectService(session)
            proj = await svc.create_project(
                project_id="proj-svc-1",
                project_name="Svc Project",
                application_id=seeded_app.application_id,
                template_level="Standard",
            )
            assert proj.project_name == "Svc Project"
            assert proj.project_status == "Draft"

    @pytest.mark.asyncio
    async def test_create_duplicate_name(self, seeded_app: Application) -> None:
        """Duplicate name raises ConflictError."""
        async with AsyncSessionLocal() as session:
            svc = ProjectService(session)
            await svc.create_project(
                project_id="proj-svc-2",
                project_name="Dup Project",
                application_id=seeded_app.application_id,
                template_level="Light",
            )
            with pytest.raises(ConflictError):
                await svc.create_project(
                    project_id="proj-svc-3",
                    project_name="Dup Project",
                    application_id=seeded_app.application_id,
                    template_level="Standard",
                )

    @pytest.mark.asyncio
    async def test_get_project(self, seeded_app: Application) -> None:
        """Can get a project."""
        async with AsyncSessionLocal() as session:
            svc = ProjectService(session)
            created = await svc.create_project(
                project_id="proj-svc-4",
                project_name="Get Project",
                application_id=seeded_app.application_id,
                template_level="Trivial",
            )
            fetched = await svc.get_project(created.project_id)
            assert fetched.project_id == created.project_id

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, seeded_app: Application) -> None:
        """Getting nonexistent project raises NotFoundError."""
        async with AsyncSessionLocal() as session:
            svc = ProjectService(session)
            with pytest.raises(Exception, match="not found"):
                await svc.get_project("no-such-id")

    @pytest.mark.asyncio
    async def test_update_project(self, seeded_app: Application) -> None:
        """Can update project info."""
        async with AsyncSessionLocal() as session:
            svc = ProjectService(session)
            created = await svc.create_project(
                project_id="proj-svc-5",
                project_name="Update Project",
                application_id=seeded_app.application_id,
                template_level="Deep",
            )
            updated = await svc.update_project(
                created.project_id,
                project_name="Updated Name",
                project_description="New desc",
            )
            assert updated.project_name == "Updated Name"
            assert updated.project_description == "New desc"

    @pytest.mark.asyncio
    async def test_archive_project(self, seeded_app: Application) -> None:
        """Can archive an Active project."""
        async with AsyncSessionLocal() as session:
            svc = ProjectService(session)
            created = await svc.create_project(
                project_id="proj-svc-6",
                project_name="Archive Project",
                application_id=seeded_app.application_id,
                template_level="Standard",
            )
            await svc.activate_project(created.project_id)
            archived = await svc.archive_project(created.project_id)
            assert archived.project_status == "Archived"

    @pytest.mark.asyncio
    async def test_activate_project(self, seeded_app: Application) -> None:
        """Can activate a Draft project."""
        async with AsyncSessionLocal() as session:
            svc = ProjectService(session)
            created = await svc.create_project(
                project_id="proj-svc-7",
                project_name="Activate Project",
                application_id=seeded_app.application_id,
                template_level="Standard",
            )
            activated = await svc.activate_project(created.project_id)
            assert activated.project_status == "Active"

    @pytest.mark.asyncio
    async def test_cancel_zero_progress(self, seeded_app: Application) -> None:
        """Zero-progress project can be cancelled directly."""
        async with AsyncSessionLocal() as session:
            svc = ProjectService(session)
            created = await svc.create_project(
                project_id="proj-svc-8",
                project_name="Cancel Project",
                application_id=seeded_app.application_id,
                template_level="Standard",
            )
            cancelled = await svc.cancel_project(created.project_id)
            assert cancelled.project_status == "Cancelled"

    @pytest.mark.asyncio
    async def test_cancel_active_project(self, seeded_app: Application) -> None:
        """Active project can be cancelled."""
        async with AsyncSessionLocal() as session:
            svc = ProjectService(session)
            created = await svc.create_project(
                project_id="proj-svc-9",
                project_name="Cancel Active",
                application_id=seeded_app.application_id,
                template_level="Standard",
            )
            await svc.activate_project(created.project_id)
            cancelled = await svc.cancel_project(created.project_id)
            assert cancelled.project_status == "Cancelled"
