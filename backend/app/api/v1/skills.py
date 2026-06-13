"""Skill registry router — import, list, DAG operations."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.infrastructure.database.session import get_db
from app.models.skill_dag import SkillDAGEdge, SkillDAGNode
from app.schemas.skill import (
    AddDAGEdgeRequestDTO,
    AddDAGNodeRequestDTO,
    BoundStageDTO,
    DAGChangeLogDTO,
    DAGEdgeDTO,
    DAGNodeDTO,
    DAGSnapshotDTO,
    DAGUndoRedoRequestDTO,
    SkillConflictItemDTO,
    SkillExecutionHistoryDTO,
    SkillImportConfirmDTO,
    SkillImportSummaryDTO,
    SkillListResponseDTO,
    SkillResponseDTO,
    SkillScanRequestDTO,
    SkillScanResultDTO,
    SkillScanResultItemDTO,
)
from app.services.dag_editor_service import DAGEditorService, Position
from app.services.skill_import_service import (
    ConflictResolution,
    SkillImportService,
)
from app.services.skill_parser import ParsedSkill, SkillParser
from app.services.skill_registry_service import SkillRegistryService

router = APIRouter(prefix="/skills", tags=["skills"])


class ScanDirectoryResponse(BaseModel):
    """Response wrapper for scan directory."""

    directory_path: str
    result: SkillScanResultDTO


def _to_scan_item_dto(parsed: ParsedSkill) -> SkillScanResultItemDTO:
    """Convert ParsedSkill to DTO."""
    return SkillScanResultItemDTO(
        skill_name=parsed.skill_name,
        version=parsed.version,
        pattern=parsed.pattern,
        tags=parsed.tags,
        platforms=parsed.platforms,
        description=parsed.description,
        directory_path=parsed.directory_path,
        parse_status=parsed.parse_status,
        parse_error_reason=parsed.parse_error_reason,
    )


def _to_parsed_skill(dto: SkillScanResultItemDTO) -> ParsedSkill:
    """Convert DTO back to ParsedSkill."""
    return ParsedSkill(
        skill_name=dto.skill_name,
        description=dto.description,
        version=dto.version,
        pattern=dto.pattern,
        tags=dto.tags,
        platforms=dto.platforms,
        directory_path=dto.directory_path,
        parse_status=dto.parse_status,
        parse_error_reason=dto.parse_error_reason,
    )


# ------------------------------------------------------------------
# Import
# ------------------------------------------------------------------
@router.post("/import/scan", response_model=SkillScanResultDTO)
async def scan_skills(
    dto: SkillScanRequestDTO,
    db: AsyncSession = Depends(get_db),
) -> SkillScanResultDTO:
    """Scan a directory for skills."""
    parser = SkillParser()
    svc = SkillImportService(db, parser)
    result = await svc.scan_directory(dto.directory_path)
    return SkillScanResultDTO(
        parsed_skills=[_to_scan_item_dto(s) for s in result.parsed_skills],
        conflicts=[
            SkillConflictItemDTO(
                new_skill=_to_scan_item_dto(c.parsed_skill),
                existing_skill=(
                    SkillResponseDTO.model_validate(c.existing_skill)
                    if c.existing_skill
                    else None
                ),
            )
            for c in result.conflicts
        ],
        errors=result.errors,
    )


@router.post("/import/confirm", response_model=SkillImportSummaryDTO)
async def confirm_skill_import(
    dto: SkillImportConfirmDTO,
    db: AsyncSession = Depends(get_db),
) -> SkillImportSummaryDTO:
    """Confirm and import selected skills."""
    parser = SkillParser()
    svc = SkillImportService(db, parser)
    parsed_skills = [_to_parsed_skill(s) for s in dto.skills_to_import]
    resolutions = None
    if dto.resolutions:
        resolutions = [
            ConflictResolution(
                skill_name=r.skill_name,
                action=r.action,
                new_name=r.new_name,
            )
            for r in dto.resolutions
        ]
    summary = await svc.confirm_import(parsed_skills, resolutions=resolutions)
    return SkillImportSummaryDTO(
        imported=summary.imported,
        skipped=summary.skipped,
        errors=summary.errors,
    )


# ------------------------------------------------------------------
# Skill CRUD (list must be before /{skill_id})
# ------------------------------------------------------------------
@router.get("", response_model=SkillListResponseDTO)
async def list_skills(
    search: str | None = None,
    pattern: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> SkillListResponseDTO:
    """List registered skills with optional filters."""
    svc = SkillRegistryService(db)
    items = await svc.list_skills(search=search, pattern=pattern, status=status)
    return SkillListResponseDTO(
        data=[SkillResponseDTO.model_validate(item) for item in items],
        total_count=len(items),
    )


# ------------------------------------------------------------------
# DAG (all fixed paths before /{skill_id})
# ------------------------------------------------------------------
@router.get("/dag", response_model=DAGSnapshotDTO)
async def get_dag(
    db: AsyncSession = Depends(get_db),
) -> DAGSnapshotDTO:
    """Get the current DAG snapshot."""
    svc = SkillRegistryService(db)
    data = await svc.get_dag()
    return DAGSnapshotDTO(
        nodes=[DAGNodeDTO.model_validate(n) for n in data["nodes"]],
        edges=[DAGEdgeDTO.model_validate(e) for e in data["edges"]],
    )


@router.post("/dag/nodes", response_model=DAGNodeDTO)
async def add_dag_node(
    dto: AddDAGNodeRequestDTO,
    db: AsyncSession = Depends(get_db),
) -> DAGNodeDTO:
    """Add a node to the DAG canvas."""
    editor = DAGEditorService(db, session_id="default")
    node = await editor.add_node(
        node_id=dto.node_id,
        skill_id=dto.skill_id,
        position=Position(x=dto.position_x, y=dto.position_y),
    )
    await db.commit()
    return DAGNodeDTO.model_validate(node)


@router.delete(
    "/dag/nodes/{node_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_dag_node(
    node_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a node from the DAG canvas."""
    editor = DAGEditorService(db, session_id="default")
    node = await db.get(SkillDAGNode, node_id)
    if node is None:
        raise NotFoundError(detail=f"Node '{node_id}' not found")
    await editor.delete_node(node)
    await db.commit()


@router.post("/dag/edges", response_model=DAGEdgeDTO)
async def add_dag_edge(
    dto: AddDAGEdgeRequestDTO,
    db: AsyncSession = Depends(get_db),
) -> DAGEdgeDTO:
    """Add an edge to the DAG canvas."""
    editor = DAGEditorService(db, session_id="default")
    edge = await editor.add_edge(
        edge_id=dto.edge_id,
        source_node_id=dto.source_node_id,
        target_node_id=dto.target_node_id,
    )
    await db.commit()
    return DAGEdgeDTO.model_validate(edge)


@router.delete(
    "/dag/edges/{edge_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_dag_edge(
    edge_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an edge from the DAG canvas."""
    edge = await db.get(SkillDAGEdge, edge_id)
    if edge is None:
        raise NotFoundError(detail=f"Edge '{edge_id}' not found")
    await db.delete(edge)
    await db.commit()


@router.post("/dag/undo", response_model=dict)
async def undo_dag(
    dto: DAGUndoRedoRequestDTO,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Undo the last DAG canvas operation."""
    editor = DAGEditorService(db, session_id=dto.session_id)
    success = await editor.undo()
    await db.commit()
    return {"success": success}


@router.post("/dag/redo", response_model=dict)
async def redo_dag(
    dto: DAGUndoRedoRequestDTO,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Redo the last undone DAG canvas operation."""
    editor = DAGEditorService(db, session_id=dto.session_id)
    success = await editor.redo()
    await db.commit()
    return {"success": success}


@router.post("/dag/save", response_model=dict)
async def save_dag(
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    """Persist the current DAG state to the database."""
    await db.commit()
    return {"success": True}


@router.get("/dag/changelog", response_model=list[DAGChangeLogDTO])
async def list_dag_changelog(
    session_id: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[DAGChangeLogDTO]:
    """List DAG change logs."""
    svc = SkillRegistryService(db)
    logs = await svc.get_changelog(session_id=session_id)
    return [DAGChangeLogDTO.model_validate(log) for log in logs]


# ------------------------------------------------------------------
# Skill detail / delete (must be last to avoid shadowing fixed paths)
# ------------------------------------------------------------------
@router.get("/{skill_id}", response_model=SkillResponseDTO)
async def get_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
) -> SkillResponseDTO:
    """Get a single skill by ID."""
    svc = SkillRegistryService(db)
    skill = await svc.get_skill(skill_id)
    if skill is None:
        raise NotFoundError(detail=f"Skill '{skill_id}' not found")
    return SkillResponseDTO.model_validate(skill)


@router.delete(
    "/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a skill by ID."""
    svc = SkillRegistryService(db)
    result = await svc.delete_skill(skill_id)
    if not result:
        raise NotFoundError(detail=f"Skill '{skill_id}' not found")


@router.get("/{skill_id}/executions", response_model=list[SkillExecutionHistoryDTO])
async def get_skill_executions(
    skill_id: str,
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
) -> list[SkillExecutionHistoryDTO]:
    """Get execution history for a skill."""
    svc = SkillRegistryService(db)
    executions = await svc.get_skill_executions(skill_id, limit=limit)
    return [SkillExecutionHistoryDTO.model_validate(e) for e in executions]


@router.get("/{skill_id}/stages", response_model=list[BoundStageDTO])
async def get_skill_bound_stages(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[BoundStageDTO]:
    """Get stages bound to a skill."""
    svc = SkillRegistryService(db)
    stages = await svc.get_bound_stages(skill_id)
    return [BoundStageDTO.model_validate(s) for s in stages]
