"""Contracts router — interface contract CRUD + state machine."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.c4.interface_contract_store import (
    ContractStatus,
    InterfaceContract,
    InterfaceContractStore,
)
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/contracts", tags=["Interface Contracts"])


async def get_store(db: AsyncSession = Depends(get_db)) -> InterfaceContractStore:
    return InterfaceContractStore(db)


@router.post("/")
async def create_contract(
    contract: InterfaceContract,
    store: InterfaceContractStore = Depends(get_store),
) -> dict[str, str]:
    """Create a new interface contract."""
    contract_id = await store.create(contract)
    return {"contract_id": contract_id}


@router.get("/container/{container_id}")
async def list_container_contracts(
    project_id: str,
    container_id: str,
    store: InterfaceContractStore = Depends(get_store),
) -> dict[str, list[dict[str, Any]]]:
    """List contracts under a container."""
    contracts = await store.list_by_container(project_id, container_id)
    return {"contracts": [_contract_to_dict(c) for c in contracts]}


@router.get("/project/{project_id}")
async def list_project_contracts(
    project_id: str,
    store: InterfaceContractStore = Depends(get_store),
) -> dict[str, list[dict[str, Any]]]:
    """List all valid contracts for a project."""
    contracts = await store.list_by_project(project_id)
    return {"contracts": [_contract_to_dict(c) for c in contracts]}


@router.post("/{contract_id}/freeze")
async def freeze_contract(
    contract_id: str,
    store: InterfaceContractStore = Depends(get_store),
) -> dict[str, str]:
    """Freeze contract: draft → frozen."""
    await store.freeze(contract_id)
    return {"status": ContractStatus.FROZEN.value}


@router.post("/{contract_id}/gap")
async def mark_gap_contract(
    contract_id: str,
    store: InterfaceContractStore = Depends(get_store),
) -> dict[str, str]:
    """Mark contract as gap."""
    await store.mark_gap(contract_id)
    return {"status": ContractStatus.GAP.value}


@router.post("/{contract_id}/deprecate")
async def deprecate_contract(
    contract_id: str,
    store: InterfaceContractStore = Depends(get_store),
) -> dict[str, str]:
    """Deprecate contract."""
    await store.deprecate(contract_id)
    return {"status": ContractStatus.DEPRECATED.value}


@router.get("/{contract_id}")
async def get_contract(
    contract_id: str,
    store: InterfaceContractStore = Depends(get_store),
) -> dict[str, Any] | None:
    """Get a single contract."""
    contract = await store.get(contract_id)
    return _contract_to_dict(contract) if contract else None


@router.get("/project/{project_id}/export-openui")
async def export_for_openui(
    project_id: str,
    store: InterfaceContractStore = Depends(get_store),
) -> dict[str, str]:
    """Export contracts as OpenUI prompt text."""
    text = await store.export_for_openui(project_id)
    return {"prompt": text}


def _contract_to_dict(contract: InterfaceContract) -> dict[str, Any]:
    return {
        "contract_id": contract.contract_id,
        "project_id": contract.project_id,
        "container_id": contract.container_id,
        "endpoint_path": contract.endpoint_path,
        "method": contract.method,
        "summary": contract.summary,
        "request_schema": contract.request_schema,
        "response_schema": contract.response_schema,
        "status": contract.status,
        "created_at": contract.created_at.isoformat() if contract.created_at else None,
        "updated_at": contract.updated_at.isoformat() if contract.updated_at else None,
    }
