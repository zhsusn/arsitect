"""Document fragment ORM model."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class Fragment(Base):
    """Document fragment lifecycle management."""

    __tablename__ = "fragments"

    fragment_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=False,
    )
    module_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT")
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        CheckConstraint(
            "doc_type IN ('PRD','DOMAIN_MODEL','ARCH','DETAIL_DESIGN',"
            "'API_DESIGN','DB_DESIGN','OTHER')",
            name="ck_fragment_doc_type",
        ),
        CheckConstraint(
            "state IN ('DRAFT','REVIEW','APPROVED','DEPRECATED')",
            name="ck_fragment_state",
        ),
    )
