"""StoryPathValidator — Validate user-story paths against requirement nav graphs.

Checks for:
1. Missing pages: a story mentions a page not found in any module spec.
2. Missing edges: a story implies a transition not defined in the nav graph.
3. Orphan pages: defined in specs but never reached by any story path.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.services.page_spec_resolver import ModuleSpec, PageSpec

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class PathGap:
    """A gap / inconsistency found during validation."""

    gap_type: str  # "missing_page" | "missing_edge" | "orphan_page" | "unreachable_page"
    story_id: str = ""
    story_title: str = ""
    page_name: str = ""
    from_page: str = ""
    to_page: str = ""
    detail: str = ""


@dataclass
class ValidationReport:
    """Result of story-path validation."""

    story_count: int = 0
    spec_page_count: int = 0
    covered_pages: set[str] = field(default_factory=set)
    missing_pages: list[PathGap] = field(default_factory=list)
    missing_edges: list[PathGap] = field(default_factory=list)
    orphan_pages: list[PathGap] = field(default_factory=list)
    coverage_percent: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "story_count": self.story_count,
            "spec_page_count": self.spec_page_count,
            "covered_pages": sorted(self.covered_pages),
            "missing_pages": [
                {"type": g.gap_type, "page": g.page_name, "detail": g.detail}
                for g in self.missing_pages
            ],
            "missing_edges": [
                {"type": g.gap_type, "from": g.from_page, "to": g.to_page, "detail": g.detail}
                for g in self.missing_edges
            ],
            "orphan_pages": [
                {"type": g.gap_type, "page": g.page_name, "detail": g.detail}
                for g in self.orphan_pages
            ],
            "coverage_percent": self.coverage_percent,
        }


# ---------------------------------------------------------------------------
# Path extraction from story page_desc
# ---------------------------------------------------------------------------


def _extract_page_mentions(text: str, all_page_names: set[str]) -> list[str]:
    """Extract ordered page mentions from story text."""
    mentions: list[tuple[int, str]] = []
    seen: set[str] = set()
    # Try to find exact page names first
    for page_name in sorted(all_page_names, key=len, reverse=True):
        if page_name in text and page_name not in seen:
            # Find all positions
            for m in re.finditer(re.escape(page_name), text):
                mentions.append((m.start(), page_name))
            seen.add(page_name)

    # Also look for URL-like mentions /projects, /canvas etc.
    for _page_name in all_page_names:
        # Heuristic: if page name contains route keywords
        pass

    mentions.sort(key=lambda x: x[0])
    return [m[1] for m in mentions]


def _extract_implied_transitions(text: str, page_names: set[str]) -> list[tuple[str, str]]:
    """Extract implied page transitions from story text.

    Only extracts forward transitions where two page names appear in order
    and are separated by a navigation keyword.
    """
    transitions: list[tuple[str, str]] = []
    nav_keywords = ["进入", "跳转到", "前往", "切换到", "打开", "到", "→", ">"]

    # Find all page mentions with positions
    mentions: list[tuple[int, str]] = []
    for name in page_names:
        start = 0
        while True:
            idx = text.find(name, start)
            if idx == -1:
                break
            mentions.append((idx, name))
            start = idx + len(name)

    mentions.sort(key=lambda x: x[0])

    # Only consider adjacent mentions in forward direction
    for i in range(len(mentions) - 1):
        _, src = mentions[i]
        _, tgt = mentions[i + 1]
        if src == tgt:
            continue
        between = text[mentions[i][0] + len(src) : mentions[i + 1][0]]
        if any(kw in between for kw in nav_keywords):
            transitions.append((src, tgt))

    return transitions


# ---------------------------------------------------------------------------
# Main validator
# ---------------------------------------------------------------------------


class StoryPathValidator:
    """Validate user story paths against requirement module specs."""

    def __init__(self, module_specs: list[ModuleSpec]) -> None:
        """Initialize with parsed module specs.

        Args:
            module_specs: All module specs for the project.
        """
        self._specs = module_specs
        self._all_pages: dict[str, PageSpec] = {}
        self._nav_edges: set[tuple[str, str]] = set()

        for mod in module_specs:
            for pg in mod.pages:
                self._all_pages[pg.page_name] = pg
            for edge in mod.nav_edges:
                self._nav_edges.add((edge.source, edge.target))

    def validate(
        self,
        stories: list[dict[str, Any]],
    ) -> ValidationReport:
        """Run validation against a list of user stories.

        Args:
            stories: Each dict should have 'story_id', 'title', 'page_desc'.

        Returns:
            ValidationReport with gaps and coverage stats.
        """
        report = ValidationReport()
        report.story_count = len(stories)
        report.spec_page_count = len(self._all_pages)
        all_page_names = set(self._all_pages.keys())

        covered: set[str] = set()
        implied_transitions: set[tuple[str, str]] = set()

        for story in stories:
            story_id = story.get("story_id", "")
            title = story.get("title", "")
            page_desc = story.get("page_desc", "") or ""
            text = f"{title}\n{page_desc}"

            # Extract page mentions
            mentions = _extract_page_mentions(text, all_page_names)
            covered.update(mentions)

            # Check missing pages (mentioned in story but not in specs)
            # Heuristic: look for capitalized phrases or quoted terms
            for unknown in self._find_unknown_pages(text, all_page_names):
                report.missing_pages.append(
                    PathGap(
                        gap_type="missing_page",
                        story_id=story_id,
                        story_title=title,
                        page_name=unknown,
                        detail=f"故事 '{title}' 提到了页面 '{unknown}'，但在详细需求中未找到定义",
                    )
                )

            # Extract implied transitions
            trans = _extract_implied_transitions(text, all_page_names)
            implied_transitions.update(trans)

        # Check missing edges
        for src, tgt in implied_transitions:
            if (src, tgt) not in self._nav_edges:
                # Try fuzzy match
                matched = self._fuzzy_edge_match(src, tgt)
                if not matched:
                    report.missing_edges.append(
                        PathGap(
                            gap_type="missing_edge",
                            from_page=src,
                            to_page=tgt,
                            detail=f"用户故事暗示了从 '{src}' 到 '{tgt}' 的跳转，但详细需求的导航图中未定义此路径",
                        )
                    )

        # Check orphan pages (in specs but not covered by any story)
        for name, _pg in self._all_pages.items():
            if name not in covered:
                report.orphan_pages.append(
                    PathGap(
                        gap_type="orphan_page",
                        page_name=name,
                        detail=f"页面 '{name}' 在详细需求中有定义，但未被任何用户故事覆盖",
                    )
                )

        report.covered_pages = covered
        if report.spec_page_count:
            report.coverage_percent = int(len(covered) / report.spec_page_count * 100)

        return report

    def _find_unknown_pages(self, text: str, known_pages: set[str]) -> list[str]:
        """Heuristic: find explicit page mentions that are not in known_pages.

        Only reports clearly quoted or book-titled page names to avoid
        false positives from natural language prose.
        """
        unknowns: list[str] = []
        # Look for quoted strings like "页面名称" or 《页面名称》
        for m in re.finditer(r'[""""]([^""""]{2,20})[""""]', text):
            candidate = m.group(1).strip()
            if candidate not in known_pages and "页面" in candidate:
                unknowns.append(candidate)
        for m in re.finditer(r"《([^《》]{2,20})》", text):
            candidate = m.group(1).strip()
            if candidate not in known_pages:
                unknowns.append(candidate)
        return unknowns

    def _fuzzy_edge_match(self, src: str, tgt: str) -> bool:
        """Check if there's a fuzzy match for an edge in the nav graph."""
        for e_src, e_tgt in self._nav_edges:
            if (src in e_src or e_src in src) and (tgt in e_tgt or e_tgt in tgt):
                return True
        return False


def validate_story_paths(
    module_specs: list[ModuleSpec],
    stories: list[dict[str, Any]],
) -> dict[str, Any]:
    """Convenience function: run validation and return dict."""
    validator = StoryPathValidator(module_specs)
    report = validator.validate(stories)
    return report.to_dict()
