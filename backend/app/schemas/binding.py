"""Pydantic DTOs for BindingRule operations."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class BindingCreateDTO(BaseModel):
    """Create binding rule request."""

    source_field: str = Field(..., min_length=1, max_length=128)
    target_field: str = Field(..., min_length=1, max_length=128)
    transform_type: str = Field(default="DIRECT")
    transform_config: str | None = None
    status: str = Field(default="ACTIVE")


class BindingUpdateDTO(BaseModel):
    """Update binding rule request."""

    source_field: str | None = Field(default=None, min_length=1, max_length=128)
    target_field: str | None = Field(default=None, min_length=1, max_length=128)
    transform_type: str | None = Field(
        default=None, pattern=r"^(DIRECT|MAP|FORMAT|FILTER)$"
    )
    transform_config: str | None = None
    status: str | None = Field(default=None, pattern=r"^(ACTIVE|INACTIVE)$")


class BindingResponseDTO(BaseModel):
    """Binding rule response."""

    rule_id: str
    project_id: str
    source_field: str
    target_field: str
    transform_type: str
    transform_config: str | None
    status: str
    created_at: datetime | None
    updated_at: datetime | None
