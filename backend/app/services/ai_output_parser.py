"""Parser for LLM-generated fix output.

Extracts file changes from the ``=== FILE: path ===```lang\n...\n`````
blocks described in ``docs/aiclient.txt``. If no block is found, the entire
output is treated as the content of the primary target file.
"""

from __future__ import annotations

import re
from typing import Any


class AIOutputParser:
    """Parse AI fix output into a mapping of file paths to content."""

    # Match === FILE: path === followed by a fenced code block.
    _FILE_BLOCK_RE = re.compile(
        r"===\s*FILE:\s*(.+?)\s*===\s*"
        r"```(?:[a-zA-Z0-9_+-]*)\n"
        r"([\s\S]*?)"
        r"```",
        re.MULTILINE,
    )

    @classmethod
    def parse_file_changes(
        cls,
        output: str,
        fallback_target: str | None = None,
    ) -> dict[str, str]:
        """Extract file changes from AI output.

        Args:
            output: Raw LLM output.
            fallback_target: Path used when no ``=== FILE:`` block is found.

        Returns:
            Mapping from relative file path to file content.
        """
        changes: dict[str, str] = {}
        for match in cls._FILE_BLOCK_RE.finditer(output):
            file_path = match.group(1).strip()
            content = match.group(2).rstrip("\n")
            if file_path:
                changes[file_path] = content

        if not changes and fallback_target:
            stripped = output.strip()
            if stripped:
                changes[fallback_target] = stripped

        return changes

    @classmethod
    def parse_sections(cls, output: str) -> dict[str, Any]:
        """Parse root cause and strategy sections when present.

        Args:
            output: Raw LLM output.

        Returns:
            Dict with optional ``root_cause`` and ``strategy`` keys.
        """
        root_cause = ""
        strategy = ""

        root_match = re.search(
            r"根因分析[：:]\s*(.+?)(?=\n\n|\n【|$)",
            output,
            re.DOTALL,
        )
        if root_match:
            root_cause = " ".join(root_match.group(1).split())

        strategy_match = re.search(
            r"修复策略(?:说明)?[：:]\s*(.+?)(?=\n\n|\n【|$)",
            output,
            re.DOTALL,
        )
        if strategy_match:
            strategy = " ".join(strategy_match.group(1).split())

        return {
            "root_cause": root_cause,
            "strategy": strategy,
        }
