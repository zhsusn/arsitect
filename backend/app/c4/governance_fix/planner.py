"""Fix plan generation service."""

from __future__ import annotations

from typing import Any

from app.c4.governance_fix.models import FixPlan, GovernanceIssue
from app.c4.governance_fix.strategies import DEFAULT_STRATEGIES


class FixPlanner:
    """Selects applicable strategies and aggregates change sets for governance issues."""

    def __init__(self, strategies: Any | None = None):
        self.strategies = list(strategies) if strategies is not None else list(DEFAULT_STRATEGIES)

    async def plan(
        self,
        issues: list[GovernanceIssue],
        project_id: str,
        context: dict[str, Any],
    ) -> list[FixPlan]:
        """Generate a fix plan for each supported issue."""
        plans: list[FixPlan] = []
        for issue in issues:
            for strategy in self.strategies:
                if strategy.supports(issue):
                    changes = await strategy.plan(issue, project_id, context)
                    if changes:
                        plans.append(
                            FixPlan(
                                project_id=project_id,
                                issue_ids=[issue.issue_id],
                                changes=changes,
                            )
                        )
                        break
        return plans

    def suggest_batch_order(self, plans: list[FixPlan]) -> list[FixPlan]:
        """Sort fix plans so that low-risk / structural changes come before destructive ones."""

        def _priority(plan: FixPlan) -> int:
            risk_priority = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
            max_risk = max(
                (risk_priority.get(c.risk_level, 1) for c in plan.changes),
                default=1,
            )
            return max_risk

        return sorted(plans, key=_priority)
