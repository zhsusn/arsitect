"""InterfaceContractStore — independent API contract storage with state machine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interface_contract import InterfaceContract as ContractModel


class ContractStatus(StrEnum):
    """Contract lifecycle states."""

    DRAFT = "DRAFT"
    FROZEN = "FROZEN"
    GAP = "GAP"
    DEPRECATED = "DEPRECATED"


@dataclass
class InterfaceContract:
    """DTO for interface contracts."""

    contract_id: str
    project_id: str
    container_id: str
    endpoint_path: str
    method: str
    summary: str = ""
    request_schema: dict[str, Any] | None = None
    response_schema: dict[str, Any] | None = None
    status: str = "draft"
    created_at: datetime | None = None
    updated_at: datetime | None = None


class InterfaceContractStore:
    """Interface contract table — independent storage for API definitions.

    Responsibilities:
    1. CRUD for interface contracts.
    2. State management (draft/frozen/gap/deprecated).
    3. Query by container.
    4. Export for OpenUI prompt generation.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ============================================================
    # CRUD
    # ============================================================
    async def create(self, contract: InterfaceContract) -> str:
        """Create interface contract."""
        record = ContractModel(
            project_id=contract.project_id,
            container_id=contract.container_id,
            endpoint_path=contract.endpoint_path,
            method_type=contract.method,
            operation_summary=contract.summary,
            request_schema=contract.request_schema,
            response_schema=contract.response_schema,
            status=ContractStatus.DRAFT.value,
        )
        self.db.add(record)
        await self.db.flush()
        return str(record.contract_id)

    async def get(self, contract_id: str) -> InterfaceContract | None:
        """Get single contract."""
        result = await self.db.execute(
            select(ContractModel).where(ContractModel.contract_id == contract_id)
        )
        record = result.scalar_one_or_none()
        return self._to_dto(record) if record else None

    async def list_by_container(
        self, project_id: str, container_id: str
    ) -> list[InterfaceContract]:
        """Query all interfaces under a container."""
        result = await self.db.execute(
            select(ContractModel)
            .where(ContractModel.project_id == project_id)
            .where(ContractModel.container_id == container_id)
            .where(ContractModel.status != ContractStatus.DEPRECATED.value)
        )
        return [self._to_dto(r) for r in result.scalars().all()]

    async def list_by_project(self, project_id: str) -> list[InterfaceContract]:
        """Query all valid interfaces for a project."""
        result = await self.db.execute(
            select(ContractModel)
            .where(ContractModel.project_id == project_id)
            .where(
                ContractModel.status.in_([ContractStatus.DRAFT.value, ContractStatus.FROZEN.value])
            )
        )
        return [self._to_dto(r) for r in result.scalars().all()]

    async def update_schema(
        self,
        contract_id: str,
        request_schema: dict[str, Any] | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> None:
        """Update interface schema."""
        import json

        updates: dict[str, Any] = {}
        if request_schema is not None:
            updates["request_schema"] = json.dumps(request_schema, ensure_ascii=False)
        if response_schema is not None:
            updates["response_schema"] = json.dumps(response_schema, ensure_ascii=False)
        if updates:
            await self.db.execute(
                update(ContractModel)
                .where(ContractModel.contract_id == contract_id)
                .values(**updates)
            )

    # ============================================================
    # State machine
    # ============================================================
    async def freeze(self, contract_id: str) -> None:
        """Freeze contract: draft → frozen."""
        await self.db.execute(
            update(ContractModel)
            .where(ContractModel.contract_id == contract_id)
            .values(status=ContractStatus.FROZEN.value)
        )

    async def mark_gap(self, contract_id: str) -> None:
        """Mark as gap: detected by prototype but missing in contract."""
        await self.db.execute(
            update(ContractModel)
            .where(ContractModel.contract_id == contract_id)
            .values(status=ContractStatus.GAP.value)
        )

    async def deprecate(self, contract_id: str) -> None:
        """Deprecate contract."""
        await self.db.execute(
            update(ContractModel)
            .where(ContractModel.contract_id == contract_id)
            .values(status=ContractStatus.DEPRECATED.value)
        )

    # ============================================================
    # OpenUI export
    # ============================================================
    async def export_for_openui(self, project_id: str) -> str:
        """Export as OpenUI prompt-friendly endpoint list."""
        contracts = await self.list_by_project(project_id)
        lines = ["Available Endpoints:"]
        for c in contracts:
            req_fields = ""
            if c.request_schema:
                fields = c.request_schema.get("properties", {})
                req_fields = ", ".join(fields.keys())
                req_fields = f" (fields: {req_fields})"

            resp_fields = ""
            if c.response_schema:
                fields = c.response_schema.get("properties", {})
                resp_fields = ", ".join(fields.keys())
                resp_fields = f" → {resp_fields}"

            lines.append(f"- {c.method} {c.endpoint_path}{req_fields}{resp_fields}")

        return "\n".join(lines)

    # ============================================================
    # DTO mapping
    # ============================================================
    @staticmethod
    def _to_dto(record: ContractModel) -> InterfaceContract:
        import json

        req_schema: dict[str, Any] | None = None
        resp_schema: dict[str, Any] | None = None
        if isinstance(record.request_schema, str):
            try:
                req_schema = json.loads(record.request_schema)
            except json.JSONDecodeError:
                req_schema = None
        elif isinstance(record.request_schema, dict):
            req_schema = record.request_schema

        if isinstance(record.response_schema, str):
            try:
                resp_schema = json.loads(record.response_schema)
            except json.JSONDecodeError:
                resp_schema = None
        elif isinstance(record.response_schema, dict):
            resp_schema = record.response_schema

        return InterfaceContract(
            contract_id=str(record.contract_id),
            project_id=record.project_id,
            container_id=record.container_id or "",
            endpoint_path=record.endpoint_path,
            method=record.method_type,
            summary=record.operation_summary or "",
            request_schema=req_schema,
            response_schema=resp_schema,
            status=record.status,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
