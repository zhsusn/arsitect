"""Tests for CanvasState model."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.application import Application
from app.models.canvas_state import CanvasState
from app.models.project import Project


class TestCanvasState:
    """CanvasState ORM tests."""

    @pytest.mark.asyncio
    async def test_create_canvas_state(self, db_session) -> None:
        """Should persist canvas state with nodes, edges, and viewport."""
        app = Application(
            application_id="app-cs-1",
            application_name="CanvasApp",
            local_path="/tmp/canvas",
        )
        db_session.add(app)
        await db_session.flush()
        proj = Project(
            project_id="proj-cs-1",
            project_name="CanvasProj",
            application_id=app.application_id,
            template_level="Standard",
        )
        db_session.add(proj)
        await db_session.flush()

        cs = CanvasState(
            canvas_state_id="cs-001",
            project_id=proj.project_id,
            nodes='[{"id":"n1","position":{"x":0,"y":0}}]',
            edges='[{"id":"e1","source":"n1","target":"n2"}]',
            viewport='{"x":10,"y":20,"zoom":1.5}',
        )
        db_session.add(cs)
        await db_session.flush()

        result = await db_session.execute(
            select(CanvasState).where(CanvasState.canvas_state_id == "cs-001")
        )
        found = result.scalar_one()
        assert found.project_id == proj.project_id
        assert '"id":"n1"' in found.nodes
        assert found.viewport == '{"x":10,"y":20,"zoom":1.5}'
        assert found.updated_at is not None

    @pytest.mark.asyncio
    async def test_project_unique_constraint(self, db_session) -> None:
        """Should enforce one canvas state per project."""
        app = Application(
            application_id="app-cs-2",
            application_name="CanvasApp2",
            local_path="/tmp/canvas2",
        )
        db_session.add(app)
        await db_session.flush()
        proj = Project(
            project_id="proj-cs-2",
            project_name="CanvasProj2",
            application_id=app.application_id,
            template_level="Standard",
        )
        db_session.add(proj)
        await db_session.flush()

        cs1 = CanvasState(
            canvas_state_id="cs-002",
            project_id=proj.project_id,
        )
        db_session.add(cs1)
        await db_session.flush()

        cs2 = CanvasState(
            canvas_state_id="cs-003",
            project_id=proj.project_id,
        )
        db_session.add(cs2)
        with pytest.raises(IntegrityError):
            await db_session.flush()
