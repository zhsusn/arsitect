"""Pydantic DTOs for WireframeNavLink operations."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class WireframeNavLinkResponseDTO(BaseModel):
    """Wireframe nav link response."""

    link_id: str
    wireframe_id: str
    project_id: str
    source_page_id: str
    target_page_id: str
    interface_refs_json: str | None
    relation_strength: str
    interface_count: int
    is_marked_missing: bool
    created_at: datetime | None
    updated_at: datetime | None
