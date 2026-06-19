"""LLM policy rule ORM model."""

from __future__ import annotations

import uuid
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.llm_policy import LlmPolicy


class LlmPolicyRuleCategory(StrEnum):
    """Rule category for UI grouping and engine priority."""

    HIGH_RISK = "high_risk"
    FILE_SYSTEM = "file_system"
    TERMINAL = "terminal"
    NETWORK = "network"


class LlmPolicyRuleActionType(StrEnum):
    """Action type that a rule can govern."""

    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    TERMINAL = "terminal"
    WEB_FETCH = "web_fetch"
    EXTERNAL_API = "external_api"


class LlmPolicyRulePermission(StrEnum):
    """Permission decision for a rule."""

    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"


class LlmPolicyRule(Base, TimestampMixin):
    """Single rule belonging to an LLM policy."""

    __tablename__ = "llm_policy_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("llm_policies.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    action_type: Mapped[str] = mapped_column(String(20), nullable=False)
    permission: Mapped[str] = mapped_column(String(10), nullable=False)
    pattern: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)
    extra_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True, default=None)

    policy: Mapped[LlmPolicy] = relationship("LlmPolicy", back_populates="rules")

    __table_args__ = (
        Index(
            "ix_llm_policy_rule_policy_category_sort",
            "policy_id",
            "category",
            "sort_order",
        ),
        Index("ix_llm_policy_rule_action_type", "action_type"),
    )
