"""Unit tests for LlmPolicyService."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.llm_policy import LlmPolicyCreate, LlmPolicyUpdate
from app.schemas.llm_policy_rule import LlmPolicyRuleCreate
from app.services.llm_policy_service import LlmPolicyService


def _policy_dto(**kwargs: Any) -> LlmPolicyCreate:
    """Build a policy DTO with sensible defaults."""
    defaults: dict[str, Any] = {
        "scope": "global",
        "default_mode": "ask",
        "rules": [],
    }
    defaults.update(kwargs)
    return LlmPolicyCreate(**defaults)


def _policy_update_dto(**kwargs: Any) -> LlmPolicyUpdate:
    """Build a policy update DTO."""
    return LlmPolicyUpdate(**kwargs)


def _rule_dto(**kwargs: Any) -> LlmPolicyRuleCreate:
    """Build a rule DTO with sensible defaults."""
    defaults: dict[str, Any] = {}
    defaults.update(kwargs)
    return LlmPolicyRuleCreate(**defaults)


class TestLlmPolicyService:
    """LlmPolicyService CRUD and template tests."""

    async def test_create_policy_with_rules(self, seed_templates: AsyncSession) -> None:
        """TEST-1810: create a policy with rules."""
        svc = LlmPolicyService(seed_templates)
        policy = await svc.create_policy(
            _policy_dto(
                name="Default",
                key="default",
                rules=[
                    {
                        "category": "file_system",
                        "action_type": "file_read",
                        "permission": "allow",
                        "pattern": "${PROJECT_ROOT}/**",
                    }
                ],
            )
        )
        assert policy.id
        assert len(policy.rules) == 1
        assert policy.rules[0].pattern == "${PROJECT_ROOT}/**"

    async def test_apply_template(self, seed_templates: AsyncSession) -> None:
        """TEST-1811: applying a template replaces rules."""
        svc = LlmPolicyService(seed_templates)
        templates = await svc.list_templates()
        assert len(templates) == 3

        policy = await svc.create_policy(
            _policy_dto(name="Default", key="default", rules=[])
        )
        updated = await svc.apply_template(policy.id, "personal")
        assert updated.template_id == "personal"
        assert len(updated.rules) > 0
        assert updated.is_customized is False

    async def test_append_rule_marks_customized(
        self, seed_templates: AsyncSession
    ) -> None:
        """TEST-1812: appending a rule to templated policy marks customized."""
        svc = LlmPolicyService(seed_templates)
        policy = await svc.create_policy(
            _policy_dto(
                name="Default", key="default", template_id="personal", rules=[]
            )
        )
        await svc.apply_template(policy.id, "personal")
        await svc.append_rule(
            policy.id,
            _rule_dto(
                category="file_system",
                action_type="file_write",
                permission="allow",
                pattern="custom/**",
            ),
        )
        refreshed = await svc.get_policy(policy.id)
        assert refreshed.is_customized is True

    async def test_update_policy_rules(self, seed_templates: AsyncSession) -> None:
        """TEST-1813: updating policy rules replaces all rules."""
        svc = LlmPolicyService(seed_templates)
        policy = await svc.create_policy(
            _policy_dto(
                name="Default",
                key="default",
                rules=[
                    {
                        "category": "file_system",
                        "action_type": "file_read",
                        "permission": "allow",
                        "pattern": "old/**",
                    }
                ],
            )
        )
        updated = await svc.update_policy(
            policy.id,
            _policy_update_dto(
                rules=[
                    {
                        "category": "file_system",
                        "action_type": "file_write",
                        "permission": "allow",
                        "pattern": "new/**",
                    }
                ]
            ),
        )
        assert len(updated.rules) == 1
        assert updated.rules[0].pattern == "new/**"

    async def test_is_customized_from_template(
        self, seed_templates: AsyncSession
    ) -> None:
        """TEST-1814: customization detection works."""
        svc = LlmPolicyService(seed_templates)
        templates = await svc.list_templates()
        personal = next(t for t in templates if t.id == "personal")

        policy = await svc.create_policy(
            _policy_dto(
                name="Default",
                key="default",
                default_mode=personal.default_mode,
                template_id=personal.id,
                rules=list(personal.rules_json),
            )
        )
        assert svc.is_customized_from_template(policy, personal) is False
