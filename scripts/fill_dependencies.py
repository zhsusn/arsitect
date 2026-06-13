"""Fill dependencies field in baseline docs based on cross-file references.

Usage:
    python scripts/fill_dependencies.py
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml


BASELINE_ROOT = Path("openspec/changes/sdlc-visualizer/baseline")


def build_index() -> dict[str, dict]:
    """Build global index of all baseline docs."""
    index: dict[str, dict] = {}
    for f in sorted(BASELINE_ROOT.rglob("*.md")):
        if f.name.startswith("_"):
            continue
        content = f.read_text(encoding="utf-8-sig")
        m = re.match(r"---\n(.*?)\n---", content, re.DOTALL)
        if not m:
            continue
        meta = yaml.safe_load(m.group(1))
        if not meta:
            continue
        fid = meta.get("fragment_id")
        if not fid:
            continue
        index[fid] = {
            "path": str(f.relative_to(BASELINE_ROOT)).replace("\\", "/"),
            "version": meta.get("version", "1.0.0"),
            "doc_type": meta.get("doc_type", ""),
            "title": meta.get("title", ""),
            "feature": _extract_feature(str(f.relative_to(BASELINE_ROOT))),
        }
    return index


def _extract_feature(rel_path: str) -> str | None:
    m = re.search(r"feature-(\d+)-([^/]+)", rel_path)
    if m:
        return f"feature-{m.group(1)}"
    return None


def _build_alias_map(index: dict) -> dict[str, str | list[str]]:
    """Build alias map from legacy IDs (PRD-000, HLD-001, DR-001) to fragment_ids."""
    alias_map: dict[str, str | list[str]] = {
        "PRD-000": "prd-sdlc-visualizer-000",
        "HLD-001": "arch-sdlc-visualizer-001",
        "HLD-002": "arch-sdlc-visualizer-002",
        "HLD-003": "arch-sdlc-visualizer-003",
        "HLD-004": "arch-sdlc-visualizer-004",
        "HLD-005": "arch-sdlc-visualizer-005",
    }
    # Map DR-XXX to both requirements and design docs
    for fid, info in index.items():
        feat = info.get("feature")
        if not feat:
            continue
        num = feat.replace("feature-", "")
        dr_key = f"DR-{int(num):03d}"
        if dr_key not in alias_map:
            alias_map[dr_key] = []
        if isinstance(alias_map[dr_key], list):
            alias_map[dr_key].append(fid)
    return alias_map


def _resolve_alias(alias: str, alias_map: dict, current_doc_type: str) -> str | None:
    """Resolve an alias to a fragment_id, considering current doc type."""
    val = alias_map.get(alias)
    if val is None:
        return None
    if isinstance(val, str):
        return val
    # For DR-XXX which maps to multiple docs, pick the most relevant one
    if current_doc_type == "DETAIL_DESIGN":
        for v in val:
            if "detail-design" in v:
                return v
    elif current_doc_type == "PRD":
        for v in val:
            if "prd-" in v and "feat" in v:
                return v
    # Fallback: return first
    return val[0] if val else None


def extract_refs_from_body(body: str) -> set[str]:
    """Extract legacy ID references from document body."""
    refs: set[str] = set()
    # PRD-000, HLD-001~005, DR-001~021
    for m in re.finditer(r"\b(PRD-000|HLD-00[0-5]|DR-0\d{2})\b", body):
        refs.add(m.group(1))
    # Gate references
    for m in re.finditer(r"\bGate\s+(1|2|2\.5|3)\b", body):
        gate = m.group(1)
        if gate == "1":
            refs.add("PRD-000")
        elif gate == "2":
            refs.add("HLD-001")
        elif gate == "2.5":
            refs.add("DR-001")  # Will be resolved contextually
        elif gate == "3":
            refs.add("UAT")
    # Relative markdown paths
    for m in re.finditer(r"\.\./[^)\s\]]+\.md", body):
        path = m.group(0)
        # Extract filename stem and try to match
        stem = Path(path).stem
        if "requirements-overview" in stem:
            refs.add("PRD-000")
        elif "architecture-core" in stem:
            refs.add("HLD-001")
        elif "data-flow" in stem:
            refs.add("HLD-002")
        elif "runtime-behavior" in stem:
            refs.add("HLD-003")
        elif "api-spec" in stem:
            refs.add("API-SPEC")
        elif "db-schema" in stem:
            refs.add("DB-SCHEMA")
    return refs


def get_default_upstream(
    doc_type: str, feature: str | None, fid: str, index: dict
) -> list[str]:
    """Get default upstream dependencies based on doc type and doc identity."""
    deps: list[str] = []

    # Root-level PRD (requirements overview) has no upstream architecture dependencies
    if fid == "prd-sdlc-visualizer-000":
        # May depend on brainstorming outputs
        for bf_fid in ("changelog-sdlc-visualizer-146", "changelog-sdlc-visualizer-392"):
            if bf_fid in index:
                deps.append(bf_fid)
        return deps

    # Root-level ARCH (design overview) only depends on PRD
    if fid == "arch-sdlc-visualizer-000":
        deps.append("prd-sdlc-visualizer-000")
        return deps

    if doc_type == "PRD" and feature:
        # Detailed requirements depend on high-level requirements
        deps.append("prd-sdlc-visualizer-000")
        deps.append("arch-sdlc-visualizer-000")

    elif doc_type == "ARCH":
        deps.append("prd-sdlc-visualizer-000")

    elif doc_type == "DETAIL_DESIGN":
        if feature:
            # Find corresponding requirements doc
            num = feature.replace("feature-", "")
            req_fid = f"prd-sdlc-visualizer-feat{int(num):02d}-629"
            if req_fid in index:
                deps.append(req_fid)
        # All detailed designs depend on high-level design
        deps.extend([
            "arch-sdlc-visualizer-000",
            "arch-sdlc-visualizer-001",
        ])
        # Also depend on shared specs
        if "api-design-sdlc-visualizer-shared-824" in index:
            deps.append("api-design-sdlc-visualizer-shared-824")
        if "db-design-sdlc-visualizer-shared-607" in index:
            deps.append("db-design-sdlc-visualizer-shared-607")

    elif doc_type == "API_DESIGN":
        deps.extend([
            "arch-sdlc-visualizer-001",
            "arch-sdlc-visualizer-002",
        ])
        if "db-design-sdlc-visualizer-shared-607" in index:
            deps.append("db-design-sdlc-visualizer-shared-607")

    elif doc_type == "DB_DESIGN":
        deps.extend([
            "arch-sdlc-visualizer-002",
            "arch-sdlc-visualizer-001",
        ])

    elif doc_type == "TEST_PLAN":
        deps.extend([
            "prd-sdlc-visualizer-000",
            "arch-sdlc-visualizer-000",
        ])

    return deps


def fill_dependencies() -> None:
    index = build_index()
    alias_map = _build_alias_map(index)

    # Extra alias mappings for special files
    alias_map["API-SPEC"] = "api-design-sdlc-visualizer-shared-824"
    alias_map["DB-SCHEMA"] = "db-design-sdlc-visualizer-shared-607"

    modified = 0
    skipped = 0

    for f in sorted(BASELINE_ROOT.rglob("*.md")):
        if f.name.startswith("_"):
            continue

        content = f.read_text(encoding="utf-8-sig")
        m = re.match(r"---\n(.*?)\n---", content, re.DOTALL)
        if not m:
            skipped += 1
            continue

        meta = yaml.safe_load(m.group(1))
        body = content[m.end():]

        fid = meta.get("fragment_id")
        doc_type = meta.get("doc_type", "")
        feature = index.get(fid, {}).get("feature")

        # Collect dependencies
        dep_ids: set[str] = set()

        # 1. Default upstream dependencies
        for dep_fid in get_default_upstream(doc_type, feature, fid, index):
            if dep_fid in index and dep_fid != fid:
                dep_ids.add(dep_fid)

        # 2. Extract explicit references from body (skip for root-level docs to avoid downstream deps)
        if fid not in ("prd-sdlc-visualizer-000", "arch-sdlc-visualizer-000"):
            refs = extract_refs_from_body(body)
            for ref in refs:
                resolved = _resolve_alias(ref, alias_map, doc_type)
                if resolved and resolved in index and resolved != fid:
                    dep_ids.add(resolved)

        # 3. For design docs, also scan for referenced DR-XXX in Mermaid/external service blocks
        if doc_type == "DETAIL_DESIGN" and feature and fid != "arch-sdlc-visualizer-000":
            for other_fid, other_info in index.items():
                if other_fid == fid:
                    continue
                other_feat = other_info.get("feature")
                if not other_feat:
                    continue
                # Check if other feature is referenced in body
                num = other_feat.replace("feature-", "")
                dr_pattern = f"DR-{int(num):03d}"
                if dr_pattern in body and other_fid in index:
                    dep_ids.add(other_fid)

        if not dep_ids:
            skipped += 1
            continue

        # Build dependencies list
        deps_list: list[dict] = []
        for dep_fid in sorted(dep_ids):
            dep_version = index.get(dep_fid, {}).get("version", "1.0.0")
            deps_list.append({"fragment_id": dep_fid, "version": dep_version})

        # Update meta
        meta["dependencies"] = deps_list

        # Rebuild content
        new_fm = yaml.dump(meta, allow_unicode=True, sort_keys=False, width=120).rstrip()
        new_content = f"---\n{new_fm}\n---{body}"

        f.write_text(new_content, encoding="utf-8")
        modified += 1

    print(f"Modified {modified} docs with dependencies")
    print(f"Skipped {skipped} docs")


if __name__ == "__main__":
    fill_dependencies()
