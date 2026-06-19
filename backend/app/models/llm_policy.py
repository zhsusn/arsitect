"""LLM policy ORM model."""

from __future__ import annotations

import uuid
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.llm_policy_rule import LlmPolicyRule
    from app.models.policy_template import PolicyTemplate


class LlmPolicyScope(StrEnum):
    """LLM policy scope levels."""

    MANAGED = "managed"
    GLOBAL = "global"
    PROJECT = "project"
    USER = "user"


class LlmPolicyDefaultMode(StrEnum):
    """Default decision mode when no rule matches."""

    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"


class LlmPolicy(Base, TimestampMixin):
    """Dedicated LLM permission policy."""

    __tablename__ = "llm_policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    scope: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    scope_target: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    priority: Mapped[int] = mapped_column(default=0, nullable=False)
    default_mode: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("policy_templates.id"), nullable=True
    )
    is_customized: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(default=True, nullable=False)

    rules: Mapped[list[LlmPolicyRule]] = relationship(
        "LlmPolicyRule",
        back_populates="policy",
        cascade="all, delete-orphan",
        order_by="LlmPolicyRule.sort_order",
    )
    template: Mapped[PolicyTemplate | None] = relationship(
        "PolicyTemplate", back_populates="policies"
    )

    __table_args__ = (
        UniqueConstraint("scope", "scope_target", "key", name="uq_llm_policy_scope_target_key"),
        Index("ix_llm_policy_template_id", "template_id"),
        Index("ix_llm_policy_is_enabled", "is_enabled"),
    )
