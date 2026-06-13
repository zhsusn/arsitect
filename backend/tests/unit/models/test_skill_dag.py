"""Tests for Skill DAG node and edge ORM models."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.skill import Skill
from app.models.skill_dag import SkillDAGEdge, SkillDAGNode


class TestSkillDAGModel:
    """Test DAG node/edge models and foreign key constraints."""

    @pytest.fixture
    async def sample_skill(self) -> Skill:
        """Create a sample skill for DAG tests."""
        _id = str(uuid.uuid4())
        async with AsyncSessionLocal() as session:
            skill = Skill(
                skill_id=_id,
                skill_name=f"dag-test-{_id[:8]}",
                version="1.0.0",
                pattern="generator",
                directory_path="/tmp/dag",
            )
            session.add(skill)
            await session.commit()
            return skill

    @pytest.mark.asyncio
    async def test_create_node(self, sample_skill: Skill) -> None:
        """Can insert a DAG node referencing a skill."""
        async with AsyncSessionLocal() as session:
            node = SkillDAGNode(
                node_id="node-001",
                skill_id=sample_skill.skill_id,
                position_x=100.0,
                position_y=200.0,
            )
            session.add(node)
            await session.commit()

            result = await session.execute(
                select(SkillDAGNode).where(SkillDAGNode.node_id == "node-001")
            )
            fetched = result.scalar_one()
            assert fetched.skill_id == sample_skill.skill_id
            assert fetched.position_x == 100.0

    @pytest.mark.asyncio
    async def test_create_edge(self, sample_skill: Skill) -> None:
        """Can insert an edge between two nodes."""
        async with AsyncSessionLocal() as session:
            n1 = SkillDAGNode(node_id="n1", skill_id=sample_skill.skill_id)
            n2 = SkillDAGNode(node_id="n2", skill_id=sample_skill.skill_id)
            session.add_all([n1, n2])
            await session.commit()

            edge = SkillDAGEdge(
                edge_id="e1",
                source_node_id="n1",
                target_node_id="n2",
                confidence=85,
                is_auto_parsed=True,
            )
            session.add(edge)
            await session.commit()

            result = await session.execute(
                select(SkillDAGEdge).where(SkillDAGEdge.edge_id == "e1")
            )
            fetched = result.scalar_one()
            assert fetched.confidence == 85
            assert fetched.is_auto_parsed is True

    @pytest.mark.asyncio
    async def test_cascade_delete_skill(self, sample_skill: Skill) -> None:
        """Deleting a skill cascades to its DAG nodes."""
        async with AsyncSessionLocal() as session:
            node = SkillDAGNode(
                node_id="n-cascade", skill_id=sample_skill.skill_id
            )
            session.add(node)
            await session.commit()

            # Delete skill
            skill = await session.get(Skill, sample_skill.skill_id)
            await session.delete(skill)
            await session.commit()

            # Node should be gone
            result = await session.execute(
                select(SkillDAGNode).where(SkillDAGNode.node_id == "n-cascade")
            )
            assert result.scalar() is None
