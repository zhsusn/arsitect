"""Tests for C4ReverseLocator."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from app.c4.binding_registry import C4BindingRegistry
from app.c4.reverse_locator import C4ReverseLocator
from app.models.application import Application
from app.models.c4_baseline import C4Baseline
from app.models.project import Project


class TestC4ReverseLocator:
    """C4ReverseLocator unit tests."""

    async def _seed_project_and_baseline(
        self, session, suffix: str = "1"
    ) -> tuple[Project, C4Baseline]:
        app = Application(
            application_id=f"app-rl-{suffix}",
            application_name=f"RlApp{suffix}",
            local_path=f"/tmp/rl{suffix}",
        )
        session.add(app)
        await session.flush()
        proj = Project(
            project_id=f"proj-rl-{suffix}",
            project_name=f"RlProj{suffix}",
            application_id=app.application_id,
            template_level="Standard",
        )
        session.add(proj)
        await session.flush()

        baseline = C4Baseline(
            baseline_id=f"c4-rl-{suffix}",
            project_id=proj.project_id,
            version="1.0.0",
            dsl_content="""workspace:
  model:
    containers:
      - id: WebApp
        name: Web Application
        technology: React
    components:
      - id: UserController
        name: User Controller
        properties:
          container_id: WebApp
""",
            dsl_hash="hash",
            level="L1-L4",
            is_current=True,
        )
        session.add(baseline)
        await session.flush()
        return proj, baseline

    @pytest.mark.asyncio
    async def test_locate_code_by_binding(self, db_session) -> None:
        """Precise binding returns code location."""
        proj, _ = await self._seed_project_and_baseline(db_session)
        registry = C4BindingRegistry(db_session)

        with tempfile.TemporaryDirectory() as tmpdir:
            real_file = Path(tmpdir) / "user.py"
            real_file.write_text("class UserController:")

            await registry.create_binding(
                project_id=proj.project_id,
                c4_node_id="UserController",
                c4_level="L3",
                artifact_id="src/user.py",
                relation_type="locates_at",
                source_location=str(real_file),
            )

            locator = C4ReverseLocator(None, registry, code_base_dir=tmpdir)
            loc = await locator.locate_code(proj.project_id, "UserController")
            assert loc is not None
            assert loc.file_path == str(real_file)

    @pytest.mark.asyncio
    async def test_locate_code_by_convention(self, db_session) -> None:
        """Fallback convention path derivation."""
        proj, _ = await self._seed_project_and_baseline(db_session)
        registry = C4BindingRegistry(db_session)

        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / proj.project_id
            src_dir = project_dir / "src"
            src_dir.mkdir(parents=True)
            (src_dir / "UserController.py").write_text("class UserController:")

            locator = C4ReverseLocator(None, registry, code_base_dir=tmpdir)
            loc = await locator.locate_code(proj.project_id, "UserController")
            assert loc is not None
            assert "UserController.py" in loc.file_path

    @pytest.mark.asyncio
    async def test_locate_node_by_binding(self, db_session) -> None:
        """Reverse: file path → C4 node via binding."""
        proj, _ = await self._seed_project_and_baseline(db_session)
        registry = C4BindingRegistry(db_session)
        await registry.create_binding(
            project_id=proj.project_id,
            c4_node_id="UserController",
            c4_level="L3",
            artifact_id="/code/user.py",
            relation_type="locates_at",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            locator = C4ReverseLocator(None, registry, code_base_dir=tmpdir)
            node = await locator.locate_node(proj.project_id, "/code/user.py")
            assert node is not None
            assert node.node_id == "UserController"
            assert node.node_type == "Component"
            assert node.level == "L3"

    @pytest.mark.asyncio
    async def test_locate_node_by_filename(self, db_session) -> None:
        """Fallback filename matching against DSL components."""
        proj, baseline = await self._seed_project_and_baseline(db_session)
        registry = C4BindingRegistry(db_session)

        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_store = AsyncMockBaselineStore(baseline.dsl_content)
            locator = C4ReverseLocator(baseline_store, registry, code_base_dir=tmpdir)
            node = await locator.locate_node(proj.project_id, "/any/UserController.py")
            assert node is not None
            assert node.node_id == "UserController"

    @pytest.mark.asyncio
    async def test_batch_queries(self, db_session) -> None:
        """Batch locate returns dict with all keys."""
        proj, _ = await self._seed_project_and_baseline(db_session)
        registry = C4BindingRegistry(db_session)

        with tempfile.TemporaryDirectory() as tmpdir:
            locator = C4ReverseLocator(None, registry, code_base_dir=tmpdir)
            results = await locator.locate_codes_batch(proj.project_id, ["A", "B"])
            assert set(results.keys()) == {"A", "B"}


class AsyncMockBaselineStore:
    """Minimal mock for C4BaselineStore."""

    def __init__(self, dsl_content: str) -> None:
        self.dsl_content = dsl_content

    async def read_current(self, project_id: str):
        from datetime import datetime

        from app.c4.baseline_store import BaselineDTO

        return BaselineDTO(
            baseline_id="mock",
            project_id=project_id,
            version="1.0.0",
            dsl_content=self.dsl_content,
            dsl_hash="hash",
            level="L1-L4",
            is_current=True,
            created_at=datetime.utcnow(),
        )
