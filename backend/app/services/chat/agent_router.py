"""Agent router for chat sessions."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cli_session import ChatTaskMode, CliMessageType, CliSession
from app.schemas.cli import (
    BugRecordCreate,
    CliCard,
    CliCardAction,
    CliResponse,
    CliResponsePayload,
    ErrorResponse,
)
from app.services.bug_fix_service import BugFixService
from app.services.chat_service import ChatService
from app.services.cli_service import CliService
from app.services.llm import get_llm_provider

Sender = Callable[[dict[str, Any]], Awaitable[None]]


def _now_ms() -> int:
    """Return current timestamp in milliseconds."""
    return int(datetime.now(UTC).timestamp() * 1000)


def _text_response(session_id: str, text: str) -> CliResponse:
    """Build a text CLI response."""
    return CliResponse(
        type="text",
        session_id=session_id,
        timestamp=_now_ms(),
        payload=CliResponsePayload.model_construct(text=text),
    )


def _thinking_response(session_id: str, text: str) -> CliResponse:
    """Build a thinking CLI response."""
    return CliResponse(
        type="thinking",
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


class AgentRouter:
    """Routes incoming chat commands to the appropriate agent handler."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with an async session.

        Args:
            db: SQLAlchemy async session.
        """
        self._db = db
        self._chat_service = ChatService(db)
        self._cli_service = CliService(db)

    async def handle_command(
        self,
        session: CliSession,
        text: str,
        payload: dict[str, Any] | None,
        sender: Sender,
    ) -> None:
        """Route a user command based on session task mode.

        Args:
            session: Active chat session.
            text: User input text.
            payload: Optional parsed request payload.
            sender: Async callable used to push CLI responses.
        """
        await sender(_text_response(session.id, f"收到：{text}").model_dump())
        await self._cli_service.add_message(session.id, CliMessageType.USER, content=text)

        metadata = (payload.get("metadata") if payload else None) or {}

        # Skill shortcuts override task mode.
        if text.startswith("/"):
            await self._handle_skill(session, text, metadata, sender)
            return

        if session.task_mode == ChatTaskMode.BUG.value:
            await self._run_bug_mode(session, text, sender)
        elif session.task_mode == ChatTaskMode.ARCH_FIX.value:
            await self._run_arch_fix_mode(session, text, metadata, sender)
        else:
            await self._run_free_chat(session, text, metadata, sender)

    async def _handle_skill(
        self,
        session: CliSession,
        text: str,
        metadata: dict[str, Any],
        sender: Sender,
    ) -> None:
        """Handle slash-command skill shortcuts."""
        from app.services.arch_governance_service import ArchGovernanceService

        command = text.split()[0].lower()
        if command == "/bug":
            session.task_mode = ChatTaskMode.BUG.value
            self._db.add(session)
            await self._db.flush()
            await sender(_text_response(session.id, "已切换至 Bug 修复模式。").model_dump())
        elif command in {"/arch", "/scan"}:
            session.task_mode = ChatTaskMode.ARCH_FIX.value
            self._db.add(session)
            await self._db.flush()
            await sender(_text_response(session.id, "已切换至架构治理模式。").model_dump())
        elif command == "/fix":
            plan = metadata.get("plan")
            project_id = metadata.get("project_id") or session.project_id
            if plan:
                session.task_mode = ChatTaskMode.ARCH_FIX.value
                session.context_json = {"plan": plan, "project_id": project_id}
                self._db.add(session)
                await self._db.flush()
                arch_svc = ArchGovernanceService(self._db)
                await arch_svc.apply_fix_plan(
                    session_id=session.id,
                    project_id=project_id,
                    plan=plan,
                    sender=sender,
                )
            else:
                await sender(
                    _text_response(session.id, "请先生成修复方案，或使用 /arch 进入架构治理模式。").model_dump()
                )
        else:
            await sender(
                _text_response(
                    session.id,
                    f"未知技能：{command}。可用：/bug /arch /scan /fix /explain",
                ).model_dump()
            )

    async def _run_free_chat(
        self,
        session: CliSession,
        text: str,
        metadata: dict[str, Any],
        sender: Sender,
    ) -> None:
        """Run a free-form chat response via the configured LLM provider."""
        provider = metadata.get("provider") or session.llm_provider or "kimi-cli"
        llm = get_llm_provider(provider)

        await sender(_thinking_response(session.id, "AI 正在思考...").model_dump())

        try:
            system_prompt = (
                "你是 Arsitect 平台的 AI 助手，帮助用户完成软件工程全生命周期任务。"
                "回答简洁、专业，使用中文。"
            )
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ]

            collected: list[str] = []

            async def _on_chunk(chunk: str) -> None:
                collected.append(chunk)
                await sender(_thinking_response(session.id, chunk).model_dump())

            response_text = await llm.chat_stream(messages, on_chunk=_on_chunk)
            await sender(_text_response(session.id, response_text).model_dump())
        except Exception as exc:  # noqa: BLE001
            await sender(
                _error_response(session.id, "LLM_ERROR", f"AI 调用失败：{exc}").model_dump()
            )

    async def _run_bug_mode(
        self,
        session: CliSession,
        text: str,
        sender: Sender,
    ) -> None:
        """Run bug-fix mode logic."""
        bug_svc = BugFixService(self._db)
        try:
            bug = await bug_svc.save_bug_record(
                BugRecordCreate(
                    project_id=session.project_id,
                    session_id=session.id,
                    error_input=text,
                )
            )
            bug = await bug_svc.generate_fix_plan(bug.id)
            card = CliCard(
                type="fix-proposal",
                data={
                    "bug_id": bug.id,
                    "root_cause": bug.root_cause,
                    "affected_files": bug.affected_files,
                    "risk": bug.fix_risk,
                    "diff": bug.fix_diff,
                },
                actions=[
                    CliCardAction(label="执行修复", command="Y", style="primary"),
                    CliCardAction(label="忽略", command="N", style="danger"),
                    CliCardAction(label="编辑后执行", command="edit", style=None),
                ],
            )
            await sender(
                CliResponse(
                    type="card",
                    session_id=session.id,
                    timestamp=_now_ms(),
                    payload=CliResponsePayload.model_construct(card=card),
                ).model_dump()
            )
        except Exception as exc:  # noqa: BLE001
            await sender(
                _error_response(session.id, "BUG_ANALYSIS_FAILED", str(exc)).model_dump()
            )

    async def _run_arch_fix_mode(
        self,
        session: CliSession,
        text: str,
        metadata: dict[str, Any],
        sender: Sender,
    ) -> None:
        """Run architecture fix mode logic."""
        from app.services.arch_governance_service import ArchGovernanceService

        context = session.context_json or {}
        plan = metadata.get("plan") or context.get("plan")
        project_id = metadata.get("project_id") or context.get("project_id") or session.project_id

        if plan:
            arch_svc = ArchGovernanceService(self._db)
            await arch_svc.apply_fix_plan(
                session_id=session.id,
                project_id=project_id,
                plan=plan,
                sender=sender,
            )
        else:
            await sender(
                _text_response(
                    session.id,
                    "架构修复模式：请从架构治理页面选择问题并生成修复方案，或发送 /fix plan=...",
                ).model_dump()
            )
