"""Tests for C4 governance fix planner and strategies."""

from __future__ import annotations

import pytest

from app.c4.governance_fix.models import ChangeSet, FixPlan, GovernanceIssue, RiskLevel, RootCause
from app.c4.governance_fix.planner import FixPlanner
from app.c4.governance_fix.strategies.add_relationship_doc import AddRelationshipDocStrategy
from app.c4.governance_fix.strategies.create_code_skeleton import CreateCodeSkeletonStrategy


@pytest.fixture
def workspace_model() -> dict:
    return {
        "workspace": {
            "model": {
                "containers": [
                    {"id": "frontend-spa", "name": "Frontend"},
                    {"id": "backend-api", "name": "Backend API"},
                ],
                "components": [
                    {"id": "dashboard", "name": "Dashboard", "properties": {"container_id": "frontend-spa"}}
                ],
                "relationships": [],
            }
        }
    }


@pytest.mark.asyncio
async def test_create_code_skeleton_for_missing_component(workspace_model: dict) -> None:
    issue = GovernanceIssue(
        issue_id="i-1",
        source="validator",
        rule_id="CON-C2F-001",
        severity="MEDIUM",
        message="Component missing code",
        c4_node_id="user-card",
        root_cause=RootCause.CODE_MISSING,
    )
    strategy = CreateCodeSkeletonStrategy()
    changes = await strategy.plan(issue, "p", {"workspace_model": workspace_model})

    assert len(changes) == 1
    assert changes[0].action == "CREATE_FILE"
    assert changes[0].target_path == "frontend/src/components/user-card.tsx"
    assert "TODO: implement user-card" in changes[0].after


@pytest.mark.asyncio
async def test_add_relationship_doc_for_missing_edge(workspace_model: dict) -> None:
    issue = GovernanceIssue(
        issue_id="i-2",
        source="validator",
        rule_id="IMP-F2C-001",
        severity="HIGH",
        message="Relationship missing in DSL",
        node_ids=["dashboard", "backend-api"],
        root_cause=RootCause.DSL_MISSING_RELATIONSHIP,
    )
    strategy = AddRelationshipDocStrategy()
    changes = await strategy.plan(
        issue,
        "p",
        {
            "workspace_model": workspace_model,
            "registry": {"components": {"dashboard": {"container_id": "frontend-spa"}}},
        },
    )

    assert len(changes) == 1
    assert changes[0].action == "EDIT_DSL"
    assert "dashboard" in changes[0].after
    assert "backend-api" in changes[0].after
    assert changes[0].risk_level == RiskLevel.MEDIUM


@pytest.mark.asyncio
async def test_planner_selects_strategies(workspace_model: dict) -> None:
    issue = GovernanceIssue(
        issue_id="i-3",
        source="validator",
        rule_id="CON-C2F-001",
        severity="MEDIUM",
        message="Component missing code",
        c4_node_id="task-list",
        root_cause=RootCause.CODE_MISSING,
    )
    planner = FixPlanner()
    plans = await planner.plan([issue], "p", {"workspace_model": workspace_model})

    assert len(plans) == 1
    assert plans[0].project_id == "p"
    assert plans[0].issue_ids == ["i-3"]
    assert len(plans[0].changes) == 1
    assert plans[0].changes[0].action == "CREATE_FILE"


@pytest.mark.asyncio
async def test_planner_returns_empty_for_unsupported_issue(workspace_model: dict) -> None:
    issue = GovernanceIssue(
        issue_id="i-4",
        source="validator",
        rule_id="UNKNOWN-001",
        severity="LOW",
        message="Unknown issue",
        root_cause=RootCause.OTHER,
    )
    planner = FixPlanner()
    plans = await planner.plan([issue], "p", {"workspace_model": workspace_model})
    assert plans == []


def test_batch_order_prefers_lower_risk() -> None:
    low_risk = FixPlan(
        project_id="p",
        issue_ids=["l"],
        changes=[
            ChangeSet(
                action="CREATE_FILE",
                target_path="a.py",
                before="",
                after="",
                rationale="",
                risk_level=RiskLevel.LOW,
                issue_id="l",
            )
        ],
    )
    high_risk = FixPlan(
        project_id="p",
        issue_ids=["h"],
        changes=[
            ChangeSet(
                action="DELETE_FILE",
                target_path="b.py",
                before="",
                after="",
                rationale="",
                risk_level=RiskLevel.HIGH,
                issue_id="h",
            )
        ],
    )
    planner = FixPlanner([])
    ordered = planner.suggest_batch_order([high_risk, low_risk])
    assert ordered[0].issue_ids == ["l"]
    assert ordered[1].issue_ids == ["h"]
