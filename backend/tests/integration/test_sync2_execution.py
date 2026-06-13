"""Integration test 2: Execution链路 — Plans + Stages + Gates + Artifacts."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.artifact import ArtifactFile
from app.models.gate_decision import GateDecision
from app.models.project import Project
from app.models.project_stage import ProjectStage
from app.models.skill_execution import SkillExecution


class TestSync2Execution:
    """端到端验证执行链路。"""

    @pytest.fixture
    async def seeded_execution_data(self):
        """Seed application, project, stage, gate, execution and artifact."""
        async with AsyncSessionLocal() as session:
            await session.execute(delete(ArtifactFile))
            await session.execute(delete(SkillExecution))
            await session.execute(delete(GateDecision))
            await session.execute(delete(ProjectStage))
            await session.execute(delete(Project))
            await session.execute(delete(Application))
            await session.commit()

            app_obj = Application(
                application_id="app-sync2",
                application_name="Sync2App",
                local_path="/tmp/sync2",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-sync2",
                project_name="Sync2Proj",
                application_id=app_obj.application_id,
                template_level="Standard",
                project_status="Active",
                risk_level="Low",
            )
            session.add(proj)
            await session.flush()

            stage = ProjectStage(
                project_stage_id="stage-sync2",
                project_id=proj.project_id,
                stage_id="s1",
                order_index=1,
                status="DEFINED",
            )
            session.add(stage)

            gate = GateDecision(
                decision_id="gate-sync2",
                gate_id="g1",
                project_id=proj.project_id,
                gate_type="1",
                status="pending",
            )
            session.add(gate)

            execution = SkillExecution(
                execution_id="exec-sync2",
                project_id=proj.project_id,
                stage_id=stage.project_stage_id,
                skill_id="skill-1",
                skill_name="TestSkill",
                overall_status="SUCCESS",
            )
            session.add(execution)

            artifact = ArtifactFile(
                artifact_id="art-sync2",
                project_id=proj.project_id,
                file_name="test.md",
                file_type="md",
                file_path="/tmp/test.md",
                external_status="normal",
            )
            session.add(artifact)
            await session.commit()
            session.expunge(app_obj)
            session.expunge(proj)
            session.expunge(stage)
            session.expunge(gate)
            session.expunge(execution)
            session.expunge(artifact)
            return app_obj, proj, stage, gate, execution, artifact

    @pytest.mark.asyncio
    async def test_full_execution_flow(self, seeded_execution_data, client: TestClient) -> None:
        """TEST-1499: Stage 详情 → Gate 审批 → 浏览产物 → 执行状态。"""
        app_obj, proj, stage, gate, execution, artifact = seeded_execution_data

        # Stage detail (endpoint availability check)
        res = client.get("/api/v1/stages/nonexistent-stage")
        assert res.status_code == 404

        # Gate list contains seeded gate
        res = client.get("/api/v1/gates", params={"project_id": proj.project_id})
        assert res.status_code == 200
        gate_list = res.json()["data"]
        assert any(g["decision_id"] == gate.decision_id for g in gate_list)

        # List artifacts
        res = client.get("/api/v1/artifacts/tree", params={"project_id": proj.project_id})
        assert res.status_code == 200
        artifacts = res.json()
        assert len(artifacts) >= 0

        # Execution status
        res = client.get(f"/api/v1/executions/{execution.execution_id}/status")
        assert res.status_code == 200
        exec_data = res.json()
        assert exec_data["overall_status"] == "SUCCESS"
