"""C4DSLManager — read/write DSL with versioning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import yaml

from app.c4.baseline_store import C4BaselineStore
from app.docforge.c4_assembler import C4Workspace


@dataclass
class DSLEditDTO:
    """DTO for manual DSL edit."""

    content: str
    edit_reason: str
    editor: str


class C4DSLManager:
    """Manage C4 DSL lifecycle: read, edit, version list, rollback."""

    def __init__(self, baseline_store: C4BaselineStore) -> None:
        self.store = baseline_store

    async def read_current(self, project_id: str) -> str | None:
        baseline = await self.store.read_current(project_id)
        return baseline.dsl_content if baseline else None

    async def read_workspace(self, project_id: str) -> C4Workspace | None:
        content = await self.read_current(project_id)
        if not content:
            return None
        return self._parse_yaml(content, project_id)

    async def edit(self, project_id: str, dto: DSLEditDTO) -> str:
        try:
            parsed = yaml.safe_load(dto.content)
            if not parsed or "workspace" not in parsed:
                raise ValueError("Invalid DSL: missing 'workspace' root key")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}") from e

        workspace = self._yaml_to_workspace(parsed, project_id)
        version = await self.store.write(
            workspace=workspace,
            dsl_content=dto.content,
            compiled_from=[f"manual_edit:{dto.editor}:{dto.edit_reason}"],
        )
        return version

    async def list_versions(self, project_id: str) -> list[dict[str, Any]]:
        baselines = await self.store.list_versions(project_id)
        return [
            {
                "version": b.version,
                "is_current": b.is_current,
                "created_at": b.created_at.isoformat(),
                "hash": b.dsl_hash[:16],
            }
            for b in baselines
        ]

    async def rollback(self, project_id: str, version: str) -> str:
        return await self.store.rollback(project_id, version)

    @staticmethod
    def _parse_yaml(content: str, project_id: str) -> C4Workspace:
        data = yaml.safe_load(content)
        ws_data = data.get("workspace", {})
        model = ws_data.get("model", {})
        return C4Workspace(
            project_id=project_id,
            version=ws_data.get("version", "1.0.0"),
            system=model.get("system"),
            actors=model.get("actors", []),
            external_systems=model.get("externalSystems", []),
            containers=model.get("containers", []),
            entities=model.get("entities", []),
            components=model.get("components", []),
            interfaces=model.get("interfaces", []),
            relationships=model.get("relationships", []),
        )

    @staticmethod
    def _yaml_to_workspace(data: dict[str, Any], project_id: str) -> C4Workspace:
        ws_data = data.get("workspace", {})
        model = ws_data.get("model", {})
        return C4Workspace(
            project_id=project_id,
            version=ws_data.get("version", "1.0.0"),
            system=model.get("system"),
            actors=model.get("actors", []),
            external_systems=model.get("externalSystems", []),
            containers=model.get("containers", []),
            entities=model.get("entities", []),
            components=model.get("components", []),
            interfaces=model.get("interfaces", []),
            relationships=model.get("relationships", []),
        )
