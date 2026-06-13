"""Tests for ArtifactFile and ArtifactVersion models."""

from __future__ import annotations

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.artifact import ArtifactFile
from app.models.artifact_version import ArtifactVersion
from app.models.project import Project


class TestArtifactFileModel:
    """ArtifactFile model tests."""

    async def _seed_app_and_project(self, session) -> tuple[Application, Project]:
        """Helper to seed application and project."""
        app = Application(
            application_id="app-art-001",
            application_name="Art App",
            local_path="/tmp/art",
        )
        session.add(app)
        await session.flush()

        proj = Project(
            project_id="proj-art-001",
            project_name="Art Project",
            application_id=app.application_id,
            template_level="Standard",
        )
        session.add(proj)
        await session.flush()
        return app, proj

    @pytest.mark.asyncio
    async def test_create_artifact(self) -> None:
        """Can create a valid artifact file."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM artifact_versions"))
            await session.execute(text("DELETE FROM artifact_files"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            _, proj = await self._seed_app_and_project(session)

            art = ArtifactFile(
                artifact_id="art-001",
                project_id=proj.project_id,
                file_name="requirements.md",
                file_path="/docs/requirements.md",
                file_type="md",
                file_size_bytes=1024,
            )
            session.add(art)
            await session.commit()

            result = await session.execute(
                select(ArtifactFile).where(ArtifactFile.artifact_id == "art-001")
            )
            fetched = result.scalar_one()
            assert fetched.file_name == "requirements.md"
            assert fetched.file_type == "md"
            assert fetched.current_version == 1
            assert fetched.external_status == "normal"

    @pytest.mark.asyncio
    async def test_file_type_constraint(self) -> None:
        """Invalid file_type is rejected."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM artifact_versions"))
            await session.execute(text("DELETE FROM artifact_files"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            _, proj = await self._seed_app_and_project(session)

            art = ArtifactFile(
                artifact_id="art-002",
                project_id=proj.project_id,
                file_name="bad.exe",
                file_path="/bad.exe",
                file_type="exe",
            )
            session.add(art)
            with pytest.raises(IntegrityError):
                await session.commit()
            await session.rollback()

    @pytest.mark.asyncio
    async def test_external_status_constraint(self) -> None:
        """Invalid external_status is rejected."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM artifact_versions"))
            await session.execute(text("DELETE FROM artifact_files"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            _, proj = await self._seed_app_and_project(session)

            art = ArtifactFile(
                artifact_id="art-003",
                project_id=proj.project_id,
                file_name="test.md",
                file_path="/test.md",
                file_type="md",
                external_status="unknown",
            )
            session.add(art)
            with pytest.raises(IntegrityError):
                await session.commit()
            await session.rollback()

    @pytest.mark.asyncio
    async def test_cascade_delete_project(self) -> None:
        """Deleting project cascades to artifact_files."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM artifact_versions"))
            await session.execute(text("DELETE FROM artifact_files"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            _, proj = await self._seed_app_and_project(session)

            art = ArtifactFile(
                artifact_id="art-004",
                project_id=proj.project_id,
                file_name="test.md",
                file_path="/test.md",
                file_type="md",
            )
            session.add(art)
            await session.commit()

            await session.delete(proj)
            await session.commit()

            result = await session.execute(
                select(ArtifactFile).where(ArtifactFile.artifact_id == "art-004")
            )
            assert result.scalar_one_or_none() is None


class TestArtifactVersionModel:
    """ArtifactVersion model tests."""

    async def _seed_app_project_artifact(
        self, session
    ) -> tuple[Application, Project, ArtifactFile]:
        """Helper to seed application, project, and artifact."""
        app = Application(
            application_id="app-ver-001",
            application_name="Ver App",
            local_path="/tmp/ver",
        )
        session.add(app)
        await session.flush()

        proj = Project(
            project_id="proj-ver-001",
            project_name="Ver Project",
            application_id=app.application_id,
            template_level="Standard",
        )
        session.add(proj)
        await session.flush()

        art = ArtifactFile(
            artifact_id="art-ver-001",
            project_id=proj.project_id,
            file_name="test.md",
            file_path="/test.md",
            file_type="md",
        )
        session.add(art)
        await session.flush()
        return app, proj, art

    @pytest.mark.asyncio
    async def test_create_version(self) -> None:
        """Can create a valid artifact version."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM artifact_versions"))
            await session.execute(text("DELETE FROM artifact_files"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            _, _, art = await self._seed_app_project_artifact(session)

            ver = ArtifactVersion(
                version_id="ver-001",
                artifact_id=art.artifact_id,
                version_number=1,
                operation_type="snapshot",
                content="Hello",
                created_by="tester",
            )
            session.add(ver)
            await session.commit()

            result = await session.execute(
                select(ArtifactVersion).where(ArtifactVersion.version_id == "ver-001")
            )
            fetched = result.scalar_one()
            assert fetched.version_number == 1
            assert fetched.operation_type == "snapshot"
            assert fetched.content == "Hello"

    @pytest.mark.asyncio
    async def test_operation_type_constraint(self) -> None:
        """Invalid operation_type is rejected."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM artifact_versions"))
            await session.execute(text("DELETE FROM artifact_files"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            _, _, art = await self._seed_app_project_artifact(session)

            ver = ArtifactVersion(
                version_id="ver-002",
                artifact_id=art.artifact_id,
                version_number=1,
                operation_type="invalid",
                content="Hello",
            )
            session.add(ver)
            with pytest.raises(IntegrityError):
                await session.commit()
            await session.rollback()

    @pytest.mark.asyncio
    async def test_cascade_delete_artifact(self) -> None:
        """Deleting artifact cascades to versions."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM artifact_versions"))
            await session.execute(text("DELETE FROM artifact_files"))
            await session.execute(text("DELETE FROM projects"))
            await session.execute(text("DELETE FROM applications"))
            await session.commit()

            _, _, art = await self._seed_app_project_artifact(session)

            ver = ArtifactVersion(
                version_id="ver-003",
                artifact_id=art.artifact_id,
                version_number=1,
                operation_type="snapshot",
                content="Hello",
            )
            session.add(ver)
            await session.commit()

            await session.delete(art)
            await session.commit()

            result = await session.execute(
                select(ArtifactVersion).where(ArtifactVersion.version_id == "ver-003")
            )
            assert result.scalar_one_or_none() is None
