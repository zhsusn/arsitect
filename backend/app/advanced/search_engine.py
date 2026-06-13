"""SearchEngine — project-wide content search."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import yaml

from app.c4.baseline_store import C4BaselineStore
from app.common.project_context import ProjectContext
from app.docforge.fragment_registry import FragmentRegistry


@dataclass
class SearchResult:
    """Single search result."""

    type: str
    id: str
    title: str
    preview: str
    path: str
    score: float


class SearchEngine:
    """Search engine.

    Responsibilities:
    1. Search artifact filenames and contents.
    2. Search C4 nodes.
    3. Search document fragments.

    MVP uses linear scan; P1 can be replaced with Elasticsearch.
    """

    PREVIEW_LENGTH = 200

    def __init__(
        self,
        fragment_registry: FragmentRegistry,
        baseline_store: C4BaselineStore,
    ) -> None:
        """Initialize with registries."""
        self.fragments = fragment_registry
        self.baseline = baseline_store

    async def search(
        self,
        project_id: str,
        query: str,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search across artifacts, C4 nodes and fragments."""
        results: list[SearchResult] = []
        query_lower = query.lower()
        filters = filters or {}

        if filters.get("type") in (None, "artifact"):
            results.extend(await self._search_artifacts(project_id, query_lower))
        if filters.get("type") in (None, "c4"):
            results.extend(await self._search_c4(project_id, query_lower))
        if filters.get("type") in (None, "fragment"):
            results.extend(await self._search_fragments(project_id, query_lower))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:50]

    async def _search_artifacts(self, project_id: str, query: str) -> list[SearchResult]:
        """Search artifact files."""
        results: list[SearchResult] = []
        with ProjectContext(project_id) as ctx:
            if not ctx.artifacts_dir.exists():
                return results
            for path in ctx.artifacts_dir.rglob("*"):
                if not path.is_file():
                    continue
                relative = str(path.relative_to(ctx.artifacts_dir))
                name_match = query in relative.lower()
                try:
                    content = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    content = ""
                content_match = query in content.lower()
                if not name_match and not content_match:
                    continue

                preview = relative
                if content_match:
                    idx = content.lower().find(query)
                    start = max(0, idx - self.PREVIEW_LENGTH // 2)
                    preview = content[start : start + self.PREVIEW_LENGTH]

                score = 1.0 if name_match else 0.7
                results.append(
                    SearchResult(
                        type="artifact",
                        id=relative,
                        title=relative,
                        preview=preview,
                        path=f"/artifacts/{relative}?project_id={project_id}",
                        score=score,
                    )
                )
        return results

    async def _search_c4(self, project_id: str, query: str) -> list[SearchResult]:
        """Search C4 containers and components."""
        results: list[SearchResult] = []
        baseline = await self.baseline.read_current(project_id)
        if baseline is None:
            return results

        try:
            data = yaml.safe_load(baseline.dsl_content or "") or {}
        except yaml.YAMLError:
            return results

        model = data.get("workspace", {}).get("model", {})
        for container in model.get("containers", []):
            name = container.get("name", "")
            cid = container.get("id", "")
            if query in name.lower() or query in cid.lower():
                results.append(
                    SearchResult(
                        type="c4_node",
                        id=cid,
                        title=f"Container: {name or cid}",
                        preview=f"Technology: {container.get('technology', 'N/A')}",
                        path=f"/c4?node={cid}&project_id={project_id}",
                        score=1.0,
                    )
                )
        for component in model.get("components", []):
            name = component.get("name", "")
            cid = component.get("id", "")
            if query in name.lower() or query in cid.lower():
                results.append(
                    SearchResult(
                        type="c4_node",
                        id=cid,
                        title=f"Component: {name or cid}",
                        preview="",
                        path=f"/c4?node={cid}&project_id={project_id}",
                        score=1.0,
                    )
                )
        return results

    async def _search_fragments(self, project_id: str, query: str) -> list[SearchResult]:
        """Search document fragments."""
        results: list[SearchResult] = []
        fragments = await self.fragments.list_by_project(project_id)
        for frag in fragments:
            title_match = query in frag.title.lower()
            content_match = query in frag.content.lower()
            if not title_match and not content_match:
                continue
            score = 1.0 if title_match else 0.5
            preview = frag.content[: self.PREVIEW_LENGTH]
            results.append(
                SearchResult(
                    type="fragment",
                    id=frag.fragment_id,
                    title=frag.title,
                    preview=preview,
                    path=f"/documents/{frag.fragment_id}",
                    score=score,
                )
            )
        return results
