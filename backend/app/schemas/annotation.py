"""Pydantic DTOs for annotation operations."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AnnotationCreateDTO(BaseModel):
    """Create annotation request."""

    project_id: str
    content: str = Field(..., min_length=1, max_length=2000)
    author: str
    annotation_type: str = "comment"


class AnnotationResponseDTO(BaseModel):
    """Annotation record response."""

    annotation_id: str
    stage_id: str
    author: str
    content: str
    annotation_type: str
    status: str
    created_at: datetime | None = None
