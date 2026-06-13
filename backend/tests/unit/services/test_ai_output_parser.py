"""Tests for the AIOutputParser."""

from __future__ import annotations

from app.services.ai_output_parser import AIOutputParser


def test_parse_single_file_block() -> None:
    """TEST-1711: Parse a single === FILE: block."""
    output = """
根因分析：工具函数职责边界不清。
修复策略：提取公共逻辑到 common/utils.ts。

=== FILE: src/common/utils.ts ===
```typescript
export function sharedUtil() {
  return 42;
}
```

验证建议：运行现有单测。
"""
    changes = AIOutputParser.parse_file_changes(output, fallback_target="src/utils.ts")

    assert len(changes) == 1
    assert "src/common/utils.ts" in changes
    assert "export function sharedUtil()" in changes["src/common/utils.ts"]


def test_parse_multiple_file_blocks() -> None:
    """TEST-1712: Parse multiple === FILE: blocks."""
    output = """
=== FILE: src/a.ts ===
```typescript
export const A = 1;
```

=== FILE: src/b.ts ===
```typescript
export const B = 2;
```
"""
    changes = AIOutputParser.parse_file_changes(output, fallback_target="src/a.ts")

    assert len(changes) == 2
    assert "export const A = 1;" in changes["src/a.ts"]
    assert "export const B = 2;" in changes["src/b.ts"]


def test_parse_fallback_when_no_blocks() -> None:
    """TEST-1713: The whole output is used as the fallback target content."""
    output = "print('hello world')"
    changes = AIOutputParser.parse_file_changes(
        output, fallback_target="src/main.py"
    )

    assert len(changes) == 1
    assert changes["src/main.py"] == "print('hello world')"


def test_parse_empty_output_returns_empty() -> None:
    """TEST-1714: Empty output produces no changes."""
    changes = AIOutputParser.parse_file_changes("   ", fallback_target="src/main.py")

    assert changes == {}


def test_parse_sections_extracts_root_cause_and_strategy() -> None:
    """TEST-1715: Root cause and strategy sections are extracted."""
    output = """
根因分析：循环依赖导致模块加载顺序不确定。
修复策略：将公共类型提取到独立文件。

=== FILE: src/types.ts ===
```typescript
export interface Foo {}
```
"""
    sections = AIOutputParser.parse_sections(output)

    assert "循环依赖" in sections["root_cause"]
    assert "公共类型" in sections["strategy"]


def test_parse_sections_returns_empty_when_missing() -> None:
    """TEST-1716: Missing sections result in empty strings."""
    output = "=== FILE: src/x.ts ===\n```\nconst x = 1;\n```"
    sections = AIOutputParser.parse_sections(output)

    assert sections["root_cause"] == ""
    assert sections["strategy"] == ""
