"""CanvasState related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PositionDTO(BaseModel):
    """Node position in the canvas."""

    x: float
    y: float


class NodeDataDTO(BaseModel):
    """Custom data attached to a React Flow node."""

    model_config = ConfigDict(extra="ignore")

    label: str | None = None
    status: str | None = None
    progress: float | None = Field(None, ge=0, le=100)
    stage_id: str | None = None
    skill_type: str | None = None
    gate_type: str | None = None
    decision_status: str | None = None
    merge_group_label: str | None = None
    merged_stage_keys: list[str] | None = None
    is_merged: bool = False


class CanvasNodeDTO(BaseModel):
    """A React Flow node representation."""

    id: str
    type: str | None = None
    position: PositionDTO
    data: NodeDataDTO | None = None
    style: dict[str, str] | None = None
    width: float | None = None
    height: float | None = None


class CanvasEdgeDTO(BaseModel):
    """A React Flow edge representation."""

    id: str
    source: str
    target: str
    type: str | None = None
    animated: bool | None = None
    style: dict[str, str] | None = None
    label: str | None = None


class ViewportDTO(BaseModel):
    """Canvas viewport state."""

    x: float
    y: float
    zoom: float = Field(1.0, ge=0.1, le=5.0)


class CanvasStateResponseDTO(BaseModel):
    """DTO for canvas state response."""

    model_config = ConfigDict(from_attributes=True)

    project_id: str
    nodes: list[CanvasNodeDTO]
    edges: list[CanvasEdgeDTO]
    viewport: ViewportDTO
    updated_at: datetime | None = None


class CanvasStateSaveDTO(BaseModel):
    """DTO for saving canvas state."""

    nodes: list[CanvasNodeDTO]
    edges: list[CanvasEdgeDTO]
    viewport: ViewportDTO | None = None


class MergeStagePayload(BaseModel):
    """DTO for merging two adjacent stages."""

    source_stage_id: str
    target_stage_id: str


class MergeStageResult(BaseModel):
    """DTO for stage merge result."""

    project_id: str
    merged_stage_id: str
    nodes: list[CanvasNodeDTO]
    edges: list[CanvasEdgeDTO]
    message: str
