"""Tests for ArtifactService."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.project import Project
from app.services.artifact_service import ArtifactService


class TestArtifactService:
    """ArtifactService tests."""

    async def _seed_app_and_project(self, session) -> tuple[Application, Project]:
        """Helper to seed application and project."""
        await session.execute(text("DELETE FROM artifact_versions"))
        await session.execute(text("DELETE FROM artifact_files"))
        await session.execute(text("DELETE FROM projects"))
        await session.execute(text("DELETE FROM applications"))
        await session.commit()

        app = Application(
            application_id="app-svc",
            application_name="Svc App",
            local_path="/tmp/svc",
        )
        session.add(app)
        await session.flush()

        proj = Project(
            project_id="proj-svc",
            project_name="Svc Project",
            application_id=app.application_id,
            template_level="Standard",
        )
        session.add(proj)
        await session.flush()
        return app, proj

    @pytest.mark.asyncio
    async def test_create_artifact(self, tmp_path) -> None:
        """Can create an artifact with initial version."""
        async with AsyncSessionLocal() as session:
            _, proj = await self._seed_app_and_project(session)
            svc = ArtifactService(session)

            file_path = str(tmp_path / "test.md")
            art = await svc.create_artifact(
                artifact_id="art-svc-1",
                project_id=proj.project_id,
                file_name="test.md",
                file_path=file_path,
                file_type="md",
                content="Initial content",
                created_by="tester",
            )
            assert art.file_name == "test.md"
            assert art.current_version == 1

            versions = await svc.list_versions(art.artifact_id)
            assert len(versions) == 1
            assert versions[0].version_number == 1
            assert versions[0].content == "Initial content"

    @pytest.mark.asyncio
    async def test_create_artifact_with_execution_id(self, tmp_path) -> None:
        """Can create an artifact linked to a skill execution."""
        from app.models.skill_execution import SkillExecution

        async with AsyncSessionLocal() as session:
            _, proj = await self._seed_app_and_project(session)
            execution = SkillExecution(
                execution_id="exec-123",
                project_id=proj.project_id,
                stage_id="stage-svc",
                skill_id="skill-svc",
                skill_name="test-skill",
                trigger_action="SINGLE_EXECUTE",
            )
            session.add(execution)
            await session.commit()

            svc = ArtifactService(session)
            file_path = str(tmp_path / "exec.md")
            art = await svc.create_artifact(
                artifact_id="art-svc-exec",
                project_id=proj.project_id,
                execution_id=execution.execution_id,
                file_name="exec.md",
                file_path=file_path,
                file_type="md",
                content="Execution output",
            )
            assert art.execution_id == execution.execution_id

    @pytest.mark.asyncio
    async def test_get_tree(self, tmp_path) -> None:
        """Tree groups artifacts by directory."""
        async with AsyncSessionLocal() as session:
            _, proj = await self._seed_app_and_project(session)
            svc = ArtifactService(session)

            await svc.create_artifact(
                artifact_id="art-svc-2a",
                project_id=proj.project_id,
                file_name="req.md",
                file_path=str(tmp_path / "docs" / "req.md"),
                file_type="md",
                content="Requirements",
            )
            await svc.create_artifact(
                artifact_id="art-svc-2b",
                project_id=proj.project_id,
                file_name="design.md",
                file_path=str(tmp_path / "docs" / "design.md"),
                file_type="md",
                content="Design",
            )
            await svc.create_artifact(
                artifact_id="art-svc-2c",
                project_id=proj.project_id,
                file_name="code.py",
                file_path=str(tmp_path / "src" / "code.py"),
                file_type="other",
                content="Code",
            )

            tree = await svc.get_tree(proj.project_id)
            directories = {item["directory"] for item in tree}
            assert str(tmp_path / "docs") in directories
            assert str(tmp_path / "src") in directories

    @pytest.mark.asyncio
    async def test_get_tree_with_search(self, tmp_path) -> None:
        """Tree search filters by file name."""
        async with AsyncSessionLocal() as session:
            _, proj = await self._seed_app_and_project(session)
            svc = ArtifactService(session)

            await svc.create_artifact(
                artifact_id="art-svc-3a",
                project_id=proj.project_id,
                file_name="req.md",
                file_path=str(tmp_path / "req.md"),
                file_type="md",
                content="Requirements",
            )
            await svc.create_artifact(
                artifact_id="art-svc-3b",
                project_id=proj.project_id,
                file_name="design.md",
                file_path=str(tmp_path / "design.md"),
                file_type="md",
                content="Design",
            )

            tree = await svc.get_tree(proj.project_id, search="req")
            assert len(tree) == 1
            assert len(tree[0]["files"]) == 1
            assert tree[0]["files"][0]["file_name"] == "req.md"

    @pytest.mark.asyncio
    async def test_get_content(self, tmp_path) -> None:
        """Can get artifact content."""
        async with AsyncSessionLocal() as session:
            _, proj = await self._seed_app_and_project(session)
            svc = ArtifactService(session)

            file_path = str(tmp_path / "content.md")
            art = await svc.create_artifact(
                artifact_id="art-svc-4",
                project_id=proj.project_id,
                file_name="content.md",
                file_path=file_path,
                file_type="md",
                content="Hello world",
            )

            content, total_lines, content_hash = await svc.get_content(art.artifact_id)
            assert content == "Hello world"
            assert total_lines == 1
            assert content_hash

    @pytest.mark.asyncio
    async def test_save_content(self, tmp_path) -> None:
        """Saving content creates a new version."""
        async with AsyncSessionLocal() as session:
            _, proj = await self._seed_app_and_project(session)
            svc = ArtifactService(session)

            file_path = str(tmp_path / "save.md")
            art = await svc.create_artifact(
                artifact_id="art-svc-5",
                project_id=proj.project_id,
                file_name="save.md",
                file_path=file_path,
                file_type="md",
                content="v1",
            )

            version = await svc.save_content(art.artifact_id, "v2", created_by="alice")
            assert version.version_number == 2
            assert version.operation_type == "snapshot"

            content, total_lines, content_hash = await svc.get_content(art.artifact_id)
            assert content == "v2"

            versions = await svc.list_versions(art.artifact_id)
            assert len(versions) == 2

    @pytest.mark.asyncio
    async def test_rollback(self, tmp_path) -> None:
        """Rollback restores content and creates rollback version."""
        async with AsyncSessionLocal() as session:
            _, proj = await self._seed_app_and_project(session)
            svc = ArtifactService(session)

            file_path = str(tmp_path / "rollback.md")
            art = await svc.create_artifact(
                artifact_id="art-svc-6",
                project_id=proj.project_id,
                file_name="rollback.md",
                file_path=file_path,
                file_type="md",
                content="original",
            )

            await svc.save_content(art.artifact_id, "modified", created_by="bob")
            version = await svc.rollback(art.artifact_id, 1, created_by="charlie")
            assert version.version_number == 3
            assert version.operation_type == "rollback"

            content, total_lines, content_hash = await svc.get_content(art.artifact_id)
            assert content == "original"

    @pytest.mark.asyncio
    async def test_get_version(self, tmp_path) -> None:
        """Can get a specific version."""
        async with AsyncSessionLocal() as session:
            _, proj = await self._seed_app_and_project(session)
            svc = ArtifactService(session)

            file_path = str(tmp_path / "version.md")
            art = await svc.create_artifact(
                artifact_id="art-svc-7",
                project_id=proj.project_id,
                file_name="version.md",
                file_path=file_path,
                file_type="md",
                content="v1",
            )

            v = await svc.get_version(art.artifact_id, 1)
            assert v.version_number == 1

    @pytest.mark.asyncio
    async def test_list_versions_limit(self, tmp_path) -> None:
        """Version list respects limit."""
        async with AsyncSessionLocal() as session:
            _, proj = await self._seed_app_and_project(session)
            svc = ArtifactService(session)

            file_path = str(tmp_path / "limit.md")
            art = await svc.create_artifact(
                artifact_id="art-svc-8",
                project_id=proj.project_id,
                file_name="limit.md",
                file_path=file_path,
                file_type="md",
                content="v1",
            )

            for i in range(2, 13):
                await svc.save_content(art.artifact_id, f"v{i}")

            versions = await svc.list_versions(art.artifact_id)
            assert len(versions) == 10
            assert versions[0].version_number == 12
