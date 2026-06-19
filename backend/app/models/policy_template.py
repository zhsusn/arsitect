"""Built-in LLM policy template ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from app.models.llm_policy import LlmPolicy


class PolicyTemplate(Base):
    """Built-in policy template seeded at application startup."""

    __tablename__ = "policy_templates"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_mode: Mapped[str] = mapped_column(String(10), nullable=False)
    rules_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)

    policies: Mapped[list[LlmPolicy]] = relationship("LlmPolicy", back_populates="template")
