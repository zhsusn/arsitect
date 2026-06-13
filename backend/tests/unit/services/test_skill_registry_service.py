"""Tests for SkillRegistryService.

Covers DR-006 Skill Registry & DAG Management detailed requirements.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.skill import Skill
from app.models.skill_changelog import SkillChangeLog
from app.models.skill_dag import SkillDAGEdge, SkillDAGNode
from app.services.skill_registry_service import SkillRegistryService


class TestSkillRegistryService:
    """SkillRegistryService unit tests."""

    @pytest.fixture
    async def seeded_skills(self) -> list[Skill]:
        """Seed sample skills."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_change_logs"))
            await session.execute(text("DELETE FROM skill_dag_edges"))
            await session.execute(text("DELETE FROM skill_dag_nodes"))
            await session.execute(text("DELETE FROM skills"))
            await session.commit()

            skills = [
                Skill(
                    skill_id="skill-001",
                    skill_name="brainstorming",
                    version="1.0.0",
                    pattern="generator",
                    tags='["sdlc"]',
                    platforms='["kimi"]',
                    description="Trigger on new ideas",
                    directory_path="/skills/brainstorming",
                    parse_status="PARSED",
                ),
                Skill(
                    skill_id="skill-002",
                    skill_name="task-breakdown",
                    version="1.2.0",
                    pattern="pipeline",
                    tags='["sdlc", "planning"]',
                    platforms='["kimi", "claude"]',
                    description="Break tasks into chunks",
                    directory_path="/skills/task-breakdown",
                    parse_status="PARSED",
                ),
                Skill(
                    skill_id="skill-003",
                    skill_name="debug-assistant",
                    version="1.0.0",
                    pattern="analyzer",
                    tags='["debug"]',
                    platforms='["cursor"]',
                    description="Debug assistant",
                    directory_path="/skills/debug-assistant",
                    parse_status="MANUAL_REQUIRED",
                    parse_error_reason="missing platforms",
                ),
            ]
            for s in skills:
                session.add(s)
            await session.commit()
            return skills

    @pytest.fixture
    async def seeded_dag(self) -> None:
        """Seed sample DAG nodes and edges."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_dag_edges"))
            await session.execute(text("DELETE FROM skill_dag_nodes"))
            await session.commit()

            nodes = [
                SkillDAGNode(node_id="node-001", skill_id="skill-001", position_x=0, position_y=0),
                SkillDAGNode(node_id="node-002", skill_id="skill-002", position_x=100, position_y=0),
            ]
            for n in nodes:
                session.add(n)
            await session.flush()
            edges = [
                SkillDAGEdge(edge_id="edge-001", source_node_id="node-001", target_node_id="node-002"),
            ]
            for e in edges:
                session.add(e)
            await session.commit()

    @pytest.fixture
    async def seeded_changelog(self) -> None:
        """Seed sample changelogs."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("DELETE FROM skill_change_logs"))
            await session.commit()

            logs = [
                SkillChangeLog(log_id="log-001", session_id="sess-1", operation_type="ADD_NODE", target_id="node-001"),
                SkillChangeLog(log_id="log-002", session_id="sess-1", operation_type="ADD_EDGE", target_id="edge-001"),
                SkillChangeLog(log_id="log-003", session_id="sess-2", operation_type="DELETE_NODE", target_id="node-002"),
            ]
            for log in logs:
                session.add(log)
            await session.commit()

    @pytest.mark.asyncio
    async def test_list_skills_no_filter(self, seeded_skills: list[Skill]) -> None:
        """TEST-0101: List all skills without filter.

        Covers AC-F-010: Skill registry list.
        """
        async with AsyncSessionLocal() as session:
            svc = SkillRegistryService(session)
            result = await svc.list_skills()
            assert len(result) == 3

    @pytest.mark.asyncio
    async def test_list_skills_by_search(self, seeded_skills: list[Skill]) -> None:
        """TEST-0102: Search skills by name substring.

        Covers AC-U-002: Node library search.
        """
        async with AsyncSessionLocal() as session:
            svc = SkillRegistryService(session)
            result = await svc.list_skills(search="brain")
            assert len(result) == 1
            assert result[0].skill_name == "brainstorming"

    @pytest.mark.asyncio
    async def test_list_skills_by_pattern(self, seeded_skills: list[Skill]) -> None:
        """TEST-0103: Filter skills by pattern.

        Covers AC-U-002: Pattern filter.
        """
        async with AsyncSessionLocal() as session:
            svc = SkillRegistryService(session)
            result = await svc.list_skills(pattern="pipeline")
            assert len(result) == 1
            assert result[0].pattern == "pipeline"

    @pytest.mark.asyncio
    async def test_list_skills_by_status(self, seeded_skills: list[Skill]) -> None:
        """TEST-0104: Filter skills by parse status.

        Covers AC-F-003 / AC-F-004: MANUAL_REQUIRED detection.
        """
        async with AsyncSessionLocal() as session:
            svc = SkillRegistryService(session)
            result = await svc.list_skills(status="MANUAL_REQUIRED")
            assert len(result) == 1
            assert result[0].skill_name == "debug-assistant"

    @pytest.mark.asyncio
    async def test_list_skills_combined_filter(self, seeded_skills: list[Skill]) -> None:
        """TEST-0105: Combined search + pattern + status filters.

        Covers AC-U-002: Multi-filter support.
        """
        async with AsyncSessionLocal() as session:
            svc = SkillRegistryService(session)
            result = await svc.list_skills(search="task", pattern="pipeline", status="PARSED")
            assert len(result) == 1
            assert result[0].skill_name == "task-breakdown"

    @pytest.mark.asyncio
    async def test_get_skill_found(self, seeded_skills: list[Skill]) -> None:
        """TEST-0106: Get skill by existing ID.

        Covers AC-F-010: Skill detail retrieval.
        """
        async with AsyncSessionLocal() as session:
            svc = SkillRegistryService(session)
            skill = await svc.get_skill("skill-001")
            assert skill is not None
            assert skill.skill_name == "brainstorming"

    @pytest.mark.asyncio
    async def test_get_skill_not_found(self, seeded_skills: list[Skill]) -> None:
        """TEST-0107: Get skill by nonexistent ID returns None.

        Covers edge case: missing skill lookup.
        """
        async with AsyncSessionLocal() as session:
            svc = SkillRegistryService(session)
            skill = await svc.get_skill("no-such-skill")
            assert skill is None

    @pytest.mark.asyncio
    async def test_delete_skill_success(self, seeded_skills: list[Skill]) -> None:
        """TEST-0108: Delete existing skill returns True.

        Covers skill registry management.
        """
        async with AsyncSessionLocal() as session:
            svc = SkillRegistryService(session)
            deleted = await svc.delete_skill("skill-003")
            assert deleted is True
            assert await svc.get_skill("skill-003") is None

    @pytest.mark.asyncio
    async def test_delete_skill_not_found(self, seeded_skills: list[Skill]) -> None:
        """TEST-0109: Delete nonexistent skill returns False.

        Covers edge case: idempotent deletion.
        """
        async with AsyncSessionLocal() as session:
            svc = SkillRegistryService(session)
            deleted = await svc.delete_skill("no-such-skill")
            assert deleted is False

    @pytest.mark.asyncio
    async def test_get_dag(self, seeded_skills: list[Skill], seeded_dag: None) -> None:
        """TEST-0110: Fetch DAG nodes and edges.

        Covers AC-F-007 / AC-F-008: DAG rendering.
        """
        async with AsyncSessionLocal() as session:
            svc = SkillRegistryService(session)
            dag = await svc.get_dag()
            assert len(dag["nodes"]) == 2
            assert len(dag["edges"]) == 1
            assert dag["edges"][0].source_node_id == "node-001"

    @pytest.mark.asyncio
    async def test_get_dag_empty(self, seeded_skills: list[Skill]) -> None:
        """TEST-0111: Fetch DAG when no nodes/edges exist.

        Covers edge case: empty DAG.
        """
        async with AsyncSessionLocal() as session:
            svc = SkillRegistryService(session)
            dag = await svc.get_dag()
            assert len(dag["nodes"]) == 0
            assert len(dag["edges"]) == 0

    @pytest.mark.asyncio
    async def test_get_changelog_all(self, seeded_changelog: None) -> None:
        """TEST-0112: Fetch all changelogs.

        Covers AC-F-009: Change log recording.
        """
        async with AsyncSessionLocal() as session:
            svc = SkillRegistryService(session)
            logs = await svc.get_changelog()
            assert len(logs) == 3

    @pytest.mark.asyncio
    async def test_get_changelog_by_session(self, seeded_changelog: None) -> None:
        """TEST-0113: Fetch changelogs filtered by session.

        Covers AC-F-009: Session-scoped change log.
        """
        async with AsyncSessionLocal() as session:
            svc = SkillRegistryService(session)
            logs = await svc.get_changelog(session_id="sess-1")
            assert len(logs) == 2
            assert all(log.session_id == "sess-1" for log in logs)

    @pytest.mark.asyncio
    async def test_get_changelog_empty_session(self, seeded_changelog: None) -> None:
        """TEST-0114: Fetch changelogs for nonexistent session returns empty.

        Covers edge case: no matching session.
        """
        async with AsyncSessionLocal() as session:
            svc = SkillRegistryService(session)
            logs = await svc.get_changelog(session_id="no-such-session")
            assert len(logs) == 0
