"""DAG editor service — canvas operations with undo/redo."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill_changelog import SkillChangeLog
from app.models.skill_dag import SkillDAGEdge, SkillDAGNode


@dataclass
class Position:
    """2D canvas position."""

    x: float = 0.0
    y: float = 0.0


UndoFn = Callable[[], None] | Callable[[], Awaitable[None]]
DoFn = Callable[[], None] | Callable[[], Awaitable[None]]


@dataclass
class EditCommand:
    """A reversible canvas edit command."""

    name: str
    do_fn: DoFn
    undo_fn: UndoFn


class DAGEditorService:
    """Handle canvas edits, undo/redo, and audit logging."""

    def __init__(
        self,
        session: AsyncSession,
        session_id: str,
    ) -> None:
        """Initialize with session and edit session ID."""
        self._session = session
        self._session_id = session_id
        self._undo_stack: list[EditCommand] = []
        self._redo_stack: list[EditCommand] = []

    async def add_node(
        self,
        node_id: str,
        skill_id: str,
        position: Position,
    ) -> SkillDAGNode:
        """Add a node to the canvas."""
        node = SkillDAGNode(
            node_id=node_id,
            skill_id=skill_id,
            position_x=position.x,
            position_y=position.y,
        )

        def do() -> None:
            self._session.add(node)

        async def undo() -> None:
            if node in self._session.new:
                self._session.expunge(node)
            else:
                await self._session.delete(node)

        await self._execute(EditCommand(name="ADD_NODE", do_fn=do, undo_fn=undo))
        return node

    async def add_edge(
        self,
        edge_id: str,
        source_node_id: str,
        target_node_id: str,
    ) -> SkillDAGEdge:
        """Add an edge between two nodes."""
        edge = SkillDAGEdge(
            edge_id=edge_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
        )

        def do() -> None:
            self._session.add(edge)

        async def undo() -> None:
            if edge in self._session.new:
                self._session.expunge(edge)
            else:
                await self._session.delete(edge)

        await self._execute(EditCommand(name="ADD_EDGE", do_fn=do, undo_fn=undo))
        return edge

    async def delete_node(self, node: SkillDAGNode) -> None:
        """Delete a node and cascade edges."""
        async def do() -> None:
            await self._session.delete(node)

        def undo() -> None:
            self._session.add(node)

        await self._execute(EditCommand(name="DELETE_NODE", do_fn=do, undo_fn=undo))

    async def undo(self) -> bool:
        """Undo the last command. Returns True if successful."""
        if not self._undo_stack:
            return False
        cmd = self._undo_stack.pop()
        if inspect.iscoroutinefunction(cmd.undo_fn):
            await cmd.undo_fn()
        else:
            cmd.undo_fn()
        self._redo_stack.append(cmd)
        return True

    async def redo(self) -> bool:
        """Redo the last undone command. Returns True if successful."""
        if not self._redo_stack:
            return False
        cmd = self._redo_stack.pop()
        if inspect.iscoroutinefunction(cmd.do_fn):
            await cmd.do_fn()
        else:
            cmd.do_fn()
        self._undo_stack.append(cmd)
        return True

    @property
    def can_undo(self) -> bool:
        """Whether there are commands to undo."""
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        """Whether there are commands to redo."""
        return len(self._redo_stack) > 0

    async def _execute(self, cmd: EditCommand) -> None:
        """Execute a command and push to undo stack."""
        if inspect.iscoroutinefunction(cmd.do_fn):
            await cmd.do_fn()
        else:
            cmd.do_fn()
        self._undo_stack.append(cmd)
        self._redo_stack.clear()

    async def save_change_log(
        self,
        operation_type: str,
        target_id: str,
        before: str | None = None,
        after: str | None = None,
    ) -> None:
        """Persist an audit log entry."""
        import uuid

        log = SkillChangeLog(
            log_id=str(uuid.uuid4()),
            session_id=self._session_id,
            operation_type=operation_type,
            target_id=target_id,
            before_snapshot=before,
            after_snapshot=after,
        )
        self._session.add(log)
        await self._session.commit()
