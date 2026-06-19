"""Direct unit tests for skills router functions (no TestClient)."""

from __future__ import annotations

import contextlib
import uuid

import pytest
from sqlalchemy import text

from app.api.v1.skills import (
    _to_parsed_skill,
    _to_scan_item_dto,
    add_dag_edge,
    add_dag_node,
    delete_dag_edge,
    delete_dag_node,
    delete_skill,
    get_dag,
    get_skill,
    list_dag_changelog,
    list_skills,
    redo_dag,
    save_dag,
    undo_dag,
)
from app.infrastructure.database.session import AsyncSessionLocal
from app.models.skill import Skill
from app.models.skill_dag import SkillDAGEdge, SkillDAGNode
from app.schemas.skill import (
    AddDAGEdgeRequestDTO,
    AddDAGNodeRequestDTO,
    DAGUndoRedoRequestDTO,
    SkillScanResultItemDTO,
)
from app.services.skill_parser import ParsedSkill


class TestSkillConverterHelpers:
    """Test pure conversion helpers."""

    def test_to_scan_item_dto(self) -> None:
        """Convert ParsedSkill to DTO."""
        parsed = ParsedSkill(
            skill_name="test",
            version="1.0",
            pattern="generator",
            tags=["sdlc"],
            platforms=["kimi"],
            description="desc",
            directory_path="/tmp",
            parse_status="ok",
            parse_error_reason=None,
        )
        dto = _to_scan_item_dto(parsed)
        assert dto.skill_name == "test"
        assert dto.parse_status == "ok"

    def test_to_parsed_skill(self) -> None:
        """Convert DTO back to ParsedSkill."""
        dto = SkillScanResultItemDTO(
            skill_name="test",
            version="1.0",
            pattern="generator",
            tags=["sdlc"],
            platforms=["kimi"],
            description="desc",
            directory_path="/tmp",
            parse_status="ok",
            parse_error_reason=None,
        )
        parsed = _to_parsed_skill(dto)
        assert parsed.skill_name == "test"
        assert parsed.parse_status == "ok"


class TestSkillRouterDirect:
    """Direct async tests for skills router endpoints."""

    @pytest.fixture
    async def clean_db(self):
        """Clean DB and seed a skill."""
        async with AsyncSessionLocal() as session:
            for tbl in ["skill_changelog", "skill_dag_edges", "skill_dag_nodes", "skills"]:
                with contextlib.suppress(Exception):
                    await session.execute(text(f"DELETE FROM {tbl}"))
            await session.commit()

            skill = Skill(
                skill_id="skill-direct",
                skill_name="DirectTest",
                version="1.0.0",
                pattern="generator",
                directory_path="/tmp/direct",
            )
            session.add(skill)
            await session.commit()
            yield session
            # cleanup after yield
            for tbl in ["skill_changelog", "skill_dag_edges", "skill_dag_nodes", "skills"]:
                with contextlib.suppress(Exception):
                    await session.execute(text(f"DELETE FROM {tbl}"))
            await session.commit()

    @pytest.mark.asyncio
    async def test_list_skills(self, clean_db) -> None:
        """Direct call to list_skills."""
        result = await list_skills(db=clean_db)
        assert result.total_count >= 1

    @pytest.mark.asyncio
    async def test_get_skill_found(self, clean_db) -> None:
        """Direct call to get_skill when skill exists."""
        result = await get_skill("skill-direct", db=clean_db)
        assert result.skill_id == "skill-direct"

    @pytest.mark.asyncio
    async def test_get_skill_not_found(self, clean_db) -> None:
        """Direct call to get_skill raises NotFoundError."""
        from app.core.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await get_skill("no-such-skill", db=clean_db)

    @pytest.mark.asyncio
    async def test_delete_skill_not_found(self, clean_db) -> None:
        """Direct call to delete_skill raises NotFoundError."""
        from app.core.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await delete_skill("no-such-skill", db=clean_db)

    @pytest.mark.asyncio
    async def test_get_dag(self, clean_db) -> None:
        """Direct call to get_dag."""
        result = await get_dag(db=clean_db)
        assert isinstance(result.nodes, list)
        assert isinstance(result.edges, list)

    @pytest.mark.asyncio
    async def test_dag_node_lifecycle(self, clean_db) -> None:
        """Add and delete a DAG node directly."""
        nid = f"n-{uuid.uuid4().hex[:8]}"
        node = await add_dag_node(
            AddDAGNodeRequestDTO(
                node_id=nid,
                skill_id="skill-direct",
                position_x=10.0,
                position_y=20.0,
            ),
            db=clean_db,
        )
        assert node.node_id == nid

        await delete_dag_node(nid, db=clean_db)
        assert await clean_db.get(SkillDAGNode, nid) is None

    @pytest.mark.asyncio
    async def test_delete_dag_node_not_found(self, clean_db) -> None:
        """Delete missing node raises NotFoundError."""
        from app.core.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await delete_dag_node("no-such-node", db=clean_db)

    @pytest.mark.asyncio
    async def test_dag_edge_lifecycle(self, clean_db) -> None:
        """Add and delete a DAG edge directly."""
        n1 = f"n1-{uuid.uuid4().hex[:8]}"
        n2 = f"n2-{uuid.uuid4().hex[:8]}"
        e1 = f"e1-{uuid.uuid4().hex[:8]}"

        await add_dag_node(
            AddDAGNodeRequestDTO(node_id=n1, skill_id="skill-direct", position_x=0, position_y=0),
            db=clean_db,
        )
        await add_dag_node(
            AddDAGNodeRequestDTO(node_id=n2, skill_id="skill-direct", position_x=0, position_y=0),
            db=clean_db,
        )

        edge = await add_dag_edge(
            AddDAGEdgeRequestDTO(edge_id=e1, source_node_id=n1, target_node_id=n2),
            db=clean_db,
        )
        assert edge.edge_id == e1

        await delete_dag_edge(e1, db=clean_db)
        assert await clean_db.get(SkillDAGEdge, e1) is None

    @pytest.mark.asyncio
    async def test_delete_dag_edge_not_found(self, clean_db) -> None:
        """Delete missing edge raises NotFoundError."""
        from app.core.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await delete_dag_edge("no-such-edge", db=clean_db)

    @pytest.mark.asyncio
    async def test_undo_redo_save(self, clean_db) -> None:
        """Undo, redo and save DAG operations."""
        dto = DAGUndoRedoRequestDTO(session_id="test-session")

        undo_res = await undo_dag(dto, db=clean_db)
        assert isinstance(undo_res["success"], bool)

        redo_res = await redo_dag(dto, db=clean_db)
        assert isinstance(redo_res["success"], bool)

        save_res = await save_dag(db=clean_db)
        assert save_res["success"] is True

    @pytest.mark.asyncio
    async def test_list_dag_changelog(self, clean_db) -> None:
        """List DAG changelog directly."""
        result = await list_dag_changelog(session_id=None, db=clean_db)
        assert isinstance(result, list)
