"""Tests for DAGEditorService."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.skill import Skill
from app.models.skill_changelog import SkillChangeLog
from app.models.skill_dag import SkillDAGEdge, SkillDAGNode
from app.services.dag_editor_service import DAGEditorService, Position


async def _make_skill(session) -> Skill:
    uid = str(uuid.uuid4())[:8]
    skill = Skill(
        skill_id=f"sk-{uid}",
        skill_name=f"Skill-{uid}",
        version="1.0.0",
        pattern="generator",
        directory_path=f"/tmp/{uid}",
    )
    session.add(skill)
    await session.flush()
    return skill


class TestDAGEditorService:
    """Test DAG canvas editing and undo/redo."""

    @pytest.mark.asyncio
    async def test_add_node(self) -> None:
        """Can add a node to the canvas."""
        async with AsyncSessionLocal() as session:
            skill = await _make_skill(session)
            svc = DAGEditorService(session, session_id="sess-001")
            nid = f"n1-{str(uuid.uuid4())[:8]}"
            node = await svc.add_node(
                node_id=nid,
                skill_id=skill.skill_id,
                position=Position(x=100, y=200),
            )
            assert node.node_id == nid
            assert node.position_x == 100.0
            await session.commit()

            fetched = await session.get(SkillDAGNode, nid)
            assert fetched is not None

    @pytest.mark.asyncio
    async def test_add_edge(self) -> None:
        """Can add an edge between nodes."""
        async with AsyncSessionLocal() as session:
            s1 = await _make_skill(session)
            s2 = await _make_skill(session)
            svc = DAGEditorService(session, session_id="sess-001")
            n1 = f"n1-{str(uuid.uuid4())[:8]}"
            n2 = f"n2-{str(uuid.uuid4())[:8]}"
            e1 = f"e1-{str(uuid.uuid4())[:8]}"
            await svc.add_node(
                node_id=n1,
                skill_id=s1.skill_id,
                position=Position(x=0, y=0),
            )
            await svc.add_node(
                node_id=n2,
                skill_id=s2.skill_id,
                position=Position(x=10, y=10),
            )
            await session.flush()
            edge = await svc.add_edge(
                edge_id=e1,
                source_node_id=n1,
                target_node_id=n2,
            )
            assert edge.edge_id == e1
            await session.commit()

            fetched = await session.get(SkillDAGEdge, e1)
            assert fetched is not None

    @pytest.mark.asyncio
    async def test_undo_redo(self) -> None:
        """Undo and redo stacks work correctly."""
        async with AsyncSessionLocal() as session:
            skill = await _make_skill(session)
            svc = DAGEditorService(session, session_id="sess-001")
            nid = f"n-undo-{str(uuid.uuid4())[:8]}"
            await svc.add_node(nid, skill.skill_id, Position())
            assert svc.can_undo is True
            assert svc.can_redo is False

            await svc.undo()
            await session.commit()
            assert svc.can_undo is False
            assert svc.can_redo is True

            fetched = await session.get(SkillDAGNode, nid)
            assert fetched is None

            await svc.redo()
            await session.commit()
            fetched = await session.get(SkillDAGNode, nid)
            assert fetched is not None

    @pytest.mark.asyncio
    async def test_undo_stack_depth(self) -> None:
        """Undo stack can hold at least 50 commands."""
        async with AsyncSessionLocal() as session:
            svc = DAGEditorService(session, session_id="sess-001")
            for i in range(55):
                skill = await _make_skill(session)
                await svc.add_node(f"n-depth-{i}-{str(uuid.uuid4())[:4]}", skill.skill_id, Position())
            assert len(svc._undo_stack) == 55

    @pytest.mark.asyncio
    async def test_save_change_log(self) -> None:
        """Can persist audit logs."""
        async with AsyncSessionLocal() as session:
            svc = DAGEditorService(session, session_id="sess-002")
            await svc.save_change_log(
                operation_type="ADD_NODE",
                target_id="n-log",
                before='{"x":0}',
                after='{"x":100}',
            )

            result = await session.execute(
                select(SkillChangeLog).where(
                    SkillChangeLog.session_id == "sess-002"
                )
            )
            log = result.scalar_one()
            assert log.operation_type == "ADD_NODE"
            assert log.target_id == "n-log"
