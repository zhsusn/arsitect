"""Tests for ArtifactRouter."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.project import Project
from app.services.artifact_service import ArtifactService
from main import app

client = TestClient(app)


class TestArtifactRouter:
    """ArtifactRouter integration tests."""

    async def _seed_app_and_project(self, session) -> tuple[Application, Project]:
        """Helper to seed application and project."""
        await session.execute(text("DELETE FROM artifact_versions"))
        await session.execute(text("DELETE FROM artifact_files"))
        await session.execute(text("DELETE FROM projects"))
        await session.execute(text("DELETE FROM applications"))
        await session.commit()

        app = Application(
            application_id="app-api",
            application_name="API App",
            local_path="/tmp/api",
        )
        session.add(app)
        await session.flush()

        proj = Project(
            project_id="proj-api",
            project_name="API Project",
            application_id=app.application_id,
            template_level="Standard",
        )
        session.add(proj)
        await session.commit()
        return app, proj

    @pytest.fixture
    async def seeded_project(self) -> Project:
        """Seed a project for router tests."""
        async with AsyncSessionLocal() as session:
            _, proj = await self._seed_app_and_project(session)
            return proj

    @pytest.mark.asyncio
    async def test_get_tree(self, seeded_project: Project, tmp_path) -> None:
        """GET /artifacts/tree returns directory tree."""
        async with AsyncSessionLocal() as session:
            svc = ArtifactService(session)
            await svc.create_artifact(
                artifact_id="art-api-1",
                project_id=seeded_project.project_id,
                file_name="req.md",
                file_path=str(tmp_path / "docs" / "req.md"),
                file_type="md",
                content="Requirements",
            )

        res = client.get(
            f"/api/v1/artifacts/tree?project_id={seeded_project.project_id}"
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 1
        directories = [d["directory"] for d in data]
        assert str(tmp_path / "docs") in directories

    @pytest.mark.asyncio
    async def test_get_tree_with_search(
        self, seeded_project: Project, tmp_path
    ) -> None:
        """GET /artifacts/tree?search= filters files."""
        async with AsyncSessionLocal() as session:
            svc = ArtifactService(session)
            await svc.create_artifact(
                artifact_id="art-api-2a",
                project_id=seeded_project.project_id,
                file_name="alpha.md",
                file_path=str(tmp_path / "alpha.md"),
                file_type="md",
                content="Alpha",
            )
            await svc.create_artifact(
                artifact_id="art-api-2b",
                project_id=seeded_project.project_id,
                file_name="beta.md",
                file_path=str(tmp_path / "beta.md"),
                file_type="md",
                content="Beta",
            )

        res = client.get(
            f"/api/v1/artifacts/tree?project_id={seeded_project.project_id}&search=alpha"
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert len(data[0]["files"]) == 1
        assert data[0]["files"][0]["file_name"] == "alpha.md"

    @pytest.mark.asyncio
    async def test_get_content(self, seeded_project: Project, tmp_path) -> None:
        """GET /artifacts/{id}/content returns content."""
        async with AsyncSessionLocal() as session:
            svc = ArtifactService(session)
            await svc.create_artifact(
                artifact_id="art-api-3",
                project_id=seeded_project.project_id,
                file_name="content.md",
                file_path=str(tmp_path / "content.md"),
                file_type="md",
                content="Hello API",
            )

        res = client.get("/api/v1/artifacts/art-api-3/content")
        assert res.status_code == 200
        data = res.json()
        assert data["artifact_id"] == "art-api-3"
        assert data["content"] == "Hello API"
        assert data["total_lines"] == 1
        assert data["content_hash"] != ""
        assert data["is_partial"] is False

    @pytest.mark.asyncio
    async def test_get_content_with_pagination(
        self, seeded_project: Project, tmp_path
    ) -> None:
        """GET /artifacts/{id}/content?offset=&limit= returns partial content."""
        async with AsyncSessionLocal() as session:
            svc = ArtifactService(session)
            lines = "\n".join([f"line {i}" for i in range(1, 6)])
            await svc.create_artifact(
                artifact_id="art-api-3p",
                project_id=seeded_project.project_id,
                file_name="lines.md",
                file_path=str(tmp_path / "lines.md"),
                file_type="md",
                content=lines,
            )

        res = client.get("/api/v1/artifacts/art-api-3p/content?offset=0&limit=2")
        assert res.status_code == 200
        data = res.json()
        assert data["content"] == "line 1\nline 2"
        assert data["total_lines"] == 5
        assert data["is_partial"] is True

        res2 = client.get("/api/v1/artifacts/art-api-3p/content?offset=2&limit=10")
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["content"] == "line 3\nline 4\nline 5"
        assert data2["is_partial"] is False

    @pytest.mark.asyncio
    async def test_get_content_not_found(self, seeded_project: Project) -> None:
        """GET unknown artifact returns 404."""
        res = client.get("/api/v1/artifacts/no-such-art/content")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_get_status(self, seeded_project: Project, tmp_path) -> None:
        """GET /artifacts/{id}/status returns status and hash."""
        async with AsyncSessionLocal() as session:
            svc = ArtifactService(session)
            await svc.create_artifact(
                artifact_id="art-api-status",
                project_id=seeded_project.project_id,
                file_name="status.md",
                file_path=str(tmp_path / "status.md"),
                file_type="md",
                content="Status test",
            )

        res = client.get("/api/v1/artifacts/art-api-status/status")
        assert res.status_code == 200
        data = res.json()
        assert data["artifact_id"] == "art-api-status"
        assert data["external_status"] == "normal"
        assert data["content_hash"] != ""
        assert data["current_version"] == 1

    @pytest.mark.asyncio
    async def test_save_content(self, seeded_project: Project, tmp_path) -> None:
        """PUT /artifacts/{id}/content saves content and creates version."""
        async with AsyncSessionLocal() as session:
            svc = ArtifactService(session)
            await svc.create_artifact(
                artifact_id="art-api-4",
                project_id=seeded_project.project_id,
                file_name="save.md",
                file_path=str(tmp_path / "save.md"),
                file_type="md",
                content="v1",
            )

        res = client.put(
            "/api/v1/artifacts/art-api-4/content",
            json={"content": "v2"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["version_number"] == 2
        assert data["operation_type"] == "snapshot"

    @pytest.mark.asyncio
    async def test_save_content_conflict(
        self, seeded_project: Project, tmp_path
    ) -> None:
        """PUT with wrong expected_hash returns 409."""
        async with AsyncSessionLocal() as session:
            svc = ArtifactService(session)
            await svc.create_artifact(
                artifact_id="art-api-4c",
                project_id=seeded_project.project_id,
                file_name="conflict.md",
                file_path=str(tmp_path / "conflict.md"),
                file_type="md",
                content="v1",
            )

        res = client.put(
            "/api/v1/artifacts/art-api-4c/content",
            json={"content": "v2", "expected_hash": "wronghash"},
        )
        assert res.status_code == 409

    @pytest.mark.asyncio
    async def test_list_versions(self, seeded_project: Project, tmp_path) -> None:
        """GET /artifacts/{id}/versions returns version list."""
        async with AsyncSessionLocal() as session:
            svc = ArtifactService(session)
            art = await svc.create_artifact(
                artifact_id="art-api-5",
                project_id=seeded_project.project_id,
                file_name="versions.md",
                file_path=str(tmp_path / "versions.md"),
                file_type="md",
                content="v1",
            )
            await svc.save_content(art.artifact_id, "v2")

        res = client.get("/api/v1/artifacts/art-api-5/versions")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 2
        assert data[0]["version_number"] == 2

    @pytest.mark.asyncio
    async def test_rollback(self, seeded_project: Project, tmp_path) -> None:
        """POST /artifacts/{id}/versions/{vn}/rollback rolls back."""
        async with AsyncSessionLocal() as session:
            svc = ArtifactService(session)
            art = await svc.create_artifact(
                artifact_id="art-api-6",
                project_id=seeded_project.project_id,
                file_name="rollback.md",
                file_path=str(tmp_path / "rollback.md"),
                file_type="md",
                content="original",
            )
            await svc.save_content(art.artifact_id, "modified")

        res = client.post("/api/v1/artifacts/art-api-6/versions/1/rollback")
        assert res.status_code == 200
        data = res.json()
        assert data["version_number"] == 3
        assert data["operation_type"] == "rollback"

        res2 = client.get("/api/v1/artifacts/art-api-6/content")
        assert res2.json()["content"] == "original"

    @pytest.mark.asyncio
    async def test_diff(self, seeded_project: Project, tmp_path) -> None:
        """GET /artifacts/{id}/versions/diff returns both contents."""
        async with AsyncSessionLocal() as session:
            svc = ArtifactService(session)
            art = await svc.create_artifact(
                artifact_id="art-api-7",
                project_id=seeded_project.project_id,
                file_name="diff.md",
                file_path=str(tmp_path / "diff.md"),
                file_type="md",
                content="v1",
            )
            await svc.save_content(art.artifact_id, "v2")

        res = client.get(
            "/api/v1/artifacts/art-api-7/versions/diff?from_version=1&to_version=2"
        )
        assert res.status_code == 200
        data = res.json()
        assert data["from_version"] == 1
        assert data["to_version"] == 2
        assert data["from_content"] == "v1"
        assert data["to_content"] == "v2"

    @pytest.mark.asyncio
    async def test_diff_not_found(self, seeded_project: Project) -> None:
        """GET diff with missing version returns 404."""
        res = client.get(
            "/api/v1/artifacts/no-such-art/versions/diff?from_version=1&to_version=2"
        )
        assert res.status_code == 404
