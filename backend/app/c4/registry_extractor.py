"""C4 registry extraction service.

Wraps ``app.c4.extractor`` so the backend can run extraction without spawning a
subprocess, persist snapshots, compute diffs and manage orphan node metadata.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from app.c4 import extractor as _extractor
from app.core.config import settings


def _registry_path(project_id: str) -> Path:
    return settings.project_root / "openspec" / "changes" / project_id / "baseline" / "_c4-registry.yaml"


def _snapshot_dir(project_id: str) -> Path:
    return settings.project_root / "data" / "c4-registry-snapshots" / project_id


def _set_extractor_paths(project_id: str) -> None:
    """Override the extractor module-level path constants for the current project."""
    project_root = settings.project_root
    _extractor._PROJECT_ROOT = project_root  # noqa: SLF001
    _extractor.SRC_ROOT = project_root / "openspec" / "changes" / project_id
    _extractor.REGISTRY_PATH = _registry_path(project_id)
    _extractor.BACKEND_ROOT = project_root / "backend" / "app"
    _extractor.FRONTEND_ROOT = project_root / "frontend" / "src"


def _load_yaml(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")


def _snapshot_path(project_id: str, timestamp: datetime) -> Path:
    return _snapshot_dir(project_id) / f"{timestamp.strftime('%Y%m%d%H%M%S')}.yaml"


def _compute_stats(registry: dict[str, Any], project_id: str) -> dict[str, Any]:
    components = registry.get("components", {})
    relationships = registry.get("relationships", [])
    connected = set()
    for rel in relationships:
        connected.add(rel.get("source", ""))
        connected.add(rel.get("target", ""))

    orphans = [
        {
            "id": cid,
            "name": info.get("name", cid),
            "container_id": info.get("container_id"),
            "source": info.get("source", "doc"),
            "implemented": bool(info.get("implemented", False)),
            "source_file": info.get("source_file") or info.get("source_code_file"),
        }
        for cid, info in components.items()
        if cid not in connected
    ]
    intentional = [o for o in orphans if components.get(o["id"], {}).get("intentional_orphan")]
    return {
        "project_id": project_id,
        "systems": len(registry.get("systems", {})),
        "actors": len(registry.get("actors", {})),
        "containers": len(registry.get("containers", {})),
        "components": len(components),
        "interfaces": len(registry.get("interfaces", [])),
        "relationships": len(relationships),
        "orphan_count": len(orphans),
        "intentional_orphan_count": len(intentional),
        "effective_orphan_count": len(orphans) - len(intentional),
        "orphans": orphans,
    }


def extract_registry(project_id: str) -> dict[str, Any]:
    """Run the C4 extractor, write the registry and persist a timestamped snapshot.

    Returns:
        Computed statistics for the extracted registry.
    """
    _set_extractor_paths(project_id)

    registry = _extractor.build_registry()
    registry_path = _registry_path(project_id)

    # Preserve intentional orphan flags set manually or in previous runs, but only
    # for components that are still disconnected. Once a component gains edges it
    # should no longer be treated as an orphan.
    previous = _load_yaml(registry_path)
    if previous:
        prev_components = previous.get("components", {})
        connected = set()
        for rel in registry.get("relationships", []):
            connected.add(rel.get("source", ""))
            connected.add(rel.get("target", ""))
        for cid, info in registry.get("components", {}).items():
            if (
                cid in prev_components
                and prev_components[cid].get("intentional_orphan")
                and cid not in connected
            ):
                info["intentional_orphan"] = True

    _write_yaml(registry_path, registry)

    now = datetime.now(UTC)
    _write_yaml(_snapshot_path(project_id, now), registry)

    return _compute_stats(registry, project_id)


def load_registry(project_id: str) -> dict[str, Any] | None:
    """Load the current registry for a project, if it exists."""
    return _load_yaml(_registry_path(project_id))


def _component_key(info: dict[str, Any]) -> str:
    """Stable comparison key for a component (ignores source file path noise)."""
    return f"{info.get('name')}:{info.get('container_id')}:{info.get('kind')}"


def compute_registry_diff(
    current: dict[str, Any],
    previous: dict[str, Any] | None,
) -> dict[str, Any]:
    """Compare two registry dictionaries and return a structured delta."""
    if previous is None:
        previous = {"components": {}, "relationships": [], "systems": {}, "actors": {}, "containers": {}}

    cur_components = current.get("components", {})
    prev_components = previous.get("components", {})

    added = [cid for cid in cur_components if cid not in prev_components]
    removed = [cid for cid in prev_components if cid not in cur_components]
    changed = [
        {
            "id": cid,
            "before": _component_key(prev_components[cid]),
            "after": _component_key(cur_components[cid]),
        }
        for cid in cur_components
        if cid in prev_components and _component_key(cur_components[cid]) != _component_key(prev_components[cid])
    ]

    cur_rels = {(r.get("source"), r.get("target"), r.get("description")) for r in current.get("relationships", [])}
    prev_rels = {(r.get("source"), r.get("target"), r.get("description")) for r in previous.get("relationships", [])}

    orphan_delta = {
        "before": previous.get("stats", {}).get("effective_orphan_count", 0),
        "after": current.get("stats", {}).get("effective_orphan_count", 0),
    }

    return {
        "components": {"added": added, "removed": removed, "changed": changed},
        "relationships": {
            "added": list(cur_rels - prev_rels),
            "removed": list(prev_rels - cur_rels),
        },
        "counts": {
            "before": {
                "components": len(prev_components),
                "relationships": len(previous.get("relationships", [])),
            },
            "after": {
                "components": len(cur_components),
                "relationships": len(current.get("relationships", [])),
            },
        },
        "orphan_delta": orphan_delta,
    }


def find_snapshot_at_or_before(project_id: str, timestamp: datetime) -> Path | None:
    """Return the latest snapshot path that is <= ``timestamp``."""
    snapshot_dir = _snapshot_dir(project_id)
    if not snapshot_dir.exists():
        return None
    candidates: list[tuple[datetime, Path]] = []
    for path in snapshot_dir.glob("*.yaml"):
        try:
            ts = datetime.strptime(path.stem, "%Y%m%d%H%M%S").replace(tzinfo=UTC)
        except ValueError:
            continue
        if ts <= timestamp:
            candidates.append((ts, path))
    if not candidates:
        return None
    return max(candidates, key=lambda x: x[0])[1]


def toggle_intentional_orphan(project_id: str, component_id: str) -> bool:
    """Toggle the ``intentional_orphan`` flag for a component in the registry.

    Returns:
        New flag value.
    """
    registry = load_registry(project_id)
    if registry is None:
        raise FileNotFoundError(f"Registry not found for project {project_id}")

    components = registry.get("components", {})
    if component_id not in components:
        raise KeyError(f"Component {component_id} not found in registry")

    info = components[component_id]
    new_value = not bool(info.get("intentional_orphan", False))
    info["intentional_orphan"] = new_value
    _write_yaml(_registry_path(project_id), registry)
    return new_value
