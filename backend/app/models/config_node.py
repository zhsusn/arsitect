"""Unified configuration node ORM model."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import CheckConstraint, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class ConfigNodeScope(StrEnum):
    """Configuration node scope levels."""

    MANAGED = "managed"
    GLOBAL = "global"
    PROJECT = "project"
    USER = "user"


class ConfigNodeType(StrEnum):
    """Supported configuration node types."""

    LLM_PROVIDER = "llm_provider"
    LLM_PERMISSION = "llm_permission"
    SECURITY_POLICY = "security_policy"
    NOTIFICATION = "notification"


class ConfigNode(Base):
    """Unified configuration node for settings, permissions and policies."""

    __tablename__ = "config_nodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    node_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    scope: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    scope_target: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(default=False, nullable=False)
    priority: Mapped[int] = mapped_column(default=0, nullable=False)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    secret_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True, default=None)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "node_type",
            "scope",
            "scope_target",
            "key",
            name="uq_config_node_type_scope_target_key",
        ),
        CheckConstraint(
            "scope IN ('managed','global','project','user')",
            name="ck_config_node_scope",
        ),
        CheckConstraint(
            "node_type IN ('llm_provider','llm_permission','security_policy','notification')",
            name="ck_config_node_type",
        ),
        Index(
            "ix_config_node_type_scope_enabled",
            "node_type",
            "scope",
            "is_enabled",
        ),
    )
