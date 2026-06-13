"""Tests for C4 governance fix plan API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_generate_fix_plan_endpoint(client: TestClient) -> None:
    """The fix-plan endpoint should return a preview plan for known issues."""
    payload = {
        "issues": [
            {
                "issue_id": "con-1",
                "source": "consistency",
                "rule_id": "CON-C2F-001",
                "severity": "ERROR",
                "message": "组件缺少代码实现",
                "node_ids": [],
                "c4_node_id": "user-card",
                "code_entity_id": "",
                "fix_hint": "",
                "fix_action": "",
                "root_cause": "CODE_MISSING",
            }
        ],
        "context": {
            "workspace_model": {
                "workspace": {
                    "model": {
                        "containers": [{"id": "frontend-spa", "name": "Frontend"}],
                        "components": [],
                        "relationships": [],
                    }
                }
            },
            "registry": {"components": {}},
            "code_entities": [],
        },
    }
    res = client.post("/api/v1/c4/governance/fix-plan?project_id=test", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["project_id"] == "test"
    assert len(data["plans"]) == 1
    assert data["plans"][0]["changes"][0]["action"] == "CREATE_FILE"


@pytest.mark.asyncio
async def test_generate_fix_plan_empty_issues(client: TestClient) -> None:
    res = client.post("/api/v1/c4/governance/fix-plan?project_id=test", json={"issues": []})
    assert res.status_code == 200
    assert res.json()["plans"] == []
