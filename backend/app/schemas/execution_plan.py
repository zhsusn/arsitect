"""ExecutionPlan Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PlanNodeDTO(BaseModel):
    """计划节点 DTO."""

    model_config = ConfigDict(from_attributes=True)

    node_id: str = Field(description="节点 ID")
    plan_id: str = Field(description="计划 ID")
    skill_id: str = Field(description="Skill ID")
    stage_id: str = Field(description="Stage ID")
    order_index: int = Field(description="排序索引")
    node_type: str = Field(description="节点类型: primary | auxiliary")
    module_id: str | None = Field(default=None, description="模块 ID")
    status: str = Field(description="状态")


class ParallelGroupDTO(BaseModel):
    """并行组 DTO."""

    model_config = ConfigDict(from_attributes=True)

    group_id: str = Field(description="组 ID")
    stage_id: str = Field(description="Stage ID")
    skill_ids: list[str] = Field(default_factory=list, description="组内 Skill ID 列表")
    group_type: str = Field(description="组类型: primary_serial | auxiliary_parallel")


class PlanAdjustmentDTO(BaseModel):
    """计划调整项 DTO."""

    node_id: str = Field(description="节点 ID")
    action: str = Field(description="操作: move_stage | move_group | add_dependency | remove_dependency | reorder")
    target_stage_id: str | None = Field(default=None, description="目标 Stage ID")
    target_group_id: str | None = Field(default=None, description="目标组 ID")
    source_node_id: str | None = Field(default=None, description="源节点 ID")


class ValidationErrorItem(BaseModel):
    """校验错误项."""

    node_id: str | None = Field(default=None, description="相关节点 ID")
    error_code: str = Field(description="错误码")
    message: str = Field(description="错误消息")


class PlanValidationResultDTO(BaseModel):
    """计划校验结果 DTO."""

    passed: bool = Field(description="是否通过校验")
    errors: list[ValidationErrorItem] = Field(default_factory=list, description="错误列表")


class ExecutionPlanCreateDTO(BaseModel):
    """创建执行计划请求 DTO."""

    project_id: str = Field(description="项目 ID")
    template_level: str | None = Field(default=None, description="模板级别")


class ExecutionPlanSummaryDTO(BaseModel):
    """执行计划列表项 DTO."""

    model_config = ConfigDict(from_attributes=True)

    plan_id: str = Field(description="计划 ID")
    project_id: str = Field(description="项目 ID")
    project_name: str | None = Field(default=None, description="项目名称")
    version: str = Field(description="版本号")
    status: str = Field(description="计划状态: Draft | Frozen | Running | Completed | Failed")
    template_level: str | None = Field(default=None, description="模板级别")
    created_at: datetime | None = Field(default=None, description="创建时间")
    updated_at: datetime | None = Field(default=None, description="更新时间")


class ExecutionPlanResponseDTO(BaseModel):
    """执行计划响应 DTO."""

    model_config = ConfigDict(from_attributes=True)

    plan_id: str = Field(description="计划 ID")
    project_id: str = Field(description="项目 ID")
    version: str = Field(description="版本号")
    is_frozen: bool = Field(description="是否冻结")
    template_level: str | None = Field(default=None, description="模板级别")
    node_order: list[str] = Field(default_factory=list, description="节点执行顺序")
    parallel_groups: list[ParallelGroupDTO] = Field(default_factory=list, description="并行组")
    dependency_matrix: dict[str, Any] = Field(default_factory=dict, description="依赖矩阵")
    nodes: list[PlanNodeDTO] = Field(default_factory=list, description="节点详情")
    created_at: datetime | None = Field(default=None, description="创建时间")
    updated_at: datetime | None = Field(default=None, description="更新时间")


class BypassRequestDTO(BaseModel):
    """旁路审批请求 DTO."""

    stage_id: str = Field(description="Stage ID")
    skill_id: str = Field(description="Skill ID")
    authorization_token: str = Field(min_length=32, max_length=128, description="授权令牌")
    acknowledged: bool = Field(description="是否确认风险")
    reason: str = Field(default="紧急执行", description="旁路理由")


class BypassRecordDTO(BaseModel):
    """旁路审批记录 DTO."""

    model_config = ConfigDict(from_attributes=True)

    record_id: str = Field(description="记录 ID")
    plan_id: str = Field(description="计划 ID")
    stage_id: str = Field(description="Stage ID")
    skill_id: str = Field(description="Skill ID")
    triggered_by: str = Field(description="触发者")
    reason: str | None = Field(default=None, description="旁路理由")
    status: str = Field(description="状态")
    deadline_at: datetime = Field(description="截止时间")
    closed_at: datetime | None = Field(default=None, description="关闭时间")
    created_at: datetime = Field(description="创建时间")


class StageReadinessDTO(BaseModel):
    """Stage 就绪状态 DTO."""

    stage_id: str = Field(description="Stage ID")
    ready: bool = Field(description="是否就绪")
    reason: str | None = Field(default=None, description="未就绪原因")


class StageExecutionResultDTO(BaseModel):
    """Stage 执行结果 DTO."""

    stage_id: str = Field(description="Stage ID")
    status: str = Field(description="状态")
    node_results: list[dict[str, Any]] = Field(default_factory=list, description="节点执行结果")


class StageCompletionDTO(BaseModel):
    """Stage 完成判定 DTO."""

    stage_id: str = Field(description="Stage ID")
    completion_status: str = Field(description="完成状态")
    warning_count: int = Field(default=0, description="告警数")


class ModuleExecutionStreamDTO(BaseModel):
    """Module 执行流 DTO."""

    module_id: str | None = Field(default=None, description="模块 ID")
    node_ids: list[str] = Field(default_factory=list, description="节点 ID 列表")
    can_parallel: bool = Field(default=True, description="是否可以并行")
