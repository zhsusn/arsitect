"""CodeScanner — lightweight code structure scanner.

Scans backend/frontend source directories and extracts:
- Python modules, classes, function names (from backend/app/)
- TypeScript/React components, pages, services (from frontend/src/)

Uses path-based heuristics + regex, NOT full AST parsing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.core.config import settings


@dataclass
class CodeEntity:
    """A discovered code entity."""

    id: str
    name: str
    type: str  # module | class | function | component | page | service | route
    file_path: str
    language: str  # python | typescript
    container_hint: str = ""  # e.g. "backend-api" from path


@dataclass
class CodeScanResult:
    """Result of scanning the codebase."""

    entities: list[CodeEntity] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entities": [
                {
                    "id": e.id,
                    "name": e.name,
                    "type": e.type,
                    "file_path": e.file_path,
                    "language": e.language,
                    "container_hint": e.container_hint,
                }
                for e in self.entities
            ],
            "summary": self.summary,
        }


class CodeScanner:
    """Scan project source code for structural entities."""

    # Regex patterns
    _PY_CLASS = re.compile(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)\s*[\(:]")
    _PY_FUNC = re.compile(r"^(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
    _PY_ROUTE = re.compile(r"@router\.(?:get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]")
    _TS_FUNC = re.compile(
        r"^(?:export\s+)?(?:async\s+)?(?:function|const)\s+([A-Z][a-zA-Z0-9_]*)\s*[\(:=]"
    )
    _TS_COMPONENT = re.compile(
        r"^(?:export\s+)?(?:default\s+)?(?:function|const)\s+([A-Z][a-zA-Z0-9_]*)\s*[\(:=]"
    )

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root or settings.project_root

    def scan(self) -> CodeScanResult:
        """Scan both backend and frontend code."""
        entities: list[CodeEntity] = []
        entities.extend(self._scan_backend())
        entities.extend(self._scan_frontend())
        summary: dict[str, int] = {}
        for e in entities:
            key = f"{e.language}:{e.type}"
            summary[key] = summary.get(key, 0) + 1
        return CodeScanResult(entities=entities, summary=summary)

    # ------------------------------------------------------------------
    # Backend (Python)
    # ------------------------------------------------------------------

    def _scan_backend(self) -> list[CodeEntity]:
        entities: list[CodeEntity] = []
        backend = self.project_root / "backend" / "app"
        if not backend.exists():
            return entities

        for py_file in backend.rglob("*.py"):
            if py_file.name.startswith("test_") or py_file.name.endswith("_test.py"):
                continue
            rel = py_file.relative_to(backend).as_posix()
            # Module-level entity
            module_name = rel.replace("/", ".").replace(".py", "")
            container = self._infer_container_from_path(rel)
            entities.append(
                CodeEntity(
                    id=f"py:{module_name}",
                    name=module_name,
                    type="module",
                    file_path=rel,
                    language="python",
                    container_hint=container,
                )
            )
            try:
                content = py_file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                content = py_file.read_text(encoding="utf-8", errors="replace")
            for match in self._PY_CLASS.finditer(content):
                cls_name = match.group(1)
                entities.append(
                    CodeEntity(
                        id=f"py:{module_name}.{cls_name}",
                        name=cls_name,
                        type="class",
                        file_path=rel,
                        language="python",
                        container_hint=container,
                    )
                )
            for match in self._PY_FUNC.finditer(content):
                func_name = match.group(1)
                if func_name.startswith("_"):
                    continue
                entities.append(
                    CodeEntity(
                        id=f"py:{module_name}.{func_name}",
                        name=func_name,
                        type="function",
                        file_path=rel,
                        language="python",
                        container_hint=container,
                    )
                )
            for match in self._PY_ROUTE.finditer(content):
                route = match.group(1)
                entities.append(
                    CodeEntity(
                        id=f"py:route:{route}",
                        name=route,
                        type="route",
                        file_path=rel,
                        language="python",
                        container_hint=container,
                    )
                )
        return entities

    # ------------------------------------------------------------------
    # Frontend (TypeScript/React)
    # ------------------------------------------------------------------

    def _scan_frontend(self) -> list[CodeEntity]:
        entities: list[CodeEntity] = []
        frontend = self.project_root / "frontend" / "src"
        if not frontend.exists():
            return entities

        for ts_file in frontend.rglob("*.ts"):
            if ts_file.name.endswith(".d.ts"):
                continue
            rel = ts_file.relative_to(frontend).as_posix()
            container = self._infer_container_from_path(rel)
            module_name = rel.replace("/", ".").replace(".ts", "")
            try:
                content = ts_file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                content = ts_file.read_text(encoding="utf-8", errors="replace")
            for match in self._TS_FUNC.finditer(content):
                name = match.group(1)
                if name.startswith("_") or name in ("useEffect", "useState", "useCallback"):
                    continue
                entities.append(
                    CodeEntity(
                        id=f"ts:{module_name}.{name}",
                        name=name,
                        type="function",
                        file_path=rel,
                        language="typescript",
                        container_hint=container,
                    )
                )

        for tsx_file in frontend.rglob("*.tsx"):
            rel = tsx_file.relative_to(frontend).as_posix()
            container = self._infer_container_from_path(rel)
            module_name = rel.replace("/", ".").replace(".tsx", "")
            try:
                content = tsx_file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                content = tsx_file.read_text(encoding="utf-8", errors="replace")
            # Heuristic: capitalized export = component
            for match in self._TS_COMPONENT.finditer(content):
                name = match.group(1)
                if name.startswith("_") or name in ("App", "Root"):
                    continue
                is_page = "/pages/" in rel or "/views/" in rel
                is_service = "/services/" in rel or "/api/" in rel
                entity_type = "page" if is_page else ("service" if is_service else "component")
                entities.append(
                    CodeEntity(
                        id=f"ts:{module_name}.{name}",
                        name=name,
                        type=entity_type,
                        file_path=rel,
                        language="typescript",
                        container_hint=container,
                    )
                )
            # File-level component if filename matches PascalCase
            stem = tsx_file.stem
            if stem[0].isupper() and stem not in ("App", "Root"):
                is_page = "/pages/" in rel or "/views/" in rel
                is_service = "/services/" in rel or "/api/" in rel
                entity_type = "page" if is_page else ("service" if is_service else "component")
                if not any(e.name == stem for e in entities if e.file_path == rel):
                    entities.append(
                        CodeEntity(
                            id=f"ts:{module_name}.{stem}",
                            name=stem,
                            type=entity_type,
                            file_path=rel,
                            language="typescript",
                            container_hint=container,
                        )
                    )
        return entities

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _infer_container_from_path(rel_path: str) -> str:
        """Infer C4 container name from file path.

        Examples:
            backend/app/api/v1/c4.py -> backend-api
            backend/app/services/arch_validation_service.py -> backend-api
            frontend/src/components/C4Renderer.tsx -> frontend-spa
            frontend/src/pages/C4Navigator/index.tsx -> frontend-spa
        """
        parts = rel_path.lower().split("/")
        if "backend" in parts or parts[0] == "app":
            return "backend-api"
        if "frontend" in parts:
            return "frontend-spa"
        if "c4" in parts:
            return "c4-dsl-engine"
        if "wireframe" in parts or "sketch" in parts:
            return "wireframe-engine"
        if "skill" in parts or "execution" in parts:
            return "skill-orchestrator"
        return ""
