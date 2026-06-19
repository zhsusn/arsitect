"""C4BindingRegistry — C4 node ↔ code/artifact mapping repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.binding_record import BindingRecord


class C4BindingRegistry:
    """Registry for C4 node to code/artifact bindings.

    Responsibilities:
    1. Query bindings by C4 node ID.
    2. Query bindings by artifact/file path.
    3. Create and manage LOCATES_AT relationships.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def query_by_c4_node(self, project_id: str, c4_node_id: str) -> list[BindingRecord]:
        """Return all bindings for a given C4 node."""
        result = await self.db.execute(
            select(BindingRecord)
            .where(BindingRecord.project_id == project_id)
            .where(BindingRecord.c4_node_id == c4_node_id)
        )
        return list(result.scalars().all())

    async def query_by_artifact(self, project_id: str, artifact_path: str) -> list[BindingRecord]:
        """Return all bindings for a given artifact path.

        Args:
            project_id: Project identifier.
            artifact_path: Artifact ID or file path.
        """
        result = await self.db.execute(
            select(BindingRecord)
            .where(BindingRecord.project_id == project_id)
            .where(BindingRecord.artifact_id == artifact_path)
        )
        return list(result.scalars().all())

    async def create_binding(
        self,
        project_id: str,
        c4_node_id: str,
        c4_level: str,
        artifact_id: str,
        relation_type: str,
        source_location: str | None = None,
        confidence: float = 1.0,
    ) -> BindingRecord:
        """Create a new binding record."""
        record = BindingRecord(
            project_id=project_id,
            c4_node_id=c4_node_id,
            c4_level=c4_level,
            artifact_id=artifact_id,
            artifact_type="code",
            relation_type=relation_type,
            source_location=source_location,
            confidence=confidence,
        )
        self.db.add(record)
        await self.db.flush()
        return record

    async def delete_bindings_by_node(self, project_id: str, c4_node_id: str) -> int:
        """Delete all bindings for a C4 node. Returns deleted count."""
        result = await self.db.execute(
            select(BindingRecord)
            .where(BindingRecord.project_id == project_id)
            .where(BindingRecord.c4_node_id == c4_node_id)
        )
        records = list(result.scalars().all())
        for record in records:
            await self.db.delete(record)
        await self.db.flush()
        return len(records)

    async def list_locates_at(self, project_id: str, c4_node_id: str) -> list[BindingRecord]:
        """Return LOCATES_AT bindings for a node."""
        result = await self.db.execute(
            select(BindingRecord)
            .where(BindingRecord.project_id == project_id)
            .where(BindingRecord.c4_node_id == c4_node_id)
            .where(BindingRecord.relation_type == "locates_at")
        )
        return list(result.scalars().all())

    async def list_by_project(
        self, project_id: str, relation_type: str | None = None
    ) -> list[BindingRecord]:
        """List all bindings for a project, optionally filtered by relation."""
        stmt = select(BindingRecord).where(BindingRecord.project_id == project_id)
        if relation_type:
            stmt = stmt.where(BindingRecord.relation_type == relation_type)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
