"""Unit tests for LLM policy API."""

from __future__ import annotations

from typing import Any


def test_list_templates(client: Any) -> None:
    """TEST-1840: list built-in policy templates."""
    resp = client.get("/api/v1/llm/policies/templates")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert {t["id"] for t in data["items"]} == {"personal", "team", "enterprise"}


def test_create_and_get_policy(client: Any) -> None:
    """TEST-1841: create and retrieve a policy with rules."""
    create_resp = client.post(
        "/api/v1/llm/policies",
        json={
            "name": "Test Policy",
            "key": "test-policy",
            "scope": "global",
            "default_mode": "ask",
            "rules": [
                {
                    "category": "file_system",
                    "action_type": "file_read",
                    "permission": "allow",
                    "pattern": "${PROJECT_ROOT}/**",
                }
            ],
        },
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    policy_id = created["id"]
    assert len(created["rules"]) == 1

    get_resp = client.get(f"/api/v1/llm/policies/{policy_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["name"] == "Test Policy"
    assert data["rules"][0]["pattern"] == "${PROJECT_ROOT}/**"


def test_apply_template(client: Any) -> None:
    """TEST-1842: apply template replaces rules and resets customization."""
    policy_resp = client.post(
        "/api/v1/llm/policies",
        json={
            "name": "Apply Target",
            "key": "apply-target",
            "scope": "global",
            "default_mode": "ask",
            "rules": [],
        },
    )
    policy_id = policy_resp.json()["id"]

    resp = client.post(
        "/api/v1/llm/policies/apply-template",
        json={"template_id": "personal", "base_policy_id": policy_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["template_id"] == "personal"
    assert data["is_customized"] is False
    assert len(data["rules"]) > 0


def test_check_permission(client: Any) -> None:
    """TEST-1843: permission check endpoint returns engine result."""
    policy_resp = client.post(
        "/api/v1/llm/policies",
        json={
            "name": "Check Policy",
            "key": "check-policy",
            "scope": "global",
            "default_mode": "deny",
            "rules": [
                {
                    "category": "file_system",
                    "action_type": "file_write",
                    "permission": "allow",
                    "pattern": "src/**",
                }
            ],
        },
    )
    policy_id = policy_resp.json()["id"]

    resp = client.post(
        "/api/v1/llm/policies/check",
        json={
            "policy_id": policy_id,
            "action_type": "file_write",
            "target": "src/main.py",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["permission"] == "allow"
    assert data["allowed"] is True
