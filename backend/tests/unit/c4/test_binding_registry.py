"""Tests for C4BindingRegistry."""

from __future__ import annotations

import pytest

from app.c4.binding_registry import C4BindingRegistry
from app.models.application import Application
from app.models.project import Project


class TestC4BindingRegistry:
    """C4BindingRegistry unit tests."""

    async def _seed_project(self, session, suffix: str = "1") -> Project:
        app = Application(
            application_id=f"app-br-{suffix}",
            application_name=f"BrApp{suffix}",
            local_path=f"/tmp/br{suffix}",
        )
        session.add(app)
        await session.flush()
        proj = Project(
            project_id=f"proj-br-{suffix}",
            project_name=f"BrProj{suffix}",
            application_id=app.application_id,
            template_level="Standard",
        )
        session.add(proj)
        await session.flush()
        return proj

    @pytest.mark.asyncio
    async def test_create_and_query_by_c4_node(self, db_session) -> None:
        """Create binding and query by C4 node."""
        proj = await self._seed_project(db_session)
        registry = C4BindingRegistry(db_session)

        record = await registry.create_binding(
            project_id=proj.project_id,
            c4_node_id="UserController",
            c4_level="L3",
            artifact_id="src/controllers/user.py",
            relation_type="locates_at",
            source_location="/projects/demo/src/controllers/user.py",
        )
        assert record.c4_node_id == "UserController"

        bindings = await registry.query_by_c4_node(proj.project_id, "UserController")
        assert len(bindings) == 1
        assert bindings[0].relation_type == "locates_at"

    @pytest.mark.asyncio
    async def test_query_by_artifact(self, db_session) -> None:
        """Query bindings by artifact path."""
        proj = await self._seed_project(db_session)
        registry = C4BindingRegistry(db_session)

        await registry.create_binding(
            project_id=proj.project_id,
            c4_node_id="OrderService",
            c4_level="L3",
            artifact_id="src/services/order.py",
            relation_type="locates_at",
        )

        bindings = await registry.query_by_artifact(
            proj.project_id, "src/services/order.py"
        )
        assert len(bindings) == 1
        assert bindings[0].c4_node_id == "OrderService"

    @pytest.mark.asyncio
    async def test_list_locates_at(self, db_session) -> None:
        """List LOCATES_AT bindings for a node."""
        proj = await self._seed_project(db_session)
        registry = C4BindingRegistry(db_session)

        await registry.create_binding(
            project_id=proj.project_id,
            c4_node_id="ProductCtrl",
            c4_level="L3",
            artifact_id="product.py",
            relation_type="locates_at",
        )
        await registry.create_binding(
            project_id=proj.project_id,
            c4_node_id="ProductCtrl",
            c4_level="L3",
            artifact_id="product_test.py",
            relation_type="generates",
        )

        locates = await registry.list_locates_at(proj.project_id, "ProductCtrl")
        assert len(locates) == 1
        assert locates[0].relation_type == "locates_at"

    @pytest.mark.asyncio
    async def test_list_by_project_with_filter(self, db_session) -> None:
        """List bindings filtered by relation type."""
        proj = await self._seed_project(db_session)
        registry = C4BindingRegistry(db_session)

        await registry.create_binding(
            project_id=proj.project_id,
            c4_node_id="A",
            c4_level="L3",
            artifact_id="a.py",
            relation_type="locates_at",
        )
        await registry.create_binding(
            project_id=proj.project_id,
            c4_node_id="B",
            c4_level="L3",
            artifact_id="b.py",
            relation_type="generates",
        )

        all_bindings = await registry.list_by_project(proj.project_id)
        assert len(all_bindings) == 2

        filtered = await registry.list_by_project(proj.project_id, "locates_at")
        assert len(filtered) == 1
        assert filtered[0].c4_node_id == "A"

    @pytest.mark.asyncio
    async def test_delete_bindings_by_node(self, db_session) -> None:
        """Delete bindings for a C4 node."""
        proj = await self._seed_project(db_session)
        registry = C4BindingRegistry(db_session)

        await registry.create_binding(
            project_id=proj.project_id,
            c4_node_id="ToDelete",
            c4_level="L3",
            artifact_id="del.py",
            relation_type="locates_at",
        )

        deleted = await registry.delete_bindings_by_node(
            proj.project_id, "ToDelete"
        )
        assert deleted == 1

        remaining = await registry.query_by_c4_node(proj.project_id, "ToDelete")
        assert len(remaining) == 0
