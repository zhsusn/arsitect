"""LLM permission evaluation service."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from typing import Any

from app.models.config_node import ConfigNodeScope
from app.services.config_service import ConfigService


@dataclass
class PermissionCheckContext:
    """Context for a permission check."""

    category: str
    path: str | None = None
    command: str | None = None
    domain: str | None = None
    project_id: str | None = None
    user_id: str | None = None


@dataclass
class PermissionRuleMatch:
    """A matched permission rule with its source."""

    node_id: str
    node_name: str
    scope: str
    scope_target: str | None
    decision: str
    pattern: str | None
    priority: int
    updated_at: Any


class LLMPermissionService:
    """Evaluate allow/ask/deny rules for LLM tool permissions."""

    _SENSITIVE_PATTERNS: list[dict[str, Any]] = [
        {"category": "file_read", "decision": "deny", "path": "**/.env"},
        {"category": "file_read", "decision": "deny", "path": "**/.ssh/**"},
        {"category": "file_read", "decision": "deny", "path": "**/id_rsa*"},
        {"category": "file_write", "decision": "deny", "path": "**/.env"},
        {"category": "file_write", "decision": "deny", "path": "**/.ssh/**"},
        {"category": "file_write", "decision": "deny", "path": "**/ops/staging-config.yaml"},
        {"category": "terminal", "decision": "deny", "command": "rm -rf*"},
        {"category": "terminal", "decision": "deny", "command": "sudo*"},
        {"category": "terminal", "decision": "deny", "command": "eval*"},
        {"category": "terminal", "decision": "deny", "command": "curl*|wget*"},
    ]

    _SAFE_TERMINAL_PATTERNS: list[str] = [
        "pytest*",
        "npm run *",
        "npm test",
        "npm run build",
        "npm run lint",
        "ruff check*",
        "ruff format*",
        "python -m pytest*",
        "git status*",
        "git diff*",
        "git log*",
    ]

    _SCOPE_RANK: dict[str, int] = {
        ConfigNodeScope.MANAGED.value: 3,
        ConfigNodeScope.USER.value: 2,
        ConfigNodeScope.PROJECT.value: 1,
        ConfigNodeScope.GLOBAL.value: 0,
    }

    def __init__(self, config_service: ConfigService) -> None:
        """Initialize with config service."""
        self._config_service = config_service

    async def check(self, ctx: PermissionCheckContext) -> dict[str, Any]:
        """Evaluate permission decision for a tool request."""
        resolved = await self._config_service.resolve(
            "llm_permission",
            project_id=ctx.project_id,
            user_id=ctx.user_id,
        )
        config = resolved.get("config", {})
        default_mode = config.get("default_mode", "ask")
        rules = config.get("rules", [])

        matches = self._collect_matches(ctx, rules, resolved.get("source_nodes", []))
        # Add built-in sensitive patterns unless explicitly overridden by managed scope.
        if not self._has_managed_override(ctx, resolved.get("source_nodes", [])):
            matches.extend(self._builtin_matches(ctx))

        # Sort: deny first, then allow, then ask; higher scope rank first.
        matches.sort(
            key=lambda m: (
                0 if m.decision == "deny" else 1 if m.decision == "allow" else 2,
                -m.priority,
                -self._SCOPE_RANK.get(m.scope, 0),
            )
        )

        decision = default_mode
        applied_rules: list[dict[str, Any]] = []
        if matches:
            top = matches[0]
            decision = top.decision
            applied_rules = [
                {
                    "node_id": m.node_id,
                    "node_name": m.node_name,
                    "scope": m.scope,
                    "scope_target": m.scope_target,
                    "decision": m.decision,
                    "matched_pattern": m.pattern,
                }
                for m in matches[:3]
            ]

        return {
            "category": ctx.category,
            "decision": decision,
            "default_mode": default_mode,
            "rules": applied_rules,
        }

    def _collect_matches(
        self,
        ctx: PermissionCheckContext,
        rules: list[dict[str, Any]],
        source_nodes: list[Any],
    ) -> list[PermissionRuleMatch]:
        """Collect user-defined rule matches."""
        matches: list[PermissionRuleMatch] = []
        node_map = {node.id: node for node in source_nodes}

        for rule in rules:
            if rule.get("category") != ctx.category:
                continue
            decision = str(rule.get("decision") or "")
            if decision not in {"allow", "ask", "deny"}:
                continue
            pattern = self._extract_pattern(ctx, rule)
            if not pattern:
                continue
            if self._matches(ctx, rule, pattern):
                node_id = rule.get("node_id", "")
                node = node_map.get(node_id)
                matches.append(
                    PermissionRuleMatch(
                        node_id=node_id,
                        node_name=node.name if node else "",
                        scope=node.scope if node else ConfigNodeScope.GLOBAL.value,
                        scope_target=node.scope_target if node else None,
                        decision=decision,
                        pattern=pattern,
                        priority=node.priority if node else 0,
                        updated_at=node.updated_at if node else None,
                    )
                )
        return matches

    def _builtin_matches(self, ctx: PermissionCheckContext) -> list[PermissionRuleMatch]:
        """Collect built-in sensitive pattern matches."""
        matches: list[PermissionRuleMatch] = []
        for rule in self._SENSITIVE_PATTERNS:
            if rule.get("category") != ctx.category:
                continue
            pattern = self._extract_pattern(ctx, rule)
            if not pattern:
                continue
            if self._matches(ctx, rule, pattern):
                matches.append(
                    PermissionRuleMatch(
                        node_id="builtin",
                        node_name="系统默认安全策略",
                        scope=ConfigNodeScope.MANAGED.value,
                        scope_target=None,
                        decision=rule.get("decision", "deny"),
                        pattern=pattern,
                        priority=999,
                        updated_at=None,
                    )
                )
        return matches

    def _has_managed_override(
        self, ctx: PermissionCheckContext, source_nodes: list[Any]
    ) -> bool:
        """Check if a managed node explicitly overrides builtin for this context."""
        for node in source_nodes:
            if node.scope != ConfigNodeScope.MANAGED.value or not node.is_enabled:
                continue
            for rule in node.config_json.get("rules", []):
                if rule.get("category") != ctx.category:
                    continue
                if self._matches(ctx, rule, self._extract_pattern(ctx, rule) or ""):
                    return True
        return False

    def _extract_pattern(
        self, ctx: PermissionCheckContext, rule: dict[str, Any]
    ) -> str | None:
        """Extract pattern field from rule based on category."""
        if ctx.category in {"file_read", "file_write"}:
            return rule.get("path")
        if ctx.category == "terminal":
            return rule.get("command")
        if ctx.category in {"web_fetch", "external_api"}:
            return rule.get("domain")
        return None

    def _matches(
        self, ctx: PermissionCheckContext, rule: dict[str, Any], pattern: str
    ) -> bool:
        """Check if context matches a rule pattern."""
        value = None
        if ctx.category in {"file_read", "file_write"}:
            value = ctx.path or ""
        elif ctx.category == "terminal":
            value = ctx.command or ""
        elif ctx.category in {"web_fetch", "external_api"}:
            value = ctx.domain or ""

        if value is None:
            return False

        # Expand placeholders.
        expanded = pattern.replace("${PROJECT_ROOT}/", "")
        # Normalize separators.
        expanded = expanded.replace("\\", "/")
        normalized_value = value.replace("\\", "/")
        return fnmatch.fnmatch(normalized_value, expanded)

    def get_default_policy(self) -> dict[str, Any]:
        """Return a safe default permission policy."""
        return {
            "default_mode": "ask",
            "rules": [
                {
                    "category": "file_read",
                    "decision": "allow",
                    "path": "${PROJECT_ROOT}/**",
                    "description": "允许读取项目内文件",
                },
                {
                    "category": "file_write",
                    "decision": "ask",
                    "path": "${PROJECT_ROOT}/**",
                    "description": "写入项目文件需确认",
                },
                {
                    "category": "file_write",
                    "decision": "allow",
                    "path": "${PROJECT_ROOT}/openspec/changes/**",
                    "description": "允许写入 OpenSpec 变更产物",
                },
                *[
                    {
                        "category": "terminal",
                        "decision": "allow",
                        "command": cmd,
                        "description": f"允许安全命令: {cmd}",
                    }
                    for cmd in self._SAFE_TERMINAL_PATTERNS
                ],
                {
                    "category": "web_fetch",
                    "decision": "ask",
                    "domain": "*",
                    "description": "抓取外部网页需确认",
                },
                {
                    "category": "external_api",
                    "decision": "ask",
                    "domain": "*",
                    "description": "调用外部 API 需确认",
                },
            ],
        }
