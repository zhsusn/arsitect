"""Template engine — four-level template management and deviation recording."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class StageTemplate:
    """A single stage within a project template.

    Attributes:
        business_stage_key: Business stage key, e.g. "clarify" / "build".
        stage_name: Human-readable stage name (Chinese).
        primary_skill_id: Main skill bound to this stage.
        auxiliary_skill_ids: Auxiliary skills bound to this stage.
        order: Execution order.
        is_gate_required: Whether a gate is required at stage exit.
        auto_advance: Whether to auto-advance after gate pass.
    """

    business_stage_key: str
    stage_name: str
    primary_skill_id: str
    auxiliary_skill_ids: list[str]
    order: int
    is_gate_required: bool = True
    auto_advance: bool = False


@dataclass
class MergeGroup:
    """A group of business stages merged into one runtime stage."""

    group_id: str
    label: str
    business_stage_keys: list[str]
    gate_at_end: bool = True
    auto_advance: bool = True


@dataclass
class ProjectTemplate:
    """A complete project template for a complexity route."""

    route: str  # trivial/light/standard/deep
    stages: list[StageTemplate]
    merge_groups: list[MergeGroup]
    execution_strategy: str = "semi_auto"
    description: str = ""

    def get_merge_policy(self) -> dict[str, Any]:
        """Return the merge policy as a JSON-serializable dict."""
        return {
            "groups": [
                {
                    "group_id": g.group_id,
                    "label": g.label,
                    "business_stage_keys": g.business_stage_keys,
                    "gate_at_end": g.gate_at_end,
                    "auto_advance": g.auto_advance,
                }
                for g in self.merge_groups
            ]
        }


@dataclass
class Deviation:
    """A deviation record between expected and actual stage execution."""

    project_id: str
    template_route: str
    deviation_type: str  # added/removed/reordered
    detail: str


# Standard 9 business stages used across all complexity routes.
BASE_STAGE_DEFINITIONS: list[StageTemplate] = [
    StageTemplate(
        "brainstorm",
        "头脑风暴",
        "brainstorming",
        ["competitive-analysis"],
        order=1,
        is_gate_required=False,
        auto_advance=True,
    ),
    StageTemplate(
        "charter",
        "项目立项",
        "requirement-analysis",
        ["project-size-estimate"],
        order=2,
        is_gate_required=True,
        auto_advance=True,
    ),
    StageTemplate(
        "clarify",
        "概要需求",
        "requirement-analysis",
        ["progress-tracker"],
        order=3,
        is_gate_required=True,
        auto_advance=True,
    ),
    StageTemplate(
        "align",
        "详细需求",
        "prd-generation",
        ["self-check"],
        order=4,
        is_gate_required=True,
        auto_advance=True,
    ),
    StageTemplate(
        "contract-hld",
        "概要设计",
        "high-level-design",
        ["functional-architecture-generator"],
        order=5,
        is_gate_required=True,
        auto_advance=True,
    ),
    StageTemplate(
        "contract-dd",
        "详细设计",
        "detailed-design",
        ["interface-first-dev"],
        order=6,
        is_gate_required=True,
        auto_advance=True,
    ),
    StageTemplate(
        "build",
        "编码实现",
        "executing-plans",
        ["unit-test-generator"],
        order=7,
        is_gate_required=True,
        auto_advance=True,
    ),
    StageTemplate(
        "verify",
        "测试验证",
        "integration-test",
        ["uat-verification"],
        order=8,
        is_gate_required=True,
        auto_advance=True,
    ),
    StageTemplate(
        "release",
        "发布上线",
        "release-management",
        ["monitoring-setup"],
        order=9,
        is_gate_required=True,
        auto_advance=False,
    ),
]

# Map business stage key to its base definition for quick lookup.
_BASE_STAGE_MAP: dict[str, StageTemplate] = {
    s.business_stage_key: s for s in BASE_STAGE_DEFINITIONS
}

# Extra stage used only by the Deep route.
_ARCHITECTURE_DRIFT_STAGE = StageTemplate(
    "architecture-drift",
    "架构漂移检测",
    "c4-governance-fix",
    ["self-check"],
    order=6,
    is_gate_required=True,
    auto_advance=True,
)

# Route-specific merge group definitions.
ROUTE_MERGE_GROUPS: dict[str, list[MergeGroup]] = {
    "trivial": [
        MergeGroup(
            "g1",
            "项目立项",
            ["brainstorm", "charter"],
            gate_at_end=True,
            auto_advance=True,
        ),
        MergeGroup(
            "g2",
            "需求对齐",
            ["clarify", "align"],
            gate_at_end=True,
            auto_advance=True,
        ),
        MergeGroup(
            "g3",
            "设计实现",
            ["contract-hld", "contract-dd", "build", "verify", "release"],
            gate_at_end=True,
            auto_advance=True,
        ),
    ],
    "light": [
        MergeGroup("g1", "头脑风暴", ["brainstorm"]),
        MergeGroup("g2", "项目立项", ["charter"]),
        MergeGroup(
            "g3",
            "需求对齐",
            ["clarify", "align"],
            gate_at_end=True,
            auto_advance=True,
        ),
        MergeGroup(
            "g4",
            "设计契约",
            ["contract-hld", "contract-dd"],
            gate_at_end=True,
            auto_advance=True,
        ),
        MergeGroup(
            "g5",
            "交付上线",
            ["build", "verify", "release"],
            gate_at_end=True,
            auto_advance=True,
        ),
    ],
    "standard": [
        MergeGroup("g1", "头脑风暴", ["brainstorm"]),
        MergeGroup("g2", "项目立项", ["charter"]),
        MergeGroup("g3", "概要需求", ["clarify"]),
        MergeGroup("g4", "详细需求", ["align"]),
        MergeGroup("g5", "概要设计", ["contract-hld"]),
        MergeGroup("g6", "详细设计", ["contract-dd"]),
        MergeGroup("g7", "编码实现", ["build"]),
        MergeGroup("g8", "测试验证", ["verify"]),
        MergeGroup("g9", "发布上线", ["release"]),
    ],
    "deep": [
        MergeGroup("g1", "头脑风暴", ["brainstorm"]),
        MergeGroup("g2", "项目立项", ["charter"]),
        MergeGroup("g3", "概要需求", ["clarify"]),
        MergeGroup("g4", "详细需求", ["align"]),
        MergeGroup("g5", "概要设计", ["contract-hld"]),
        MergeGroup("g6", "详细设计", ["contract-dd"]),
        MergeGroup(
            "g7",
            "架构漂移检测",
            ["architecture-drift"],
            gate_at_end=True,
            auto_advance=True,
        ),
        MergeGroup("g8", "编码实现", ["build"]),
        MergeGroup("g9", "测试验证", ["verify"]),
        MergeGroup("g10", "发布上线", ["release"]),
    ],
}

ROUTE_EXECUTION_STRATEGY: dict[str, str] = {
    "trivial": "full_auto",
    "light": "full_auto",
    "standard": "semi_auto",
    "deep": "full_manual",
}

ROUTE_DESCRIPTION: dict[str, str] = {
    "trivial": "Trivial project: single page CRUD",
    "light": "Light project: multi-page with auth",
    "standard": "Standard project: full SDLC",
    "deep": "Deep project: enterprise-grade with architecture drift detection",
}


class TemplateEngine:
    """Template engine.

    Responsibilities:
    1. Manage four default project templates.
    2. Recommend stage-skill bindings.
    3. Provide merge policies per complexity route.
    4. Record deviations from the template.
    """

    def __init__(self) -> None:
        """Initialize default templates."""
        self._templates: dict[str, ProjectTemplate] = {}
        self._init_default_templates()

    def _build_route_stages(self, route: str) -> list[StageTemplate]:
        """Build the stage sequence for a route from base definitions and merge groups."""
        groups = ROUTE_MERGE_GROUPS[route]
        route_stages: list[StageTemplate] = []
        for idx, group in enumerate(groups, start=1):
            # Resolve base definitions for all keys in the group.
            defs: list[StageTemplate] = []
            for key in group.business_stage_keys:
                if key == "architecture-drift":
                    defs.append(_ARCHITECTURE_DRIFT_STAGE)
                else:
                    defs.append(_BASE_STAGE_MAP[key])

            # The representative stage is the last one in the group (gate at end).
            representative = defs[-1]

            # Collect all unique skills across the group. The representative's
            # primary skill remains the stage primary; all others become auxiliary.
            all_primary = {d.primary_skill_id for d in defs}
            all_auxiliary: list[str] = []
            seen = set()
            for d in defs:
                for skill in d.auxiliary_skill_ids:
                    if skill not in seen:
                        seen.add(skill)
                        all_auxiliary.append(skill)
            # Add other primaries as auxiliary so they are not lost in merged groups.
            for skill in all_primary:
                if skill != representative.primary_skill_id and skill not in seen:
                    seen.add(skill)
                    all_auxiliary.append(skill)

            route_stages.append(
                StageTemplate(
                    business_stage_key=representative.business_stage_key,
                    stage_name=group.label,
                    primary_skill_id=representative.primary_skill_id,
                    auxiliary_skill_ids=all_auxiliary,
                    order=idx,
                    is_gate_required=group.gate_at_end,
                    auto_advance=group.auto_advance,
                )
            )
        return route_stages

    def _init_default_templates(self) -> None:
        """Load built-in templates for the four complexity routes."""
        for route in ("trivial", "light", "standard", "deep"):
            self._templates[route] = ProjectTemplate(
                route=route,
                description=ROUTE_DESCRIPTION[route],
                stages=self._build_route_stages(route),
                merge_groups=ROUTE_MERGE_GROUPS[route],
                execution_strategy=ROUTE_EXECUTION_STRATEGY[route],
            )

    def get_template(self, route: str) -> ProjectTemplate | None:
        """Return the template for a route (case-insensitive)."""
        return self._templates.get(route.lower())

    def list_routes(self) -> list[str]:
        """Return all available template routes."""
        return list(self._templates.keys())

    def list_available_skills(self, route: str, stage: str) -> list[str]:
        """Return all available skills for a stage in a template."""
        template = self.get_template(route)
        if template is None:
            return []
        for s in template.stages:
            if s.business_stage_key == stage:
                return [s.primary_skill_id] + s.auxiliary_skill_ids
        return []

    def get_base_stage(self, business_stage_key: str) -> StageTemplate | None:
        """Return the base definition for a business stage key."""
        if business_stage_key == "architecture-drift":
            return _ARCHITECTURE_DRIFT_STAGE
        return _BASE_STAGE_MAP.get(business_stage_key)

    def get_merge_policy(self, route: str) -> dict[str, Any] | None:
        """Return the merge policy JSON for a complexity route."""
        template = self.get_template(route)
        if template is None:
            return None
        return template.get_merge_policy()

    def record_deviation(
        self,
        deviations: list[Deviation],
        project_id: str,
        template_route: str,
        actual_stages: list[str],
    ) -> list[Deviation]:
        """Record added/removed stage deviations against a template."""
        template = self.get_template(template_route)
        if template is None:
            return []

        expected_stages = [s.business_stage_key for s in template.stages]
        new_deviations: list[Deviation] = []

        # Added stages
        for stage in actual_stages:
            if stage not in expected_stages:
                new_deviations.append(
                    Deviation(
                        project_id=project_id,
                        template_route=template_route,
                        deviation_type="added",
                        detail=f"Stage '{stage}' not in template",
                    )
                )

        # Removed stages
        for stage in expected_stages:
            if stage not in actual_stages:
                new_deviations.append(
                    Deviation(
                        project_id=project_id,
                        template_route=template_route,
                        deviation_type="removed",
                        detail=f"Stage '{stage}' missing from execution",
                    )
                )

        deviations.extend(new_deviations)
        return new_deviations
