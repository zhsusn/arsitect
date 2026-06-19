"""Application ORM model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base, TimestampMixin


class Application(Base, TimestampMixin):
    """Application metadata table."""

    __tablename__ = "applications"

    application_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    application_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    local_path: Mapped[str] = mapped_column(String(4096), nullable=False)
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False, default="default")
    path_accessible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("workspace_id", "application_name", name="uq_app_name_per_ws"),
        {"sqlite_autoincrement": False},
    )
