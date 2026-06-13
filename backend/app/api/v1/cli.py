"""AI CLI Terminal API routes."""

from __future__ import annotations

from collections.abc import Awaitable
from contextlib import suppress
from typing import Any

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.infrastructure.database.session import get_db
from app.models.cli_session import CliMessageType
from app.schemas.cli import (
    ArchIssueListResponse,
    ArchIssueResponse,
    ArchScanRequest,
    ArchScanResponse,
    BugRecordCreate,
    BugRecordExecuteRequest,
    BugRecordListResponse,
    BugRecordResponse,
    CliCard,
    CliCardAction,
    CliMessageListResponse,
    CliMessageResponse,
    CliRequest,
    CliRequestPayload,
    CliResponse,
    CliResponsePayload,
    CliSessionCloseResponse,
    CliSessionCreate,
    CliSessionModeRequest,
    CliSessionResponse,
    ErrorResponse,
    ExecResult,
    ScanRule,
)
from app.services.arch_governance_service import ArchGovernanceService
from app.services.bug_fix_service import BugFixService
from app.services.cli_service import CliService

router = APIRouter(tags=["cli"])


def _current_user_id() -> str:
    """Placeholder authentication dependency.

    Returns:
        Fixed user ID for MVP.
    """
    return "user-mvp"


@router.post(
    "/cli/sessions",
    response_model=CliSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_cli_session(
    dto: CliSessionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(_current_user_id),
) -> CliSessionResponse:
    """Create a new AI CLI session."""
    svc = CliService(db)
    session = await svc.create_session(
        project_id=dto.project_id,
        user_id=user_id,
        mode=dto.mode,
    )
    return CliSessionResponse.model_validate(session)


@router.get(
    "/cli/sessions/{session_id}/history",
    response_model=CliMessageListResponse,
)
async def get_cli_session_history(
    session_id: str,
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> CliMessageListResponse:
    """Get recent messages for a CLI session."""
    svc = CliService(db)
    messages = await svc.list_messages(session_id, limit=limit)
    return CliMessageListResponse(
        data=[CliMessageResponse.model_validate(m) for m in messages]
    )


@router.post(
    "/cli/sessions/{session_id}/close",
    response_model=CliSessionCloseResponse,
)
async def close_cli_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> CliSessionCloseResponse:
    """Close a CLI session."""
    svc = CliService(db)
    await svc.close_session(session_id)
    return CliSessionCloseResponse(status="closed", session_id=session_id)


@router.post(
    "/cli/sessions/{session_id}/mode",
    response_model=CliSessionResponse,
)
async def switch_cli_session_mode(
    session_id: str,
    dto: CliSessionModeRequest,
    db: AsyncSession = Depends(get_db),
) -> CliSessionResponse:
    """Switch the working mode of a CLI session."""
    svc = CliService(db)
    session = await svc.switch_mode(session_id, dto.mode)
    return CliSessionResponse.model_validate(session)


@router.post("/bugs", response_model=BugRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_bug_record(
    dto: BugRecordCreate,
    db: AsyncSession = Depends(get_db),
) -> BugRecordResponse:
    """Create a bug record from raw error input."""
    svc = BugFixService(db)
    bug = await svc.save_bug_record(dto)
    return BugRecordResponse.model_validate(bug)


@router.get("/bugs", response_model=BugRecordListResponse)
async def list_bug_records(
    project_id: str = Query(...),
    signature: str | None = Query(None),
    limit: int = Query(20, ge=1),
    db: AsyncSession = Depends(get_db),
) -> BugRecordListResponse:
    """List bug records for a project."""
    from sqlalchemy import select

    from app.models.cli_session import BugRecord

    stmt = select(BugRecord).where(BugRecord.project_id == project_id)
    if signature:
        stmt = stmt.where(BugRecord.error_signature == signature)
    stmt = stmt.order_by(BugRecord.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    bugs = result.scalars().all()
    return BugRecordListResponse(
        data=[BugRecordResponse.model_validate(b) for b in bugs]
    )


@router.get("/bugs/{bug_id}", response_model=BugRecordResponse)
async def get_bug_record(
    bug_id: str,
    db: AsyncSession = Depends(get_db),
) -> BugRecordResponse:
    """Get a bug record by ID."""
    svc = BugFixService(db)
    bug = await svc.get_bug_record(bug_id)
    return BugRecordResponse.model_validate(bug)


@router.post("/bugs/{bug_id}/execute", response_model=ExecResult)
async def execute_bug_fix(
    bug_id: str,
    dto: BugRecordExecuteRequest,
    db: AsyncSession = Depends(get_db),
) -> ExecResult:
    """Execute a bug fix plan."""
    svc = BugFixService(db)
    return await svc.execute_fix(bug_id, edited_diff=dto.edited_diff)


@router.post("/bugs/{bug_id}/ignore", response_model=BugRecordResponse)
async def ignore_bug_fix(
    bug_id: str,
    db: AsyncSession = Depends(get_db),
) -> BugRecordResponse:
    """Ignore a bug fix proposal."""
    svc = BugFixService(db)
    bug = await svc.ignore_fix(bug_id)
    return BugRecordResponse.model_validate(bug)


@router.post("/arch/scan", response_model=ArchScanResponse)
async def scan_arch_issues(
    dto: ArchScanRequest,
    db: AsyncSession = Depends(get_db),
) -> ArchScanResponse:
    """Trigger an architecture scan."""
    svc = ArchGovernanceService(db)
    return await svc.scan_project(
        project_id=dto.project_id,
        session_id=dto.session_id,
        rules=dto.rules,
    )


@router.get("/arch/issues", response_model=ArchIssueListResponse)
async def list_arch_issues(
    project_id: str = Query(...),
    status: str | None = Query(None),
    severity: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> ArchIssueListResponse:
    """List architecture issues for a project."""
    svc = ArchGovernanceService(db)
    issues = await svc.list_issues(project_id, status=status, severity=severity)
    return ArchIssueListResponse(
        data=[ArchIssueResponse.model_validate(i) for i in issues]
    )


@router.get("/arch/issues/{issue_id}", response_model=ArchIssueResponse)
async def get_arch_issue(
    issue_id: str,
    db: AsyncSession = Depends(get_db),
) -> ArchIssueResponse:
    """Get an architecture issue by ID."""
    svc = ArchGovernanceService(db)
    issue = await svc.get_issue(issue_id)
    return ArchIssueResponse.model_validate(issue)


@router.post("/arch/issues/{issue_id}/plan", response_model=ArchIssueResponse)
async def generate_arch_plan(
    issue_id: str,
    db: AsyncSession = Depends(get_db),
) -> ArchIssueResponse:
    """Generate a governance plan for an architecture issue."""
    svc = ArchGovernanceService(db)
    issue = await svc.generate_arch_plan(issue_id)
    return ArchIssueResponse.model_validate(issue)


@router.post("/arch/issues/{issue_id}/execute", response_model=ExecResult)
async def execute_arch_governance(
    issue_id: str,
    db: AsyncSession = Depends(get_db),
) -> ExecResult:
    """Execute a refactoring plan for an architecture issue."""
    svc = ArchGovernanceService(db)
    return await svc.execute_governance(issue_id, action="execute")


@router.post("/arch/issues/{issue_id}/skip", response_model=ArchIssueResponse)
async def skip_arch_issue(
    issue_id: str,
    db: AsyncSession = Depends(get_db),
) -> ArchIssueResponse:
    """Skip an architecture issue."""
    svc = ArchGovernanceService(db)
    issue = await svc.execute_governance(issue_id, action="skip")
    return ArchIssueResponse.model_validate(issue)


@router.get("/arch/rules", response_model=list[ScanRule])
async def list_arch_rules(
    db: AsyncSession = Depends(get_db),
) -> list[ScanRule]:
    """Get scan rule configuration."""
    svc = ArchGovernanceService(db)
    return await svc.list_rules()


@router.put("/arch/rules", response_model=list[ScanRule])
async def update_arch_rules(
    rules: list[ScanRule],
    db: AsyncSession = Depends(get_db),
) -> list[ScanRule]:
    """Update scan rule configuration."""
    svc = ArchGovernanceService(db)
    return await svc.update_rules(rules)


@router.websocket("/cli/ws/{session_id}")
async def cli_websocket(
    websocket: WebSocket,
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """WebSocket endpoint for interactive CLI sessions.

    Handles command, action, abort, and ping messages.
    """
    await websocket.accept()
    cli_svc = CliService(db)

    def sender(data: dict[str, Any]) -> Awaitable[None]:
        return _safe_send(websocket, data)

    try:
        session = await cli_svc.get_session(session_id)
    except NotFoundError as exc:
        if await _safe_send(
            websocket,
            _error_response(session_id, "SESSION_NOT_FOUND", str(exc)).model_dump(),
        ):
            await websocket.close()
        return

    if not await _safe_send(
        websocket,
        _text_response(
            session_id,
            f"已连接会话 {session_id}，当前模式：{session.mode}",
        ).model_dump(),
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
                    _error_response(
                        session_id, "INVALID_MESSAGE", f"Invalid message: {exc}"
                    ).model_dump(),
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
                await _handle_action(websocket, session_id, request, cli_svc, db)
                continue

            if request.type in {"command", "input"}:
                text = request.payload.text or request.payload.command or ""
                metadata = request.payload.metadata or {}
                print(f"[CLI WS] received type={request.type} text={text!r} metadata_keys={list(metadata.keys())}")
                if not text:
                    await _safe_send(
                        websocket,
                        _error_response(
                            session_id, "EMPTY_INPUT", "请输入内容"
                        ).model_dump(),
                    )
                    continue
                await cli_svc.add_message(
                    session_id,
                    CliMessageType.USER,
                    content=text,
                )
                await _handle_command(
                    websocket, session_id, text, session.mode, db, request.payload
                )
                continue

            await _safe_send(
                websocket,
                _error_response(
                    session_id, "UNSUPPORTED_TYPE", f"Unsupported type: {request.type}"
                ).model_dump(),
            )
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        await _safe_send(
            websocket,
            _error_response(
                session_id, "INTERNAL_ERROR", f"Unexpected error: {exc}"
            ).model_dump(),
        )
        with suppress(Exception):
            await websocket.close()


async def _handle_command(
    websocket: WebSocket,
    session_id: str,
    text: str,
    mode: str,
    db: AsyncSession,
    payload: CliRequestPayload | None = None,
) -> None:
    """Route a user command to the appropriate service.

    Args:
        websocket: Active WebSocket connection.
        session_id: CLI session ID.
        text: User input text.
        mode: Session working mode.
        db: SQLAlchemy async session.
        payload: Optional parsed request payload for structured commands.
    """
    async def safe_sender(data: dict[str, Any]) -> None:
        await _safe_send(websocket, data)

    await _safe_send(
        websocket,
        _text_response(session_id, f"收到：{text}").model_dump(),
    )

    if mode == "bug":
        bug_svc = BugFixService(db)
        try:
            bug = await bug_svc.save_bug_record(
                BugRecordCreate(
                    project_id="project-mvp",
                    session_id=session_id,
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
            await _safe_send(
                websocket,
                CliResponse(
                    type="card",
                    session_id=session_id,
                    timestamp=_now_ms(),
                    payload=CliResponsePayload.model_construct(card=card),
                ).model_dump(),
            )
        except Exception as exc:
            await _safe_send(
                websocket,
                _error_response(session_id, "BUG_ANALYSIS_FAILED", str(exc)).model_dump(),
            )
    elif mode == "arch":
        metadata = (payload.metadata if payload else None) or {}
        action = metadata.get("action")
        print(f"[CLI CMD] arch mode action={action!r}")
        if action == "apply_arch_fix_plan":
            plan = metadata.get("plan", {})
            project_id = metadata.get("project_id", "project-mvp")
            plans = plan.get("plans", []) if isinstance(plan, dict) else []
            total_changes = sum(len(p.get("changes", [])) for p in plans)
            print(f"[CLI CMD] apply_arch_fix_plan project_id={project_id} total_changes={total_changes}")
            arch_svc = ArchGovernanceService(db)
            try:
                await arch_svc.apply_fix_plan(
                    session_id=session_id,
                    project_id=project_id,
                    plan=plan,
                    sender=safe_sender,
                )
            except Exception as exc:
                print(f"[CLI CMD] apply_arch_fix_plan failed: {exc}")
                await _safe_send(
                    websocket,
                    _error_response(
                        session_id, "APPLY_FIX_PLAN_FAILED", str(exc)
                    ).model_dump(),
                )
        else:
            await _safe_send(
                websocket,
                _text_response(
                    session_id,
                    "架构模式：请从架构治理页面选择问题并生成修复方案。",
                ).model_dump(),
            )
    else:
        await _safe_send(
            websocket,
            _text_response(session_id, "系统已收到您的输入。").model_dump(),
        )


async def _handle_action(
    websocket: WebSocket,
    session_id: str,
    request: CliRequest,
    cli_svc: CliService,
    db: AsyncSession,
) -> None:
    """Handle action messages such as card button clicks.

    Args:
        websocket: Active WebSocket connection.
        session_id: CLI session ID.
        request: Parsed CLI request.
        cli_svc: CLI session service.
        db: SQLAlchemy async session.
    """
    command = request.payload.command or ""
    metadata = request.payload.metadata or {}
    await cli_svc.add_message(
        session_id,
        CliMessageType.USER,
        content=f"[action] {command}",
    )

    async def safe_sender(data: dict[str, Any]) -> None:
        await _safe_send(websocket, data)

    if command in {"fix", "skip", "edit"} and metadata.get("change"):
        arch_svc = ArchGovernanceService(db)
        project_id = metadata.get("project_id", "project-mvp")
        await arch_svc.handle_change_action(
            session_id=session_id,
            project_id=project_id,
            command=command,
            metadata=metadata,
            sender=safe_sender,
        )
        return

    await _safe_send(
        websocket,
        _text_response(session_id, f"已执行操作：{command}").model_dump(),
    )


def _text_response(session_id: str, text: str) -> CliResponse:
    """Build a text CLI response.

    Args:
        session_id: CLI session ID.
        text: Text content.

    Returns:
        CLI response payload.
    """
    return CliResponse(
        type="text",
        session_id=session_id,
        timestamp=_now_ms(),
        payload=CliResponsePayload.model_construct(text=text),
    )


def _error_response(
    session_id: str, code: str, message: str
) -> CliResponse:
    """Build an error CLI response.

    Args:
        session_id: CLI session ID.
        code: Error code.
        message: Error message.

    Returns:
        CLI response payload.
    """
    return CliResponse(
        type="error",
        session_id=session_id,
        timestamp=_now_ms(),
        payload=CliResponsePayload.model_construct(
            error=ErrorResponse.model_construct(code=code, message=message)
        ),
    )


async def _safe_send(websocket: WebSocket, data: dict[str, Any]) -> bool:
    """Send JSON data over a WebSocket, swallowing disconnect errors.

    Long-running handlers (e.g. LLM calls) may outlive the frontend tab.
    Without this wrapper, a ``send_json`` on a closed socket propagates as an
    unhandled ASGI exception and crashes the whole WebSocket task.

    Args:
        websocket: Active WebSocket connection.
        data: JSON-serializable payload.

    Returns:
        True if the message was sent, False if the client has disconnected.
    """
    try:
        await websocket.send_json(data)
        return True
    except WebSocketDisconnect:
        return False
    except RuntimeError:
        # Starlette/websockets raise RuntimeError for many terminal states,
        # e.g. "Cannot call 'send' once a close message has been sent."
        # Treat any RuntimeError from send as a disconnected client.
        return False


def _now_ms() -> int:
    """Return the current Unix timestamp in milliseconds.

    Returns:
        Unix milliseconds.
    """
    from datetime import UTC, datetime

    return int(datetime.now(UTC).timestamp() * 1000)
