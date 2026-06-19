"""Unit tests for LlmRuleEngine."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.llm_policy import LlmPolicyCreate
from app.services.llm_policy_service import LlmPolicyService
from app.services.llm_rule_engine import LlmRuleEngine


def _policy_dto(**kwargs: Any) -> LlmPolicyCreate:
    """Build a policy DTO with sensible defaults."""
    defaults: dict[str, Any] = {"scope": "global", "default_mode": "ask", "rules": []}
    defaults.update(kwargs)
    return LlmPolicyCreate(**defaults)

class TestLlmRuleEngine:
    """LlmRuleEngine permission evaluation tests."""

    async def test_default_mode_ask(self, seed_templates: AsyncSession) -> None:
        """TEST-1820: no rules defaults to ask."""
        svc = LlmPolicyService(seed_templates)
        policy = await svc.create_policy(
            _policy_dto(
                name="Default",
                key="default",
                scope="global",
                default_mode="ask",
                rules=[],
            )
        )
        engine = LlmRuleEngine(svc)
        result = await engine.check_by_policy_id(
            policy.id, "file_write", "backend/app/main.py"
        )
        assert result["permission"] == "ask"
        assert result["allowed"] is False

    async def test_allow_rule_overrides_default(
        self, seed_templates: AsyncSession
    ) -> None:
        """TEST-1821: allow rule permits project file write."""
        svc = LlmPolicyService(seed_templates)
        policy = await svc.create_policy(
            _policy_dto(
                name="Allow",
                key="allow",
                scope="global",
                default_mode="ask",
                rules=[
                    {
                        "category": "file_system",
                        "action_type": "file_write",
                        "permission": "allow",
                        "pattern": "backend/app/main.py",
                    }
                ],
            )
        )
        engine = LlmRuleEngine(svc)
        result = await engine.check_by_policy_id(
            policy.id, "file_write", "backend/app/main.py"
        )
        assert result["permission"] == "allow"
        assert result["allowed"] is True

    async def test_deny_rule_wins_over_allow(
        self, seed_templates: AsyncSession
    ) -> None:
        """TEST-1822: deny rule beats allow rule for sensitive files."""
        svc = LlmPolicyService(seed_templates)
        policy = await svc.create_policy(
            _policy_dto(
                name="AllowAll",
                key="allow-all",
                scope="global",
                default_mode="allow",
                rules=[
                    {
                        "category": "file_system",
                        "action_type": "file_write",
                        "permission": "allow",
                        "pattern": "**",
                    }
                ],
            )
        )
        engine = LlmRuleEngine(svc)
        result = await engine.check_by_policy_id(
            policy.id, "file_write", "backend/.env"
        )
        assert result["permission"] == "deny"
        assert result["allowed"] is False

    async def test_longest_match_wins(self, seed_templates: AsyncSession) -> None:
        """TEST-1823: longest matching pattern wins."""
        svc = LlmPolicyService(seed_templates)
        policy = await svc.create_policy(
            _policy_dto(
                name="Longest",
                key="longest",
                scope="global",
                default_mode="ask",
                rules=[
                    {
                        "category": "file_system",
                        "action_type": "file_write",
                        "permission": "allow",
                        "pattern": "${PROJECT_ROOT}/**",
                    },
                    {
                        "category": "file_system",
                        "action_type": "file_write",
                        "permission": "deny",
                        "pattern": "${PROJECT_ROOT}/ops/**",
                    },
                ],
            )
        )
        engine = LlmRuleEngine(svc)
        result = await engine.check_by_policy_id(
            policy.id, "file_write", "ops/staging-config.yaml"
        )
        assert result["permission"] == "deny"

    async def test_category_priority(self, seed_templates: AsyncSession) -> None:
        """TEST-1824: high_risk category wins over file_system."""
        svc = LlmPolicyService(seed_templates)
        policy = await svc.create_policy(
            _policy_dto(
                name="Category",
                key="category",
                scope="global",
                default_mode="ask",
                rules=[
                    {
                        "category": "file_system",
                        "action_type": "terminal",
                        "permission": "allow",
                        "pattern": "npm run deploy",
                    },
                    {
                        "category": "high_risk",
                        "action_type": "terminal",
                        "permission": "deny",
                        "pattern": "npm run deploy",
                    },
                ],
            )
        )
        engine = LlmRuleEngine(svc)
        result = await engine.check_by_policy_id(
            policy.id, "terminal", "npm run deploy"
        )
        assert result["permission"] == "deny"

    async def test_terminal_safe_command_allowed(
        self, seed_templates: AsyncSession
    ) -> None:
        """TEST-1825: safe terminal command from seeded template is allowed."""
        svc = LlmPolicyService(seed_templates)
        policy = await svc.create_policy(
            _policy_dto(
                name="Default",
                key="default",
                scope="global",
                default_mode="ask",
                template_id="personal",
                rules=[],
            )
        )
        await svc.apply_template(policy.id, "personal")
        engine = LlmRuleEngine(svc)
        result = await engine.check_by_policy_id(
            policy.id, "terminal", "pytest tests/"
        )
        assert result["permission"] == "allow"

    async def test_terminal_dangerous_command_denied(
        self, seed_templates: AsyncSession
    ) -> None:
        """TEST-1826: dangerous terminal command is denied by builtin policy."""
        svc = LlmPolicyService(seed_templates)
        policy = await svc.create_policy(
            _policy_dto(
                name="Default",
                key="default",
                scope="global",
                default_mode="ask",
                rules=[],
            )
        )
        engine = LlmRuleEngine(svc)
        result = await engine.check_by_policy_id(
            policy.id, "terminal", "rm -rf /"
        )
        assert result["permission"] == "deny"
