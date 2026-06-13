"""Build rich context for governance fix strategies and LLM prompts."""

from __future__ import annotations

from typing import Any

import yaml
from sqlalchemy.ext.asyncio import AsyncSession

from app.c4.baseline_store import C4BaselineStore
from app.c4.code_scanner import CodeScanner
from app.c4.dsl_manager import C4DSLManager
from app.c4.registry_extractor import load_registry
from app.core.config import settings


class FixContextBuilder:
    """Assemble project context needed to plan a fix."""

    def __init__(self, project_id: str, db: AsyncSession) -> None:
        self.project_id = project_id
        self.db = db
        self.project_root = settings.project_root

    async def build(self) -> dict[str, Any]:
        """Return context dict.

        Contains:
        - workspace_model: parsed DSL model dict
        - registry: C4 registry dict
        - code_entities: list of CodeEntity dicts
        - doc_files: list of relative markdown paths under openspec/changes/{project}
        - project_root: Path
        """
        baseline_store = C4BaselineStore(self.db)
        dsl_manager = C4DSLManager(baseline_store)
        workspace = await dsl_manager.read_workspace(self.project_id)

        workspace_model: dict[str, Any] = {}
        if workspace:
            # Re-serialize the workspace to a plain dict for easier patching.
            workspace_model = self._workspace_to_dict(workspace)

        registry = load_registry(self.project_id) or {}
        code_entities = CodeScanner().scan().to_dict()["entities"]

        doc_files: list[str] = []
        doc_dir = self.project_root / "openspec" / "changes" / self.project_id
        if doc_dir.exists():
            doc_files = [
                str(p.relative_to(self.project_root).as_posix())
                for p in sorted(doc_dir.rglob("*.md"))
            ]

        return {
            "project_id": self.project_id,
            "project_root": self.project_root,
            "workspace_model": workspace_model,
            "registry": registry,
            "code_entities": code_entities,
            "doc_files": doc_files,
        }

    @staticmethod
    def _workspace_to_dict(workspace: Any) -> dict[str, Any]:
        """Convert C4Workspace to a plain dict matching DSL YAML structure."""
        # C4DSLManager parses YAML into C4Workspace; round-trip through YAML
        # to get a mutable dict without adding serialization logic.
        from app.docforge.c4_assembler import C4Assembler

        assembler = C4Assembler()
        dsl_text = assembler.serialize_to_yaml(workspace)
        return yaml.safe_load(dsl_text)
