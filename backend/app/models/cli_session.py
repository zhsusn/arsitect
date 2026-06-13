"""AI CLI Terminal ORM models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


class CliMode(StrEnum):
    """CLI working modes."""

    BUG = "bug"
    ARCH = "arch"


class CliSessionStatus(StrEnum):
    """CLI session lifecycle states."""

    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


class CliMessageType(StrEnum):
    """CLI message types."""

    USER = "user"
    AI = "ai"
    SYSTEM = "system"
    ERROR = "error"
    SUCCESS = "success"
    CARD = "card"
    PROGRESS = "progress"


class BugRecordStatus(StrEnum):
    """Bug record lifecycle states."""

    PENDING = "pending"
    EXECUTED = "executed"
    VERIFIED = "verified"
    FAILED = "failed"
    IGNORED = "ignored"


class BugFixRisk(StrEnum):
    """Bug fix risk levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ArchIssueSeverity(StrEnum):
    """Architecture issue severity levels."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class ArchIssueStatus(StrEnum):
    """Architecture issue lifecycle states."""

    DETECTED = "detected"
    PLANNED = "planned"
    EXECUTED = "executed"
    VERIFIED = "verified"
    CLOSED = "closed"
    SKIPPED = "skipped"


class CliSession(Base):
    """AI CLI terminal session entity."""

    __tablename__ = "cli_sessions"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: f"CLI-{uuid.uuid4()}"
    )
    project_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    mode: Mapped[str] = mapped_column(
        String(10), nullable=False, default=CliMode.BUG.value
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=CliSessionStatus.ACTIVE.value
    )
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    messages: Mapped[list[CliMessage]] = relationship(
        "CliMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="CliMessage.sequence_no",
    )
    bug_records: Mapped[list[BugRecord]] = relationship(
        "BugRecord",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    arch_issues: Mapped[list[ArchIssue]] = relationship(
        "ArchIssue",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("mode IN ('bug', 'arch')", name="ck_cli_session_mode"),
        CheckConstraint(
            "status IN ('active', 'paused', 'closed')",
            name="ck_cli_session_status",
        ),
    )


class CliMessage(Base):
    """Message exchanged within a CLI session."""

    __tablename__ = "cli_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        ForeignKey("cli_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_type: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    card_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    meta_data: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, nullable=True)
    sequence_no: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), nullable=False
    )

    session: Mapped[CliSession] = relationship(
        "CliSession", back_populates="messages"
    )

    __table_args__ = (
        CheckConstraint(
            "message_type IN ('user', 'ai', 'system', 'error', 'success', 'card',"
            " 'progress')",
            name="ck_cli_message_type",
        ),
    )


class BugRecord(Base):
    """Bug record produced by a CLI bug-fix session."""

    __tablename__ = "bug_records"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    session_id: Mapped[str | None] = mapped_column(
        ForeignKey("cli_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    error_signature: Mapped[str] = mapped_column(String(255), nullable=False)
    error_type: Mapped[str] = mapped_column(String(50), nullable=False)
    error_input: Mapped[str] = mapped_column(Text, nullable=False)
    error_stack: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    affected_files: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    fix_diff: Mapped[str | None] = mapped_column(Text, nullable=True)
    fix_risk: Mapped[str] = mapped_column(
        String(10), nullable=False, default=BugFixRisk.MEDIUM.value
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=BugRecordStatus.PENDING.value
    )
    executed_by: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ai"
    )
    verified_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    similar_bug_id: Mapped[str | None] = mapped_column(
        ForeignKey("bug_records.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    session: Mapped[CliSession] = relationship(
        "CliSession", back_populates="bug_records"
    )

    __table_args__ = (
        CheckConstraint(
            "fix_risk IN ('low', 'medium', 'high')",
            name="ck_bug_records_risk",
        ),
        CheckConstraint(
            "status IN ('pending', 'executed', 'verified', 'failed', 'ignored')",
            name="ck_bug_records_status",
        ),
    )


class ArchIssue(Base):
    """Architecture governance issue produced by a CLI arch session."""

    __tablename__ = "arch_issues"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    session_id: Mapped[str | None] = mapped_column(
        ForeignKey("cli_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    issue_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    rule_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    governance_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    refactor_diff: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_points: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ArchIssueStatus.DETECTED.value
    )
    executed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    backup_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    change_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    exec_result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    adr_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    session: Mapped[CliSession] = relationship(
        "CliSession", back_populates="arch_issues"
    )

    __table_args__ = (
        CheckConstraint(
            "severity IN ('critical', 'warning', 'info')",
            name="ck_arch_issues_severity",
        ),
        CheckConstraint(
            "status IN ('detected', 'planned', 'executed', 'verified', 'closed',"
            " 'skipped')",
            name="ck_arch_issues_status",
        ),
    )
