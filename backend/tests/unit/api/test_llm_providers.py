"""Unit tests for LLM provider API."""

from __future__ import annotations

from typing import Any


def test_list_providers_empty(client: Any) -> None:
    """TEST-1830: list providers returns empty list."""
    resp = client.get("/api/v1/llm/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_create_and_get_provider(client: Any) -> None:
    """TEST-1831: create and retrieve a provider."""
    create_resp = client.post(
        "/api/v1/llm/providers",
        json={
            "name": "Kimi CLI",
            "key": "kimi-default",
            "scope": "global",
            "provider_type": "kimi-cli",
            "config_json": {"kimi_cli_path": "kimi"},
        },
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    provider_id = created["id"]

    get_resp = client.get(f"/api/v1/llm/providers/{provider_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["name"] == "Kimi CLI"
    assert "api_key" not in data


def test_delete_default_provider_forbidden(client: Any) -> None:
    """TEST-1832: deleting default provider is forbidden."""
    create_resp = client.post(
        "/api/v1/llm/providers",
        json={
            "name": "Default",
            "key": "default",
            "scope": "global",
            "provider_type": "kimi-cli",
            "is_default": True,
        },
    )
    provider_id = create_resp.json()["id"]
    delete_resp = client.delete(f"/api/v1/llm/providers/{provider_id}")
    assert delete_resp.status_code == 400


def test_set_default_provider(client: Any) -> None:
    """TEST-1833: set provider as default."""
    p1 = client.post(
        "/api/v1/llm/providers",
        json={
            "name": "First",
            "key": "first",
            "scope": "global",
            "provider_type": "kimi-cli",
            "is_default": True,
        },
    ).json()
    p2 = client.post(
        "/api/v1/llm/providers",
        json={
            "name": "Second",
            "key": "second",
            "scope": "global",
            "provider_type": "kimi-cli",
        },
    ).json()

    resp = client.post(f"/api/v1/llm/providers/{p2['id']}/set-default")
    assert resp.status_code == 200

    first = client.get(f"/api/v1/llm/providers/{p1['id']}").json()
    assert first["is_default"] is False
    second = client.get(f"/api/v1/llm/providers/{p2['id']}").json()
    assert second["is_default"] is True
