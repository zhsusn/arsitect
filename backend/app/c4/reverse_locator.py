"""C4ReverseLocator — bidirectional mapping between C4 nodes and code files."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

from app.c4.baseline_store import C4BaselineStore
from app.c4.binding_registry import C4BindingRegistry


@dataclass
class CodeLocation:
    """Code location information."""

    file_path: str
    line_number: int | None = None
    snippet: str | None = None


@dataclass
class NodeLocation:
    """C4 node location in DSL."""

    node_id: str
    node_type: str  # Component / Code
    level: str  # L3 / L4
    dsl_path: str


class C4ReverseLocator:
    """C4 reverse locator.

    Responsibilities:
    1. C4 node → code file (locate_code).
    2. Code file → C4 node (locate_node).
    3. Based on BindingRegistry LOCATES_AT relations.
    """

    def __init__(
        self,
        baseline_store: C4BaselineStore,
        binding_registry: C4BindingRegistry,
        code_base_dir: str = "./projects",
    ) -> None:
        self.baseline = baseline_store
        self.bindings = binding_registry
        self.code_base_dir = Path(code_base_dir)

    # ============================================================
    # Forward: C4 node → code file
    # ============================================================
    async def locate_code(self, project_id: str, c4_node_id: str) -> CodeLocation | None:
        """Locate local code file from C4 node ID.

        Strategy:
        1. Query BindingRegistry (precise mapping).
        2. Infer by convention path (fallback).
        """
        records = await self.bindings.list_locates_at(project_id, c4_node_id)
        if records:
            binding = records[0]
            file_path = binding.source_location or ""
            if file_path and os.path.exists(file_path):
                return CodeLocation(file_path=file_path)

        return self._infer_code_path(project_id, c4_node_id)

    # ============================================================
    # Reverse: code file → C4 node
    # ============================================================
    async def locate_node(self, project_id: str, file_path: str) -> NodeLocation | None:
        """Find C4 node from code file path."""
        records = await self.bindings.query_by_artifact(project_id, file_path)
        for binding in records:
            if binding.c4_level in ("L3", "L4"):
                return NodeLocation(
                    node_id=binding.c4_node_id,
                    node_type="Component" if binding.c4_level == "L3" else "Code",
                    level=binding.c4_level,
                    dsl_path=f"model.components.{binding.c4_node_id}",
                )

        return await self._match_by_filename(project_id, file_path)

    # ============================================================
    # Batch queries
    # ============================================================
    async def locate_codes_batch(
        self, project_id: str, node_ids: list[str]
    ) -> dict[str, CodeLocation | None]:
        """Batch locate code files."""
        results: dict[str, CodeLocation | None] = {}
        for node_id in node_ids:
            results[node_id] = await self.locate_code(project_id, node_id)
        return results

    async def locate_nodes_batch(
        self, project_id: str, file_paths: list[str]
    ) -> dict[str, NodeLocation | None]:
        """Batch locate nodes."""
        results: dict[str, NodeLocation | None] = {}
        for file_path in file_paths:
            results[file_path] = await self.locate_node(project_id, file_path)
        return results

    # ============================================================
    # Internal helpers
    # ============================================================
    def _infer_code_path(self, project_id: str, c4_node_id: str) -> CodeLocation | None:
        """Infer code path by convention."""
        project_dir = self.code_base_dir / project_id
        if not project_dir.exists():
            return None

        patterns = [
            f"src/**/{c4_node_id}.py",
            f"src/**/{c4_node_id.lower()}.py",
            f"src/**/controllers/{c4_node_id}.py",
            f"**/{c4_node_id}.py",
        ]

        for pattern in patterns:
            matches = list(project_dir.rglob(pattern.replace("**/*", "").replace("*.py", ".py")))
            if matches:
                return CodeLocation(file_path=str(matches[0]))

        return None

    async def _match_by_filename(self, project_id: str, file_path: str) -> NodeLocation | None:
        """Match C4 node by filename."""
        filename = Path(file_path).stem

        baseline = await self.baseline.read_current(project_id)
        if not baseline:
            return None

        try:
            data = yaml.safe_load(baseline.dsl_content)
            components = data.get("workspace", {}).get("model", {}).get("components", [])
            for comp in components:
                comp_name = comp.get("name", "")
                if filename.lower() in comp["id"].lower() or filename.lower() in comp_name.lower():
                    return NodeLocation(
                        node_id=comp["id"],
                        node_type="Component",
                        level="L3",
                        dsl_path=f"model.components.{comp['id']}",
                    )
        except yaml.YAMLError:
            pass

        return None
