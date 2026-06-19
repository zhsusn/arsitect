"""ExecutionLog ORM model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class ExecutionLog(Base):
    """执行日志表."""

    __tablename__ = "execution_logs"

    log_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    execution_id: Mapped[str] = mapped_column(
        ForeignKey("skill_executions.execution_id", ondelete="CASCADE"),
        nullable=False,
    )
    log_anchor: Mapped[str] = mapped_column(String(32), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    level: Mapped[str] = mapped_column(String(8), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "level IN ('INFO', 'WARN', 'ERROR', 'DEBUG')",
            name="ck_log_level",
        ),
    )
