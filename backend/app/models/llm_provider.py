"""LLM provider ORM model."""

from __future__ import annotations

import uuid
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    pass


class LlmProviderScope(StrEnum):
    """LLM provider scope levels."""

    MANAGED = "managed"
    GLOBAL = "global"
    PROJECT = "project"
    USER = "user"


class LlmProviderType(StrEnum):
    """Supported LLM provider types."""

    KIMI_CLI = "kimi-cli"
    KIMI_API = "kimi-api"
    OPENAI = "openai"
    ARSITECT_AGENT = "arsitect-agent"


class LlmProvider(Base, TimestampMixin):
    """Dedicated LLM provider configuration node."""

    __tablename__ = "llm_providers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    scope: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    scope_target: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    priority: Mapped[int] = mapped_column(default=0, nullable=False)
    provider_type: Mapped[str] = mapped_column(String(20), nullable=False)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    secret_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True, default=None)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("scope", "scope_target", "key", name="uq_llm_provider_scope_target_key"),
        Index("ix_llm_provider_is_default_scope", "is_default", "scope"),
        Index("ix_llm_provider_is_enabled", "is_enabled"),
    )
