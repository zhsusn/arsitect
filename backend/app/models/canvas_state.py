"""CanvasState ORM model — persists React Flow canvas state per project."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class CanvasState(Base):
    """A project's canvas state including nodes, edges, and viewport."""

    __tablename__ = "canvas_states"

    canvas_state_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    nodes: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    edges: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    viewport: Mapped[str] = mapped_column(
        Text, nullable=False, default='{"x": 0, "y": 0, "zoom": 1}'
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (Index("ix_canvas_states_project_id", "project_id"),)
