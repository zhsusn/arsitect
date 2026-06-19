"""Unit tests for CliService."""

from __future__ import annotations

import pytest

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.cli_session import CliMessageType, CliSessionStatus
from app.schemas.cli import CliMode
from app.services.cli_service import CliService


class TestCliService:
    """CliService lifecycle and message history tests."""

    async def test_create_session_bug(self, cli_service: CliService) -> None:
        """TEST-1501: Creates a bug-mode session and seeds a welcome message."""
        session = await cli_service.create_session("proj-1", "user-1", CliMode.BUG)

        assert session.project_id == "proj-1"
        assert session.user_id == "user-1"
        assert session.mode == CliMode.BUG
        assert session.status == CliSessionStatus.ACTIVE

        messages = await cli_service.list_messages(session.id)
        assert len(messages) == 1
        assert messages[0].message_type == CliMessageType.SYSTEM
        assert "bug" in messages[0].content.lower()

    async def test_create_session_arch(self, cli_service: CliService) -> None:
        """TEST-1502: Creates an arch-mode session."""
        session = await cli_service.create_session("proj-1", "user-1", CliMode.ARCH)

        assert session.mode == CliMode.ARCH

    async def test_create_session_invalid_mode(self, cli_service: CliService) -> None:
        """TEST-1503: Invalid mode raises BadRequestError."""
        with pytest.raises(BadRequestError, match="Invalid CLI mode"):
            await cli_service.create_session("proj-1", "user-1", "unknown")

    async def test_get_session(self, cli_service: CliService) -> None:
        """TEST-1504: get_session returns the created session."""
        created = await cli_service.create_session("proj-1", "user-1")
        fetched = await cli_service.get_session(created.id)

        assert fetched.id == created.id

    async def test_get_session_not_found(self, cli_service: CliService) -> None:
        """TEST-1505: get_session raises NotFoundError for missing session."""
        with pytest.raises(NotFoundError, match="Session 'missing' not found"):
            await cli_service.get_session("missing")

    async def test_close_session(self, cli_service: CliService) -> None:
        """TEST-1506: close_session marks the session closed and records timestamp."""
        session = await cli_service.create_session("proj-1", "user-1")
        closed = await cli_service.close_session(session.id)

        assert closed.status == CliSessionStatus.CLOSED
        assert closed.closed_at is not None

        messages = await cli_service.list_messages(session.id)
        assert any(m.message_type == CliMessageType.SYSTEM for m in messages)

    async def test_close_session_already_closed(self, cli_service: CliService) -> None:
        """TEST-1507: Closing an already closed session is idempotent."""
        session = await cli_service.create_session("proj-1", "user-1")
        first = await cli_service.close_session(session.id)
        second = await cli_service.close_session(session.id)

        assert second.status == CliSessionStatus.CLOSED
        assert second.id == first.id

    async def test_switch_mode(self, cli_service: CliService) -> None:
        """TEST-1508: switch_mode changes the session mode and reactivates it."""
        session = await cli_service.create_session("proj-1", "user-1", CliMode.BUG)
        updated = await cli_service.switch_mode(session.id, CliMode.ARCH)

        assert updated.mode == CliMode.ARCH
        assert updated.status == CliSessionStatus.ACTIVE

    async def test_switch_mode_invalid(self, cli_service: CliService) -> None:
        """TEST-1509: Invalid target mode raises BadRequestError."""
        session = await cli_service.create_session("proj-1", "user-1")
        with pytest.raises(BadRequestError, match="Invalid CLI mode"):
            await cli_service.switch_mode(session.id, "unknown")

    async def test_switch_mode_closed_session(self, cli_service: CliService) -> None:
        """TEST-1510: Mode switch on a closed session raises BadRequestError."""
        session = await cli_service.create_session("proj-1", "user-1")
        await cli_service.close_session(session.id)

        with pytest.raises(BadRequestError, match="Cannot switch mode of a closed session"):
            await cli_service.switch_mode(session.id, CliMode.ARCH)

    async def test_add_message(self, cli_service: CliService) -> None:
        """TEST-1511: add_message appends a message with auto-increment sequence."""
        session = await cli_service.create_session("proj-1", "user-1")
        message = await cli_service.add_message(
            session.id,
            CliMessageType.USER,
            content="hello",
            card_data={"key": "value"},
            metadata={"meta": "data"},
        )

        assert message.session_id == session.id
        assert message.message_type == CliMessageType.USER
        assert message.content == "hello"
        assert message.card_data == {"key": "value"}
        assert message.sequence_no == 2  # after welcome message

    async def test_list_messages_order_and_limit(
        self,
        cli_service: CliService,
    ) -> None:
        """TEST-1512: list_messages returns the most recent messages in ascending order."""
        session = await cli_service.create_session("proj-1", "user-1")
        for i in range(5):
            await cli_service.add_message(session.id, CliMessageType.USER, content=f"msg-{i}")

        messages = await cli_service.list_messages(session.id, limit=3)
        assert len(messages) == 3
        assert [m.content for m in messages] == ["msg-2", "msg-3", "msg-4"]
        assert all(
            messages[i].sequence_no < messages[i + 1].sequence_no for i in range(len(messages) - 1)
        )
