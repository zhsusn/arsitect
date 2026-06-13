"""Fallback strategy: produce a guidance document for issues without a concrete auto-fix."""

from __future__ import annotations

from typing import Any

from app.c4.governance_fix.models import ChangeSet, GovernanceIssue, RiskLevel, RootCause
from app.c4.governance_fix.strategies.base import FixStrategy


class DocumentGuidanceStrategy(FixStrategy):
    """Generate a markdown guidance note when no specialized strategy is available.

    This is the strategy of last resort so that the fix-plan modal never shows an
    entirely empty plan for a selected issue.
    """

    def supports(self, issue: GovernanceIssue) -> bool:
        # Only act as a last-resort fallback when no specialized strategy matched.
        return issue.root_cause in (
            RootCause.UNKNOWN,
            RootCause.NEEDS_HUMAN_DECISION,
        )

    async def plan(
        self,
        issue: GovernanceIssue,
        project_id: str,
        context: dict[str, Any],
    ) -> list[ChangeSet]:
        safe_rule = (issue.rule_id or "UNKNOWN").replace("/", "-")
        safe_id = (issue.issue_id or "unknown").replace("/", "-")
        target_path = f"docs/governance/{safe_rule}-{safe_id}-guidance.md"
        content = (
            f"# 治理项修复指引\\n\\n"
            f"- **规则**: {issue.rule_id}\\n"
            f"- **严重级别**: {issue.severity}\\n"
            f"- **问题描述**: {issue.message}\\n"
            f"- **修复方向**: {issue.fix_hint or '请结合具体上下文人工制定修复方案'}\\n\\n"
            f"> 该问题暂无完全自动化的修复策略，请在确认后人工处理或补充对应设计文档。\\n"
        )
        return [
            ChangeSet(
                action="UPDATE_DOC",
                target_path=target_path,
                before="",
                after=content,
                rationale=f"[{issue.rule_id}] {issue.message}",
                risk_level=RiskLevel.LOW,
                auto_applicable=False,
                requires_confirmation=True,
                issue_id=issue.issue_id,
            )
        ]
