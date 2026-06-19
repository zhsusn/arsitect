"""Locator router — reverse mapping between C4 nodes and code files."""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.c4.baseline_store import C4BaselineStore
from app.c4.binding_registry import C4BindingRegistry
from app.c4.reverse_locator import C4ReverseLocator
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/locator", tags=["Reverse Locator"])


async def get_locator(db: AsyncSession = Depends(get_db)) -> C4ReverseLocator:
    return C4ReverseLocator(C4BaselineStore(db), C4BindingRegistry(db))


@router.get("/code")
async def locate_code(
    project_id: str,
    node_id: str,
    locator: C4ReverseLocator = Depends(get_locator),
) -> dict[str, Any]:
    """C4 node → code file."""
    location = await locator.locate_code(project_id, node_id)
    if not location:
        raise HTTPException(status_code=404, detail=f"Code location not found for node {node_id}")
    return {
        "file_path": location.file_path,
        "exists": os.path.exists(location.file_path),
    }


@router.get("/node")
async def locate_node(
    project_id: str,
    file_path: str,
    locator: C4ReverseLocator = Depends(get_locator),
) -> dict[str, Any]:
    """Code file → C4 node."""
    node = await locator.locate_node(project_id, file_path)
    if not node:
        raise HTTPException(status_code=404, detail=f"C4 node not found for file {file_path}")
    return {
        "node_id": node.node_id,
        "type": node.node_type,
        "level": node.level,
        "dsl_path": node.dsl_path,
    }


@router.post("/code/batch")
async def locate_codes_batch(
    project_id: str,
    node_ids: list[str],
    locator: C4ReverseLocator = Depends(get_locator),
) -> dict[str, Any]:
    """Batch: C4 nodes → code files."""
    results = await locator.locate_codes_batch(project_id, node_ids)
    return {
        "results": {
            nid: {
                "file_path": loc.file_path if loc else None,
                "exists": os.path.exists(loc.file_path) if loc else False,
            }
            for nid, loc in results.items()
        }
    }


@router.post("/node/batch")
async def locate_nodes_batch(
    project_id: str,
    file_paths: list[str],
    locator: C4ReverseLocator = Depends(get_locator),
) -> dict[str, Any]:
    """Batch: code files → C4 nodes."""
    results = await locator.locate_nodes_batch(project_id, file_paths)
    return {
        "results": {
            fp: {
                "node_id": node.node_id if node else None,
                "type": node.node_type if node else None,
                "level": node.level if node else None,
            }
            for fp, node in results.items()
        }
    }
