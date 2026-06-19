"""LLM permission rule engine with longest-match-first evaluation."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm_policy import LlmPolicy
from app.services.llm_policy_service import LlmPolicyService

# Category priority: lower number wins.
_CATEGORY_PRIORITY: dict[str, int] = {
    "high_risk": 0,
    "file_system": 1,
    "terminal": 2,
    "network": 3,
}

# Built-in sensitive deny patterns applied unless managed policy overrides.
_BUILTIN_DENY_PATTERNS: list[dict[str, Any]] = [
    {
        "category": "file_system",
        "action_type": "file_read",
        "permission": "deny",
        "pattern": "**/.env",
    },
    {
        "category": "file_system",
        "action_type": "file_read",
        "permission": "deny",
        "pattern": "**/.ssh/**",
    },
    {
        "category": "file_system",
        "action_type": "file_read",
        "permission": "deny",
        "pattern": "**/id_rsa*",
    },
    {
        "category": "file_system",
        "action_type": "file_write",
        "permission": "deny",
        "pattern": "**/.env",
    },
    {
        "category": "file_system",
        "action_type": "file_write",
        "permission": "deny",
        "pattern": "**/.ssh/**",
    },
    {
        "category": "file_system",
        "action_type": "file_write",
        "permission": "deny",
        "pattern": "**/ops/staging-config.yaml",
    },
    {"category": "terminal", "action_type": "terminal", "permission": "deny", "pattern": "rm -rf*"},
    {"category": "terminal", "action_type": "terminal", "permission": "deny", "pattern": "sudo*"},
    {"category": "terminal", "action_type": "terminal", "permission": "deny", "pattern": "eval*"},
    {
        "category": "terminal",
        "action_type": "terminal",
        "permission": "deny",
        "pattern": "curl*|wget*",
    },
]


@dataclass
class RuleMatch:
    """A matched rule with metadata."""

    rule_id: str
    policy_id: str
    category: str
    action_type: str
    permission: str
    pattern: str
    description: str | None


class LlmRuleEngine:
    """Evaluate allow/ask/deny rules for LLM tool permissions."""

    def __init__(self, policy_service: LlmPolicyService) -> None:
        """Initialize with policy service."""
        self._policy_service = policy_service

    async def check(
        self,
        session: AsyncSession,
        policy_key: str | None,
        scope: str | None,
        scope_target: str | None,
        action_type: str,
        target: str,
        *,
        project_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Evaluate permission for an action."""
        policy = await self._policy_service.resolve_policy(
            policy_key=policy_key,
            scope=scope,
            scope_target=scope_target,
            project_id=project_id,
            user_id=user_id,
        )

        if policy is None:
            return self._fallback_result(action_type, target)

        return self._check_policy(policy, action_type, target)

    async def check_by_policy_id(
        self,
        policy_id: str,
        action_type: str,
        target: str,
    ) -> dict[str, Any]:
        """Evaluate permission using a specific policy ID."""
        policy = await self._policy_service.get_policy(policy_id)
        return self._check_policy(policy, action_type, target)

    def _check_policy(self, policy: LlmPolicy, action_type: str, target: str) -> dict[str, Any]:
        """Run rule engine against a loaded policy."""
        candidates: list[RuleMatch] = []
        for rule in policy.rules:
            if rule.action_type != action_type:
                continue
            expanded = self._expand_pattern(rule.pattern)
            if self._matches(target, expanded):
                candidates.append(
                    RuleMatch(
                        rule_id=rule.id,
                        policy_id=policy.id,
                        category=rule.category,
                        action_type=rule.action_type,
                        permission=rule.permission,
                        pattern=rule.pattern,
                        description=rule.description,
                    )
                )

        # Apply built-in sensitive patterns unless managed policy exists.
        if policy.scope != "managed":
            for builtin in _BUILTIN_DENY_PATTERNS:
                if builtin["action_type"] != action_type:
                    continue
                expanded = self._expand_pattern(builtin["pattern"])
                if self._matches(target, expanded):
                    candidates.append(
                        RuleMatch(
                            rule_id="builtin",
                            policy_id=policy.id,
                            category=builtin["category"],
                            action_type=builtin["action_type"],
                            permission=builtin["permission"],
                            pattern=builtin["pattern"],
                            description="系统默认安全策略",
                        )
                    )

        if not candidates:
            return {
                "allowed": policy.default_mode == "allow",
                "permission": policy.default_mode,
                "matched_rule": None,
                "message": f"未命中任何规则，使用默认模式：{policy.default_mode}",
                "suggest_whitelist": policy.default_mode != "allow",
            }

        # Sort by category priority, then pattern length (longest first).
        candidates.sort(
            key=lambda m: (
                _CATEGORY_PRIORITY.get(m.category, 99),
                -len(m.pattern),
            )
        )

        top = candidates[0]
        allowed = top.permission == "allow"
        message = f"命中规则：{top.description or top.pattern} -> {top.permission}"
        return {
            "allowed": allowed,
            "permission": top.permission,
            "matched_rule": {
                "rule_id": top.rule_id,
                "policy_id": top.policy_id,
                "category": top.category,
                "action_type": top.action_type,
                "permission": top.permission,
                "pattern": top.pattern,
                "description": top.description,
            },
            "message": message,
            "suggest_whitelist": top.permission == "ask" or top.permission == "deny",
        }

    def _expand_pattern(self, pattern: str) -> str:
        """Expand placeholders and normalize separators."""
        expanded = pattern.replace("${PROJECT_ROOT}/", "")
        expanded = expanded.replace("\\", "/")
        return expanded

    def _matches(self, target: str, pattern: str) -> bool:
        """Match target against glob pattern with ** support."""
        normalized = target.replace("\\", "/")
        # Python fnmatch does not support **; treat it as *.
        glob_pattern = pattern.replace("**", "*")
        return fnmatch.fnmatch(normalized, glob_pattern)

    def _fallback_result(self, action_type: str, target: str) -> dict[str, Any]:
        """Return safe fallback when no policy is found."""
        # Check built-in sensitive patterns even without policy.
        for builtin in _BUILTIN_DENY_PATTERNS:
            if builtin["action_type"] != action_type:
                continue
            expanded = self._expand_pattern(builtin["pattern"])
            if self._matches(target, expanded):
                return {
                    "allowed": False,
                    "permission": "deny",
                    "matched_rule": {
                        "rule_id": "builtin",
                        "category": builtin["category"],
                        "action_type": builtin["action_type"],
                        "permission": "deny",
                        "pattern": builtin["pattern"],
                        "description": "系统默认安全策略",
                    },
                    "message": "命中系统默认安全策略：拒绝",
                    "suggest_whitelist": False,
                }

        return {
            "allowed": False,
            "permission": "ask",
            "matched_rule": None,
            "message": "未找到生效策略，默认询问",
            "suggest_whitelist": True,
        }
