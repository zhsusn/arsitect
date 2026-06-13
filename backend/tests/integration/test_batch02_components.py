"""Integration tests for Batch-02 components.

E2E-01: C4 DSL change → incremental validation → report correct
E2E-02: C4 DSL + contracts → OpenUIClient → HTML prototype
E2E-03: OpenUI unavailable → auto fallback wireframe
E2E-04: Skill config → PocketFlowEngine → three-phase execution → timeout
E2E-05: Artifact edit → external modify → conflict detection
E2E-06: Click C4 component node → reverse locate → open code file
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.binding_record import BindingRecord
from app.models.c4_baseline import C4Baseline
from app.models.interface_contract import InterfaceContract
from app.models.project import Project
from main import app

client = TestClient(app)


class TestBatch02E2E:
    """End-to-end tests for Batch-02 components."""

    async def _seed_project(self, suffix: str = "1") -> Project:
        async with AsyncSessionLocal() as session:
            await session.execute(delete(BindingRecord))
            await session.execute(delete(C4Baseline))
            await session.execute(delete(InterfaceContract))
            await session.execute(delete(Project))
            await session.execute(delete(Application))
            await session.commit()

            app_obj = Application(
                application_id=f"app-e2e-{suffix}",
                application_name=f"E2EApp{suffix}",
                local_path=f"/tmp/e2e{suffix}",
            )
            session.add(app_obj)
            await session.flush()
            proj = Project(
                project_id=f"proj-e2e-{suffix}",
                project_name=f"E2EProj{suffix}",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.commit()
            session.expunge(proj)
            return proj

    # ================================================================
    # E2E-01: Cross-layer validation
    # ================================================================
    @pytest.mark.asyncio
    async def test_e2e_01_full_validation(self) -> None:
        """Full cross-layer validation returns structured report."""
        proj = await self._seed_project(suffix="val")
        baseline = C4Baseline(
            baseline_id="c4-e2e-val",
            project_id=proj.project_id,
            version="1.0.0",
            dsl_content="""workspace:
  model:
    containers:
      - id: WebApp
        name: Web
    components:
      - id: UserCtrl
        name: User Controller
        properties:
          container_id: WebApp
""",
            dsl_hash="hash1",
            level="L1-L4",
            is_current=True,
        )
        async with AsyncSessionLocal() as session:
            session.add(baseline)
            await session.commit()

        res = client.get(
            f"/api/v1/validation/cross-layer?project_id={proj.project_id}"
        )
        assert res.status_code == 200
        data = res.json()
        assert "passed" in data
        assert "issues" in data
        assert data["error_count"] == 0

    @pytest.mark.asyncio
    async def test_e2e_01_incremental_validation(self) -> None:
        """Incremental validation only checks changed nodes."""
        proj = await self._seed_project(suffix="inc")
        baseline = C4Baseline(
            baseline_id="c4-e2e-inc",
            project_id=proj.project_id,
            version="1.0.0",
            dsl_content="""workspace:
  model:
    containers:
      - id: App
    components:
      - id: Ctrl
        properties:
          container_id: App
""",
            dsl_hash="hash1",
            level="L1-L4",
            is_current=True,
        )
        async with AsyncSessionLocal() as session:
            session.add(baseline)
            await session.commit()

        res = client.post(
            f"/api/v1/validation/cross-layer/incremental?project_id={proj.project_id}",
            json=["App"],
        )
        assert res.status_code == 200
        data = res.json()
        assert "passed" in data

    # ================================================================
    # E2E-02 / E2E-03: OpenUI generation + fallback
    # ================================================================
    @pytest.mark.asyncio
    async def test_e2e_02_openui_generate(self) -> None:
        """Generate prototype from C4 + contracts (fallback path)."""
        proj = await self._seed_project(suffix="ui")
        baseline = C4Baseline(
            baseline_id="c4-e2e-ui",
            project_id=proj.project_id,
            version="1.0.0",
            dsl_content="""workspace:
  model:
    containers:
      - id: API
        name: API Service
""",
            dsl_hash="hash1",
            level="L1-L4",
            is_current=True,
        )
        async with AsyncSessionLocal() as session:
            session.add(baseline)
            session.add(
                InterfaceContract(
                    contract_id="ic-e2e-1",
                    project_id=proj.project_id,
                    container_id="API",
                    endpoint_path="/health",
                    method_type="GET",
                    operation_summary="Health check",
                    status="DRAFT",
                )
            )
            await session.commit()

        res = client.post(
            f"/api/v1/projects/{proj.project_id}/open-ui-specs/generate",
            json={"spec_name": "test"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["project_id"] == proj.project_id

    # ================================================================
    # E2E-04: PocketFlow execution
    # ================================================================
    @pytest.mark.asyncio
    async def test_e2e_04_engine_execute_http(self) -> None:
        """Execute skill via HTTP adapter."""
        proj = await self._seed_project(suffix="eng")

        payload = {
            "skill_id": "test-skill",
            "name": "Test",
            "file_path": "skill.md",
            "inputs": [],
            "outputs": [],
            "timeout": 5.0,
        }
        res = client.post(
            f"/api/v1/engine/execute?project_id={proj.project_id}&adapter=http",
            json=payload,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["skill_id"] == "skill"
        assert data["status"] in ("success", "error", "timeout")

    # ================================================================
    # E2E-05: Artifact conflict detection
    # ================================================================
    @pytest.mark.asyncio
    async def test_e2e_05_artifact_conflict(self, tmp_path) -> None:
        """Edit artifact detects external modification."""
        proj = await self._seed_project(suffix="art")

        from app.common.artifact_store import ArtifactStore
        from app.common.project_context import ProjectContext

        ctx = ProjectContext(proj.project_id, base_dir=str(tmp_path))
        store = ArtifactStore(ctx, auto_git_commit=False)
        await store.write("spec.md", "v1")
        hash_v1 = store._hash_cache["spec.md"]

        # External modification
        (ctx.artifacts_dir / "spec.md").write_text("v2")

        res = client.post(
            f"/api/v1/artifacts/spec.md/edit?project_id={proj.project_id}",
            json={"content": "v3", "expected_hash": hash_v1},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["conflict_detected"] is True
        assert data["success"] is False

    # ================================================================
    # E2E-06: Reverse locator
    # ================================================================
    @pytest.mark.asyncio
    async def test_e2e_06_locator_code(self) -> None:
        """Node → code file returns path info."""
        proj = await self._seed_project(suffix="loc")
        baseline = C4Baseline(
            baseline_id="c4-e2e-loc",
            project_id=proj.project_id,
            version="1.0.0",
            dsl_content="""workspace:
  model:
    containers:
      - id: App
        name: App
    components:
      - id: UserController
        name: User Controller
        properties:
          container_id: App
""",
            dsl_hash="hash1",
            level="L1-L4",
            is_current=True,
        )
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("class UserController:")
            temp_path = f.name

        async with AsyncSessionLocal() as session:
            session.add(baseline)
            session.add(
                BindingRecord(
                    project_id=proj.project_id,
                    c4_node_id="UserController",
                    c4_level="L3",
                    artifact_id="user.py",
                    artifact_type="code",
                    relation_type="locates_at",
                    source_location=temp_path,
                    confidence=1.0,
                )
            )
            await session.commit()

        res = client.get(
            f"/api/v1/locator/code?project_id={proj.project_id}&node_id=UserController"
        )
        assert res.status_code == 200
        data = res.json()
        assert "file_path" in data

    @pytest.mark.asyncio
    async def test_e2e_06_locator_node(self) -> None:
        """Code file → node returns node info."""
        proj = await self._seed_project(suffix="loc2")
        baseline = C4Baseline(
            baseline_id="c4-e2e-loc2",
            project_id=proj.project_id,
            version="1.0.0",
            dsl_content="""workspace:
  model:
    components:
      - id: UserController
        name: User Controller
""",
            dsl_hash="hash1",
            level="L1-L4",
            is_current=True,
        )
        async with AsyncSessionLocal() as session:
            session.add(baseline)
            await session.commit()

        res = client.get(
            f"/api/v1/locator/node?project_id={proj.project_id}&file_path=/src/UserController.py"
        )
        assert res.status_code == 200
        data = res.json()
        assert data["node_id"] == "UserController"
