"""Complexity router — five-dimension assessment and route recommendation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ComplexityRoute(StrEnum):
    """Four complexity routes mapped to project template levels."""

    TRIVIAL = "trivial"  # XS: < 1 week
    LIGHT = "light"  # S: 1-2 weeks
    STANDARD = "standard"  # M: 2-4 weeks
    DEEP = "deep"  # L: > 4 weeks


@dataclass
class ComplexityMetrics:
    """Five-dimension complexity metrics."""

    code_lines: int  # Estimated lines of code
    external_deps: int  # External dependencies
    data_models: int  # Data models
    api_endpoints: int  # API endpoints
    business_rules: int  # Business rules


@dataclass
class ComplexityAssessment:
    """Result of a complexity assessment."""

    route: ComplexityRoute
    confidence: float  # 0-1
    metrics: ComplexityMetrics
    reasoning: str
    manual_override: bool = False


class ComplexityRouter:
    """Complexity router.

    Responsibilities:
    1. Five-dimension scoring.
    2. Four-route recommendation.
    3. Manual override support.
    """

    # Per-dimension thresholds.
    THRESHOLDS: dict[ComplexityRoute, dict[str, int]] = {
        ComplexityRoute.TRIVIAL: {
            "code_lines": 500,
            "external_deps": 3,
            "data_models": 3,
            "api_endpoints": 5,
            "business_rules": 5,
        },
        ComplexityRoute.LIGHT: {
            "code_lines": 2000,
            "external_deps": 8,
            "data_models": 8,
            "api_endpoints": 15,
            "business_rules": 15,
        },
        ComplexityRoute.STANDARD: {
            "code_lines": 5000,
            "external_deps": 15,
            "data_models": 15,
            "api_endpoints": 30,
            "business_rules": 30,
        },
        # DEEP: anything exceeding STANDARD thresholds.
    }

    def assess(self, metrics: ComplexityMetrics) -> ComplexityAssessment:
        """Assess complexity and recommend a route.

        Algorithm:
        1. Score each dimension independently.
        2. Take the highest route as the overall recommendation.
        3. Compute confidence based on dimension consistency.
        """
        dimension_scores = self._score_dimensions(metrics)

        max_route = max(
            dimension_scores.items(),
            key=lambda x: self._route_rank(x[1]),
        )
        route = max_route[1]

        unique_routes = set(dimension_scores.values())
        if len(unique_routes) == 1:
            confidence = 1.0
        elif len(unique_routes) == 2:
            confidence = 0.7
        else:
            confidence = 0.4

        reasoning = self._build_reasoning(metrics, dimension_scores)

        return ComplexityAssessment(
            route=route,
            confidence=confidence,
            metrics=metrics,
            reasoning=reasoning,
        )

    def _score_dimensions(self, metrics: ComplexityMetrics) -> dict[str, ComplexityRoute]:
        """Score each dimension independently."""
        return {
            "code_lines": self._route_for_metric("code_lines", metrics.code_lines),
            "external_deps": self._route_for_metric("external_deps", metrics.external_deps),
            "data_models": self._route_for_metric("data_models", metrics.data_models),
            "api_endpoints": self._route_for_metric("api_endpoints", metrics.api_endpoints),
            "business_rules": self._route_for_metric("business_rules", metrics.business_rules),
        }

    def _route_for_metric(self, dimension: str, value: int) -> ComplexityRoute:
        """Return the route for a single dimension value."""
        thresholds = self.THRESHOLDS
        if value <= thresholds[ComplexityRoute.TRIVIAL][dimension]:
            return ComplexityRoute.TRIVIAL
        if value <= thresholds[ComplexityRoute.LIGHT][dimension]:
            return ComplexityRoute.LIGHT
        if value <= thresholds[ComplexityRoute.STANDARD][dimension]:
            return ComplexityRoute.STANDARD
        return ComplexityRoute.DEEP

    @staticmethod
    def _route_rank(route: ComplexityRoute) -> int:
        """Return numeric rank for route comparison."""
        ranks = {
            ComplexityRoute.TRIVIAL: 0,
            ComplexityRoute.LIGHT: 1,
            ComplexityRoute.STANDARD: 2,
            ComplexityRoute.DEEP: 3,
        }
        return ranks[route]

    def _build_reasoning(
        self, metrics: ComplexityMetrics, scores: dict[str, ComplexityRoute]
    ) -> str:
        """Build human-readable assessment reasoning."""
        lines = ["Complexity Assessment:"]
        lines.append(f"  Code Lines: {metrics.code_lines} ({scores['code_lines'].value})")
        lines.append(f"  External Deps: {metrics.external_deps} ({scores['external_deps'].value})")
        lines.append(f"  Data Models: {metrics.data_models} ({scores['data_models'].value})")
        lines.append(f"  API Endpoints: {metrics.api_endpoints} ({scores['api_endpoints'].value})")
        lines.append(
            f"  Business Rules: {metrics.business_rules} ({scores['business_rules'].value})"
        )
        return "\n".join(lines)

    def apply_manual_override(
        self, assessment: ComplexityAssessment, manual_route: str
    ) -> ComplexityAssessment:
        """Apply a manual override to the recommended route."""
        assessment.route = ComplexityRoute(manual_route)
        assessment.manual_override = True
        assessment.reasoning += f"\n[MANUAL OVERRIDE] Route manually set to {manual_route}"
        return assessment
