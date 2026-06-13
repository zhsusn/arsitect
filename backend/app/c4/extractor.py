"""C4 extraction engine — backend service module.

Regenerates `openspec/changes/{project_id}/baseline/_c4-registry.yaml`.
It merges three sources:

1. High-level-design (HLD) Markdown: L1 systems, L2 containers, coarse L3 components,
   and high-level relationships.
2. Detailed-design (DD) Markdown: module-specific components and cross-module
   dependency tables.
3. Source code: backend Python classes / API routers and frontend React/TS
   components / stores / service modules, plus their intra-project imports.

Improvements over the legacy version:
- Stricter filtering of generic / DTO / schema / model classes.
- ID normalization so `projectservice` and `project-service` merge.
- Container inference from file path (frontend-spa, backend-api, c4-dsl-engine, etc.).
- Relationship extraction from Python/React imports and DD dependency tables.
- Router components extracted from FastAPI `api/v1/*.py` modules.
- Frontend service-module and Zustand-store components.
- Bulk Service -> Repository healing by stem and substring matching.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

# extractor.py lives at backend/app/c4/extractor.py; project root is 3 levels up.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = _PROJECT_ROOT / "openspec/changes/sdlc-visualizer"
REGISTRY_PATH = _PROJECT_ROOT / "openspec/changes/sdlc-visualizer/baseline/_c4-registry.yaml"
BACKEND_ROOT = _PROJECT_ROOT / "backend/app"
FRONTEND_ROOT = _PROJECT_ROOT / "frontend/src"


# ---------------------------------------------------------------------------
# ID normalization
# ---------------------------------------------------------------------------
def _slug_id(text: str) -> str:
    """Normalize a label to kebab-case ID."""
    text = text.lower()
    text = re.sub(r"[\ud800-\udfff]", "", text)
    text = re.sub(r"[^a-z0-9\s_-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = text.strip("-")
    return text


def _canonical_key(text: str) -> str:
    """Return a collision key ignoring separators, used for deduplication."""
    return _slug_id(text).replace("-", "")


# ---------------------------------------------------------------------------
# Generic / skip lists
# ---------------------------------------------------------------------------
_GENERIC_IDS = {
    "api",
    "repository",
    "service",
    "store",
    "manager",
    "engine",
    "handler",
    "controller",
    "router",
    "adapter",
    "worker",
    "consumer",
    "producer",
    "generator",
    "resolver",
    "validator",
    "calculator",
    "aggregator",
    "collector",
    "parser",
}

_GENERIC_LABELS = {
    "api",
    "service",
    "repository",
    "store",
    "manager",
    "engine",
    "handler",
    "controller",
    "router",
    "adapter",
    "api 层",
    "service 层",
    "repository 层",
    "file",
    "git",
    "db",
    "sse",
    "cli",
    "frontend",
    "backend",
    "database",
    "client",
    "kimi",
    "openspec",
    "post",
    "get",
    "put",
    "delete",
    "patch",
    "files",
    "filesystem",
    "local filesystem",
    "sketches",
    "wireframes",
}

# Suffixes that identify a frontend UI primitive / helper.
_FRONTEND_SUFFIXES = (
    "tab",
    "panel",
    "shell",
    "handle",
    "layer",
    "controller",
    "bar",
    "manager",
    "router",
    "store",
    "pane",
    "view",
    "card",
    "list",
    "grid",
    "form",
    "modal",
    "dialog",
    "drawer",
    "badge",
    "popover",
    "sidebar",
    "mask",
    "confirmation",
    "button",
    "input",
    "chart",
    "canvas",
    "flow",
    "tree",
    "table",
)


# ---------------------------------------------------------------------------
# Container inference
# ---------------------------------------------------------------------------
def _infer_container_from_path(file_path: Path | None) -> str | None:
    """Infer C4 L2 container from the source file path."""
    if file_path is None:
        return None
    parts = file_path.parts
    path_str = str(file_path).replace("\\", "/")

    if FRONTEND_ROOT.name in parts or "frontend" in path_str:
        return "frontend-spa"

    if "backend/app/c4" in path_str or path_str.startswith("backend/app/c4/"):
        return "c4-dsl-engine"
    if "backend/app/services/wireframe" in path_str or "wireframe_generator" in path_str:
        return "wireframe-engine"
    if (
        "backend/app/scheduler" in path_str
        or "backend/app/services/pocketflow" in path_str
        or path_str.startswith("backend/app/engine/")
    ):
        return "skill-orchestrator"
    if "backend/app" in path_str:
        return "backend-api"

    return None


def _infer_container_from_name(name: str, source_path: Path | None = None) -> str:
    """Fallback container inference when no file path is available."""
    path_str = str(source_path).replace("\\", "/") if source_path else ""
    lower_name = name.lower()

    # React/UI components are almost always frontend
    if lower_name.endswith(_FRONTEND_SUFFIXES):
        # Backend class named *Store (e.g. ArtifactStore) stays backend
        if lower_name.endswith("store") and ("backend" in path_str or "app/common" in path_str):
            return "backend-api"
        return "frontend-spa"

    # Zustand stores described in shared frontend design docs
    if lower_name.endswith("store") and "shared/design" in path_str:
        return "frontend-spa"

    return "backend-api"


# ---------------------------------------------------------------------------
# Markdown extraction
# ---------------------------------------------------------------------------
def _clean_mermaid_label(label: str) -> str:
    label = re.sub(r"<[^>]+>", " ", label)
    label = re.sub(r"[\ud800-\udfff]", "", label)
    label = label.split("\n")[0].split("/")[0].strip()
    return label


def extract_mermaid_nodes(content: str) -> list[tuple[str, str, str]]:
    """Return (node_id, label, diagram_type) tuples from Mermaid blocks."""
    entities: list[tuple[str, str, str]] = []
    for mermaid_match in re.finditer(r"```mermaid\n(.*?)```", content, re.DOTALL):
        diagram = mermaid_match.group(1)
        first_line = diagram.strip().splitlines()[0] if diagram.strip() else ""
        diagram_type = "er"
        if "erDiagram" in first_line:
            diagram_type = "er"
        elif "flowchart" in first_line or "graph" in first_line:
            diagram_type = "flowchart"

        if diagram_type != "flowchart":
            continue
        for m in re.finditer(r"([A-Za-z_]\w*)\s*\[\"([^\"]+)\"\]", diagram):
            node_id = m.group(1)
            label = _clean_mermaid_label(m.group(2))
            if node_id.startswith("subgraph"):
                continue
            if label.lower() in _GENERIC_LABELS:
                continue
            if len(label) < 3:
                continue
            entities.append((node_id, label, diagram_type))
    return entities


def extract_python_classes(content: str) -> list[str]:
    """Extract class names from Markdown code snippets."""
    classes: list[str] = []
    suffix_group = "|".join(_BACKEND_IMPL_SUFFIXES)
    pattern = rf"class\s+([A-Z]\w*(?:{suffix_group}))"
    for m in re.finditer(pattern, content):
        name = m.group(1)
        if name.lower() in _GENERIC_IDS:
            continue
        if name.startswith("Test"):
            continue
        if name not in classes:
            classes.append(name)
    return classes


def extract_react_components(content: str) -> list[str]:
    """Extract React component names from Markdown backticks."""
    comps: list[str] = []
    pattern1 = r"`([A-Z][a-zA-Z]+(?:Tab|Panel|Shell|Handle|Layer|Controller|Bar|Manager|Router|Store|Pane|View|Card|List|Grid|Form|Modal|Dialog|Drawer|Badge|Popover|Sidebar|Mask|Confirmation|Button|Input|Chart|Canvas|Flow|Tree|Table))`"
    for m in re.finditer(pattern1, content):
        name = m.group(1)
        if name not in comps:
            comps.append(name)
    return comps


def extract_api_endpoints(content: str) -> list[tuple[str, str]]:
    """Extract `METHOD /path` endpoints."""
    endpoints: list[tuple[str, str]] = []
    for m in re.finditer(r"`([A-Z]+)\s+(/[a-zA-Z0-9/{}._-]+)`", content):
        method, path = m.group(1), m.group(2)
        if (method, path) not in endpoints:
            endpoints.append((method, path))
    return endpoints


def extract_dependency_tables(content: str) -> list[tuple[str, str, str]]:
    """Extract (source, target, description) rows from cross-module dependency tables."""
    rows: list[tuple[str, str, str]] = []
    for table in re.finditer(
        r"\|[^\n]*依赖方[^\n]*\|\n\|[-:|\s]+\|\n((?:\|[^\n]+\|\n?)+)",
        content,
    ):
        body = table.group(1)
        for line in body.strip().splitlines():
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 3:
                continue
            src, tgt, desc = cells[0], cells[1], cells[2] if len(cells) > 2 else ""
            src = src.strip("`").strip()
            tgt = tgt.strip("`").strip()
            desc = desc.strip("`").strip()
            if not src or not tgt:
                continue
            rows.append((src, tgt, desc))
    return rows


# ---------------------------------------------------------------------------
# Source-code scanning
# ---------------------------------------------------------------------------
_BACKEND_IMPL_SUFFIXES = (
    "Service",
    "Repository",
    "Store",
    "Manager",
    "Engine",
    "Orchestrator",
    "Adapter",
    "Handler",
    "Controller",
    "Router",
    "Consumer",
    "Producer",
    "Worker",
    "Scheduler",
    "Generator",
    "Resolver",
    "Validator",
    "Calculator",
    "Aggregator",
    "Collector",
    "Parser",
)

_EXCLUDE_SUFFIXES = (
    "DTO",
    "Schema",
    "Model",
    "Request",
    "Response",
    "Config",
    "Settings",
    "Base",
    "Mixin",
    "Form",
    "Filter",
    "Params",
    "Token",
    "Exception",
    "Error",
)

# IDs that are design-time abstractions / ports and intentionally have no code.
_INTENTIONAL_ORPHAN_IDS = frozenset({"filesystemadapter", "localfilesystemadapter"})


def _looks_like_entity(name: str) -> bool:
    """Whether a Python/TS identifier should be treated as an L3 component."""
    if not name or not name[0].isupper():
        return False
    lower = name.lower()
    if lower in _GENERIC_IDS:
        return False
    if name.startswith("Test"):
        return False
    if any(name.endswith(s) for s in _EXCLUDE_SUFFIXES):
        return False
    return bool(name.endswith(_BACKEND_IMPL_SUFFIXES))


def _should_scan_backend_file(py_file: Path) -> bool:
    """Skip data-only / common utility / test files."""
    path_str = str(py_file).replace("\\", "/")
    skip_fragments = (
        "/models/",
        "/schemas/",
        "/migrations/",
        "/tests/",
        "/alembic/",
        "/__pycache__/",
    )
    if any(frag in path_str for frag in skip_fragments):
        return False
    # Allow api/, services/, repositories/, c4/, scheduler/, engine/, advanced/,
    # governance/, docforge/, common/, infrastructure/database/repositories/.
    allowed_roots = (
        "backend/app/api/",
        "backend/app/services/",
        "backend/app/repositories/",
        "backend/app/c4/",
        "backend/app/scheduler/",
        "backend/app/engine/",
        "backend/app/advanced/",
        "backend/app/governance/",
        "backend/app/docforge/",
        "backend/app/common/",
        "backend/app/infrastructure/database/repositories/",
    )
    return any(path_str.startswith(str(_PROJECT_ROOT / r).replace("\\", "/")) for r in allowed_roots)


def _scan_backend_routers(root: Path) -> dict[str, dict[str, Any]]:
    """Extract FastAPI router modules as L3 components."""
    entities: dict[str, dict[str, Any]] = {}
    api_dir = root / "api/v1"
    if not api_dir.exists():
        return entities
    for py_file in api_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        text = py_file.read_text(encoding="utf-8", errors="replace")
        if "APIRouter" not in text:
            continue
        stem = py_file.stem
        name = "ApiV1Router" if stem == "router" else f"{stem.title().replace('_', '')}Router"
        eid = _canonical_key(name)
        if eid not in entities:
            entities[eid] = {
                "name": name,
                "container_id": "backend-api",
                "file": str(py_file.relative_to(_PROJECT_ROOT).as_posix()),
                "kind": "router",
            }
    return entities


def scan_backend_code(
    root: Path,
) -> tuple[dict[str, dict[str, Any]], list[tuple[str, str, str, str, str | None]]]:
    """Scan backend Python source for classes and intra-project imports via AST.

    Returns:
        entities: dict[canonical_id, {name, container, file, kind}]
        imports: list[(source_canonical_id, target_canonical_id, imported_name,
                      "", resolved_source_file)]
    """
    import ast
    from collections import defaultdict

    entities: dict[str, dict[str, Any]] = {}
    raw_imports: list[tuple[str, str, str, str]] = []
    abs_path_to_entities: dict[Path, list[str]] = defaultdict(list)

    # Routers are module-level, not classes.
    for eid, info in _scan_backend_routers(root).items():
        entities[eid] = info
        abs_path_to_entities[(_PROJECT_ROOT / info["file"]).resolve()].append(eid)

    for py_file in root.rglob("*.py"):
        if not _should_scan_backend_file(py_file):
            continue
        text = py_file.read_text(encoding="utf-8", errors="replace")
        rel_path = str(py_file.relative_to(_PROJECT_ROOT).as_posix())
        abs_path = py_file.resolve()
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue

        container = _infer_container_from_path(py_file) or "backend-api"
        local_classes: list[str] = []
        imported_items: list[tuple[str, str]] = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef) and _looks_like_entity(node.name):
                local_classes.append(node.name)
                eid = _canonical_key(node.name)
                if eid not in entities:
                    entities[eid] = {
                        "name": node.name,
                        "container_id": container,
                        "file": rel_path,
                        "kind": "class",
                    }
                abs_path_to_entities[abs_path].append(eid)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if not module.startswith(("app.", "backend.")):
                    continue
                for alias in node.names:
                    name = alias.asname or alias.name
                    imported_items.append((name, module))

        local_items = local_classes + [
            info["name"]
            for info in entities.values()
            if info.get("kind") == "router" and info.get("file") == rel_path
        ]
        for src_cls in local_items:
            src_id = _canonical_key(src_cls)
            if src_id not in entities:
                continue
            for imp_name, module in imported_items:
                raw_imports.append((rel_path, src_cls, imp_name, module))

    imports: list[tuple[str, str, str, str, str | None]] = []
    for _rel_path, src_name, imp_name, module in raw_imports:
        src_id = _canonical_key(src_name)
        if src_id not in entities:
            continue
        tgt_id = _canonical_key(imp_name)
        resolved_file = None
        if tgt_id not in entities:
            resolved_file = _resolve_py_import_path(module, imp_name)
        imports.append((src_id, tgt_id, imp_name, "", resolved_file))

    # Second pass: resolve imports whose target name is not a known entity by
    # looking up the entities defined in the resolved target file.
    resolved_imports: list[tuple[str, str, str, str, str | None]] = []
    for src_id, tgt_id, imp_name, import_path, resolved in imports:
        if resolved and tgt_id not in entities:
            target_abs = (_PROJECT_ROOT / resolved).resolve()
            for cand_id in abs_path_to_entities.get(target_abs, []):
                if cand_id != src_id:
                    resolved_imports.append((src_id, cand_id, imp_name, import_path, resolved))
        else:
            resolved_imports.append((src_id, tgt_id, imp_name, import_path, resolved))
    return entities, resolved_imports


# ---------------------------------------------------------------------------
# Frontend scanning
# ---------------------------------------------------------------------------
def _should_scan_frontend_file(ts_file: Path) -> bool:
    """Keep all page/shared components, stores, services and App."""
    path_str = str(ts_file).replace("\\", "/")
    if "/frontend/src/stores/" in path_str:
        return True
    if "/frontend/src/services/" in path_str:
        return True
    if path_str.endswith("frontend/src/App.tsx"):
        return True
    if "/frontend/src/pages/" in path_str:
        return path_str.endswith(".tsx")
    if "/frontend/src/components/" in path_str:
        return path_str.endswith(".tsx")
    return False


def _camelize(stem: str) -> str:
    parts = stem.replace("-", "_").split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


def scan_frontend_code(
    root: Path,
) -> tuple[dict[str, dict[str, Any]], list[tuple[str, str, str, str, str | None]]]:
    """Scan frontend TS/TSX source for components, stores and service modules.

    Returns:
        entities: dict[canonical_id, {name, container, file, kind}]
        imports: list[(source_canonical_id, target_canonical_id, imported_name,
                      import_source_path, resolved_source_file)]
    """
    entities: dict[str, dict[str, Any]] = {}
    imports: list[tuple[str, str, str, str, str | None]] = []
    abs_path_to_entities: dict[Path, list[str]] = defaultdict(list)

    def _register(name: str, kind: str, rel_path: str, abs_path: Path, container: str) -> str:
        eid = _canonical_key(name)
        if eid not in entities:
            entities[eid] = {
                "name": name,
                "container_id": container,
                "file": rel_path,
                "kind": kind,
            }
        abs_path_to_entities[abs_path].append(eid)
        return eid

    for ts_file in root.rglob("*.ts"):
        if not _should_scan_frontend_file(ts_file):
            continue
        text = ts_file.read_text(encoding="utf-8", errors="replace")
        container = _infer_container_from_path(ts_file) or "frontend-spa"
        rel_path = str(ts_file.relative_to(_PROJECT_ROOT).as_posix())
        abs_path = ts_file.resolve()

        local_names: list[str] = []

        if "/stores/" in str(ts_file).replace("\\", "/"):
            for m in re.finditer(
                r"export\s+(?:const|function)\s+(use[A-Z][a-zA-Z0-9]*Store|[a-z][a-zA-Z0-9]*Store)\b",
                text,
            ):
                local_names.append(m.group(1))

        if "/services/" in str(ts_file).replace("\\", "/"):
            # One module component per service file, named by camelCased stem + 'Api'.
            stem = ts_file.stem
            name = f"{_camelize(stem)}Api"
            local_names.append(name)

        for name in local_names:
            kind = "store" if "Store" in name else "service-module"
            _register(name, kind, rel_path, abs_path, container)

        file_imports = _collect_ts_imports(text, rel_path)
        for src_name in local_names:
            src_id = _canonical_key(src_name)
            for imp_name, src_path, resolved in file_imports:
                tgt_id = _canonical_key(imp_name)
                if tgt_id == src_id:
                    continue
                imports.append((src_id, tgt_id, imp_name, src_path, resolved))

    for ts_file in root.rglob("*.tsx"):
        if not _should_scan_frontend_file(ts_file):
            continue
        text = ts_file.read_text(encoding="utf-8", errors="replace")
        container = _infer_container_from_path(ts_file) or "frontend-spa"
        rel_path = str(ts_file.relative_to(_PROJECT_ROOT).as_posix())
        abs_path = ts_file.resolve()

        local_comps: list[str] = []
        for m in re.finditer(
            r"(?:export\s+)?(?:function|const)\s+([A-Z][a-zA-Z0-9]*)\s*[\(:=]",
            text,
        ):
            local_comps.append(m.group(1))
        for m in re.finditer(r"export\s+default\s+(?:function\s+)?([A-Z][a-zA-Z0-9]*)\b", text):
            if m.group(1) not in local_comps:
                local_comps.append(m.group(1))
        for m in re.finditer(r"class\s+([A-Z][a-zA-Z0-9]*)\s+extends", text):
            if m.group(1) not in local_comps:
                local_comps.append(m.group(1))

        if not local_comps:
            continue

        for comp in local_comps:
            _register(comp, "component", rel_path, abs_path, container)

        file_imports = _collect_ts_imports(text, rel_path)
        for src_comp in local_comps:
            src_id = _canonical_key(src_comp)
            for imp_name, src_path, resolved in file_imports:
                tgt_id = _canonical_key(imp_name)
                if tgt_id == src_id:
                    continue
                imports.append((src_id, tgt_id, imp_name, src_path, resolved))

    # Use the per-file entity map to resolve imports whose target name does not
    # match a known entity (common for service functions imported by name).
    resolved_imports: list[tuple[str, str, str, str, str | None]] = []
    for src_id, tgt_id, imp_name, src_path, resolved in imports:
        if resolved and tgt_id not in entities:
            target_abs = (_PROJECT_ROOT / resolved).resolve()
            for cand_id in abs_path_to_entities.get(target_abs, []):
                if cand_id != src_id:
                    resolved_imports.append((src_id, cand_id, imp_name, src_path, resolved))
        else:
            resolved_imports.append((src_id, tgt_id, imp_name, src_path, resolved))
    return entities, resolved_imports


def _resolve_ts_import_path(importer_file: str, src_path: str) -> str | None:
    """Resolve a TS import source path to a project-relative file path."""
    importer_path = _PROJECT_ROOT / importer_file
    if src_path.startswith("@/"):
        base = _PROJECT_ROOT / "frontend" / "src" / src_path[2:]
    else:
        base = importer_path.parent / src_path
    candidates = [
        base,
        base.with_suffix(".ts"),
        base.with_suffix(".tsx"),
        base / "index.ts",
        base / "index.tsx",
    ]
    for cand in candidates:
        if cand.exists():
            return str(cand.resolve().relative_to(_PROJECT_ROOT).as_posix())
    return None


def _resolve_py_import_path(module: str, name: str | None = None) -> str | None:
    """Resolve a Python import module (and optional submodule alias) to a project-relative file path."""
    if not module.startswith(("app.", "backend.")):
        return None

    def _try(parts: list[str]) -> str | None:
        if parts[0] == "app":
            rel_parts = parts[1:]
        elif parts[0] == "backend" and len(parts) > 2 and parts[1] == "app":
            rel_parts = parts[2:]
        else:
            rel_parts = parts
        rel = Path(*rel_parts)
        candidates = [rel.with_suffix(".py"), rel / "__init__.py"]
        for cand in candidates:
            f = BACKEND_ROOT / cand
            if f.exists():
                return str(f.resolve().relative_to(_PROJECT_ROOT).as_posix())
        return None

    # If the imported alias is a submodule (lowercase), prefer module.alias first.
    if name and not name[0].isupper():
        sub = _try((module + "." + name).split("."))
        if sub:
            return sub
    return _try(module.split("."))


def _collect_ts_imports(text: str, importer_file: str) -> list[tuple[str, str, str | None]]:
    """Return (imported_name, source_path, resolved_project_path) for local project imports.

    Supports both relative (``./`` / ``../``) and Vite/TS alias (``@/``) imports, and
    includes lowercase named/default imports such as hooks and service functions.
    """
    imported: list[tuple[str, str, str | None]] = []
    for m in re.finditer(
        r"import\s+(?:(?:\{([\s\S]*?)\})|([a-zA-Z_$][\w$]*))\s+from\s+['\"]([^'\"]+)['\"]",
        text,
    ):
        named = m.group(1) or ""
        default_imp = m.group(2) or ""
        src_path = m.group(3)
        if not (src_path.startswith(".") or src_path.startswith("@/")):
            continue
        resolved = _resolve_ts_import_path(importer_file, src_path)
        if default_imp:
            imported.append((default_imp, src_path, resolved))
        for n in named.split(","):
            n = n.strip().split(" as ")[0].strip()
            if n:
                imported.append((n, src_path, resolved))
    return imported


# ---------------------------------------------------------------------------
# Registry builder
# ---------------------------------------------------------------------------
class RegistryBuilder:
    """Incremental builder for the C4 registry."""

    def __init__(self) -> None:
        self.systems: dict[str, dict[str, Any]] = {}
        self.actors: dict[str, dict[str, Any]] = {}
        self.containers: dict[str, dict[str, Any]] = {}
        self.components: dict[str, dict[str, Any]] = {}
        self.interfaces: list[dict[str, Any]] = []
        self.relationships: list[dict[str, Any]] = []
        self._rel_set: set[tuple[str, str, str]] = set()
        self._canonical_to_id: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Adders
    # ------------------------------------------------------------------
    def add_system(self, eid: str, name: str, aliases: list[str], level: str = "L1") -> None:
        if eid not in self.systems:
            self.systems[eid] = {"name": name, "aliases": aliases, "level": level}

    def add_actor(self, eid: str, name: str, aliases: list[str], level: str = "L1") -> None:
        if eid not in self.actors:
            self.actors[eid] = {"name": name, "aliases": aliases, "level": level}

    def add_container(self, eid: str, name: str, aliases: list[str], level: str = "L2") -> None:
        if eid not in self.containers:
            self.containers[eid] = {"name": name, "aliases": aliases, "level": level}

    def add_component(
        self,
        eid: str,
        name: str,
        aliases: list[str] | None = None,
        container_id: str | None = None,
        level: str = "L3",
        source: str = "doc",
        source_file: str | None = None,
        kind: str | None = None,
    ) -> str:
        """Add or merge a component. Returns the final component ID."""
        if not eid:
            return ""
        canon = _canonical_key(eid)

        existing_id = self._canonical_to_id.get(canon)
        if existing_id:
            existing = self.components[existing_id]
            existing["aliases"] = list({*(existing.get("aliases") or []), *(aliases or []), eid})
            if container_id:
                existing["container_id"] = container_id
            if source_file:
                if existing.get("source") == "doc" and source == "code":
                    existing["source_code_file"] = source_file
                else:
                    existing["source_file"] = source_file
            if kind and not existing.get("kind"):
                existing["kind"] = kind
            if source == "code":
                existing["implemented"] = True
            return existing_id

        if eid in _GENERIC_IDS or _canonical_key(eid) in _GENERIC_IDS:
            return ""

        self.components[eid] = {
            "name": name,
            "aliases": list(aliases or []),
            "level": level,
        }
        if container_id:
            self.components[eid]["container_id"] = container_id
        if source:
            self.components[eid]["source"] = source
        if source_file:
            self.components[eid]["source_file"] = source_file
        if kind:
            self.components[eid]["kind"] = kind
        self.components[eid]["implemented"] = source == "code"
        self._canonical_to_id[canon] = eid
        return eid

    def add_relationship(self, source: str, target: str, description: str = "") -> None:
        if not source or not target or source == target:
            return
        key = (source, target, description)
        if key in self._rel_set:
            return
        self._rel_set.add(key)
        self.relationships.append({"source": source, "target": target, "description": description})

    def add_interface(self, iid: str, method: str, path: str, source_container: str | None = None) -> None:
        if not any(i["id"] == iid for i in self.interfaces):
            self.interfaces.append({
                "id": iid,
                "method": method,
                "path": path,
                "source_container": source_container,
            })

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def resolve(self, label_or_id: str) -> str | None:
        """Try to map a label/ID to a registered component/system/container ID."""
        label = label_or_id.strip("`").strip()
        lower = label.lower()
        for d in (self.components, self.containers, self.systems, self.actors):
            if label in d:
                return label
            if lower in d:
                return lower
        canon = _canonical_key(label)
        final_id = self._canonical_to_id.get(canon)
        if final_id:
            return final_id
        for eid, info in self.components.items():
            for alias in info.get("aliases", []):
                if _canonical_key(alias) == canon:
                    return eid
        return None

    def ensure_component(self, eid: str, name: str, container_id: str, kind: str = "derived") -> str:
        """Ensure a derived component exists (e.g. inferred service module)."""
        if eid in self.components:
            return eid
        self.add_component(eid, name, aliases=[], container_id=container_id, source="code")
        if eid in self.components:
            self.components[eid]["kind"] = kind
        return eid

    def to_dict(self) -> dict[str, Any]:
        return {
            "systems": self.systems,
            "actors": self.actors,
            "containers": self.containers,
            "components": self.components,
            "interfaces": self.interfaces,
            "relationships": self.relationships,
        }


# ---------------------------------------------------------------------------
# Build pipeline
# ---------------------------------------------------------------------------
def _load_hld(builder: RegistryBuilder) -> None:
    """Load hard-coded HLD entities from high-level-design docs."""
    hld_dir = SRC_ROOT / "high-level-design"
    for md_file in sorted(hld_dir.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8-sig")
        if "Context" in content:
            for eid, name, aliases in [
                ("sdlc-visualizer", "SDLC Visualizer", ["Arsitect 可视化驾驶舱", "Pg_Viz"]),
                ("kimi-cli", "Kimi CLI", ["AI Skill 执行器", "Pg_Kimi"]),
                ("openui-service", "OpenUI Service", ["OpenUI Docker", "Pg_OpenUI"]),
                ("git", "Git", ["产物版本管理", "Pg_Git"]),
                ("local-filesystem", "本地文件系统", ["openspec/changes/", "Pg_FS"]),
            ]:
                builder.add_system(eid, name, aliases)
            builder.add_actor("developer", "超级个体", ["独立开发者", "Tech Lead", "Pg_User"])

        if "Container" in content:
            for eid, name, aliases in [
                ("frontend-spa", "React 19 SPA", ["Frontend", "前端", "Pg_SPA", "SPA"]),
                ("backend-api", "FastAPI", ["REST API", "REST API + SSE", "Pg_API"]),
                ("skill-orchestrator", "Skill Orchestrator", ["PocketFlow 三阶段调度", "编排引擎", "Pg_Orchestrator"]),
                ("c4-dsl-engine", "C4 DSL Engine", ["自研解析渲染", "Pg_C4Engine"]),
                ("wireframe-engine", "WireframeEngine", ["领域感知线框", "Pg_Wireframe"]),
                ("sqlite-db", "SQLite", ["元数据与状态", "Pg_SQLite"]),
                ("git-repo", "Git 仓库", ["每项目独立 .git", "Pg_GitLocal"]),
                ("artifact-store", "产物目录", ["openspec/changes/", "Pg_Artifacts"]),
                ("kimi-cli-process", "Kimi CLI", ["子进程 STDIO", "Pg_KimiCLI"]),
                ("openui-docker", "OpenUI Docker", ["HTTP :7878", "Pg_OpenUI_Docker"]),
            ]:
                builder.add_container(eid, name, aliases)

        if "Component" in content:
            for eid, name, aliases, container in [
                ("project-api", "Project API", ["项目 / 应用 / 模块 CRUD", "Pg_ProjectAPI"], "backend-api"),
                ("canvas-api", "Canvas API", ["节点 / 边 / 布局", "Pg_CanvasAPI"], "backend-api"),
                ("skill-api", "Skill API", ["导入 / 解析 / 执行", "Pg_SkillAPI"], "backend-api"),
                ("artifact-api", "Artifact API", ["产物 / 版本 / diff", "Pg_ArtifactAPI"], "backend-api"),
                ("gate-api", "Gate API", ["审批 / 摘要 / 历史", "Pg_GateAPI"], "backend-api"),
                ("c4-api", "C4 API", ["DSL / 渲染 / 导出", "Pg_C4API"], "c4-dsl-engine"),
                ("prototype-api", "Prototype API", ["OpenUI / Wireframe", "Pg_ProtoAPI"], "wireframe-engine"),
                ("project-service", "Project Service", ["双态管理 / Timebox", "Pg_ProjectSvc"], "backend-api"),
                ("orchestrator-service", "Orchestrator Service", ["DAG 调度 / 并行执行", "Pg_OrcheSvc"], "skill-orchestrator"),
                ("skill-service", "Skill Service", ["CLI 适配 / 日志捕获", "Pg_SkillSvc"], "backend-api"),
                ("artifact-service", "Artifact Service", ["Git 快照 / 冲突检测", "Pg_ArtifactSvc"], "backend-api"),
                ("gate-service", "Gate Service", ["自检摘要 / HITL", "Pg_GateSvc"], "backend-api"),
                ("size-estimate-service", "SizeEstimate Service", ["五维度评估 / 路由", "Pg_SizeSvc"], "backend-api"),
                ("c4-service", "C4 Service", ["DSL 生成 / 层级穿透", "Pg_C4Svc"], "c4-dsl-engine"),
                ("prototype-service", "Prototype Service", ["OpenUI 适配 / Wireframe", "Pg_ProtoSvc"], "wireframe-engine"),
                ("db-repository", "Repository", ["SQLAlchemy 2.0", "Pg_DBRepo"], "backend-api"),
                ("file-repository", "File Repository", ["本地文件系统", "Pg_FileRepo"], "backend-api"),
                ("git-repository", "Git Repository", ["GitPython", "Pg_GitRepo"], "backend-api"),
                ("cli-adapter", "CLI Adapter", ["Kimi STDIO", "Pg_CLIAdapter"], "skill-orchestrator"),
                ("sse-manager", "SSE Manager", ["事件推送", "Pg_SSEMgr"], "frontend-spa"),
            ]:
                builder.add_component(eid, name, aliases, container_id=container, source="doc")


def _load_hld_relationships(builder: RegistryBuilder) -> None:
    """Load hard-coded high-level relationships."""
    pairs = [
        ("developer", "sdlc-visualizer", "浏览 / 执行 / 审批"),
        ("sdlc-visualizer", "kimi-cli", "子进程 STDIO JSON Lines"),
        ("sdlc-visualizer", "openui-service", "HTTP API 原型渲染"),
        ("sdlc-visualizer", "git", "GitPython / simple-git"),
        ("sdlc-visualizer", "local-filesystem", "读写产物文件"),
        ("kimi-cli", "local-filesystem", "写产物文件"),
        ("git", "local-filesystem", "版本快照"),
        ("frontend-spa", "backend-api", "REST + SSE"),
        ("backend-api", "sqlite-db", "SQLAlchemy 2.0 AsyncSession"),
        ("backend-api", "skill-orchestrator", "调度"),
        ("backend-api", "c4-dsl-engine", "调用"),
        ("backend-api", "wireframe-engine", "调用"),
        ("skill-orchestrator", "kimi-cli-process", "subprocess JSON Lines"),
        ("skill-orchestrator", "git-repo", "GitPython"),
        ("backend-api", "artifact-store", "文件读写"),
        ("c4-dsl-engine", "artifact-store", "读取 / 写入"),
        ("wireframe-engine", "artifact-store", "读取"),
        ("frontend-spa", "openui-docker", "iframe / HTTP"),
        ("kimi-cli-process", "artifact-store", "写产物"),
        ("git-repo", "artifact-store", "版本快照"),
        ("project-api", "project-service", ""),
        ("canvas-api", "orchestrator-service", ""),
        ("skill-api", "skill-service", ""),
        ("artifact-api", "artifact-service", ""),
        ("gate-api", "gate-service", ""),
        ("c4-api", "c4-service", ""),
        ("prototype-api", "prototype-service", ""),
        ("project-service", "db-repository", ""),
        ("orchestrator-service", "db-repository", ""),
        ("orchestrator-service", "cli-adapter", ""),
        ("skill-service", "cli-adapter", ""),
        ("skill-service", "db-repository", ""),
        ("artifact-service", "file-repository", ""),
        ("artifact-service", "git-repository", ""),
        ("artifact-service", "db-repository", ""),
        ("gate-service", "db-repository", ""),
        ("gate-service", "sse-manager", ""),
        ("size-estimate-service", "db-repository", ""),
        ("c4-service", "file-repository", ""),
        ("prototype-service", "file-repository", ""),
        ("prototype-service", "openui-docker", "HTTP"),
        ("skill-orchestrator", "skill-service", "执行计划"),
        ("prototype-service", "c4-service", "接口缺失时回退"),
    ]
    for src, tgt, desc in pairs:
        builder.add_relationship(src, tgt, desc)


def _load_detailed_design(builder: RegistryBuilder) -> None:
    """Extract components and dependency-table relationships from DD docs."""
    dd_dir = SRC_ROOT / "detailed-design"
    for md_file in sorted(dd_dir.rglob("*.md")):
        # Skip audit / scratch / private notes.
        if md_file.name.startswith("_"):
            continue
        content = md_file.read_text(encoding="utf-8-sig")

        for cls in extract_python_classes(content):
            container = _infer_container_from_name(cls, md_file)
            builder.add_component(
                _slug_id(cls),
                cls,
                aliases=[cls],
                container_id=container,
                source="doc",
                source_file=str(md_file.relative_to(_PROJECT_ROOT).as_posix()),
            )

        # React components are taken from the actual source code; DD docs list many
        # planned UI primitives that never materialised and become orphan nodes.
        # We still map them if a code component with the same canonical key exists.
        for comp in extract_react_components(content):
            canon = _canonical_key(comp)
            if canon in builder._canonical_to_id:
                eid = builder._canonical_to_id[canon]
                builder.components[eid]["aliases"] = list(
                    {*builder.components[eid].get("aliases", []), comp}
                )
            # Otherwise intentionally skip to avoid design-only orphan primitives.

        for node_id, label, _ in extract_mermaid_nodes(content):
            if label.lower() in _GENERIC_LABELS:
                continue
            eid = _slug_id(label.split()[0] if " " in label else label)
            if eid in _GENERIC_IDS or eid.startswith("dr-") or re.fullmatch(r"p\d+", eid):
                continue
            container = _infer_container_from_name(label, md_file)
            builder.add_component(
                eid,
                label,
                aliases=[node_id, label],
                container_id=container,
                source="doc",
                source_file=str(md_file.relative_to(_PROJECT_ROOT).as_posix()),
            )

        for src, tgt, desc in extract_dependency_tables(content):
            src_id = builder.resolve(src)
            tgt_id = builder.resolve(tgt)
            if src_id and tgt_id:
                builder.add_relationship(src_id, tgt_id, desc)


def _load_interfaces(builder: RegistryBuilder) -> None:
    """Load API interfaces from interface-contracts and DD docs."""
    seen: set[tuple[str, str]] = set()
    for dir_path in (SRC_ROOT / "interface-contracts", SRC_ROOT / "detailed-design"):
        for md_file in sorted(dir_path.rglob("*.md")):
            if md_file.name.startswith("_"):
                continue
            content = md_file.read_text(encoding="utf-8-sig")
            for method, path in extract_api_endpoints(content):
                if (method, path) in seen:
                    continue
                seen.add((method, path))
                iid = _slug_id(f"{method}-{path.replace('/', '-').replace('{', '').replace('}', '')}")
                source_container = _infer_api_container_from_path(path)
                builder.add_interface(iid, method, path, source_container=source_container)


_DOMAIN_TO_API = {
    "projects": "project-api",
    "applications": "project-api",
    "user-stories": "project-api",
    "stages": "canvas-api",
    "canvas-state": "canvas-api",
    "templates": "canvas-api",
    "annotations": "canvas-api",
    "binding": "canvas-api",
    "skills": "skill-api",
    "skill-executions": "skill-api",
    "executions": "skill-api",
    "pocketflow": "skill-orchestrator",
    "scheduler": "skill-orchestrator",
    "artifacts": "artifact-api",
    "gate-decisions": "gate-api",
    "bypass": "gate-api",
    "c4": "c4-api",
    "render-state": "c4-api",
    "open-ui": "prototype-api",
    "wireframe": "prototype-api",
    "sketch": "prototype-api",
    "sketch-page": "prototype-api",
    "complexity": "backend-api",
    "monitoring": "backend-api",
    "arch-validation": "backend-api",
    "governance": "backend-api",
    "validation": "backend-api",
    "docforge-admin": "backend-api",
    "contracts": "backend-api",
    "locator": "backend-api",
    "advanced": "backend-api",
    "history": "backend-api",
    "engine": "skill-orchestrator",
}


def _infer_api_container_from_path(path: str) -> str | None:
    """Map an API path like /api/v1/projects to its owning HLD API component."""
    parts = [p for p in path.split("/") if p]
    for part in parts:
        if part in _DOMAIN_TO_API:
            return _DOMAIN_TO_API[part]
    return None


def _merge_code_entities(
    builder: RegistryBuilder,
    code_entities: dict[str, dict[str, Any]],
) -> None:
    """Merge code-scanned entities into the registry, marking them implemented."""
    for _canon, info in code_entities.items():
        eid = _slug_id(info["name"])
        builder.add_component(
            eid,
            info["name"],
            aliases=[info["name"]],
            container_id=info.get("container_id"),
            source="code",
            source_file=info.get("file"),
            kind=info.get("kind"),
        )


def _service_module_from_frontend_path(src_path: str) -> tuple[str, str] | None:
    """If import path points to a frontend service module, return (eid, name)."""
    if "/services/" not in src_path.replace("\\", "/") and not src_path.endswith("/services"):
        return None
    # Resolve path stem, handling relative '../services/project' or './services/project'.
    stem = Path(src_path).name
    if not stem or stem in ("api", "index"):
        return None
    name = f"{_camelize(stem)}Api"
    return _canonical_key(name), name


def _add_code_relationships(
    builder: RegistryBuilder,
    imports: list[tuple[str, str, str, str, str | None]],
) -> None:
    """Turn import edges into C4 relationships with domain-aware filtering."""
    from collections import defaultdict

    # Map source file paths to the entities defined in them. This lets us
    # connect imports whose imported name does not match a registry entity
    # (e.g. a service function imported from a service-module file).
    file_to_entities: dict[str, list[str]] = defaultdict(list)
    for cid, info in builder.components.items():
        sf = info.get("source_file") or info.get("source_code_file")
        if sf:
            file_to_entities[sf].append(cid)

    for src_id, tgt_id, _imp_name, import_path, resolved_file in imports:
        src_final = builder._canonical_to_id.get(src_id)
        if not src_final or src_final not in builder.components:
            continue

        target_ids: list[str] = []
        tgt_final = builder._canonical_to_id.get(tgt_id)
        if tgt_final:
            target_ids.append(tgt_final)
        elif resolved_file:
            for cand_id in file_to_entities.get(resolved_file, []):
                if cand_id != src_final:
                    target_ids.append(cand_id)

        # Fallback for frontend service modules imported by path but not yet
        # resolved to a file entity.
        if not target_ids and import_path:
            module_hint = _service_module_from_frontend_path(import_path)
            if module_hint:
                mod_canon, mod_name = module_hint
                mod_id = builder._canonical_to_id.get(mod_canon)
                if not mod_id:
                    mod_id = builder.ensure_component(
                        _slug_id(mod_name), mod_name, "frontend-spa", kind="service-module"
                    )
                if mod_id != src_final:
                    target_ids.append(mod_id)

        for tgt_final in target_ids:
            if tgt_final not in builder.components:
                continue

            src_info = builder.components[src_final]
            tgt_info = builder.components[tgt_final]
            src_name = src_info["name"]
            tgt_name = tgt_info["name"]
            src_cont = src_info.get("container_id")
            tgt_cont = tgt_info.get("container_id")

            # Router -> Service
            if (
                src_info.get("kind") == "router"
                or src_name.endswith("Router")
                or src_name.endswith("API")
            ) and tgt_name.endswith(("Service", "Manager", "Engine", "Adapter", "Store")):
                builder.add_relationship(src_final, tgt_final, "调用")
                continue

            # Service -> Repository
            if src_name.endswith("Service") and tgt_name.endswith("Repository"):
                builder.add_relationship(src_final, tgt_final, "持久化/查询")
                continue

            # Service -> Service / Manager / Adapter / Engine / Store
            if src_name.endswith("Service") and tgt_name.endswith((
                "Service", "Manager", "Adapter", "Engine", "Store", "Handler", "Worker"
            )):
                builder.add_relationship(src_final, tgt_final, "调用")
                continue

            # Manager -> Service / Repository / Engine
            if src_name.endswith("Manager") and tgt_name.endswith((
                "Service", "Repository", "Engine", "Adapter", "Store"
            )):
                builder.add_relationship(src_final, tgt_final, "调用")
                continue

            # Frontend Component -> Store
            if src_cont == "frontend-spa" and tgt_name.endswith("Store"):
                builder.add_relationship(src_final, tgt_final, "状态订阅")
                continue

            # Frontend Component / Store -> Service module
            if src_cont == "frontend-spa" and tgt_info.get("kind") == "service-module":
                builder.add_relationship(src_final, tgt_final, "调用")
                continue

            # Frontend composition
            if src_cont == "frontend-spa" and tgt_cont == "frontend-spa":
                builder.add_relationship(src_final, tgt_final, "包含/渲染")
                continue

            # Generic backend / engine / orchestrator dependency
            if src_cont not in ("frontend-spa", None) and tgt_cont not in ("frontend-spa", None):
                builder.add_relationship(src_final, tgt_final, "依赖")


def _heal_service_repository_pairs(builder: RegistryBuilder) -> None:
    """Add obvious Service -> Repository edges that import-scan missed."""
    services = {
        eid: info
        for eid, info in builder.components.items()
        if info["name"].endswith("Service")
    }
    repos = {
        eid: info
        for eid, info in builder.components.items()
        if info["name"].endswith("Repository")
    }
    for sid, sinfo in services.items():
        sname = sinfo["name"]
        stem = sname[:-7].lower()
        for rid, rinfo in repos.items():
            rname = rinfo["name"]
            rstem = rname[:-10].lower()
            if not rstem:
                continue
            # Exact stem match, or repository contains service stem, or vice versa.
            if (
                stem == rstem
                or stem in rstem
                or rstem in stem
            ):
                builder.add_relationship(sid, rid, "持久化/查询")


def _bind_routers_to_apis(builder: RegistryBuilder) -> None:
    """Connect code-level API routers back to HLD coarse API components or containers."""
    for eid, info in builder.components.items():
        if info.get("kind") != "router":
            continue
        name = info["name"]
        stem = name[:-6].lower() if name.endswith("Router") else name.lower()
        # Try direct domain mapping or name contains domain.
        mapped = _DOMAIN_TO_API.get(stem)
        if not mapped:
            for domain, api_id in _DOMAIN_TO_API.items():
                if domain.replace("-", "") in stem or stem in domain.replace("-", ""):
                    mapped = api_id
                    break
        if mapped and (mapped in builder.components or mapped in builder.containers):
            builder.add_relationship(mapped, eid, "由...实现")


def _mark_intentional_orphans(builder: RegistryBuilder) -> None:
    """Flag leaf utilities that are intentionally standalone."""
    connected = set()
    for r in builder.relationships:
        connected.add(r["source"])
        connected.add(r["target"])
    for eid, info in builder.components.items():
        if eid in connected:
            continue
        if eid in _INTENTIONAL_ORPHAN_IDS:
            info["intentional_orphan"] = True
            continue
        name = info["name"]
        src_files = " ".join(
            f for f in (info.get("source_file"), info.get("source_code_file")) if f
        )
        path_lower = src_files.lower()
        # Frontend state containers / renderers / service stubs that nothing uses.
        if info.get("container_id") == "frontend-spa":
            if info.get("kind") in ("service-module", "store") or any(
                name.lower().endswith(s)
                for s in (
                    "button", "input", "badge", "popover", "mask", "handle", "layer",
                    "view", "panel", "overlay", "card", "item", "state", "directions",
                    "header", "steps", "menu", "menuitem", "tab", "row", "btn", "block",
                    "path", "tag", "chip", "icon", "avatar", "divider", "spacer",
                )
            ) or name.lower() in {"react", "app"}:
                info["intentional_orphan"] = True
            continue
        # Backend cross-cutting helpers that do not depend on registry entities
        # and are not depended upon by anyone.
        backend_util_suffixes = (
            "Manager", "Handler", "Adapter", "Controller", "Router",
            "Engine", "Worker", "Producer", "Consumer",
            "Validator", "Resolver", "Generator", "Calculator", "Aggregator", "Collector",
        )
        # Cross-cutting utilities or implemented algorithmic helpers with no dependents.
        has_code_file = "/services/" in path_lower or "/c4/" in path_lower or any(
            frag in path_lower for frag in ("advanced", "common", "governance", "docforge")
        )
        if name.endswith(backend_util_suffixes) and has_code_file:
            info["intentional_orphan"] = True


def build_registry() -> dict[str, Any]:
    """Build the full C4 registry."""
    builder = RegistryBuilder()

    _load_hld(builder)
    _load_hld_relationships(builder)
    _load_detailed_design(builder)
    _load_interfaces(builder)

    backend_entities, backend_imports = scan_backend_code(BACKEND_ROOT)
    frontend_entities, frontend_imports = scan_frontend_code(FRONTEND_ROOT)

    _merge_code_entities(builder, backend_entities)
    _merge_code_entities(builder, frontend_entities)

    _add_code_relationships(builder, backend_imports)
    _add_code_relationships(builder, frontend_imports)

    # Fallback heuristics
    _heal_service_repository_pairs(builder)
    _bind_routers_to_apis(builder)
    _mark_intentional_orphans(builder)

    return builder.to_dict()


def main() -> None:
    """Entry point: regenerate registry file."""
    registry = build_registry()
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REGISTRY_PATH.open("w", encoding="utf-8") as f:
        yaml.dump(registry, f, allow_unicode=True, sort_keys=False, width=120)
    print(f"C4 registry written to {REGISTRY_PATH}")
    print(f"  Systems:    {len(registry['systems'])}")
    print(f"  Actors:     {len(registry['actors'])}")
    print(f"  Containers: {len(registry['containers'])}")
    print(f"  Components: {len(registry['components'])}")
    print(f"  Interfaces: {len(registry['interfaces'])}")
    print(f"  Relationships: {len(registry['relationships'])}")


if __name__ == "__main__":
    main()
