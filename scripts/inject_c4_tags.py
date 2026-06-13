"""Inject @C4- tags into baseline docs based on c4-registry.yaml.

Usage:
    python scripts/inject_c4_tags.py
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml


BASELINE_ROOT = Path("openspec/changes/sdlc-visualizer/baseline")
REGISTRY_PATH = Path("openspec/changes/sdlc-visualizer/baseline/_c4-registry.yaml")

_GENERIC_IDS = {"api", "service", "repository", "store", "manager", "engine", "handler", "controller", "router", "adapter", "dr-003", "dr-004", "dr-005", "dr-009", "dr-010", "dr-015"}


def load_registry() -> dict:
    with REGISTRY_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_front_matter(content: str) -> tuple[dict, str]:
    if not content.startswith("---\n"):
        return {}, content
    end = content.find("\n---\n", 4)
    if end == -1:
        return {}, content
    fm = yaml.safe_load(content[4:end])
    body = content[end + 5 :].lstrip("\n")
    return fm or {}, body


def _body_contains_any(body: str, names: list[str]) -> bool:
    """Check if any name appears in body (outside mermaid blocks)."""
    # Strip mermaid blocks for matching
    clean = re.sub(r"```mermaid\n.*?```", "", body, flags=re.DOTALL)
    return any(name in clean for name in names)


def collect_matching_entities(registry: dict, doc_level: str) -> list[str]:
    tags: list[str] = []

    if doc_level == "L1":
        for eid, info in registry.get("systems", {}).items():
            names = [info["name"]] + info.get("aliases", [])
            tags.append((f"@C4-L1-System:{eid}", names))
        for eid, info in registry.get("actors", {}).items():
            names = [info["name"]] + info.get("aliases", [])
            tags.append((f"@C4-L1-Actor:{eid}", names))

    elif doc_level == "L2":
        for eid, info in registry.get("containers", {}).items():
            names = [info["name"]] + info.get("aliases", [])
            tags.append((f"@C4-L2-Container:{eid}", names))
        for eid, info in registry.get("systems", {}).items():
            names = [info["name"]] + info.get("aliases", [])
            tags.append((f"@C4-L1-System:{eid}", names))

    elif doc_level == "L3":
        for eid, info in registry.get("components", {}).items():
            if eid in _GENERIC_IDS:
                continue
            names = [info["name"]] + info.get("aliases", [])
            tags.append((f"@C4-L3-Component:{eid}", names))
        for iface in registry.get("interfaces", []):
            names = [f"{iface['method']} {iface['path']}", iface["path"]]
            tags.append((f"@C4-Interface:{iface['method']} {iface['path']}", names))
        for eid, info in registry.get("containers", {}).items():
            names = [info["name"]] + info.get("aliases", [])
            tags.append((f"@C4-L2-Container:{eid}", names))
        for eid, info in registry.get("systems", {}).items():
            names = [info["name"]] + info.get("aliases", [])
            tags.append((f"@C4-L1-System:{eid}", names))

    return tags


def inject_tags_for_doc(baseline_path: Path, registry: dict) -> str | None:
    content = baseline_path.read_text(encoding="utf-8-sig")
    meta, body = parse_front_matter(content)
    if not meta:
        return None

    doc_type = meta.get("doc_type", "")
    level = meta.get("c4_binding", {}).get("level", "")
    if not level:
        level = {"PRD": "L1", "ARCH": "L2", "DB_DESIGN": "L2", "DETAIL_DESIGN": "L3", "API_DESIGN": "L3"}.get(doc_type, "")
    if not level:
        return None

    entities = collect_matching_entities(registry, level)
    found_tags: list[str] = []
    for tag, names in entities:
        if _body_contains_any(body, names):
            found_tags.append(tag)

    if not found_tags:
        return None

    # Build global reference block
    block_lines = ["> **C4 绑定引用**："]
    for tag in sorted(set(found_tags)):
        block_lines.append(f"> - `{tag}`")
    block = "\n".join(block_lines)

    # Insert after first heading (title) in body
    lines = body.splitlines()
    heading_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("# "):
            heading_idx = i
            break

    if heading_idx == -1:
        # No title heading; prepend to body
        new_body = block + "\n\n" + body
    else:
        # Insert after heading + trailing blank lines
        insert_idx = heading_idx + 1
        while insert_idx < len(lines) and lines[insert_idx].strip() == "":
            insert_idx += 1
        lines.insert(insert_idx, "")
        lines.insert(insert_idx + 1, block)
        lines.insert(insert_idx + 2, "")
        new_body = "\n".join(lines)

    # Avoid duplicating if already present
    if "> **C4 绑定引用**：" in content:
        return None

    new_content = f"---\n{yaml.dump(meta, allow_unicode=True, sort_keys=False, width=120).rstrip()}\n---\n\n{new_body}\n"
    return new_content


def main() -> None:
    registry = load_registry()
    modified = 0
    skipped = 0

    for md_file in sorted(BASELINE_ROOT.rglob("*.md")):
        if md_file.name.startswith("_"):
            continue
        result = inject_tags_for_doc(md_file, registry)
        if result is None:
            skipped += 1
            continue
        md_file.write_text(result, encoding="utf-8")
        modified += 1

    print(f"Modified {modified} baseline docs with @C4- tags")
    print(f"Skipped {skipped} docs")


if __name__ == "__main__":
    main()
