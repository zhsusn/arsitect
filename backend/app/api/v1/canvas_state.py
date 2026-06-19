"""Canvas state router — GET / POST project canvas state."""

from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.infrastructure.database.repositories.canvas_state_repo import (
    CanvasStateRepository,
)
from app.infrastructure.database.repositories.template_repo import TemplateRepository
from app.infrastructure.database.session import get_db
from app.models.canvas_state import CanvasState
from app.models.project import Project
from app.models.project_path_config import ProjectPathConfig
from app.models.project_stage import ProjectStage
from app.schemas.canvas_state import (
    CanvasEdgeDTO,
    CanvasNodeDTO,
    CanvasStateResponseDTO,
    CanvasStateSaveDTO,
    MergeStagePayload,
    MergeStageResult,
    NodeDataDTO,
    PositionDTO,
    ViewportDTO,
)

router = APIRouter(prefix="/projects", tags=["画布状态"])

_DEFAULT_VIEWPORT = ViewportDTO(x=0, y=0, zoom=1)


def _parse_nodes(raw: str) -> list[CanvasNodeDTO]:
    data: list[Any] = json.loads(raw)
    return [
        CanvasNodeDTO(
            id=n["id"],
            type=n.get("type"),
            position=PositionDTO(**n["position"]),
            data=NodeDataDTO(**n["data"]) if n.get("data") else None,
            style=n.get("style"),
            width=n.get("width"),
            height=n.get("height"),
        )
        for n in data
    ]


def _parse_edges(raw: str) -> list[CanvasEdgeDTO]:
    data: list[Any] = json.loads(raw)
    return [
        CanvasEdgeDTO(
            id=e["id"],
            source=e["source"],
            target=e["target"],
            type=e.get("type"),
            animated=e.get("animated"),
            style=e.get("style"),
            label=e.get("label"),
        )
        for e in data
    ]


def _parse_viewport(raw: str) -> ViewportDTO:
    data: dict[str, Any] = json.loads(raw)
    return ViewportDTO(x=data.get("x", 0), y=data.get("y", 0), zoom=data.get("zoom", 1))


def _serialize_nodes(nodes: list[CanvasNodeDTO]) -> str:
    return json.dumps([n.model_dump(mode="json", exclude_none=True) for n in nodes])


def _serialize_edges(edges: list[CanvasEdgeDTO]) -> str:
    return json.dumps([e.model_dump(mode="json", exclude_none=True) for e in edges])


def _serialize_viewport(viewport: ViewportDTO) -> str:
    return json.dumps(viewport.model_dump(mode="json"))


def _to_response_dto(canvas_state: CanvasState) -> CanvasStateResponseDTO:
    return CanvasStateResponseDTO(
        project_id=canvas_state.project_id,
        nodes=_parse_nodes(canvas_state.nodes),
        edges=_parse_edges(canvas_state.edges),
        viewport=_parse_viewport(canvas_state.viewport),
        updated_at=canvas_state.updated_at,
    )


async def _enrich_nodes_with_runtime(
    session: AsyncSession,
    project_id: str,
    nodes: list[CanvasNodeDTO],
) -> list[CanvasNodeDTO]:
    """Overlay runtime_status from project_stages onto stage nodes."""
    stmt = (
        select(ProjectStage)
        .where(ProjectStage.project_id == project_id)
        .order_by(ProjectStage.order_index.asc())
    )
    result = await session.execute(stmt)
    stages = list(result.scalars().all())
    if not stages:
        return nodes

    runtime_map: dict[str, str] = {}
    business_key_map: dict[str, str] = {}
    for s in stages:
        runtime_map[str(s.order_index)] = s.runtime_status
        business_key_map[str(s.order_index)] = ""

    enriched: list[CanvasNodeDTO] = []
    for node in nodes:
        if node.type == "stage":
            order_key = node.id.replace("stage-", "")
            runtime_status = runtime_map.get(order_key)
            if runtime_status is not None and node.data is not None:
                node.data.status = runtime_status
        enriched.append(node)
    return enriched


def _build_merge_group_map(
    merge_policy: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    """Map each business stage key to its merge group metadata."""
    if not merge_policy:
        return {}
    result: dict[str, dict[str, Any]] = {}
    for group in merge_policy.get("groups", []):
        keys = group.get("business_stage_keys", [])
        label = group.get("label")
        for key in keys:
            result[key] = {"label": label, "keys": keys}
    return result


def _resolve_business_stage_key(stage: Any) -> str | None:
    """Return the business stage key for a template or project stage."""
    return getattr(stage, "business_stage_key", None) or getattr(stage, "stage_id", None)


def _build_default_canvas_state(
    project_id: str,
    stages: list[Any],
    merge_policy: dict[str, Any] | None = None,
) -> CanvasState:
    """Generate a default canvas state from template stages with skills and gates."""
    nodes: list[CanvasNodeDTO] = []
    edges: list[CanvasEdgeDTO] = []
    x_offset = 0
    y_pos = 100
    node_width = 160
    node_gap = 60
    skill_y_offset = 180
    skill_gap_y = 90
    group_map = _build_merge_group_map(merge_policy)

    for i, stage in enumerate(stages):
        node_id = f"stage-{stage.order_index}"
        stage_x = float(x_offset)
        business_key = _resolve_business_stage_key(stage)
        group = group_map.get(business_key) if business_key else None
        merged_keys = group["keys"] if group else None
        is_merged = bool(merged_keys and len(merged_keys) > 1)
        nodes.append(
            CanvasNodeDTO(
                id=node_id,
                type="stage",
                position=PositionDTO(x=stage_x, y=float(y_pos)),
                data=NodeDataDTO(
                    label=stage.stage_name,
                    status="Pending",
                    progress=0.0,
                    merge_group_label=group["label"] if group else None,
                    merged_stage_keys=merged_keys,
                    is_merged=is_merged,
                ),
                width=node_width,
                height=60,
            )
        )

        # Add gate node if present
        if stage.gate_id:
            gate_node_id = f"gate-{stage.gate_id}"
            gate_x = stage_x + node_width + node_gap / 2 - 60
            nodes.append(
                CanvasNodeDTO(
                    id=gate_node_id,
                    type="gate",
                    position=PositionDTO(x=gate_x, y=float(y_pos)),
                    data=NodeDataDTO(
                        label=f"Gate {stage.gate_id[-4:]}",
                        gate_type="",
                        decision_status="pending",
                        progress=None,
                    ),
                    width=120,
                    height=50,
                )
            )
            edges.append(
                CanvasEdgeDTO(
                    id=f"edge-stage-gate-{node_id}-{gate_node_id}",
                    source=node_id,
                    target=gate_node_id,
                    type="default",
                    animated=False,
                )
            )
            if i + 1 < len(stages):
                next_id = f"stage-{stages[i + 1].order_index}"
                edges.append(
                    CanvasEdgeDTO(
                        id=f"edge-gate-stage-{gate_node_id}-{next_id}",
                        source=gate_node_id,
                        target=next_id,
                        type="default",
                        animated=False,
                    )
                )

        # Add skill nodes
        skill_idx = 0
        if stage.primary_skill_id:
            skill_id = f"skill-{stage.primary_skill_id}"
            nodes.append(
                CanvasNodeDTO(
                    id=skill_id,
                    type="skill",
                    position=PositionDTO(
                        x=stage_x, y=float(skill_y_offset + skill_idx * skill_gap_y)
                    ),
                    data=NodeDataDTO(
                        label=stage.primary_skill_id[-8:],
                        status="Pending",
                        progress=0.0,
                        stage_id=node_id,
                        skill_type="primary",
                    ),
                    width=node_width,
                    height=60,
                )
            )
            edges.append(
                CanvasEdgeDTO(
                    id=f"edge-stage-skill-{node_id}-{skill_id}",
                    source=node_id,
                    target=skill_id,
                    type="default",
                    animated=False,
                )
            )
            skill_idx += 1

        if stage.auxiliary_skill_ids:
            try:
                aux_ids: list[str] = json.loads(stage.auxiliary_skill_ids)
            except Exception:
                aux_ids = []
            for aux_id in aux_ids:
                skill_node_id = f"skill-{aux_id}"
                nodes.append(
                    CanvasNodeDTO(
                        id=skill_node_id,
                        type="skill",
                        position=PositionDTO(
                            x=stage_x, y=float(skill_y_offset + skill_idx * skill_gap_y)
                        ),
                        data=NodeDataDTO(
                            label=aux_id[-8:],
                            status="Pending",
                            progress=0.0,
                            stage_id=node_id,
                            skill_type="auxiliary",
                        ),
                        width=node_width,
                        height=60,
                    )
                )
                edges.append(
                    CanvasEdgeDTO(
                        id=f"edge-stage-skill-{node_id}-{skill_node_id}",
                        source=node_id,
                        target=skill_node_id,
                        type="default",
                        animated=False,
                    )
                )
                skill_idx += 1

        if i > 0 and not stage.gate_id:
            prev_id = f"stage-{stages[i - 1].order_index}"
            edges.append(
                CanvasEdgeDTO(
                    id=f"edge-{prev_id}-{node_id}",
                    source=prev_id,
                    target=node_id,
                    type="default",
                    animated=False,
                )
            )
        x_offset += node_width + node_gap

    return CanvasState(
        canvas_state_id=str(uuid.uuid4()),
        project_id=project_id,
        nodes=_serialize_nodes(nodes),
        edges=_serialize_edges(edges),
        viewport=_serialize_viewport(_DEFAULT_VIEWPORT),
    )


async def _get_merge_policy_for_project(
    session: AsyncSession, project_id: str
) -> dict[str, Any] | None:
    """Load merge policy from ProjectPathConfig or fall back to Project."""
    path_config_result = await session.execute(
        select(ProjectPathConfig).where(ProjectPathConfig.project_id == project_id)
    )
    path_config = path_config_result.scalar_one_or_none()
    raw_policy: str | None = None
    if path_config is not None:
        raw_policy = path_config.merge_policy_json
    else:
        proj = await session.get(Project, project_id)
        if proj is not None:
            raw_policy = proj.merge_policy_json

    if not raw_policy:
        return None
    try:
        policy = json.loads(raw_policy)
    except Exception:
        return None
    if isinstance(policy, dict):
        return policy
    return None


@router.get("/{project_id}/canvas/state", response_model=CanvasStateResponseDTO)
async def get_canvas_state(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> CanvasStateResponseDTO:
    """Get canvas state for a project; auto-create from template if absent."""
    repo = CanvasStateRepository(db)
    state = await repo.get_by_project_id(project_id)
    if state is None:
        # Auto-generate from project's template stages
        proj = await db.get(Project, project_id)
        if proj is None:
            raise NotFoundError(detail=f"Project '{project_id}' not found")

        tpl_repo = TemplateRepository(db)
        stages = await tpl_repo.get_stages_for_template(proj.template_level)
        if not stages:
            raise NotFoundError(detail=f"No template stages found for template '{proj.template_level}'")

        merge_policy = await _get_merge_policy_for_project(db, project_id)
        state = _build_default_canvas_state(project_id, stages, merge_policy)
        state = await repo.save(state)

    nodes = _parse_nodes(state.nodes)
    nodes = await _enrich_nodes_with_runtime(db, project_id, nodes)
    state.nodes = _serialize_nodes(nodes)
    return _to_response_dto(state)


@router.post(
    "/{project_id}/canvas/state",
    response_model=CanvasStateResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def save_canvas_state(
    project_id: str,
    dto: CanvasStateSaveDTO,
    db: AsyncSession = Depends(get_db),
) -> CanvasStateResponseDTO:
    """Create or update canvas state for a project."""
    repo = CanvasStateRepository(db)
    existing = await repo.get_by_project_id(project_id)

    viewport = dto.viewport or _DEFAULT_VIEWPORT

    if existing is not None:
        existing.nodes = _serialize_nodes(dto.nodes)
        existing.edges = _serialize_edges(dto.edges)
        existing.viewport = _serialize_viewport(viewport)
        state = await repo.save(existing)
    else:
        state = CanvasState(
            canvas_state_id=str(uuid.uuid4()),
            project_id=project_id,
            nodes=_serialize_nodes(dto.nodes),
            edges=_serialize_edges(dto.edges),
            viewport=_serialize_viewport(viewport),
        )
        state = await repo.save(state)

    return _to_response_dto(state)


@router.post(
    "/{project_id}/canvas/merge-stages",
    response_model=MergeStageResult,
    status_code=status.HTTP_200_OK,
)
async def merge_stages(
    project_id: str,
    payload: MergeStagePayload,
    db: AsyncSession = Depends(get_db),
) -> MergeStageResult:
    """Merge two adjacent stage nodes in the canvas."""
    repo = CanvasStateRepository(db)
    state = await repo.get_by_project_id(project_id)
    if state is None:
        raise NotFoundError(detail=f"Canvas state for project '{project_id}' not found")

    nodes = _parse_nodes(state.nodes)
    edges = _parse_edges(state.edges)

    source_id = payload.source_stage_id
    target_id = payload.target_stage_id

    source_node = next((n for n in nodes if n.id == source_id), None)
    target_node = next((n for n in nodes if n.id == target_id), None)

    if source_node is None or target_node is None:
        raise NotFoundError(detail="One or both stage nodes not found")

    # Merge label
    source_label = source_node.data.label if source_node.data else ""
    target_label = target_node.data.label if target_node.data else ""
    merged_label = f"{source_label}+{target_label}"

    if source_node.data:
        source_node.data.label = merged_label
        # Mark as merged status if needed
        if source_node.data.status == "Pending":
            source_node.data.status = "Draft"

    # Update skill nodes that belonged to target stage
    for n in nodes:
        if n.type == "skill" and n.data and n.data.stage_id == target_id:
            n.data.stage_id = source_id

    # Remove target stage node
    nodes = [n for n in nodes if n.id != target_id]

    # Remove edges connected to target stage and rewire
    new_edges: list[CanvasEdgeDTO] = []
    for e in edges:
        if e.source == target_id and e.target == source_id:
            continue
        if e.source == source_id and e.target == target_id:
            continue
        if e.source == target_id:
            # Rewire to source
            if not any(ne.source == source_id and ne.target == e.target for ne in new_edges):
                new_edges.append(
                    CanvasEdgeDTO(
                        id=f"edge-{source_id}-{e.target}",
                        source=source_id,
                        target=e.target,
                        type=e.type,
                        animated=e.animated,
                        style=e.style,
                        label=e.label,
                    )
                )
        elif e.target == target_id:
            # Rewire to source
            if not any(ne.source == e.source and ne.target == source_id for ne in new_edges):
                new_edges.append(
                    CanvasEdgeDTO(
                        id=f"edge-{e.source}-{source_id}",
                        source=e.source,
                        target=source_id,
                        type=e.type,
                        animated=e.animated,
                        style=e.style,
                        label=e.label,
                    )
                )
        else:
            new_edges.append(e)

    # Deduplicate edges
    seen = set()
    deduped_edges: list[CanvasEdgeDTO] = []
    for e in new_edges:
        key = (e.source, e.target)
        if key not in seen:
            seen.add(key)
            deduped_edges.append(e)

    # Save updated state
    state.nodes = _serialize_nodes(nodes)
    state.edges = _serialize_edges(deduped_edges)
    await repo.save(state)

    return MergeStageResult(
        project_id=project_id,
        merged_stage_id=source_id,
        nodes=nodes,
        edges=deduped_edges,
        message=f"Stages '{source_label}' and '{target_label}' merged successfully",
    )
