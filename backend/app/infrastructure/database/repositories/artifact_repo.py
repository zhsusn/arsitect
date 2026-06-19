"""Artifact repository with CRUD and version management."""

from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import ArtifactFile
from app.models.artifact_version import ArtifactVersion


class ArtifactRepository:
    """Repository for ArtifactFile entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session

    async def create(self, artifact: ArtifactFile) -> ArtifactFile:
        """Create a new artifact record."""
        self._session.add(artifact)
        await self._session.commit()
        await self._session.refresh(artifact)
        return artifact

    async def get_by_id(self, artifact_id: str) -> ArtifactFile | None:
        """Fetch an artifact by its primary key."""
        return await self._session.get(ArtifactFile, artifact_id)

    async def list_by_project(
        self,
        project_id: str,
        *,
        search: str | None = None,
        filter_stage: str | None = None,
        filter_skill: str | None = None,
        filter_type: str | None = None,
    ) -> list[ArtifactFile]:
        """List artifacts by project ID with optional filters."""
        stmt = select(ArtifactFile).where(ArtifactFile.project_id == project_id)

        if search:
            stmt = stmt.where(
                ArtifactFile.file_name.ilike(f"%{search}%")
                | ArtifactFile.file_path.ilike(f"%{search}%")
            )
        if filter_stage:
            stmt = stmt.where(ArtifactFile.stage_id == filter_stage)
        if filter_skill:
            stmt = stmt.where(ArtifactFile.skill_id == filter_skill)
        if filter_type:
            stmt = stmt.where(ArtifactFile.file_type == filter_type)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, artifact: ArtifactFile) -> ArtifactFile:
        """Update an existing artifact."""
        self._session.add(artifact)
        await self._session.commit()
        await self._session.refresh(artifact)
        return artifact

    async def delete(self, artifact_id: str) -> bool:
        """Delete an artifact by ID. Returns True if deleted."""
        art = await self.get_by_id(artifact_id)
        if art is None:
            return False
        await self._session.delete(art)
        await self._session.commit()
        return True


class ArtifactVersionRepository:
    """Repository for ArtifactVersion entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session

    async def create_version(self, version: ArtifactVersion) -> ArtifactVersion:
        """Create a new version record."""
        self._session.add(version)
        await self._session.commit()
        await self._session.refresh(version)
        return version

    async def list_versions(self, artifact_id: str, *, limit: int = 10) -> list[ArtifactVersion]:
        """List versions for an artifact, newest first."""
        stmt = (
            select(ArtifactVersion)
            .where(ArtifactVersion.artifact_id == artifact_id)
            .order_by(desc(ArtifactVersion.version_number))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_version(self, artifact_id: str, version_number: int) -> ArtifactVersion | None:
        """Fetch a specific version by artifact_id and version_number."""
        stmt = select(ArtifactVersion).where(
            ArtifactVersion.artifact_id == artifact_id,
            ArtifactVersion.version_number == version_number,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
