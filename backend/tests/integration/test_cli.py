"""Integration tests for AI CLI Terminal endpoints.

Covers CLI-001 ~ CLI-005:
- Create session
- Fetch message history
- Close session
- Switch session mode
- Interactive WebSocket command exchange
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestCliIntegration:
    """End-to-end verification of the CLI REST and WebSocket surface."""

    @pytest.fixture
    async def session_id(self, client: TestClient) -> str:
        """Create a CLI session and return its ID."""
        response = client.post(
            "/api/v1/cli/sessions",
            json={"project_id": "proj-cli-int", "mode": "bug"},
        )
        assert response.status_code == 201
        return response.json()["id"]

    @pytest.mark.asyncio
    async def test_create_session(self, client: TestClient) -> None:
        """TEST-1531: POST /cli/sessions creates a session and returns schema fields."""
        response = client.post(
            "/api/v1/cli/sessions",
            json={"project_id": "proj-cli-create", "mode": "arch"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["project_id"] == "proj-cli-create"
        assert data["mode"] == "arch"
        assert data["status"] == "active"
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_get_session_history(self, client: TestClient, session_id: str) -> None:
        """TEST-1532: GET /cli/sessions/{id}/history returns the welcome message."""
        response = client.get(f"/api/v1/cli/sessions/{session_id}/history")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) >= 1
        assert data["data"][0]["message_type"] == "system"

    @pytest.mark.asyncio
    async def test_close_session(self, client: TestClient, session_id: str) -> None:
        """TEST-1533: POST /cli/sessions/{id}/close closes the session."""
        response = client.post(f"/api/v1/cli/sessions/{session_id}/close")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["status"] == "closed"

    @pytest.mark.asyncio
    async def test_switch_session_mode(self, client: TestClient, session_id: str) -> None:
        """TEST-1534: POST /cli/sessions/{id}/mode switches the working mode."""
        response = client.post(
            f"/api/v1/cli/sessions/{session_id}/mode",
            json={"mode": "arch"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["mode"] == "arch"
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_websocket_command_exchange(
        self,
        client: TestClient,
        session_id: str,
    ) -> None:
        """TEST-1535: WebSocket accepts a command and returns text + fix-proposal card."""
        with client.websocket_connect(f"/api/v1/cli/ws/{session_id}") as ws:
            connected = ws.receive_json()
            assert connected["type"] == "text"
            assert session_id in connected["payload"]["text"]

            ws.send_json(
                {
                    "type": "command",
                    "session_id": session_id,
                    "payload": {"text": "ValueError: integration test"},
                }
            )

            echo = ws.receive_json()
            assert echo["type"] == "text"
            assert "ValueError" in echo["payload"]["text"]

            card = ws.receive_json()
            assert card["type"] == "card"
            assert card["payload"]["card"]["type"] == "fix-proposal"
            assert "bug_id" in card["payload"]["card"]["data"]

            ws.send_json({"type": "ping", "session_id": session_id, "payload": {}})
            pong = ws.receive_json()
            assert pong["type"] == "pong"

    @pytest.mark.asyncio
    async def test_websocket_apply_arch_fix_plan(
        self,
        client: TestClient,
    ) -> None:
        """TEST-1536: WebSocket accepts apply_arch_fix_plan and streams progress + done."""
        response = client.post(
            "/api/v1/cli/sessions",
            json={"project_id": "proj-arch-fix", "mode": "arch"},
        )
        assert response.status_code == 201
        session_id = response.json()["id"]

        with client.websocket_connect(f"/api/v1/cli/ws/{session_id}") as ws:
            connected = ws.receive_json()
            assert connected["type"] == "text"

            ws.send_json(
                {
                    "type": "command",
                    "session_id": session_id,
                    "payload": {
                        "text": "apply_arch_fix_plan",
                        "metadata": {
                            "action": "apply_arch_fix_plan",
                            "project_id": "proj-arch-fix",
                            "plan": {"plans": []},
                        },
                    },
                }
            )

            echo = ws.receive_json()
            assert echo["type"] == "text"

            # Consume progress/text messages until the terminal done message.
            for _ in range(10):
                msg = ws.receive_json()
                if msg["type"] == "done":
                    break
            else:
                raise AssertionError("Expected done message not received")
