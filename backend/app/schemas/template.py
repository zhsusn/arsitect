"""Template related Pydantic schemas."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, field_validator


class MergeGroupDTO(BaseModel):
    """DTO for a merge group inside a merge policy."""

    group_id: str
    label: str
    business_stage_keys: list[str]
    gate_at_end: bool = True
    auto_advance: bool = True


class MergePolicyDTO(BaseModel):
    """DTO for a template merge policy."""

    groups: list[MergeGroupDTO] = Field(default_factory=list)


class TemplateStageDTO(BaseModel):
    """DTO for a template stage."""

    model_config = {"from_attributes": True}

    stage_id: str
    stage_name: str
    business_stage_key: str
    order_index: int
    template_id: str
    primary_skill_id: str | None = None
    auxiliary_skill_ids: list[str] | None = None
    gate_id: str | None = None
    skippable: bool = False
    merge_group_id: str | None = None
    is_gate_required: bool = True
    auto_advance: bool = False

    @field_validator("auxiliary_skill_ids", mode="before")
    @classmethod
    def _parse_json_list(cls, v: Any) -> Any:
        if isinstance(v, str):
            return json.loads(v)
        return v


class TemplateResponseDTO(BaseModel):
    """DTO for a template."""

    model_config = {"from_attributes": True}

    template_id: str
    template_name: str
    description: str
    stage_count: int
    estimated_skill_count: int
    applicable_complexity: str
    config_json: dict[str, Any] | None = None
    default_execution_strategy: str = "semi_auto"
    merge_policy_json: MergePolicyDTO | None = None

    @field_validator("config_json", mode="before")
    @classmethod
    def _parse_json_string(cls, v: Any) -> Any:
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("merge_policy_json", mode="before")
    @classmethod
    def _parse_merge_policy(cls, v: Any) -> Any:
        if isinstance(v, str):
            return json.loads(v)
        return v


class TemplateDetailDTO(BaseModel):
    """Template with its stage sequence."""

    template: TemplateResponseDTO
    stages: list[TemplateStageDTO]


class ProjectStageDTO(BaseModel):
    """DTO for a project stage."""

    model_config = {"from_attributes": True}

    project_stage_id: str
    project_id: str
    stage_id: str
    order_index: int
    status: str
    primary_skill_id: str | None = None
    skippable: bool = False
    is_frozen: bool = False
    merge_group_id: str | None = None
    execution_status: str


class TemplateDeviationPreviewRequestDTO(BaseModel):
    """Request to preview template deviation."""

    new_template_id: str = Field(..., description="目标模板 ID")


class TemplateDeviationPreviewDTO(BaseModel):
    """Preview of template switch impact."""

    frozen_count: int
    removed_count: int
    added_count: int
    retained_count: int


class TemplateStageUpdateDTO(BaseModel):
    """Request to update a template stage's skill bindings."""

    primary_skill_id: str | None = Field(None, description="主 Skill ID")
    auxiliary_skill_ids: list[str] | None = Field(None, description="辅助 Skill ID 列表")


class TemplateExecutionStrategyUpdateDTO(BaseModel):
    """Request to update a template's default execution strategy."""

    default_execution_strategy: str = Field(
        ..., description="默认执行策略: full_auto / semi_auto / full_manual"
    )


class TemplateExecutionStrategyResponseDTO(BaseModel):
    """Response for template execution strategy update."""

    template_id: str
    default_execution_strategy: str


class DeviationItemDTO(BaseModel):
    """Single deviation item."""

    stage_id: str
    stage_name: str
    change_type: str = Field(..., description="新增 / 删除 / 修改")
    old_skill_id: str | None = None
    new_skill_id: str | None = None
    old_auxiliary_skill_ids: list[str] | None = None
    new_auxiliary_skill_ids: list[str] | None = None


class TemplateDeviationConfirmDTO(BaseModel):
    """Request to confirm template deviation."""

    new_template_id: str = Field(..., description="目标模板 ID")
    reason: str = Field(..., min_length=1, description="偏离原因")
    risk_acknowledged: bool = Field(False, description="是否已确认风险")
    deviation_items: list[DeviationItemDTO] = Field(default_factory=list)


class TemplateDeviationLogDTO(BaseModel):
    """DTO for a deviation log entry."""

    model_config = {"from_attributes": True}

    deviation_id: str
    project_id: str
    decision_type: str
    reason: str | None = None
    details_json: str | None = None
    operator_id: str | None = None
    created_at: str | None = None


class StageSkippableUpdateDTO(BaseModel):
    """Request to update stage skippable flag."""

    skippable: bool


class StageReorderDTO(BaseModel):
    """Request to reorder stages."""

    stage_orders: list[tuple[str, int]] = Field(
        ..., description="List of (project_stage_id, new_order_index)"
    )


class StageMergeDTO(BaseModel):
    """Request to merge two adjacent stages."""

    source_stage_id: str
    target_stage_id: str
    new_stage_name: str | None = None


class StageSplitDTO(BaseModel):
    """Request to split a stage into two."""

    stage_id: str
    split_after_skill_id: str | None = None
    first_stage_name: str | None = None
    second_stage_name: str | None = None
