"""Artifact browser router — tree, content, versioning, editing."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.artifacts.artifact_editor import ArtifactEditor
from app.common.artifact_store import ArtifactStore
from app.common.project_context import ProjectContext
from app.infrastructure.database.session import get_db
from app.schemas.artifact import (
    ArtifactContentDTO,
    ArtifactStatusDTO,
    ArtifactTreeDirectoryDTO,
    ArtifactVersionDTO,
    DiffResponseDTO,
    SaveContentRequestDTO,
)
from app.services.artifact_service import ArtifactService

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("/tree", response_model=list[ArtifactTreeDirectoryDTO])
async def get_artifact_tree(
    project_id: str,
    search: str | None = None,
    filter_stage: str | None = None,
    filter_skill: str | None = None,
    filter_type: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Get artifact directory tree for a project."""
    svc = ArtifactService(db)
    return await svc.get_tree(
        project_id,
        search=search,
        filter_stage=filter_stage,
        filter_skill=filter_skill,
        filter_type=filter_type,
    )


@router.get("/{artifact_id}/content", response_model=ArtifactContentDTO)
async def get_artifact_content(
    artifact_id: str,
    offset: int = 0,
    limit: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> ArtifactContentDTO:
    """Get artifact file content with optional line slicing."""
    svc = ArtifactService(db)
    content, total_lines, content_hash = await svc.get_content(
        artifact_id, offset=offset, limit=limit
    )
    is_partial = limit is not None and total_lines > offset + limit
    return ArtifactContentDTO(
        artifact_id=artifact_id,
        content=content,
        total_lines=total_lines,
        content_hash=content_hash,
        is_partial=is_partial,
    )


@router.get("/{artifact_id}/status", response_model=ArtifactStatusDTO)
async def get_artifact_status(
    artifact_id: str,
    db: AsyncSession = Depends(get_db),
) -> ArtifactStatusDTO:
    """Get artifact status including external status and content hash."""
    svc = ArtifactService(db)
    status = await svc.get_status(artifact_id)
    return ArtifactStatusDTO.model_validate(status)


@router.get("/{artifact_id}/download")
async def download_artifact(
    artifact_id: str,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Download artifact file with Content-Disposition attachment."""
    svc = ArtifactService(db)
    file_path = await svc.get_download_path(artifact_id)
    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=Path(file_path).name,
    )


@router.put("/{artifact_id}/content", response_model=ArtifactVersionDTO)
async def save_artifact_content(
    artifact_id: str,
    dto: SaveContentRequestDTO,
    db: AsyncSession = Depends(get_db),
) -> ArtifactVersionDTO:
    """Save artifact content and create a snapshot version."""
    svc = ArtifactService(db)
    version = await svc.save_content(artifact_id, dto.content, expected_hash=dto.expected_hash)
    return ArtifactVersionDTO.model_validate(version)


@router.get("/{artifact_id}/versions", response_model=list[ArtifactVersionDTO])
async def list_artifact_versions(
    artifact_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[ArtifactVersionDTO]:
    """List artifact versions (latest 10)."""
    svc = ArtifactService(db)
    versions = await svc.list_versions(artifact_id)
    return [ArtifactVersionDTO.model_validate(v) for v in versions]


@router.post(
    "/{artifact_id}/versions/{version_number}/rollback",
    response_model=ArtifactVersionDTO,
)
async def rollback_artifact_version(
    artifact_id: str,
    version_number: int,
    db: AsyncSession = Depends(get_db),
) -> ArtifactVersionDTO:
    """Rollback artifact to a specific version."""
    svc = ArtifactService(db)
    version = await svc.rollback(artifact_id, version_number)
    return ArtifactVersionDTO.model_validate(version)


@router.get("/{artifact_id}/versions/diff", response_model=DiffResponseDTO)
async def diff_artifact_versions(
    artifact_id: str,
    from_version: int,
    to_version: int,
    db: AsyncSession = Depends(get_db),
) -> DiffResponseDTO:
    """Diff two artifact versions (simplified: return both contents)."""
    svc = ArtifactService(db)
    from_v = await svc.get_version(artifact_id, from_version)
    to_v = await svc.get_version(artifact_id, to_version)
    return DiffResponseDTO(
        from_version=from_version,
        to_version=to_version,
        from_content=from_v.content or "",
        to_content=to_v.content or "",
    )


@router.post("/{artifact_path:path}/edit")
async def edit_artifact(
    artifact_path: str,
    project_id: str,
    dto: SaveContentRequestDTO,
) -> dict[str, Any]:
    """Edit artifact with conflict detection.

    Uses ArtifactEditor + ArtifactStore for filesystem-level editing.
    """
    with ProjectContext(project_id) as ctx:
        store = ArtifactStore(ctx)
        editor = ArtifactEditor(store)
        result = await editor.save(
            relative_path=artifact_path,
            new_content=dto.content,
            expected_hash=dto.expected_hash,
        )
        return {
            "success": result.success,
            "new_hash": result.new_hash,
            "conflict_detected": result.conflict_detected,
            "message": result.message,
            "previous_hash": result.previous_hash,
        }
