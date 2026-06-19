"""Tests for ProjectService."""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.core.exceptions import ConflictError
from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.project_path_config import ProjectPathConfig
from app.models.stage_skill_binding import StageSkillBinding
from app.services.project_service import ProjectService


class TestProjectService:
    """ProjectService tests."""

    @pytest_asyncio.fixture
    async def seeded_templates(self) -> None:
        """Seed built-in templates and stages."""
        from app.core.seed import _seed_templates_and_stages

        async with AsyncSessionLocal() as session:
            await _seed_templates_and_stages(session)
            await session.commit()

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

    @pytest.mark.asyncio
    async def test_create_project_initializes_path_config(
        self, seeded_app: Application, seeded_templates: None
    ) -> None:
        """Creating a project persists project_path_config from the template."""
        async with AsyncSessionLocal() as session:
            svc = ProjectService(session)
            created = await svc.create_project(
                project_id="proj-svc-path",
                project_name="Path Config Project",
                application_id=seeded_app.application_id,
                template_level="Standard",
            )
            assert created.execution_strategy == "semi_auto"
            assert created.merge_policy_json is not None

            from sqlalchemy import select

            path_config_result = await session.execute(
                select(ProjectPathConfig).where(
                    ProjectPathConfig.project_id == created.project_id
                )
            )
            path_config = path_config_result.scalar_one_or_none()
            assert path_config is not None
            assert path_config.template_level == "Standard"
            assert path_config.execution_strategy == "semi_auto"

    @pytest.mark.asyncio
    async def test_create_project_initializes_skill_bindings(
        self, seeded_app: Application, seeded_templates: None
    ) -> None:
        """Creating a project creates stage skill binding snapshots."""
        async with AsyncSessionLocal() as session:
            svc = ProjectService(session)
            created = await svc.create_project(
                project_id="proj-svc-bind",
                project_name="Skill Binding Project",
                application_id=seeded_app.application_id,
                template_level="Standard",
            )

            from sqlalchemy import select

            from app.models.project_stage import ProjectStage

            stage_result = await session.execute(
                select(ProjectStage).where(ProjectStage.project_id == created.project_id)
            )
            stages = list(stage_result.scalars().all())
            assert len(stages) > 0

            binding_result = await session.execute(
                select(StageSkillBinding).where(
                    StageSkillBinding.project_stage_id.in_(
                        [s.project_stage_id for s in stages]
                    )
                )
            )
            bindings = list(binding_result.scalars().all())
            assert len(bindings) > 0
            primary_bindings = [b for b in bindings if b.role == "primary"]
            assert len(primary_bindings) > 0
            auxiliary_bindings = [b for b in bindings if b.role == "auxiliary"]
            assert len(auxiliary_bindings) > 0

    @pytest.mark.asyncio
    async def test_update_execution_strategy(
        self, seeded_app: Application, seeded_templates: None
    ) -> None:
        """Project execution strategy can be updated and cascades to pending stages."""
        from sqlalchemy import select

        from app.models.project_stage import ProjectStage

        async with AsyncSessionLocal() as session:
            svc = ProjectService(session)
            created = await svc.create_project(
                project_id="proj-svc-strat",
                project_name="Strategy Project",
                application_id=seeded_app.application_id,
                template_level="Standard",
            )
            assert created.execution_strategy == "semi_auto"

            result = await svc.update_execution_strategy(
                created.project_id,
                execution_strategy="full_auto",
                reason=" smoke test",
            )
            assert result["execution_strategy"] == "full_auto"

            updated = await svc.get_project(created.project_id)
            assert updated.execution_strategy == "full_auto"

            from sqlalchemy import select

            path_config_result = await session.execute(
                select(ProjectPathConfig).where(
                    ProjectPathConfig.project_id == created.project_id
                )
            )
            path_config = path_config_result.scalar_one_or_none()
            assert path_config is not None
            assert path_config.execution_strategy == "full_auto"

            stage_result = await session.execute(
                select(ProjectStage).where(
                    ProjectStage.project_id == created.project_id,
                    ProjectStage.runtime_status.in_({"not_started", "ready", "blocked"}),
                )
            )
            stages = list(stage_result.scalars().all())
            assert len(stages) > 0
            assert all(s.execution_strategy == "full_auto" for s in stages)
