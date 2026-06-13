"""CI gate for C4 registry orphan count.

Usage:
    python ops/c4_registry_gate.py [project_id]

The gate regenerates the registry using ``backend/app/c4/extractor.py`` and fails
if the effective orphan count increased compared to the committed registry.

Exit codes:
    0 - orphan count did not increase (registry updated)
    1 - orphan count increased or extraction failed
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

# ops/ is at the project root, while the extractor lives inside the backend package.
project_root = Path(__file__).resolve().parents[1]
backend_dir = project_root / "backend"
sys.path.insert(0, str(backend_dir))

from app.c4 import extractor  # noqa: E402


def effective_orphan_count(registry: dict) -> int:
    """Count components that are not connected by any relationship and not intentional."""
    components = registry.get("components", {})
    relationships = registry.get("relationships", [])
    connected = set()
    for rel in relationships:
        connected.add(rel.get("source", ""))
        connected.add(rel.get("target", ""))
    orphans = [cid for cid, info in components.items() if cid not in connected]
    intentional = [
        cid for cid in orphans if components.get(cid, {}).get("intentional_orphan")
    ]
    return len(orphans) - len(intentional)


def main() -> int:
    project_id = sys.argv[1] if len(sys.argv) > 1 else "sdlc-visualizer"

    # Point the extractor at the current project.
    extractor._PROJECT_ROOT = project_root  # noqa: SLF001
    extractor.SRC_ROOT = project_root / "openspec" / "changes" / project_id
    extractor.REGISTRY_PATH = (
        project_root / "openspec" / "changes" / project_id / "baseline" / "_c4-registry.yaml"
    )
    extractor.BACKEND_ROOT = project_root / "backend" / "app"
    extractor.FRONTEND_ROOT = project_root / "frontend" / "src"

    registry_path = extractor.REGISTRY_PATH
    old_registry = (
        yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        if registry_path.exists()
        else {}
    )
    old_count = effective_orphan_count(old_registry)

    new_registry = extractor.build_registry()
    new_count = effective_orphan_count(new_registry)

    print(f"Effective orphan count: {old_count} -> {new_count}")
    if new_count > old_count:
        print(f"FAIL: effective orphan count increased from {old_count} to {new_count}")
        return 1

    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        yaml.dump(new_registry, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )
    print("PASS: effective orphan count did not increase")
    return 0


if __name__ == "__main__":
    sys.exit(main())
