"""Complexity related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ComplexityInputDTO(BaseModel):
    """DTO for complexity assessment input (five dimensions)."""

    module_count: int = Field(..., ge=1, le=50)
    interface_count: int = Field(..., ge=0, le=100)
    page_count: int = Field(..., ge=0, le=50)
    tech_complexity: str = Field(..., pattern=r"^(Low|Medium|High)$")
    risk_level: str = Field(..., pattern=r"^(Low|Medium|High)$")


class ComplexityScoreDTO(BaseModel):
    """DTO for computed complexity scores."""

    optimistic_score: int
    expected_score: int
    conservative_score: int
    complexity_level: str


class SizeEstimateCreateDTO(BaseModel):
    """DTO for creating a size estimate."""

    module_count: int = Field(..., ge=1, le=50)
    interface_count: int = Field(..., ge=0, le=100)
    page_count: int = Field(..., ge=0, le=50)
    tech_complexity: str = Field(..., pattern=r"^(Low|Medium|High)$")
    risk_level: str = Field(..., pattern=r"^(Low|Medium|High)$")


class SizeEstimateResponseDTO(BaseModel):
    """DTO for size estimate response."""

    model_config = ConfigDict(from_attributes=True)

    estimate_id: str
    project_id: str
    module_count: int
    interface_count: int
    page_count: int
    tech_complexity: str
    risk_level: str
    optimistic_score: int | None
    expected_score: int | None
    conservative_score: int | None
    complexity_level: str | None
    created_at: datetime | None = None


class ComplexityAssessInputDTO(BaseModel):
    """DTO for complexity assessment input (five numeric dimensions)."""

    module_count: int = Field(..., ge=1, le=50)
    interface_complexity: int = Field(..., ge=1, le=10)
    page_count: int = Field(..., ge=1, le=100)
    entity_count: int = Field(..., ge=1, le=50)
    integration_count: int = Field(..., ge=1, le=20)


class ComplexityAssessResultDTO(BaseModel):
    """DTO for computed complexity assessment result."""

    optimistic_score: int
    expected_score: int
    conservative_score: int
    complexity_level: str
    route: str | None = None
    confidence: float | None = None
    reasoning: str | None = None
    radar_values: dict[str, float] | None = None


class PathDecisionCreateDTO(BaseModel):
    """DTO for creating a path decision log entry."""

    project_id: str | None = None
    decision_type: str = Field(..., pattern=r"^(assess|downgrade|path_select)$")
    from_path: str | None = None
    to_path: str
    reason: str | None = None


class PathDecisionResponseDTO(BaseModel):
    """DTO for path decision log response."""

    decision_id: str
    project_id: str | None = None
    decision_type: str
    from_path: str | None = None
    to_path: str
    reason: str | None = None
    created_at: str | None = None


class ComplexityTemplateDTO(BaseModel):
    """DTO for complexity template recommendation."""

    level: str
    label: str
    recommended_template: str
    description: str
    stage_count: int
    estimated_skill_count: int
