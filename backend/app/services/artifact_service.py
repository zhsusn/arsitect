"""Artifact browser service."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import aiofiles
import aiofiles.os as aio_os
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.infrastructure.database.repositories.artifact_repo import (
    ArtifactRepository,
    ArtifactVersionRepository,
)
from app.models.artifact import ArtifactFile
from app.models.artifact_version import ArtifactVersion


def _djb2_hash(content: str) -> str:
    """Compute a simple djb2 hash for conflict detection."""
    hash_val = 5381
    for ch in content:
        hash_val = ((hash_val << 5) + hash_val) + ord(ch)
        hash_val &= 0xFFFFFFFF
    return format(hash_val, "08x")


class ArtifactService:
    """Orchestrates artifact CRUD, content I/O, and versioning."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session
        self._repo = ArtifactRepository(session)
        self._version_repo = ArtifactVersionRepository(session)

    async def create_artifact(
        self,
        *,
        artifact_id: str | None = None,
        project_id: str,
        stage_id: str | None = None,
        skill_id: str | None = None,
        execution_id: str | None = None,
        file_name: str,
        file_path: str,
        file_type: str,
        file_size_bytes: int = 0,
        content: str = "",
        created_by: str | None = None,
    ) -> ArtifactFile:
        """Create a new artifact with an initial version snapshot."""
        artifact = ArtifactFile(
            artifact_id=artifact_id or "",
            project_id=project_id,
            stage_id=stage_id,
            skill_id=skill_id,
            execution_id=execution_id,
            file_name=file_name,
            file_path=file_path,
            file_type=file_type,
            file_size_bytes=file_size_bytes,
            current_version=1,
        )
        created = await self._repo.create(artifact)

        await self._write_file(file_path, content)

        version = ArtifactVersion(
            artifact_id=created.artifact_id,
            version_number=1,
            operation_type="snapshot",
            content=content,
            created_by=created_by,
        )
        await self._version_repo.create_version(version)
        return created

    async def get_tree(
        self,
        project_id: str,
        *,
        search: str | None = None,
        filter_stage: str | None = None,
        filter_skill: str | None = None,
        filter_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Build a directory tree grouped by file_path prefix."""
        artifacts = await self._repo.list_by_project(
            project_id,
            search=search,
            filter_stage=filter_stage,
            filter_skill=filter_skill,
            filter_type=filter_type,
        )

        for art in artifacts:
            await self._check_external_status(art)

        tree: dict[str, list[dict[str, Any]]] = {}
        for art in artifacts:
            directory = os.path.dirname(art.file_path) or "/"
            if directory not in tree:
                tree[directory] = []
            tree[directory].append(
                {
                    "artifact_id": art.artifact_id,
                    "file_name": art.file_name,
                    "file_type": art.file_type,
                    "file_size_bytes": art.file_size_bytes,
                    "current_version": art.current_version,
                    "external_status": art.external_status,
                    "stale_flag": art.stale_flag,
                    "stage_id": art.stage_id,
                    "skill_id": art.skill_id,
                    "execution_id": art.execution_id,
                    "created_at": (art.created_at.isoformat() if art.created_at else None),
                    "updated_at": (art.updated_at.isoformat() if art.updated_at else None),
                }
            )

        return [{"directory": d, "files": files} for d, files in sorted(tree.items())]

    async def _check_external_status(self, artifact: ArtifactFile) -> None:
        """Check if the file still exists on disk and update status."""
        if not artifact.file_path:
            return
        try:
            await aio_os.stat(artifact.file_path)
            new_status = "normal"
        except OSError:
            new_status = "deleted"
        if artifact.external_status != new_status:
            artifact.external_status = new_status
            await self._repo.update(artifact)

    async def get_content(
        self,
        artifact_id: str,
        *,
        offset: int = 0,
        limit: int | None = None,
    ) -> tuple[str, int, str]:
        """Get artifact content from disk with optional line slicing.

        Returns:
            Tuple of (content_slice, total_lines, content_hash)
        """
        artifact = await self._repo.get_by_id(artifact_id)
        if artifact is None:
            raise NotFoundError(detail=f"Artifact '{artifact_id}' not found")

        full_content = await self._read_file_or_fallback(artifact)
        lines = full_content.splitlines()
        total_lines = len(lines)

        if limit is not None:
            slice_lines = lines[offset : offset + limit]
            content_slice = "\n".join(slice_lines)
        else:
            content_slice = full_content

        content_hash = _djb2_hash(full_content)
        return content_slice, total_lines, content_hash

    async def _read_file_or_fallback(self, artifact: ArtifactFile) -> str:
        """Read text from file_path, falling back to latest version."""
        try:
            return await self._read_file(artifact.file_path)
        except OSError:
            versions = await self._version_repo.list_versions(artifact.artifact_id, limit=1)
            if versions:
                return versions[0].content or ""
            return ""

    async def save_content(
        self,
        artifact_id: str,
        content: str,
        *,
        expected_hash: str | None = None,
        created_by: str | None = None,
    ) -> ArtifactVersion:
        """Save content to disk and create a snapshot version."""
        artifact = await self._repo.get_by_id(artifact_id)
        if artifact is None:
            raise NotFoundError(detail=f"Artifact '{artifact_id}' not found")

        if expected_hash is not None:
            current_content = await self._read_file_or_fallback(artifact)
            current_hash = _djb2_hash(current_content)
            if current_hash != expected_hash:
                raise ConflictError(detail="文件已被外部修改")

        await self._write_file(artifact.file_path, content)

        new_version_number = artifact.current_version + 1
        artifact.current_version = new_version_number
        artifact.file_size_bytes = len(content.encode("utf-8"))
        artifact.external_status = "normal"
        await self._repo.update(artifact)

        version = ArtifactVersion(
            artifact_id=artifact_id,
            version_number=new_version_number,
            operation_type="snapshot",
            content=content,
            created_by=created_by,
        )
        return await self._version_repo.create_version(version)

    async def rollback(
        self, artifact_id: str, version_number: int, created_by: str | None = None
    ) -> ArtifactVersion:
        """Rollback to a specific version."""
        artifact = await self._repo.get_by_id(artifact_id)
        if artifact is None:
            raise NotFoundError(detail=f"Artifact '{artifact_id}' not found")

        target = await self._version_repo.get_version(artifact_id, version_number)
        if target is None:
            raise NotFoundError(
                detail=f"Version {version_number} not found for artifact '{artifact_id}'"
            )

        content = target.content or ""
        await self._write_file(artifact.file_path, content)

        new_version_number = artifact.current_version + 1
        artifact.current_version = new_version_number
        artifact.file_size_bytes = len(content.encode("utf-8"))
        artifact.external_status = "normal"
        await self._repo.update(artifact)

        version = ArtifactVersion(
            artifact_id=artifact_id,
            version_number=new_version_number,
            operation_type="rollback",
            content=content,
            created_by=created_by,
        )
        return await self._version_repo.create_version(version)

    async def list_versions(self, artifact_id: str) -> list[ArtifactVersion]:
        """List artifact versions (latest 10)."""
        return await self._version_repo.list_versions(artifact_id)

    async def get_version(self, artifact_id: str, version_number: int) -> ArtifactVersion:
        """Get a specific artifact version."""
        version = await self._version_repo.get_version(artifact_id, version_number)
        if version is None:
            raise NotFoundError(
                detail=f"Version {version_number} not found for artifact '{artifact_id}'"
            )
        return version

    async def get_status(self, artifact_id: str) -> dict[str, Any]:
        """Get artifact status including content hash."""
        artifact = await self._repo.get_by_id(artifact_id)
        if artifact is None:
            raise NotFoundError(detail=f"Artifact '{artifact_id}' not found")

        await self._check_external_status(artifact)

        full_content = await self._read_file_or_fallback(artifact)
        content_hash = _djb2_hash(full_content)

        return {
            "artifact_id": artifact.artifact_id,
            "external_status": artifact.external_status,
            "file_size_bytes": artifact.file_size_bytes,
            "current_version": artifact.current_version,
            "content_hash": content_hash,
            "updated_at": (artifact.updated_at.isoformat() if artifact.updated_at else None),
        }

    async def get_download_path(self, artifact_id: str) -> str:
        """Return the absolute file path for downloading an artifact."""
        artifact = await self._repo.get_by_id(artifact_id)
        if artifact is None:
            raise NotFoundError(detail=f"Artifact '{artifact_id}' not found")
        await self._check_external_status(artifact)
        if artifact.external_status == "deleted":
            raise NotFoundError(detail=f"Artifact '{artifact_id}' has been deleted externally")
        return artifact.file_path

    async def _read_file(self, file_path: str) -> str:
        """Read text from file_path asynchronously."""
        async with aiofiles.open(file_path, encoding="utf-8") as f:
            return await f.read()  # type: ignore[no-any-return]

    async def _write_file(self, file_path: str, content: str) -> None:
        """Write text to file_path asynchronously."""
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(file_path, mode="w", encoding="utf-8") as f:
            await f.write(content)
