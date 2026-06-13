"""Template engine — four-level template management and deviation recording."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StageTemplate:
    """A single stage within a project template."""

    name: str                      # e.g. setup/analysis/design/develop/verify/deploy
    required_skills: list[str]     # Required skill IDs
    optional_skills: list[str]     # Optional skill IDs
    order: int                     # Execution order


@dataclass
class ProjectTemplate:
    """A complete project template for a complexity route."""

    route: str                     # trivial/light/standard/deep
    stages: list[StageTemplate]
    description: str = ""


@dataclass
class Deviation:
    """A deviation record between expected and actual stage execution."""

    project_id: str
    template_route: str
    deviation_type: str            # added/removed/reordered
    detail: str


class TemplateEngine:
    """Template engine.

    Responsibilities:
    1. Manage four default project templates.
    2. Recommend stage-skill bindings.
    3. Record deviations from the template.
    """

    def __init__(self) -> None:
        """Initialize default templates."""
        self._templates: dict[str, ProjectTemplate] = {}
        self._init_default_templates()

    def _init_default_templates(self) -> None:
        """Load built-in templates for the four complexity routes."""
        self._templates["trivial"] = ProjectTemplate(
            route="trivial",
            description="Trivial project: single page CRUD",
            stages=[
                StageTemplate("setup", ["init-project"], [], 1),
                StageTemplate("develop", ["generate-page", "generate-api"], [], 2),
                StageTemplate("verify", ["run-tests"], [], 3),
            ],
        )
        self._templates["light"] = ProjectTemplate(
            route="light",
            description="Light project: multi-page with auth",
            stages=[
                StageTemplate("setup", ["init-project", "setup-auth"], [], 1),
                StageTemplate("analysis", ["analyze-requirements"], [], 2),
                StageTemplate(
                    "design",
                    ["design-database", "design-api"],
                    ["design-ui"],
                    3,
                ),
                StageTemplate(
                    "develop", ["generate-pages", "generate-apis"], [], 4
                ),
                StageTemplate(
                    "verify", ["run-tests"], ["security-scan"], 5
                ),
            ],
        )
        self._templates["standard"] = ProjectTemplate(
            route="standard",
            description="Standard project: full SDLC",
            stages=[
                StageTemplate("setup", ["init-project", "setup-ci"], [], 1),
                StageTemplate(
                    "analysis",
                    ["analyze-requirements", "write-prd"],
                    [],
                    2,
                ),
                StageTemplate(
                    "design",
                    ["design-architecture", "design-database", "design-api"],
                    ["design-ui"],
                    3,
                ),
                StageTemplate(
                    "develop",
                    ["implement-backend", "implement-frontend"],
                    [],
                    4,
                ),
                StageTemplate(
                    "verify",
                    ["unit-tests", "integration-tests", "e2e-tests"],
                    [],
                    5,
                ),
                StageTemplate(
                    "deploy",
                    ["deploy-staging"],
                    ["deploy-production"],
                    6,
                ),
            ],
        )
        self._templates["deep"] = ProjectTemplate(
            route="deep",
            description="Deep project: enterprise-grade",
            stages=[
                StageTemplate(
                    "setup",
                    ["init-project", "setup-ci", "setup-monitoring"],
                    [],
                    1,
                ),
                StageTemplate(
                    "analysis",
                    ["analyze-requirements", "write-prd", "stakeholder-review"],
                    [],
                    2,
                ),
                StageTemplate(
                    "design",
                    [
                        "design-architecture",
                        "design-database",
                        "design-api",
                        "design-security",
                    ],
                    ["design-ui", "design-performance"],
                    3,
                ),
                StageTemplate(
                    "develop",
                    [
                        "implement-backend",
                        "implement-frontend",
                        "implement-infra",
                    ],
                    [],
                    4,
                ),
                StageTemplate(
                    "verify",
                    [
                        "unit-tests",
                        "integration-tests",
                        "e2e-tests",
                        "security-audit",
                        "performance-tests",
                    ],
                    [],
                    5,
                ),
                StageTemplate(
                    "deploy",
                    ["deploy-staging", "deploy-production", "setup-monitoring"],
                    [],
                    6,
                ),
            ],
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
            if s.name == stage:
                return s.required_skills + s.optional_skills
        return []

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

        expected_stages = [s.name for s in template.stages]
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
