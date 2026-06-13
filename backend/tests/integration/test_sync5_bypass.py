"""Integration test 5: Bypass链路 - 旁路审批端到端验证.

Covers DR-017 / FR-Bypass-001 ~ FR-Bypass-004:
- 申请旁路
- 列表查询
- 审批闭环

Test-IDs: TEST-1504 ~ TEST-1507
Policy: default
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.application import Application
from app.models.bypass_record import BypassRecord
from app.models.execution_plan import ExecutionPlan
from app.models.gate_decision import GateDecision
from app.models.project import Project


class TestSync5Bypass:
    """端到端验证 HITL Bypass Approval 主链路."""

    @pytest.fixture
    async def seeded_project_with_plan(self) -> tuple[Project, ExecutionPlan]:
        """Seed application, project and execution plan."""
        async with AsyncSessionLocal() as session:
            await session.execute(delete(BypassRecord))
            await session.execute(delete(GateDecision))
            await session.execute(delete(ExecutionPlan))
            await session.execute(delete(Project))
            await session.execute(delete(Application))
            await session.commit()

            app_obj = Application(
                application_id="app-bypass-int",
                application_name="Bypass Integration App",
                local_path="/tmp/bypass-int",
            )
            session.add(app_obj)
            await session.flush()

            proj = Project(
                project_id="proj-bypass-int",
                project_name="Bypass Integration Project",
                application_id=app_obj.application_id,
                template_level="Standard",
            )
            session.add(proj)
            await session.flush()

            plan = ExecutionPlan(
                plan_id=f"plan-{proj.project_id}",
                project_id=proj.project_id,
                version="1.0.0",
                is_frozen=False,
                template_level="Standard",
            )
            session.add(plan)
            await session.flush()

            gate = GateDecision(
                decision_id="gate-1",
                gate_id="gate-1",
                project_id=proj.project_id,
                gate_type="1",
                status="pending",
            )
            session.add(gate)
            await session.commit()
            session.expunge(proj)
            session.expunge(plan)
            return proj, plan

    @pytest.mark.asyncio
    async def test_bypass_full_flow(self, seeded_project_with_plan: tuple[Project, ExecutionPlan], client: TestClient) -> None:
        """TEST-1504: Bypass 申请 -> 列表 -> 审批闭环.

        Covers AC-F-001 / AC-F-003 / AC-F-005 / AC-F-008.
        """
        proj, plan = seeded_project_with_plan

        # APPLY bypass
        apply_payload = {
            "plan_id": plan.plan_id,
            "stage_id": "stage-1",
            "skill_id": "skill-1",
            "triggered_by": "user-1",
            "reason": "Production hotfix required",
            "authorizer_token": "x" * 32,  # 32-byte dummy token matching schema min-length
            "deadline_hours": 24,
        }
        res = client.post("/api/v1/gates/gate-1/bypass", json=apply_payload)
        assert res.status_code == 200
        created = res.json()
        record_id = created["record_id"]
        assert created["status"] == "PENDING_POST_APPROVAL"
        assert created["reason"] == "Production hotfix required"

        # LIST bypass applications
        res = client.get(f"/api/v1/projects/{proj.project_id}/bypass-applications")
        assert res.status_code == 200
        apps = res.json()
        assert isinstance(apps, list)
        assert any(a["record_id"] == record_id for a in apps)

        # APPROVE bypass
        approve_payload = {"approved_by": "admin-1"}
        res = client.post(
            f"/api/v1/bypass-applications/{record_id}/approve",
            json=approve_payload,
        )
        assert res.status_code == 200
        approved = res.json()
        assert approved["status"] == "CLOSED"

    @pytest.mark.asyncio
    async def test_bypass_apply_short_reason(self, seeded_project_with_plan: tuple[Project, ExecutionPlan], client: TestClient) -> None:
        """TEST-1505: 理由过短返回 422.

        Covers AC-V-002: 输入长度校验.
        """
        proj, plan = seeded_project_with_plan
        payload = {
            "plan_id": plan.plan_id,
            "stage_id": "stage-1",
            "skill_id": "skill-1",
            "triggered_by": "user-1",
            "reason": "x",
            "authorizer_token": "x" * 32,
        }
        res = client.post("/api/v1/gates/gate-1/bypass", json=payload)
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_bypass_approve_not_found(self, seeded_project_with_plan: tuple[Project, ExecutionPlan], client: TestClient) -> None:
        """TEST-1506: 审批不存在的记录返回 404.

        Covers AC-E-002: 记录缺失.
        """
        res = client.post(
            "/api/v1/bypass-applications/no-such-record/approve",
            json={"approved_by": "admin-1"},
        )
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_bypass_list_empty(self, seeded_project_with_plan: tuple[Project, ExecutionPlan], client: TestClient) -> None:
        """TEST-1507: 无旁路记录时列表为空.

        Covers edge case: 空列表.
        """
        proj, _ = seeded_project_with_plan
        res = client.get(f"/api/v1/projects/{proj.project_id}/bypass-applications")
        assert res.status_code == 200
        apps = res.json()
        assert apps == []
