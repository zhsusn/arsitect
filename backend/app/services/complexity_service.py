"""Complexity assessment service — delegates to ComplexityRouter."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.governance.complexity_router import (
    ComplexityMetrics,
    ComplexityRoute,
    ComplexityRouter,
)
from app.models.project import Project
from app.models.size_estimate import SizeEstimate


class ComplexityService:
    """Evaluates project complexity across five dimensions."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async session."""
        self._session = session
        self._router = ComplexityRouter()

    @staticmethod
    def assess(
        *,
        module_count: int,
        interface_complexity: int,
        page_count: int,
        entity_count: int,
        integration_count: int,
    ) -> dict[str, int | str | dict[str, float]]:
        """Calculate complexity scores from five numeric dimensions.

        This method is kept for backward compatibility of the public API.
        Internally it maps the legacy dimensions to the design's five
        dimensions and delegates to :class:`ComplexityRouter`.
        """
        metrics = ComplexityService._legacy_to_metrics(
            module_count=module_count,
            interface_complexity=interface_complexity,
            page_count=page_count,
            entity_count=entity_count,
            integration_count=integration_count,
        )
        assessment = ComplexityRouter().assess(metrics)
        return {
            "optimistic_score": 0,
            "expected_score": 0,
            "conservative_score": 0,
            "complexity_level": assessment.route.value.capitalize(),
            "route": assessment.route.value,
            "confidence": assessment.confidence,
            "reasoning": assessment.reasoning,
            "radar_values": {
                "code_lines": float(metrics.code_lines),
                "external_deps": float(metrics.external_deps),
                "data_models": float(metrics.data_models),
                "api_endpoints": float(metrics.api_endpoints),
                "business_rules": float(metrics.business_rules),
            },
        }

    @staticmethod
    def assess_metrics(metrics: ComplexityMetrics) -> ComplexityRoute:
        """Assess raw five-dimension metrics and return the recommended route."""
        return ComplexityRouter().assess(metrics).route

    @staticmethod
    def calculate_scores(
        *,
        module_count: int,
        interface_count: int,
        page_count: int,
        tech_complexity: str,
        risk_level: str,
    ) -> dict[str, int | str]:
        """Calculate three-tier complexity scores for a size estimate.

        Kept for backward compatibility; internally delegates to
        :class:`ComplexityRouter`.
        """
        metrics = ComplexityService._legacy_to_metrics(
            module_count=module_count,
            interface_complexity=max(1, interface_count // 2),
            page_count=page_count,
            entity_count=page_count,
            integration_count=interface_count,
        )
        assessment = ComplexityRouter().assess(metrics)
        return {
            "optimistic_score": 0,
            "expected_score": 0,
            "conservative_score": 0,
            "complexity_level": assessment.route.value.capitalize(),
        }

    async def create_size_estimate(
        self,
        *,
        project_id: str,
        module_count: int,
        interface_count: int,
        page_count: int,
        tech_complexity: str,
        risk_level: str,
    ) -> SizeEstimate:
        """Create a size estimate for a project with computed scores."""
        proj = await self._session.get(Project, project_id)
        if proj is None:
            raise NotFoundError(detail=f"Project '{project_id}' not found")

        metrics = self._legacy_to_metrics(
            module_count=module_count,
            interface_complexity=max(1, interface_count // 2),
            page_count=page_count,
            entity_count=page_count,
            integration_count=interface_count,
        )
        assessment = self._router.assess(metrics)

        estimate = SizeEstimate(
            estimate_id=str(uuid.uuid4()),
            project_id=project_id,
            module_count=module_count,
            interface_count=interface_count,
            page_count=page_count,
            tech_complexity=tech_complexity,
            risk_level=risk_level,
            optimistic_score=0,
            expected_score=0,
            conservative_score=0,
            complexity_level=assessment.route.value.capitalize(),
            created_at=datetime.now(UTC),
        )
        self._session.add(estimate)
        await self._session.commit()
        await self._session.refresh(estimate)
        return estimate

    async def list_size_estimates(
        self, project_id: str
    ) -> list[SizeEstimate]:
        """List all size estimates for a project (newest first)."""
        from sqlalchemy import select

        stmt = (
            select(SizeEstimate)
            .where(SizeEstimate.project_id == project_id)
            .order_by(SizeEstimate.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def get_template_recommendation(level: str) -> dict[str, str | int]:
        """Return template recommendation for a complexity level."""
        recommendations: dict[str, dict[str, str | int]] = {
            "Trivial": {
                "level": "Trivial",
                "label": "轻量",
                "recommended_template": "trivial",
                "description": "小型脚本或工具，1-2 个模块，低风险",
                "stage_count": 4,
                "estimated_skill_count": 3,
            },
            "Light": {
                "level": "Light",
                "label": "轻量",
                "recommended_template": "light",
                "description": "小型功能模块，3-5 个模块，中等风险可控",
                "stage_count": 6,
                "estimated_skill_count": 6,
            },
            "Standard": {
                "level": "Standard",
                "label": "标准",
                "recommended_template": "standard",
                "description": "中等规模项目，6-15 个模块，需要完整 SDLC",
                "stage_count": 8,
                "estimated_skill_count": 10,
            },
            "Deep": {
                "level": "Deep",
                "label": "深度",
                "recommended_template": "deep",
                "description": "大型复杂项目，15+ 模块，高风险，需严格治理",
                "stage_count": 12,
                "estimated_skill_count": 18,
            },
        }

        if level not in recommendations:
            raise ValidationError(
                detail=f"Invalid complexity level '{level}'. "
                "Must be one of: Trivial, Light, Standard, Deep."
            )

        return recommendations[level]

    @staticmethod
    def _legacy_to_metrics(
        *,
        module_count: int,
        interface_complexity: int,
        page_count: int,
        entity_count: int,
        integration_count: int,
    ) -> ComplexityMetrics:
        """Map legacy API dimensions to the design's five dimensions."""
        return ComplexityMetrics(
            code_lines=max(1, module_count * 100),
            external_deps=max(0, integration_count),
            data_models=max(0, entity_count),
            api_endpoints=max(0, interface_complexity * 2),
            business_rules=max(0, module_count * 3),
        )
