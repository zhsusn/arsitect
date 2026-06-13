"""Chat API routes."""

from __future__ import annotations

from collections.abc import Awaitable
from contextlib import suppress
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.infrastructure.database.session import get_db
from app.models.cli_session import CliMessageType
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionModeRequest,
    ChatSessionResponse,
)
from app.schemas.cli import (
    CliRequest,
    CliResponse,
    CliResponsePayload,
    CliSessionCloseResponse,
    CliSessionResponse,
    ErrorResponse,
)
from app.services.chat.agent_router import AgentRouter
from app.services.chat_service import ChatService

router = APIRouter(tags=["chat"])


def _current_user_id() -> str:
    """Placeholder authentication dependency."""
    return "user-mvp"


def _now_ms() -> int:
    """Return the current Unix timestamp in milliseconds."""
    return int(datetime.now(UTC).timestamp() * 1000)


def _text_response(session_id: str, text: str) -> CliResponse:
    """Build a text CLI response."""
    return CliResponse(
        type="text",
        session_id=session_id,
        timestamp=_now_ms(),
        payload=CliResponsePayload.model_construct(text=text),
    )


def _error_response(session_id: str, code: str, message: str) -> CliResponse:
    """Build an error CLI response."""
    return CliResponse(
        type="error",
        session_id=session_id,
        timestamp=_now_ms(),
        payload=CliResponsePayload.model_construct(
            error=ErrorResponse.model_construct(code=code, message=message)
        ),
    )


async def _safe_send(websocket: WebSocket, data: dict[str, Any]) -> bool:
    """Send JSON data over a WebSocket, swallowing disconnect errors."""
    try:
        await websocket.send_json(data)
        return True
    except WebSocketDisconnect:
        return False
    except RuntimeError:
        return False


@router.post(
    "/chat/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat_session(
    dto: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(_current_user_id),
) -> ChatSessionResponse:
    """Create a new chat session."""
    svc = ChatService(db)
    session = await svc.create_session(
        project_id=dto.project_id,
        user_id=user_id,
        task_mode=dto.task_mode,
        llm_provider=dto.llm_provider,
    )
    return ChatSessionResponse(
        session=CliSessionResponse.model_validate(session),
        messages=[],
        history=[],
    )


@router.get(
    "/chat/sessions/{session_id}/history",
    response_model=ChatSessionResponse,
)
async def get_chat_session_history(
    session_id: str,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionResponse:
    """Get recent messages for a chat session."""
    svc = ChatService(db)
    session = await svc.get_session(session_id)
    messages = await svc.list_messages(session_id, limit=limit)
    return ChatSessionResponse(
        session=CliSessionResponse.model_validate(session),
        messages=[],
        history=[CliSessionResponse.model_validate(m) for m in messages],
    )


@router.post(
    "/chat/sessions/{session_id}/close",
    response_model=CliSessionCloseResponse,
)
async def close_chat_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> CliSessionCloseResponse:
    """Close a chat session."""
    svc = ChatService(db)
    await svc.close_session(session_id)
    return CliSessionCloseResponse(status="closed", session_id=session_id)


@router.post(
    "/chat/sessions/{session_id}/mode",
    response_model=CliSessionResponse,
)
async def update_chat_session_mode(
    session_id: str,
    dto: ChatSessionModeRequest,
    db: AsyncSession = Depends(get_db),
) -> CliSessionResponse:
    """Update a chat session's task mode and/or provider."""
    svc = ChatService(db)
    session = await svc.update_mode(
        session_id=session_id,
        task_mode=dto.task_mode,
        llm_provider=dto.llm_provider,
        context_json=dto.context_json,
    )
    return CliSessionResponse.model_validate(session)


@router.websocket("/chat/ws/{session_id}")
async def chat_websocket(
    websocket: WebSocket,
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """WebSocket endpoint for interactive chat sessions."""
    await websocket.accept()
    chat_svc = ChatService(db)
    agent_router = AgentRouter(db)

    def sender(data: dict[str, Any]) -> Awaitable[None]:
        async def _send() -> None:
            await _safe_send(websocket, data)

        return _send()

    try:
        session = await chat_svc.get_session(session_id)
    except NotFoundError as exc:
        if await _safe_send(
            websocket,
            _error_response(session_id, "SESSION_NOT_FOUND", str(exc)).model_dump(),
        ):
            await websocket.close()
        return

    if not await _safe_send(
        websocket,
        _text_response(session_id, f"已连接会话 {session_id}，当前模式：{session.task_mode}").model_dump(),
    ):
        return

    try:
        while True:
            raw = await websocket.receive_json()
            try:
                request = CliRequest.model_validate(raw)
            except Exception as exc:
                await _safe_send(
                    websocket,
                    _error_response(session_id, "INVALID_MESSAGE", f"Invalid message: {exc}").model_dump(),
                )
                continue

            if request.type == "ping":
                await _safe_send(
                    websocket,
                    CliResponse(
                        type="pong",
                        session_id=session_id,
                        timestamp=_now_ms(),
                        payload=CliResponsePayload.model_construct(),
                    ).model_dump(),
                )
                continue

            if request.type == "abort":
                await _safe_send(
                    websocket,
                    _text_response(session_id, "已中止当前任务。").model_dump(),
                )
                continue

            if request.type == "action":
                command = request.payload.command or ""
                metadata = request.payload.metadata or {}
                await chat_svc._cli_service.add_message(
                    session_id,
                    CliMessageType.USER,
                    content=f"[action] {command}",
                )
                if command in {"fix", "skip", "edit", "Y", "N"} and metadata.get("change"):
                    from app.services.arch_governance_service import ArchGovernanceService

                    arch_svc = ArchGovernanceService(db)
                    project_id = metadata.get("project_id") or session.project_id
                    await arch_svc.handle_change_action(
                        session_id=session_id,
                        project_id=project_id,
                        command=command if command not in {"Y", "N"} else "fix" if command == "Y" else "skip",
                        metadata=metadata,
                        sender=sender,
                    )
                elif command in {"Y", "N", "edit"} and metadata.get("bug_id"):
                    from app.services.bug_fix_service import BugFixService

                    bug_svc = BugFixService(db)
                    bug_id = str(metadata.get("bug_id"))
                    if command == "N":
                        await bug_svc.ignore_fix(bug_id)
                        await sender(_text_response(session_id, "已忽略该 Bug 修复建议。").model_dump())
                    elif command == "Y":
                        result = await bug_svc.execute_fix(bug_id)
                        await sender(
                            _text_response(
                                session_id,
                                f"Bug 修复已执行：{result.success and '成功' or '失败'}",
                            ).model_dump()
                        )
                    else:
                        edited_diff = metadata.get("edited_diff")
                        result = await bug_svc.execute_fix(bug_id, edited_diff=edited_diff)
                        await sender(
                            _text_response(
                                session_id,
                                f"Bug 修复已执行：{result.success and '成功' or '失败'}",
                            ).model_dump()
                        )
                else:
                    await _safe_send(
                        websocket,
                        _text_response(session_id, f"已执行操作：{command}").model_dump(),
                    )
                continue

            if request.type in {"command", "input"}:
                text = request.payload.text or request.payload.command or ""
                payload = request.payload.model_dump() if request.payload else None
                if not text:
                    await _safe_send(
                        websocket,
                        _error_response(session_id, "EMPTY_INPUT", "请输入内容").model_dump(),
                    )
                    continue
                await agent_router.handle_command(session, text, payload, sender)
                continue

            await _safe_send(
                websocket,
                _error_response(session_id, "UNSUPPORTED_TYPE", f"Unsupported type: {request.type}").model_dump(),
            )
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        await _safe_send(
            websocket,
            _error_response(session_id, "INTERNAL_ERROR", f"Unexpected error: {exc}").model_dump(),
        )
        with suppress(Exception):
            await websocket.close()
