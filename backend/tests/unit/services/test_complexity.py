"""Tests for ComplexityService three-tier scoring."""

from __future__ import annotations

import pytest

from app.governance.complexity_router import ComplexityRoute
from app.services.complexity_service import ComplexityService


class TestComplexityServiceThreeTierScores:
    """Tests for ComplexityService three-tier score calculation."""

    @pytest.mark.parametrize(
        ("route", "expected_optimistic", "expected_expected", "expected_conservative"),
        [
            (ComplexityRoute.TRIVIAL, 10, 20, 30),
            (ComplexityRoute.LIGHT, 30, 45, 60),
            (ComplexityRoute.STANDARD, 60, 75, 90),
            (ComplexityRoute.DEEP, 90, 105, 120),
        ],
    )
    def test_calculate_three_tier_scores_at_full_confidence(
        self,
        route: ComplexityRoute,
        expected_optimistic: int,
        expected_expected: int,
        expected_conservative: int,
    ) -> None:
        """Base scores are returned when confidence is 1.0."""
        scores = ComplexityService._calculate_three_tier_scores(route, 1.0)
        assert scores["optimistic_score"] == expected_optimistic
        assert scores["expected_score"] == expected_expected
        assert scores["conservative_score"] == expected_conservative

    @pytest.mark.parametrize(
        ("confidence", "expected_spread"),
        [
            (1.0, 0),
            (0.8, 5),
            (0.7, 5),
            (0.5, 15),
            (0.4, 15),
            (0.3, 25),
        ],
    )
    def test_confidence_widens_score_spread(
        self, confidence: float, expected_spread: int
    ) -> None:
        """Lower confidence increases the gap between optimistic and conservative."""
        scores = ComplexityService._calculate_three_tier_scores(
            ComplexityRoute.STANDARD, confidence
        )
        assert scores["optimistic_score"] == max(0, 60 - expected_spread)
        assert scores["expected_score"] == 75
        assert scores["conservative_score"] == 90 + expected_spread

    def test_assess_returns_non_zero_scores(self) -> None:
        """Assess produces real three-tier scores instead of zeros."""
        result = ComplexityService.assess(
            module_count=3,
            interface_complexity=2,
            page_count=2,
            entity_count=2,
            integration_count=1,
        )
        assert result["optimistic_score"] > 0
        assert result["expected_score"] > 0
        assert result["conservative_score"] > 0
        assert result["optimistic_score"] < result["expected_score"]
        assert result["expected_score"] < result["conservative_score"]

    def test_calculate_scores_returns_non_zero_scores(self) -> None:
        """Calculate scores produces real three-tier scores."""
        result = ComplexityService.calculate_scores(
            module_count=10,
            interface_count=8,
            page_count=5,
            tech_complexity="Medium",
            risk_level="Low",
        )
        assert result["optimistic_score"] > 0
        assert result["expected_score"] > 0
        assert result["conservative_score"] > 0

    def test_assess_trivial_route(self) -> None:
        """Very small inputs route to Trivial with the lowest scores."""
        result = ComplexityService.assess(
            module_count=1,
            interface_complexity=1,
            page_count=1,
            entity_count=1,
            integration_count=0,
        )
        assert result["route"] == "trivial"
        assert result["optimistic_score"] <= result["expected_score"]
        assert result["expected_score"] <= result["conservative_score"]
