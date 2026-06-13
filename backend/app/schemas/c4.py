"""C4 related Pydantic schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class DSLEditDTO(BaseModel):
    """DTO for manual DSL edit."""

    content: str
    edit_reason: str
    editor: str


class C4DSLVersionDTO(BaseModel):
    """DTO for DSL version listing."""

    version: str
    is_current: bool
    created_at: str
    hash: str


class AnalysisIssueDTO(BaseModel):
    """Single architecture analysis finding."""

    rule_id: str
    severity: str
    message: str
    node_ids: list[str]
    fix_hint: str


class ConsistencyIssueDTO(BaseModel):
    """Single design-to-code consistency finding."""

    rule_id: str
    severity: str
    message: str
    c4_node_id: str = ""
    code_entity_id: str = ""
    fix_hint: str = ""
    fix_action: str = ""


class ConsistencyReportDTO(BaseModel):
    """Complete consistency check result."""

    passed: bool
    issues: list[ConsistencyIssueDTO]
    summary: dict[str, int]
    code_scan_summary: dict[str, int]


class AnalysisReportDTO(BaseModel):
    """Complete architecture analysis result."""

    passed: bool
    issues: list[AnalysisIssueDTO]
    summary: dict[str, int]


class C4LevelAnalysisDTO(BaseModel):
    """Analysis result for a single C4 level."""

    level: str
    passed: bool
    issues: list[AnalysisIssueDTO]
    summary: dict[str, int]


class C4AnalyzeResponseDTO(BaseModel):
    """DTO for full C4 architecture governance analysis."""

    project_id: str
    overall_passed: bool
    levels: list[C4LevelAnalysisDTO]
    consistency: ConsistencyReportDTO | None = None


class C4RenderResponseDTO(BaseModel):
    """DTO for C4 Mermaid render response."""

    mermaid_code: str
    view_level: str
    node_count: int
    edge_count: int
    debug_info: str = ""
    analysis_report: AnalysisReportDTO | None = None
    consistency_report: ConsistencyReportDTO | None = None


class C4WireframeResponseDTO(BaseModel):
    """DTO for wireframe generation response."""

    svg: str
    page_count: int
    edge_count: int
    orphan_pages: list[str]
    pages: list[dict[str, str]]


class C4SketchResponseDTO(BaseModel):
    """DTO for sketch generation response."""

    html: str
    format: str = "html"


class C4OrphanComponentDTO(BaseModel):
    """Single orphan component summary."""

    id: str
    name: str
    container_id: str | None = None
    source: str = "doc"
    implemented: bool = False
    intentional_orphan: bool = False
    source_file: str | None = None


class C4RegistryStatsDTO(BaseModel):
    """C4 registry statistics."""

    project_id: str
    systems: int
    actors: int
    containers: int
    components: int
    interfaces: int
    relationships: int
    orphan_count: int
    intentional_orphan_count: int
    effective_orphan_count: int
    orphans: list[C4OrphanComponentDTO]


class C4ExtractResponseDTO(BaseModel):
    """DTO for C4 registry extraction trigger response."""

    project_id: str
    message: str
    stats: C4RegistryStatsDTO


class C4DiffItemDTO(BaseModel):
    """Single changed entity in a registry diff."""

    id: str
    before: str | None = None
    after: str | None = None


class C4RelationshipTupleDTO(BaseModel):
    """A relationship represented as (source, target, description)."""

    source: str
    target: str
    description: str | None = None


class C4RegistryDiffDTO(BaseModel):
    """DTO for registry diff between two points in time."""

    project_id: str
    since: str
    components_added: list[str]
    components_removed: list[str]
    components_changed: list[C4DiffItemDTO]
    relationships_added: list[C4RelationshipTupleDTO]
    relationships_removed: list[C4RelationshipTupleDTO]
    orphan_count_before: int
    orphan_count_after: int
    components_before: int
    components_after: int
    relationships_before: int
    relationships_after: int


class C4OrphanToggleResponseDTO(BaseModel):
    """DTO for toggling the intentional orphan flag."""

    project_id: str
    component_id: str
    intentional_orphan: bool


class C4FixIssueDTO(BaseModel):
    """Single issue submitted to the governance fix planner."""

    issue_id: str
    source: str = "validator"
    rule_id: str
    severity: str
    message: str
    node_ids: list[str] = []
    c4_node_id: str = ""
    code_entity_id: str = ""
    fix_hint: str = ""
    fix_action: str = ""
    root_cause: str = "UNKNOWN"
    auto_fixable: bool = False
    confidence: str = "LOW"
    extra: dict[str, Any] = {}


class C4FixPlanRequestDTO(BaseModel):
    """Request body for generating a C4 governance fix plan."""

    issues: list[C4FixIssueDTO]
    context: dict[str, Any] | None = None


class C4ChangeSetDTO(BaseModel):
    """Single proposed change in a fix plan."""

    action: str
    target_path: str
    before: str | None = None
    after: str | None = None
    rationale: str = ""
    risk_level: str = "LOW"
    auto_applicable: bool = False
    requires_confirmation: bool = True
    issue_id: str = ""


class C4FixPlanItemDTO(BaseModel):
    """A single plan returned by the fix planner."""

    issue_ids: list[str]
    changes: list[C4ChangeSetDTO]
    dry_run: bool = True


class C4FixPlanResponseDTO(BaseModel):
    """Response containing one or more fix plans for the submitted issues."""

    project_id: str
    plans: list[C4FixPlanItemDTO]
    analysis: str = ""
    strategy_prompt: str = ""


class C4OptimizeChangeRequestDTO(BaseModel):
    """Request to optimize a single change via AI."""

    prompt: str
    change: C4ChangeSetDTO


class C4OptimizeChangeResponseDTO(BaseModel):
    """Response containing the optimized change."""

    change: C4ChangeSetDTO
