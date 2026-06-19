"""BindingService — CRUD for data-binding rules."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.binding_rule import BindingRule


class BindingService:
    """Handle binding rule lifecycle."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session.

        Args:
            session: Async SQLAlchemy session.
        """
        self._session = session

    async def create_rule(
        self,
        project_id: str,
        source_field: str,
        target_field: str,
        transform_type: str,
        transform_config: str | None,
        status: str,
    ) -> BindingRule:
        """Create a new binding rule.

        Args:
            project_id: Project identifier.
            source_field: Source data field path.
            target_field: Target UI/data field path.
            transform_type: DIRECT | MAP | FORMAT | FILTER.
            transform_config: Optional JSON transform config.
            status: ACTIVE | INACTIVE.

        Returns:
            Created BindingRule instance.
        """
        if transform_type not in {"DIRECT", "MAP", "FORMAT", "FILTER"}:
            raise BadRequestError(detail="Invalid transform_type value")
        if status not in {"ACTIVE", "INACTIVE"}:
            raise BadRequestError(detail="Invalid status value")

        rule = BindingRule(
            rule_id=f"bind-{uuid.uuid4()}",
            project_id=project_id,
            source_field=source_field,
            target_field=target_field,
            transform_type=transform_type,
            transform_config=transform_config,
            status=status,
        )
        self._session.add(rule)
        await self._session.flush()
        return rule

    async def get_rule(self, rule_id: str) -> BindingRule:
        """Fetch a rule by ID.

        Args:
            rule_id: Rule identifier.

        Returns:
            BindingRule instance.

        Raises:
            NotFoundError: If rule does not exist.
        """
        result = await self._session.execute(
            select(BindingRule).where(BindingRule.rule_id == rule_id)
        )
        rule = result.scalar_one_or_none()
        if rule is None:
            raise NotFoundError(detail=f"Binding rule '{rule_id}' not found")
        return rule

    async def list_rules(self, project_id: str) -> list[BindingRule]:
        """List rules for a project.

        Args:
            project_id: Project identifier.

        Returns:
            List of BindingRule instances ordered by updated_at desc.
        """
        result = await self._session.execute(
            select(BindingRule)
            .where(BindingRule.project_id == project_id)
            .order_by(BindingRule.updated_at.desc())
        )
        return list(result.scalars().all())

    async def update_rule(self, rule_id: str, updates: dict[str, Any]) -> BindingRule:
        """Update an existing rule.

        Args:
            rule_id: Rule identifier.
            updates: Dictionary of fields to update.

        Returns:
            Updated BindingRule instance.

        Raises:
            NotFoundError: If rule does not exist.
        """
        rule = await self.get_rule(rule_id)
        for key, value in updates.items():
            if value is not None and hasattr(rule, key):
                setattr(rule, key, value)
        await self._session.flush()
        return rule

    async def delete_rule(self, rule_id: str) -> None:
        """Delete a rule.

        Args:
            rule_id: Rule identifier.

        Raises:
            NotFoundError: If rule does not exist.
        """
        rule = await self.get_rule(rule_id)
        await self._session.delete(rule)
        await self._session.flush()
