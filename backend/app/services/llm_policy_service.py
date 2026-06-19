"""LLM policy CRUD service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.llm_policy import LlmPolicy
from app.models.llm_policy_rule import LlmPolicyRule
from app.models.policy_template import PolicyTemplate
from app.schemas.llm_policy import LlmPolicyCreate, LlmPolicyUpdate
from app.schemas.llm_policy_rule import LlmPolicyRuleCreate


class LlmPolicyService:
    """CRUD and template management for LLM policies."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with async session."""
        self._session = session

    async def list_policies(
        self,
        *,
        scope: str | None = None,
        scope_target: str | None = None,
        keyword: str | None = None,
        is_enabled: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[LlmPolicy], int]:
        """List LLM policies with filters and total count."""
        filters = []
        if scope:
            filters.append(LlmPolicy.scope == scope)
        if scope_target:
            filters.append(LlmPolicy.scope_target == scope_target)
        if keyword:
            filters.append(
                or_(
                    LlmPolicy.name.ilike(f"%{keyword}%"),
                    LlmPolicy.key.ilike(f"%{keyword}%"),
                )
            )
        if is_enabled is not None:
            filters.append(LlmPolicy.is_enabled == is_enabled)

        total_stmt = select(func.count(LlmPolicy.id))
        list_stmt = select(LlmPolicy)
        if filters:
            clause = and_(*filters)
            total_stmt = total_stmt.where(clause)
            list_stmt = list_stmt.where(clause)

        total = (await self._session.execute(total_stmt)).scalar_one()

        result = await self._session.execute(
            list_stmt.options(selectinload(LlmPolicy.rules))
            .order_by(
                desc(LlmPolicy.priority),
                desc(LlmPolicy.updated_at),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_policy(self, policy_id: str) -> LlmPolicy:
        """Get an LLM policy by ID with rules loaded."""
        result = await self._session.execute(
            select(LlmPolicy)
            .options(selectinload(LlmPolicy.rules))
            .where(LlmPolicy.id == policy_id)
        )
        policy = result.scalar_one_or_none()
        if policy is None:
            raise NotFoundError(f"LLM policy not found: {policy_id}")
        return policy

    async def get_policy_by_key(
        self,
        scope: str,
        scope_target: str | None,
        key: str,
    ) -> LlmPolicy | None:
        """Get an LLM policy by unique composite key with rules loaded."""
        result = await self._session.execute(
            select(LlmPolicy)
            .options(selectinload(LlmPolicy.rules))
            .where(
                and_(
                    LlmPolicy.scope == scope,
                    LlmPolicy.scope_target == scope_target,
                    LlmPolicy.key == key,
                )
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_policy(self, dto: LlmPolicyCreate, *, user_id: str | None = None) -> LlmPolicy:
        """Create a new LLM policy with rules."""
        existing = await self.get_policy_by_key(dto.scope, dto.scope_target, dto.key)
        if existing:
            raise ValueError(
                f"LLM policy already exists: {dto.scope}/{dto.scope_target or '-'}/{dto.key}"
            )

        now = datetime.now(UTC)
        policy = LlmPolicy(
            name=dto.name,
            key=dto.key,
            scope=dto.scope,
            scope_target=dto.scope_target,
            priority=dto.priority,
            default_mode=dto.default_mode,
            description=dto.description,
            template_id=dto.template_id,
            is_customized=dto.is_customized,
            is_enabled=dto.is_enabled,
            created_at=now,
            updated_at=now,
        )
        self._session.add(policy)
        await self._session.flush()

        for idx, rule_data in enumerate(dto.rules):
            await self._add_rule_from_dict(policy.id, rule_data, idx)

        await self._session.flush()
        await self._session.refresh(policy)
        await self._session.refresh(policy, attribute_names=["rules"])
        return policy

    async def update_policy(
        self,
        policy_id: str,
        dto: LlmPolicyUpdate,
        *,
        user_id: str | None = None,
    ) -> LlmPolicy:
        """Update an LLM policy."""
        policy = await self.get_policy(policy_id)
        update_data = dto.model_dump(exclude_unset=True)
        rules_data = update_data.pop("rules", None)

        for field, value in update_data.items():
            setattr(policy, field, value)
        policy.updated_at = datetime.now(UTC)
        self._session.add(policy)

        if rules_data is not None:
            # Delete existing rules and recreate.
            existing = await self._session.execute(
                select(LlmPolicyRule).where(LlmPolicyRule.policy_id == policy.id)
            )
            for rule in existing.scalars().all():
                await self._session.delete(rule)
            for idx, rule_data in enumerate(rules_data):
                await self._add_rule_from_dict(policy.id, rule_data, idx)

            # Detect customization if based on a template.
            if policy.template_id:
                template = await self._get_template(policy.template_id)
                policy.is_customized = self.is_customized_from_template(policy, template)

        await self._session.flush()
        await self._session.refresh(policy)
        await self._session.refresh(policy, attribute_names=["rules"])
        return policy

    async def delete_policy(self, policy_id: str) -> None:
        """Delete an LLM policy."""
        policy = await self.get_policy(policy_id)
        await self._session.delete(policy)
        await self._session.flush()

    async def apply_template(self, policy_id: str, template_id: str) -> LlmPolicy:
        """Replace policy rules with template rules."""
        policy = await self.get_policy(policy_id)
        template = await self._get_template(template_id)

        # Remove existing rules.
        existing = await self._session.execute(
            select(LlmPolicyRule).where(LlmPolicyRule.policy_id == policy.id)
        )
        for rule in existing.scalars().all():
            await self._session.delete(rule)

        # Add template rules.
        for idx, rule_data in enumerate(template.rules_json):
            await self._add_rule_from_dict(policy.id, rule_data, idx)

        policy.template_id = template.id
        policy.default_mode = template.default_mode
        policy.is_customized = False
        policy.updated_at = datetime.now(UTC)
        self._session.add(policy)
        await self._session.flush()
        await self._session.refresh(policy)
        await self._session.refresh(policy, attribute_names=["rules"])
        return policy

    async def reset_to_template(self, policy_id: str) -> LlmPolicy:
        """Reset a policy to its current template."""
        policy = await self.get_policy(policy_id)
        if not policy.template_id:
            raise ValueError("策略未关联模板")
        return await self.apply_template(policy.id, policy.template_id)

    async def append_rule(
        self,
        policy_id: str,
        dto: LlmPolicyRuleCreate,
        *,
        user_id: str | None = None,
    ) -> LlmPolicyRule:
        """Append a single rule to a policy."""
        policy = await self.get_policy(policy_id)

        # Compute next sort_order in category.
        result = await self._session.execute(
            select(func.max(LlmPolicyRule.sort_order)).where(
                and_(
                    LlmPolicyRule.policy_id == policy.id,
                    LlmPolicyRule.category == dto.category,
                )
            )
        )
        max_order = result.scalar_one_or_none() or 0

        rule = LlmPolicyRule(
            policy_id=policy.id,
            category=dto.category,
            action_type=dto.action_type,
            permission=dto.permission,
            pattern=dto.pattern,
            description=dto.description,
            sort_order=max_order + 1,
            extra_json=dto.extra_json,
        )
        self._session.add(rule)

        # Mark as customized if based on template.
        if policy.template_id:
            template = await self._get_template(policy.template_id)
            self._session.add(rule)
            await self._session.flush()
            await self._session.refresh(policy, attribute_names=["rules"])
            policy.is_customized = self.is_customized_from_template(policy, template)
            self._session.add(policy)

        await self._session.flush()
        await self._session.refresh(rule)
        return rule

    async def update_rule_order(self, policy_id: str, rule_ids: list[str]) -> list[LlmPolicyRule]:
        """Update sort order of rules within a policy."""
        policy = await self.get_policy(policy_id)
        rules_result = await self._session.execute(
            select(LlmPolicyRule).where(LlmPolicyRule.policy_id == policy.id)
        )
        rule_map = {r.id: r for r in rules_result.scalars().all()}

        updated: list[LlmPolicyRule] = []
        for idx, rule_id in enumerate(rule_ids):
            rule = rule_map.get(rule_id)
            if rule is None:
                continue
            rule.sort_order = idx
            self._session.add(rule)
            updated.append(rule)

        await self._session.flush()
        return updated

    async def list_templates(self) -> list[PolicyTemplate]:
        """List all policy templates."""
        result = await self._session.execute(
            select(PolicyTemplate).order_by(asc(PolicyTemplate.id))
        )
        return list(result.scalars().all())

    async def get_template(self, template_id: str) -> PolicyTemplate:
        """Get a policy template by ID."""
        return await self._get_template(template_id)

    async def _get_template(self, template_id: str) -> PolicyTemplate:
        """Internal helper to fetch a template by ID."""
        result = await self._session.execute(
            select(PolicyTemplate).where(PolicyTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        if template is None:
            raise NotFoundError(f"Policy template not found: {template_id}")
        return template

    async def _add_rule_from_dict(
        self, policy_id: str, data: dict[str, Any], sort_order: int
    ) -> LlmPolicyRule:
        """Create a rule from a dict payload."""
        rule = LlmPolicyRule(
            policy_id=policy_id,
            category=data.get("category", "file_system"),
            action_type=data.get("action_type", "file_read"),
            permission=data.get("permission", "ask"),
            pattern=data.get("pattern", "*"),
            description=data.get("description"),
            sort_order=data.get("sort_order", sort_order),
            extra_json=data.get("extra_json"),
        )
        self._session.add(rule)
        return rule

    @staticmethod
    def is_customized_from_template(policy: LlmPolicy, template: PolicyTemplate) -> bool:
        """Return True if policy rules differ from the template."""
        if policy.default_mode != template.default_mode:
            return True

        existing = sorted(
            [
                {
                    "category": r.category,
                    "action_type": r.action_type,
                    "permission": r.permission,
                    "pattern": r.pattern,
                }
                for r in policy.rules
            ],
            key=lambda x: (x["category"], x["action_type"], x["pattern"]),
        )
        expected = sorted(
            [
                {
                    "category": r.get("category"),
                    "action_type": r.get("action_type"),
                    "permission": r.get("permission"),
                    "pattern": r.get("pattern"),
                }
                for r in template.rules_json
            ],
            key=lambda x: (x["category"], x["action_type"], x["pattern"]),
        )
        return existing != expected

    async def resolve_policy(
        self,
        *,
        policy_key: str | None = None,
        policy_id: str | None = None,
        scope: str | None = None,
        scope_target: str | None = None,
        project_id: str | None = None,
        user_id: str | None = None,
    ) -> LlmPolicy | None:
        """Resolve an effective policy across scopes.

        Precedence: managed > user > project > global.
        """
        if policy_id:
            return await self.get_policy(policy_id)

        scopes: list[tuple[str, str | None]] = [("global", None)]
        if project_id:
            scopes.append(("project", project_id))
        if user_id:
            scopes.append(("user", user_id))
        scopes.append(("managed", None))

        for s, target in reversed(scopes):
            key = policy_key or "default"
            policy = await self.get_policy_by_key(s, target, key)
            if policy and policy.is_enabled:
                return policy

        # Fallback to any enabled policy in scope.
        for s, target in reversed(scopes):
            result = await self._session.execute(
                select(LlmPolicy)
                .options(selectinload(LlmPolicy.rules))
                .where(
                    and_(
                        LlmPolicy.scope == s,
                        LlmPolicy.scope_target == target,
                        LlmPolicy.is_enabled == True,  # noqa: E712
                    )
                )
                .order_by(desc(LlmPolicy.priority))
                .limit(1)
            )
            policy = result.scalar_one_or_none()
            if policy:
                return policy

        return None
