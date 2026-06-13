"""DocLinter — document diagnosis and auto-fix engine."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from app.docforge.schemas.extraction_schemas import LintIssue, LintReport
from app.docforge.schemas.template_schemas import DEFAULT_TEMPLATES, TemplateDef

SEVERITY_ORDER = ["BLOCKER", "ERROR", "WARNING", "INFO"]


class DocLinter:
    """First gate for document ingress.

    Core flow:
    1. Detect doc_type
    2. Validate Front Matter
    3. Validate c4_binding block
    4. Validate @C4- tags
    5. Auto-fix + report
    """

    RULES = {
        "frontmatter": re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL),
        "c4_tag": re.compile(r"@C4-([A-Za-z0-9-]+):([^\s\n,;]+)"),
        "section_anchor": re.compile(
            r"^(#{1,6})\s+(.+?)\s*\{ #([a-zA-Z0-9_-]+)\}\s*$", re.MULTILINE
        ),
    }

    def __init__(self, auto_fix: bool = True, strict_mode: bool = False) -> None:
        self.auto_fix = auto_fix
        self.strict_mode = strict_mode

    def lint(self, content: str, file_path: str = "") -> LintReport:
        """Lint document and return report."""
        issues: list[LintIssue] = []
        fixed_content = content

        # 1. Detect doc_type
        doc_type = self._detect_doc_type(content, file_path)
        if not doc_type:
            issues.append(
                LintIssue(
                    rule_id="VAL-DOC-001",
                    severity="BLOCKER",
                    message="无法识别文档类型",
                    location="文件头",
                    fix_hint="在 YAML Front Matter 中添加 doc_type: PRD",
                    auto_fixable=False,
                    fix_strategy="MANUAL",
                )
            )
            return self._build_report(file_path, None, issues, content)

        template = DEFAULT_TEMPLATES[doc_type]

        # 2. Front Matter check
        fm, fm_issues, fixed_content = self._check_frontmatter(
            fixed_content, doc_type, template
        )
        issues.extend(fm_issues)

        # 3. c4_binding check
        if fm:
            binding_issues, fixed_content = self._check_c4_binding(
                fixed_content, doc_type, template, fm
            )
            issues.extend(binding_issues)

        # 4. @C4- tags check
        tag_issues, fixed_content = self._check_c4_tags(
            fixed_content, doc_type, template
        )
        issues.extend(tag_issues)

        return self._build_report(file_path, doc_type, issues, fixed_content)

    def fix(self, content: str, file_path: str = "") -> tuple[str, LintReport]:
        """Lint and auto-fix document."""
        self.auto_fix = True
        report = self.lint(content, file_path)
        return report.fixed_content or content, report

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------
    def _detect_doc_type(self, content: str, file_path: str) -> str | None:
        name_map = {
            "prd": "PRD",
            "requirement": "PRD",
            "domain": "DOMAIN_MODEL",
            "entity": "DOMAIN_MODEL",
            "arch": "ARCH",
            "architecture": "ARCH",
            "detail": "DETAIL_DESIGN",
            "design": "DETAIL_DESIGN",
            "api": "API_DESIGN",
            "interface": "API_DESIGN",
            "db": "DB_DESIGN",
            "database": "DB_DESIGN",
        }
        file_lower = Path(file_path).stem.lower()
        for key, dt in name_map.items():
            if key in file_lower:
                return dt

        if "接口" in content and ("GET" in content or "POST" in content):
            return "API_DESIGN"
        if "容器" in content and "技术栈" in content:
            return "ARCH"

        fm_match = self.RULES["frontmatter"].search(content)
        if fm_match:
            try:
                fm = yaml.safe_load(fm_match.group(1))
                if fm and "doc_type" in fm:
                    return fm["doc_type"].upper()
            except yaml.YAMLError:
                pass
        return None

    # ------------------------------------------------------------------
    # Front Matter
    # ------------------------------------------------------------------
    def _check_frontmatter(
        self, content: str, doc_type: str, template: TemplateDef
    ) -> tuple[dict[str, Any] | None, list[LintIssue], str]:
        issues: list[LintIssue] = []
        fixed = content

        fm_match = self.RULES["frontmatter"].search(content)
        if not fm_match:
            issues.append(
                LintIssue(
                    rule_id="VAL-DOC-002",
                    severity="BLOCKER",
                    message="缺少 YAML Front Matter 区块",
                    location="文档开头",
                    fix_hint=f"添加 ---\ndoc_type: {doc_type}\nc4_binding:\n  level: "
                    f"{template.expected_level}\n---",
                    auto_fixable=True,
                    fix_strategy="AUTO",
                )
            )
            if self.auto_fix:
                default_fm = self._generate_default_frontmatter(doc_type, template)
                fixed = f"---\n{default_fm}---\n\n{content}"
                fm = yaml.safe_load(default_fm)
            else:
                fm = {}
            return fm, issues, fixed

        try:
            fm = yaml.safe_load(fm_match.group(1))
        except yaml.YAMLError as e:
            issues.append(
                LintIssue(
                    rule_id="VAL-DOC-003",
                    severity="BLOCKER",
                    message=f"YAML Front Matter 解析失败: {e}",
                    location="文档开头",
                    fix_hint="检查 YAML 缩进和语法",
                    auto_fixable=False,
                    fix_strategy="MANUAL",
                )
            )
            return {}, issues, fixed

        for field in template.required_frontmatter:
            if field not in (fm or {}):
                sev = "BLOCKER" if field == "c4_binding" else "ERROR"
                issues.append(
                    LintIssue(
                        rule_id=f"VAL-DOC-{field.upper()}-001",
                        severity=sev,
                        message=f"Front Matter 缺少必填字段: {field}",
                        location="YAML Front Matter",
                        fix_hint=f"添加 {field}: <值>",
                        auto_fixable=True,
                        fix_strategy="AUTO",
                    )
                )

        return fm or {}, issues, fixed

    # ------------------------------------------------------------------
    # c4_binding
    # ------------------------------------------------------------------
    def _check_c4_binding(
        self,
        content: str,
        doc_type: str,
        template: TemplateDef,
        frontmatter: dict[str, Any],
    ) -> tuple[list[LintIssue], str]:
        issues: list[LintIssue] = []
        fixed = content

        binding = frontmatter.get("c4_binding", {})
        if not isinstance(binding, dict):
            issues.append(
                LintIssue(
                    rule_id="VAL-DOC-BIND-001",
                    severity="BLOCKER",
                    message="c4_binding 必须是 YAML 对象",
                    location="c4_binding",
                    fix_hint="改为 c4_binding:\n  level: L1\n  system_id: xxx",
                    auto_fixable=True,
                    fix_strategy="AUTO",
                )
            )
            return issues, fixed

        expected_level = template.expected_level
        actual_level = binding.get("level")
        if actual_level != expected_level:
            issues.append(
                LintIssue(
                    rule_id="VAL-DOC-BIND-002",
                    severity="ERROR",
                    message=f"c4_binding.level 应为 {expected_level}，实际为 "
                    f"{actual_level}",
                    location="c4_binding.level",
                    fix_hint=f"修改为 level: {expected_level}",
                    auto_fixable=True,
                    fix_strategy="AUTO",
                )
            )

        return issues, fixed

    # ------------------------------------------------------------------
    # @C4- tags
    # ------------------------------------------------------------------
    def _check_c4_tags(
        self, content: str, doc_type: str, template: TemplateDef
    ) -> tuple[list[LintIssue], str]:
        issues: list[LintIssue] = []
        fixed = content

        found_tags: dict[str, list[tuple[str, int]]] = {}
        for match in self.RULES["c4_tag"].finditer(content):
            tag_type = match.group(1)
            tag_value = match.group(2)
            found_tags.setdefault(tag_type, []).append((tag_value, match.start()))

        for required in template.required_c4_tags:
            tag_name = required.replace("@C4-", "")
            if tag_name not in found_tags:
                issues.append(
                    LintIssue(
                        rule_id=f"VAL-DOC-TAG-{tag_name}-001",
                        severity="ERROR",
                        message=f"缺少必填 @C4- 标签: {required}",
                        location="全文",
                        fix_hint=f"添加 {required}:<标识符>",
                        auto_fixable=False,
                        fix_strategy="MANUAL",
                    )
                )

        for tag_type, occurrences in found_tags.items():
            for value, pos in occurrences:
                if not re.match(r"^[A-Z][a-zA-Z0-9_-]+$|^[a-z][a-z0-9_-]+$", value):
                    issues.append(
                        LintIssue(
                            rule_id="VAL-DOC-TAG-FMT-001",
                            severity="WARNING",
                            message=f"@C4-{tag_type} 值 '{value}' 格式不规范",
                            location=f"位置 {pos}",
                            fix_hint="使用 PascalCase 或 snake_case",
                            auto_fixable=True,
                            fix_strategy="AUTO",
                        )
                    )

        return issues, fixed

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _generate_default_frontmatter(self, doc_type: str, template: TemplateDef) -> str:
        return (
            f"doc_type: {doc_type}\n"
            "version: 1.0.0\n"
            "c4_binding:\n"
            f"  level: {template.expected_level}\n"
            "  # TODO: 请补充具体绑定标识\n"
        )

    def _build_report(
        self,
        file_path: str,
        doc_type: str | None,
        issues: list[LintIssue],
        fixed_content: str,
    ) -> LintReport:
        blockers = sum(1 for i in issues if i.severity == "BLOCKER")
        errors = sum(1 for i in issues if i.severity == "ERROR")
        warnings = sum(1 for i in issues if i.severity == "WARNING")
        passed = blockers == 0 and errors == 0
        if self.strict_mode:
            passed = passed and warnings == 0

        summary = (
            f"[{'PASS' if passed else 'FAIL'}] {doc_type or 'UNKNOWN'} - "
            f"{Path(file_path).name}\n"
            f"  BLOCKER: {blockers} | ERROR: {errors} | WARNING: {warnings}\n"
            f"  {'Ready for downstream' if passed else 'Fix BLOCKER/ERROR first'}"
        )
        return LintReport(
            file_path=file_path,
            doc_type=doc_type,
            passed=passed,
            issues=issues,
            fixed_content=fixed_content if self.auto_fix else None,
            summary=summary,
        )
