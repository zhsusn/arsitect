"""BindingRule ORM model for data-binding rules."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class BindingRule(Base):
    """数据绑定规则表."""

    __tablename__ = "binding_rules"

    rule_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=False,
    )
    source_field: Mapped[str] = mapped_column(String(128), nullable=False)
    target_field: Mapped[str] = mapped_column(String(128), nullable=False)
    transform_type: Mapped[str] = mapped_column(String(16), nullable=False, default="DIRECT")
    transform_config: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        CheckConstraint(
            "transform_type IN ('DIRECT', 'MAP', 'FORMAT', 'FILTER')",
            name="ck_binding_transform_type",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_binding_status",
        ),
    )
