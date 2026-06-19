"""Project review Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProjectReviewCreateDTO(BaseModel):
    """DTO for creating a project review record."""

    review_type: str
    item_id: str
    item_type: str
    status: str = "pending"
    notes: str | None = None
    reviewer_id: str | None = None


class ProjectReviewUpdateDTO(BaseModel):
    """DTO for updating a project review record."""

    status: str | None = None
    notes: str | None = None
    reviewer_id: str | None = None


class ProjectReviewResponseDTO(BaseModel):
    """DTO for project review response."""

    model_config = ConfigDict(from_attributes=True)

    review_id: str
    project_id: str
    review_type: str
    item_id: str
    item_type: str
    status: str
    notes: str | None = None
    reviewer_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
