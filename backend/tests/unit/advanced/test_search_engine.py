"""Tests for SearchEngine — project-wide artifact/C4/fragment search."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.advanced.search_engine import SearchEngine
from app.c4.baseline_store import C4BaselineStore
from app.docforge.fragment_registry import FragmentCreateDTO, FragmentRegistry
from app.models.application import Application
from app.models.c4_baseline import C4Baseline
from app.models.project import Project


class TestSearchEngine:
    """SearchEngine unit tests."""

    @pytest.fixture
    def dsl_content(self) -> str:
        """Sample C4 DSL with containers and components."""
        return """
workspace:
  model:
    containers:
      - id: web
        name: Web Application
        technology: React
      - id: api
        name: API Server
        technology: FastAPI
    components:
      - id: order_ctrl
        name: OrderController
"""

    async def _seed_project(
        self,
        session,
        project_id: str,
        dsl_content: str,
    ) -> None:
        """Seed application, project, baseline and fragments."""
        app_obj = Application(
            application_id=f"app-{project_id}",
            application_name=f"App {project_id}",
            local_path="/tmp/test",
        )
        session.add(app_obj)
        await session.flush()

        project = Project(
            project_id=project_id,
            project_name=f"Project {project_id}",
            application_id=app_obj.application_id,
            template_level="Standard",
        )
        session.add(project)
        await session.flush()

        baseline = C4Baseline(
            project_id=project_id,
            version="1.0.0",
            dsl_content=dsl_content,
            dsl_hash="abc",
            level="L1-L4",
            is_current=True,
        )
        session.add(baseline)
        await session.flush()

    async def _seed_artifacts(
        self,
        project_id: str,
        base_dir: Path,
    ) -> None:
        """Create sample artifact files on disk."""
        artifacts_dir = base_dir / "projects" / project_id / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        (artifacts_dir / "design.md").write_text(
            "# Order design\nThis describes order processing.",
            encoding="utf-8",
        )
        (artifacts_dir / "README.md").write_text("# Overview", encoding="utf-8")
        binary = artifacts_dir / "image.png"
        binary.write_bytes(b"\x89PNG\r\n\x1a\n\xff\xfe")

    async def _seed_fragments(
        self,
        session,
        project_id: str,
    ) -> None:
        """Seed document fragments via FragmentRegistry."""
        registry = FragmentRegistry(session)
        await registry.create(
            FragmentCreateDTO(
                project_id=project_id,
                title="Order Spec",
                slug="order-spec",
                doc_type="PRD",
                content="Order creation flow and payment rules.",
            )
        )
        await registry.create(
            FragmentCreateDTO(
                project_id=project_id,
                title="User Manual",
                slug="user-manual",
                doc_type="OTHER",
                content="How to use the dashboard.",
            )
        )

    @pytest.mark.asyncio
    async def test_search_artifacts(
        self,
        db_session,
        tmp_path: Path,
        monkeypatch,
        dsl_content: str,
    ) -> None:
        """Search should find artifacts by filename and content."""
        monkeypatch.chdir(tmp_path)
        await self._seed_project(db_session, "proj-se", dsl_content)
        await self._seed_artifacts("proj-se", tmp_path)

        engine = SearchEngine(
            FragmentRegistry(db_session),
            C4BaselineStore(db_session),
        )
        results = await engine.search("proj-se", "order")

        types = {r.type for r in results}
        assert "artifact" in types
        artifact_titles = {r.title for r in results if r.type == "artifact"}
        assert "design.md" in artifact_titles

    @pytest.mark.asyncio
    async def test_search_c4_nodes(
        self,
        db_session,
        tmp_path: Path,
        monkeypatch,
        dsl_content: str,
    ) -> None:
        """Search should return matching C4 containers and components."""
        monkeypatch.chdir(tmp_path)
        await self._seed_project(db_session, "proj-se", dsl_content)

        engine = SearchEngine(
            FragmentRegistry(db_session),
            C4BaselineStore(db_session),
        )
        results = await engine.search("proj-se", "api")

        c4_results = [r for r in results if r.type == "c4_node"]
        assert len(c4_results) >= 1
        assert any("API Server" in r.title for r in c4_results)

    @pytest.mark.asyncio
    async def test_search_fragments(
        self,
        db_session,
        tmp_path: Path,
        monkeypatch,
        dsl_content: str,
    ) -> None:
        """Search should return matching document fragments."""
        monkeypatch.chdir(tmp_path)
        await self._seed_project(db_session, "proj-se", dsl_content)
        await self._seed_fragments(db_session, "proj-se")

        engine = SearchEngine(
            FragmentRegistry(db_session),
            C4BaselineStore(db_session),
        )
        results = await engine.search("proj-se", "payment")

        fragments = [r for r in results if r.type == "fragment"]
        assert len(fragments) == 1
        assert fragments[0].title == "Order Spec"

    @pytest.mark.asyncio
    async def test_search_with_type_filter(
        self,
        db_session,
        tmp_path: Path,
        monkeypatch,
        dsl_content: str,
    ) -> None:
        """Type filter should restrict results to a single source."""
        monkeypatch.chdir(tmp_path)
        await self._seed_project(db_session, "proj-se", dsl_content)
        await self._seed_artifacts("proj-se", tmp_path)
        await self._seed_fragments(db_session, "proj-se")

        engine = SearchEngine(
            FragmentRegistry(db_session),
            C4BaselineStore(db_session),
        )
        results = await engine.search("proj-se", "order", filters={"type": "c4"})

        assert all(r.type == "c4_node" for r in results)

    @pytest.mark.asyncio
    async def test_search_no_baseline_returns_no_c4(
        self,
        db_session,
        tmp_path: Path,
        monkeypatch,
    ) -> None:
        """Missing C4 baseline should not break search; C4 results empty."""
        monkeypatch.chdir(tmp_path)
        await self._seed_project(db_session, "proj-no-base", "")

        engine = SearchEngine(
            FragmentRegistry(db_session),
            C4BaselineStore(db_session),
        )
        results = await engine.search("proj-no-base", "api")

        assert not any(r.type == "c4_node" for r in results)

    @pytest.mark.asyncio
    async def test_search_binary_file_ignored(
        self,
        db_session,
        tmp_path: Path,
        monkeypatch,
        dsl_content: str,
    ) -> None:
        """Binary files that cannot be decoded should still appear by name."""
        monkeypatch.chdir(tmp_path)
        await self._seed_project(db_session, "proj-se", dsl_content)
        await self._seed_artifacts("proj-se", tmp_path)

        engine = SearchEngine(
            FragmentRegistry(db_session),
            C4BaselineStore(db_session),
        )
        results = await engine.search("proj-se", "image.png")

        artifacts = [r for r in results if r.type == "artifact"]
        assert len(artifacts) == 1
        assert artifacts[0].title == "image.png"
