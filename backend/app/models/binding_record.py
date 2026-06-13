"""C4 Binding Record — artifact to C4 node mapping."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class BindingRecord(Base):
    """SDLC artifact ↔ C4 node binding graph."""

    __tablename__ = "binding_records"

    binding_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=False,
    )
    artifact_id: Mapped[str] = mapped_column(String(200), nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(50), nullable=False)
    c4_node_id: Mapped[str] = mapped_column(String(200), nullable=False)
    c4_level: Mapped[str] = mapped_column(String(5), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(default=1.0, nullable=False)
    source_location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        CheckConstraint(
            "c4_level IN ('L1','L2','L3','L4')",
            name="ck_binding_c4_level",
        ),
        CheckConstraint(
            "relation_type IN ('binds_to','injects_into','implements',"
            "'locates_at','generates')",
            name="ck_binding_relation_type",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_binding_confidence",
        ),
    )
