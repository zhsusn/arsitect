"""Chat session business logic service."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.cli_session import (
    ChatTaskMode,
    CliMessage,
    CliMessageType,
    CliSession,
    CliSessionStatus,
)
from app.services.cli_service import CliService


class ChatService:
    """Orchestrates chat session lifecycle and message history."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session.

        Args:
            session: SQLAlchemy async session.
        """
        self._session = session
        self._cli_service = CliService(session)

    async def create_session(
        self,
        project_id: str,
        user_id: str,
        task_mode: str = ChatTaskMode.FREE_CHAT.value,
        llm_provider: str | None = None,
    ) -> CliSession:
        """Create a new chat session.

        Args:
            project_id: Associated project ID.
            user_id: Creating user ID.
            task_mode: Task mode for the session.
            llm_provider: Optional LLM provider identifier.

        Returns:
            Created chat session.

        Raises:
            BadRequestError: If the task mode is invalid.
        """
        if task_mode not in {m.value for m in ChatTaskMode}:
            raise BadRequestError(detail=f"Invalid task mode: {task_mode}")

        session = CliSession(
            project_id=project_id,
            user_id=user_id,
            mode="bug",  # Kept for backwards compatibility with CliSession.mode.
            task_mode=task_mode,
            llm_provider=llm_provider,
            status=CliSessionStatus.ACTIVE,
            context_json={},
        )
        self._session.add(session)
        await self._session.flush()
        await self._cli_service.add_message(
            session.id,
            CliMessageType.SYSTEM,
            f"欢迎使用 AI 助手\n当前模式：{task_mode}",
        )
        return session

    async def get_session(self, session_id: str) -> CliSession:
        """Fetch a session by ID.

        Args:
            session_id: Session ID.

        Returns:
            Chat session.

        Raises:
            NotFoundError: If the session does not exist.
        """
        session = await self._session.get(CliSession, session_id)
        if session is None:
            raise NotFoundError(detail=f"Session '{session_id}' not found")
        return session

    async def list_messages(
        self,
        session_id: str,
        limit: int = 50,
    ) -> list[CliMessage]:
        """List the most recent messages in a session.

        Args:
            session_id: Session ID.
            limit: Maximum number of messages to return.

        Returns:
            List of messages ordered by sequence ascending.
        """
        return await self._cli_service.list_messages(session_id, limit=limit)

    async def close_session(self, session_id: str) -> CliSession:
        """Close a chat session.

        Args:
            session_id: Session ID.

        Returns:
            Closed session.
        """
        return await self._cli_service.close_session(session_id)

    async def update_mode(
        self,
        session_id: str,
        task_mode: str | None = None,
        llm_provider: str | None = None,
        context_json: dict[str, Any] | None = None,
    ) -> CliSession:
        """Update a session's task mode, provider, and/or context.

        Args:
            session_id: Session ID.
            task_mode: Optional new task mode.
            llm_provider: Optional new LLM provider.
            context_json: Optional context to merge into existing context.

        Returns:
            Updated session.

        Raises:
            BadRequestError: If the task mode is invalid.
            NotFoundError: If the session does not exist.
        """
        session = await self.get_session(session_id)

        if task_mode is not None:
            if task_mode not in {m.value for m in ChatTaskMode}:
                raise BadRequestError(detail=f"Invalid task mode: {task_mode}")
            session.task_mode = task_mode

        if llm_provider is not None:
            session.llm_provider = llm_provider

        if context_json is not None:
            current_context = session.context_json or {}
            current_context.update(context_json)
            session.context_json = current_context

        self._session.add(session)
        await self._session.flush()
        return session
