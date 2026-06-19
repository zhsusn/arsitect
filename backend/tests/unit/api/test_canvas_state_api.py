"""Tests for CanvasStateRouter."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.canvas_state import CanvasState
from app.models.project import Project
from app.models.project_path_config import ProjectPathConfig
from app.models.template import Template
from app.models.template_stage import TemplateStage
from main import app

client = TestClient(app)


class TestCanvasStateRouter:
    """Canvas state API tests."""

    async def _seed_project(self, session, suffix: str = "1") -> Project:
        """Helper to create an application + project."""
        app_obj = Application(
            application_id=f"app-csapi-{suffix}",
            application_name=f"CsApiApp{suffix}",
            local_path=f"/tmp/csapi{suffix}",
        )
        session.add(app_obj)
        await session.flush()
        proj = Project(
            project_id=f"proj-csapi-{suffix}",
            project_name=f"CsApiProj{suffix}",
            application_id=app_obj.application_id,
            template_level="Standard",
            project_status="Active",
            risk_level="Low",
        )
        session.add(proj)
        await session.flush()
        return proj

    @pytest.mark.asyncio
    async def test_get_canvas_state_not_found(self) -> None:
        """GET returns 404 when canvas state does not exist."""
        res = client.get("/api/v1/projects/proj-missing/canvas/state")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_save_and_get_canvas_state(self) -> None:
        """POST creates canvas state; GET returns it."""
        async with AsyncSessionLocal() as session:
            proj = await self._seed_project(session, suffix="crud")
            await session.commit()

        payload = {
            "nodes": [
                {
                    "id": "n1",
                    "type": "stage",
                    "position": {"x": 0, "y": 0},
                    "data": {"label": "Stage 1", "status": "DEFINED"},
                }
            ],
            "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
            "viewport": {"x": 10, "y": 20, "zoom": 1.2},
        }

        res = client.post(f"/api/v1/projects/{proj.project_id}/canvas/state", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["project_id"] == proj.project_id
        assert len(data["nodes"]) == 1
        assert data["nodes"][0]["id"] == "n1"
        assert data["edges"][0]["source"] == "n1"
        assert data["viewport"]["zoom"] == 1.2

        res2 = client.get(f"/api/v1/projects/{proj.project_id}/canvas/state")
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["project_id"] == proj.project_id
        assert data2["nodes"][0]["data"]["status"] == "DEFINED"

    @pytest.mark.asyncio
    async def test_update_canvas_state(self) -> None:
        """POST updates existing canvas state."""
        async with AsyncSessionLocal() as session:
            proj = await self._seed_project(session, suffix="update")
            cs = CanvasState(
                canvas_state_id="cs-upd",
                project_id=proj.project_id,
                nodes="[]",
                edges="[]",
                viewport='{"x":0,"y":0,"zoom":1}',
            )
            session.add(cs)
            await session.commit()

        payload = {
            "nodes": [{"id": "n2", "position": {"x": 100, "y": 200}, "data": {"label": "Updated"}}],
            "edges": [],
            "viewport": {"x": 50, "y": 50, "zoom": 0.8},
        }

        res = client.post(f"/api/v1/projects/{proj.project_id}/canvas/state", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert len(data["nodes"]) == 1
        assert data["nodes"][0]["data"]["label"] == "Updated"
        assert data["viewport"]["zoom"] == 0.8

    @pytest.mark.asyncio
    async def test_get_canvas_state_includes_merge_group(self) -> None:
        """GET auto-generated canvas state exposes merge group metadata."""
        async with AsyncSessionLocal() as session:
            app_obj = Application(
                application_id="app-csapi-merge",
                application_name="CsApiMergeApp",
                local_path="/tmp/csapi-merge",
            )
            session.add(app_obj)
            await session.flush()

            tpl = Template(
                template_id="Trivial",
                template_name="Trivial 模板",
                description="Trivial",
                stage_count=3,
                estimated_skill_count=3,
                applicable_complexity="Trivial",
                default_execution_strategy="full_auto",
                merge_policy_json='{"groups": [{"group_id": "g1", "label": "项目立项", "business_stage_keys": ["brainstorm", "charter"], "gate_at_end": true, "auto_advance": true}, {"group_id": "g2", "label": "需求对齐", "business_stage_keys": ["clarify", "align"], "gate_at_end": true, "auto_advance": true}, {"group_id": "g3", "label": "设计实现", "business_stage_keys": ["contract-hld", "contract-dd", "build", "verify", "release"], "gate_at_end": true, "auto_advance": true}]}',
            )
            session.add(tpl)
            await session.flush()

            stages = [
                TemplateStage(
                    stage_id="ts-charter",
                    stage_name="项目立项",
                    business_stage_key="charter",
                    order_index=1,
                    template_id="Trivial",
                    primary_skill_id="requirement-analysis",
                ),
                TemplateStage(
                    stage_id="ts-align",
                    stage_name="需求对齐",
                    business_stage_key="align",
                    order_index=2,
                    template_id="Trivial",
                    primary_skill_id="prd-generation",
                ),
                TemplateStage(
                    stage_id="ts-release",
                    stage_name="设计实现",
                    business_stage_key="release",
                    order_index=3,
                    template_id="Trivial",
                    primary_skill_id="release-management",
                ),
            ]
            session.add_all(stages)
            await session.flush()

            proj = Project(
                project_id="proj-csapi-merge",
                project_name="CsApiMergeProj",
                application_id=app_obj.application_id,
                template_level="Trivial",
                project_status="Active",
                risk_level="Low",
                merge_policy_json=tpl.merge_policy_json,
            )
            session.add(proj)
            await session.flush()

            session.add(
                ProjectPathConfig(
                    config_id="cfg-csapi-merge",
                    project_id=proj.project_id,
                    template_level="Trivial",
                    execution_strategy="full_auto",
                    merge_policy_json=tpl.merge_policy_json,
                )
            )
            await session.commit()

        res = client.get(f"/api/v1/projects/{proj.project_id}/canvas/state")
        assert res.status_code == 200
        data = res.json()
        stage_nodes = [n for n in data["nodes"] if n.get("type") == "stage"]
        assert len(stage_nodes) == 3

        merged = [n for n in stage_nodes if n["data"].get("is_merged")]
        assert len(merged) >= 1
        assert all(len(n["data"]["merged_stage_keys"]) > 1 for n in merged)

        release_node = next(
            (n for n in stage_nodes if n["data"]["label"] == "设计实现"), None
        )
        assert release_node is not None
        assert release_node["data"]["merge_group_label"] == "设计实现"
        assert set(release_node["data"]["merged_stage_keys"]) == {
            "contract-hld",
            "contract-dd",
            "build",
            "verify",
            "release",
        }
