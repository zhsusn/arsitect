"""AI CLI session business logic service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.cli_session import CliMessage, CliMessageType, CliSession, CliSessionStatus
from app.schemas.cli import CliMode


class CliService:
    """Orchestrates CLI session lifecycle and message history."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session.

        Args:
            session: SQLAlchemy async session.
        """
        self._session = session

    async def create_session(
        self,
        project_id: str,
        user_id: str,
        mode: str = "bug",
    ) -> CliSession:
        """Create a new CLI session.

        Args:
            project_id: Associated project ID.
            user_id: Creating user ID.
            mode: Working mode, either ``bug`` or ``arch``.

        Returns:
            Created CLI session.

        Raises:
            BadRequestError: If the mode is invalid.
        """
        if mode not in {CliMode.BUG, CliMode.ARCH}:
            raise BadRequestError(detail=f"Invalid CLI mode: {mode}")
        session = CliSession(
            project_id=project_id,
            user_id=user_id,
            mode=mode,
            status=CliSessionStatus.ACTIVE,
        )
        self._session.add(session)
        await self._session.flush()
        await self.add_message(
            session.id,
            CliMessageType.SYSTEM,
            f"欢迎使用 AI CLI 终端\n当前模式：{mode}",
        )
        return session

    async def get_session(self, session_id: str) -> CliSession:
        """Fetch a session by ID.

        Args:
            session_id: Session ID.

        Returns:
            CLI session.

        Raises:
            NotFoundError: If the session does not exist.
        """
        session = await self._session.get(CliSession, session_id)
        if session is None:
            raise NotFoundError(detail=f"Session '{session_id}' not found")
        return session

    async def close_session(self, session_id: str) -> CliSession:
        """Close a session and record the closed timestamp.

        Args:
            session_id: Session ID.

        Returns:
            Closed CLI session.
        """
        session = await self.get_session(session_id)
        if session.status == CliSessionStatus.CLOSED:
            return session
        session.status = CliSessionStatus.CLOSED
        session.closed_at = datetime.now(UTC)
        self._session.add(session)
        await self.add_message(
            session.id,
            CliMessageType.SYSTEM,
            "会话已关闭。",
        )
        return session

    async def switch_mode(self, session_id: str, mode: str) -> CliSession:
        """Switch a session's working mode.

        Args:
            session_id: Session ID.
            mode: Target mode, either ``bug`` or ``arch``.

        Returns:
            Updated CLI session.

        Raises:
            BadRequestError: If the mode is invalid or session is closed.
            NotFoundError: If the session does not exist.
        """
        if mode not in {CliMode.BUG, CliMode.ARCH}:
            raise BadRequestError(detail=f"Invalid CLI mode: {mode}")
        session = await self.get_session(session_id)
        if session.status == CliSessionStatus.CLOSED:
            raise BadRequestError(detail="Cannot switch mode of a closed session")
        session.mode = mode
        session.status = CliSessionStatus.ACTIVE
        self._session.add(session)
        await self.add_message(
            session.id,
            CliMessageType.SYSTEM,
            f"已切换至 {mode} 模式。",
        )
        return session

    async def list_messages(
        self,
        session_id: str,
        limit: int = 10,
    ) -> list[CliMessage]:
        """List the most recent messages in a session.

        Args:
            session_id: Session ID.
            limit: Maximum number of messages to return.

        Returns:
            List of CLI messages ordered by sequence ascending.
        """
        await self.get_session(session_id)
        stmt = (
            select(CliMessage)
            .where(CliMessage.session_id == session_id)
            .order_by(CliMessage.sequence_no.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(reversed(result.scalars().all()))

    async def add_message(
        self,
        session_id: str,
        message_type: str,
        content: str | None = None,
        card_data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CliMessage:
        """Append a message to a session.

        Args:
            session_id: Session ID.
            message_type: Message type.
            content: Text content.
            card_data: Optional card payload.
            metadata: Optional metadata.

        Returns:
            Created CLI message.
        """
        next_seq = await self._next_sequence(session_id)
        message = CliMessage(
            session_id=session_id,
            message_type=message_type,
            content=content,
            card_data=card_data,
            metadata=metadata,
            sequence_no=next_seq,
        )
        self._session.add(message)
        await self._session.flush()
        return message

    async def _next_sequence(self, session_id: str) -> int:
        """Compute the next message sequence number for a session.

        Args:
            session_id: Session ID.

        Returns:
            Next sequence number (starting at 1).
        """
        stmt = select(func.coalesce(func.max(CliMessage.sequence_no), 0)).where(
            CliMessage.session_id == session_id
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one()) + 1
