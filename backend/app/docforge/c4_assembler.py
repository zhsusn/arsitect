"""C4Assembler — snippets deduplication, merge, and DSL generation."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import yaml

from app.docforge.schemas.extraction_schemas import C4Snippet


@dataclass
class C4Workspace:
    """In-memory C4 workspace model (arsitect.aac.yml structure)."""

    project_id: str
    version: str = "1.0.0"

    # L1
    system: dict[str, Any] | None = None
    actors: list[dict[str, Any]] = field(default_factory=list)
    external_systems: list[dict[str, Any]] = field(default_factory=list)

    # L2
    containers: list[dict[str, Any]] = field(default_factory=list)
    entities: list[dict[str, Any]] = field(default_factory=list)

    # L3
    components: list[dict[str, Any]] = field(default_factory=list)
    interfaces: list[dict[str, Any]] = field(default_factory=list)

    # L4
    code_elements: list[dict[str, Any]] = field(default_factory=list)

    # Relations
    relationships: list[dict[str, Any]] = field(default_factory=list)

    # Provenance
    source_fragments: list[str] = field(default_factory=list)


class C4Assembler:
    """Assemble C4 snippets into unified workspace.

    Pipeline:
    1. Group by element_type.
    2. Deduplicate & merge within each type.
    3. Cross-level reference validation.
    4. Build C4Workspace.
    """

    TYPE_TO_FIELD: dict[str, str] = {
        "System": "system",
        "Actor": "actors",
        "ExternalSystem": "external_systems",
        "Container": "containers",
        "Entity": "entities",
        "Component": "components",
        "Interface": "interfaces",
        "CodePath": "code_elements",
        "Table": "entities",
        "Column": "entities",
        "Relationship": "relationships",
        "binding_reference": "system",
    }

    def assemble(self, snippets: list[C4Snippet], project_id: str) -> C4Workspace:
        workspace = C4Workspace(project_id=project_id)
        grouped = self._group_by_type(snippets)

        for element_type, type_snippets in grouped.items():
            merged = self._deduplicate_merge(type_snippets)
            self._add_to_workspace(workspace, element_type, merged)

        self._validate_cross_references(workspace)
        workspace.source_fragments = list(
            {
                s.properties.get("_fragment_id", "")
                for s in snippets
                if "_fragment_id" in s.properties
            }
            - {""}
        )
        return workspace

    def serialize_to_yaml(self, workspace: C4Workspace) -> str:
        """Serialize workspace to Structurizr-compatible YAML."""
        data: dict[str, Any] = {
            "workspace": {
                "project_id": workspace.project_id,
                "version": workspace.version,
                "model": {},
                "views": {},
            }
        }
        model = data["workspace"]["model"]

        if workspace.system:
            model["system"] = workspace.system
        if workspace.actors:
            model["actors"] = workspace.actors
        if workspace.external_systems:
            model["externalSystems"] = workspace.external_systems
        if workspace.containers:
            model["containers"] = workspace.containers
        if workspace.components:
            model["components"] = workspace.components
        if workspace.entities:
            model["entities"] = workspace.entities
        if workspace.interfaces:
            model["interfaces"] = workspace.interfaces
        if workspace.relationships:
            model["relationships"] = workspace.relationships

        data["workspace"]["views"] = self._generate_views(workspace)
        return yaml.dump(
            data, allow_unicode=True, sort_keys=False, default_flow_style=False
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _group_by_type(self, snippets: list[C4Snippet]) -> dict[str, list[C4Snippet]]:
        grouped: dict[str, list[C4Snippet]] = defaultdict(list)
        for s in snippets:
            grouped[s.element_type].append(s)
        return dict(grouped)

    def _deduplicate_merge(
        self, snippets: list[C4Snippet]
    ) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        for snippet in snippets:
            eid = snippet.element_id
            if eid not in merged:
                merged[eid] = {
                    "id": eid,
                    "name": snippet.name or eid,
                    "description": snippet.description,
                    "properties": dict(snippet.properties),
                }
            else:
                existing = merged[eid]
                if snippet.description and not existing["description"]:
                    existing["description"] = snippet.description
                existing["properties"].update(snippet.properties)
        return list(merged.values())

    def _add_to_workspace(
        self, workspace: C4Workspace, element_type: str, items: list[dict[str, Any]]
    ) -> None:
        field = self.TYPE_TO_FIELD.get(element_type)
        if not field:
            return
        if field == "system":
            if items:
                workspace.system = items[0]
        else:
            getattr(workspace, field).extend(items)

    def _validate_cross_references(self, workspace: C4Workspace) -> None:
        container_ids = {c["id"] for c in workspace.containers}
        for comp in workspace.components:
            cref = comp.get("properties", {}).get("container_id")
            if cref and cref not in container_ids:
                comp["properties"]["_validation_error"] = (
                    f"Container '{cref}' not found"
                )

    def _generate_views(self, workspace: C4Workspace) -> dict[str, Any]:
        views: dict[str, Any] = {}
        if workspace.system or workspace.actors:
            views["systemContext"] = {
                "description": "System Context View",
                "include": ["*"],
            }
        if workspace.containers:
            views["container"] = {
                "description": "Container View",
                "include": [c["id"] for c in workspace.containers],
            }
        if workspace.components:
            for container in workspace.containers:
                cid = container["id"]
                related = [
                    c["id"]
                    for c in workspace.components
                    if c.get("properties", {}).get("container_id") == cid
                ]
                if related:
                    views[f"component_{cid}"] = {
                        "description": f"Component View for {cid}",
                        "container": cid,
                        "include": related,
                    }
        return views
