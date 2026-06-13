"""Validation router — cross-layer consistency checks."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.c4.baseline_store import C4BaselineStore
from app.c4.binding_registry import C4BindingRegistry
from app.c4.cross_layer_validator import CrossLayerValidator, ValidationReport
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/validation", tags=["Validation"])


async def get_validator(db: AsyncSession = Depends(get_db)) -> CrossLayerValidator:
    return CrossLayerValidator(C4BaselineStore(db), C4BindingRegistry(db))


@router.get("/cross-layer")
async def validate_cross_layer(
    project_id: str,
    validator: CrossLayerValidator = Depends(get_validator),
) -> dict[str, Any]:
    """Execute full cross-layer validation."""
    report = await validator.validate(project_id)
    return _report_to_dict(report)


@router.post("/cross-layer/incremental")
async def validate_incremental(
    project_id: str,
    changed_nodes: list[str],
    validator: CrossLayerValidator = Depends(get_validator),
) -> dict[str, Any]:
    """Incremental validation — only check changed nodes."""
    report = await validator.validate_incremental(project_id, changed_nodes)
    return _report_to_dict(report)


def _report_to_dict(report: ValidationReport) -> dict[str, Any]:
    return {
        "project_id": report.project_id,
        "passed": report.passed,
        "error_count": report.error_count,
        "warning_count": report.warning_count,
        "info_count": report.info_count,
        "summary": report.summary,
        "issues": [
            {
                "rule_id": i.rule_id,
                "severity": i.severity.value,
                "message": i.message,
                "c4_node_id": i.c4_node_id,
                "c4_level": i.c4_level,
                "suggestion": i.suggestion,
            }
            for i in report.issues
        ],
    }
