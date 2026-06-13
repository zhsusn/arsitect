"""StructuredExtractor — deterministic rule-based C4 tag extraction."""

from __future__ import annotations

import re

import yaml

from app.docforge.schemas.extraction_schemas import C4Snippet


class StructuredExtractor:
    """Rule-based extractor for @C4- tags (confidence = 1.0).

    Supports 20 standard extraction rules:
    - YAML Front Matter: c4_binding block
    - Section anchors: ## Title {#anchor}
    - @C4-System, @C4-Actor, @C4-Container, @C4-Component, etc.
    - @C4-Interface:METHOD /path
    """

    RULES = {
        "frontmatter": re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL),
        "section_anchor": re.compile(
            r"^(#{1,6})\s+(.+?)\s*\{ #([a-zA-Z0-9_-]+)\}\s*$", re.MULTILINE
        ),
        "c4_tag": re.compile(r"@C4-([A-Za-z0-9-]+):([^\s\n,;]+)"),
        "interface_def": re.compile(
            r"@C4-Interface:(GET|POST|PUT|PATCH|DELETE)\s+(\S+)"
        ),
    }

    TAG_TO_ELEMENT: dict[str, str] = {
        "System": "System",
        "Actor": "Actor",
        "External-System": "ExternalSystem",
        "Container": "Container",
        "Component": "Component",
        "Entity": "Entity",
        "Relationship": "Relationship",
        "Interface": "Interface",
        "Technology": "Technology",
        "Code-Path": "CodePath",
        "Table": "Table",
        "Column": "Column",
        "Method": "Method",
        "Attribute": "Attribute",
        "Page-Type": "PageType",
    }

    def extract(self, content: str, doc_type: str) -> list[C4Snippet]:
        """Extract C4 structured data from document.

        Args:
            content: Full document text.
            doc_type: PRD / DOMAIN_MODEL / ARCH / DETAIL_DESIGN / API_DESIGN /
                DB_DESIGN.

        Returns:
            List of C4Snippet with confidence=1.0.
        """
        snippets: list[C4Snippet] = []
        snippets.extend(self._extract_from_frontmatter(content))
        snippets.extend(self._extract_c4_tags(content))
        snippets.extend(self._extract_interfaces(content))
        self._extract_section_anchors(content)
        return snippets

    def _extract_from_frontmatter(self, content: str) -> list[C4Snippet]:
        snippets: list[C4Snippet] = []
        match = self.RULES["frontmatter"].search(content)
        if not match:
            return snippets
        try:
            fm = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            return snippets

        if not fm or "c4_binding" not in fm:
            return snippets

        binding = fm["c4_binding"]
        if isinstance(binding, dict) and "system_id" in binding:
            snippets.append(
                C4Snippet(
                    element_type="binding_reference",
                    element_id=binding["system_id"],
                    name=binding.get("system_name", binding["system_id"]),
                    properties=dict(binding),
                    source_location="frontmatter.c4_binding",
                )
            )
        return snippets

    def _extract_c4_tags(self, content: str) -> list[C4Snippet]:
        snippets: list[C4Snippet] = []
        for match in self.RULES["c4_tag"].finditer(content):
            tag_type = match.group(1)
            element_id = match.group(2)
            element_type = self.TAG_TO_ELEMENT.get(tag_type)
            if element_type:
                desc = self._extract_description(content, match.start())
                snippets.append(
                    C4Snippet(
                        element_type=element_type,
                        element_id=element_id,
                        name=element_id,
                        description=desc,
                        source_location=f"@{match.start()}",
                    )
                )
        return snippets

    def _extract_interfaces(self, content: str) -> list[C4Snippet]:
        snippets: list[C4Snippet] = []
        for match in self.RULES["interface_def"].finditer(content):
            method = match.group(1)
            path = match.group(2)
            element_id = f"{method}_{path.replace('/', '_').strip('_')}"
            snippets.append(
                C4Snippet(
                    element_type="Interface",
                    element_id=element_id,
                    name=f"{method} {path}",
                    properties={"method": method, "path": path},
                    source_location=f"@{match.start()}",
                )
            )
        return snippets

    def _extract_section_anchors(self, content: str) -> dict[str, str]:
        anchors: dict[str, str] = {}
        for match in self.RULES["section_anchor"].finditer(content):
            anchor_id = match.group(3)
            title = match.group(2).strip()
            anchors[anchor_id] = title
        return anchors

    def _extract_description(
        self, content: str, position: int, max_chars: int = 200
    ) -> str:
        after = content[position : position + max_chars]
        lines = [line.strip() for line in after.split("\n") if line.strip()]
        if len(lines) > 1:
            return lines[1][:200]
        return ""

    def register_rule(self, name: str, pattern: re.Pattern[str]) -> None:
        """Register a new extraction rule."""
        self.RULES[name] = pattern

    def get_rules(self) -> dict[str, re.Pattern[str]]:
        """Return all rules."""
        return dict(self.RULES)
