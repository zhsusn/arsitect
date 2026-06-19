"""Skill DAG node and edge ORM models."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class SkillDAGNode(Base):
    """DAG node representing a Skill on the canvas."""

    __tablename__ = "skill_dag_nodes"

    node_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    skill_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("skills.skill_id", ondelete="CASCADE"),
        nullable=False,
    )
    position_x: Mapped[float] = mapped_column(nullable=False, default=0.0)
    position_y: Mapped[float] = mapped_column(nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = ({"sqlite_autoincrement": False},)


class SkillDAGEdge(Base):
    """DAG edge representing dependency between nodes."""

    __tablename__ = "skill_dag_edges"

    edge_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_node_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("skill_dag_nodes.node_id", ondelete="CASCADE"),
        nullable=False,
    )
    target_node_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("skill_dag_nodes.node_id", ondelete="CASCADE"),
        nullable=False,
    )
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_auto_parsed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = ({"sqlite_autoincrement": False},)
