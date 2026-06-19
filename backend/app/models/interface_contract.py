"""InterfaceContract ORM model for frozen API contracts."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class InterfaceContract(Base):
    """接口契约表 — OpenUI 原型生成的上游输入之一."""

    __tablename__ = "interface_contracts"

    contract_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=False,
    )
    container_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="所属 C4 Container 标识"
    )
    endpoint_path: Mapped[str] = mapped_column(String(256), nullable=False)
    method_type: Mapped[str] = mapped_column(String(8), nullable=False, comment="HTTP 方法")
    operation_summary: Mapped[str | None] = mapped_column(String(256), nullable=True)
    request_schema: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="请求参数结构 JSON"
    )
    response_schema: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="响应结构 JSON"
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT")
    frozen_at: Mapped[datetime | None] = mapped_column(
        nullable=True, comment="冻结时间（Gate 签字后）"
    )
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        CheckConstraint(
            "method_type IN ('GET','POST','PUT','PATCH','DELETE')",
            name="ck_contract_method",
        ),
        CheckConstraint(
            "status IN ('DRAFT','FROZEN','GAP','DEPRECATED')",
            name="ck_contract_status",
        ),
    )
