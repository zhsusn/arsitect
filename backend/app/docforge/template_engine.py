"""DocumentTemplateEngine — template validation and c4_binding gate."""

from __future__ import annotations

import re
from typing import Any, cast

import yaml

from app.docforge.schemas.template_schemas import (
    DEFAULT_TEMPLATES,
    DOC_TYPE_LEVEL_MAP,
    TemplateDef,
)


class ValidationResult:
    """Template validation result."""

    def __init__(
        self,
        passed: bool,
        doc_type: str | None = None,
        missing_fields: list[str] | None = None,
        errors: list[str] | None = None,
    ) -> None:
        self.passed = passed
        self.doc_type = doc_type
        self.missing_fields = missing_fields or []
        self.errors = errors or []


class DocumentTemplateEngine:
    """Gatekeeper for document templates.

    Responsibilities:
    1. Manage template definitions.
    2. Validate documents against templates.
    3. Validate c4_binding completeness.
    """

    def __init__(self) -> None:
        self._templates: dict[str, TemplateDef] = dict(DEFAULT_TEMPLATES)

    def validate(self, content: str, doc_type: str) -> ValidationResult:
        """Validate document against template requirements."""
        errors: list[str] = []
        missing_fields: list[str] = []

        if doc_type not in self._templates:
            return ValidationResult(passed=False, errors=[f"未知的文档类型: {doc_type}"])

        template = self._templates[doc_type]
        frontmatter = self._extract_frontmatter(content)
        if frontmatter is None:
            return ValidationResult(
                passed=False,
                doc_type=doc_type,
                errors=["缺少 YAML Front Matter"],
            )

        for field in template.required_frontmatter:
            if field not in frontmatter:
                missing_fields.append(field)
                errors.append(f"缺少必填 Front Matter 字段: {field}")

        c4_binding = frontmatter.get("c4_binding", {})
        if not isinstance(c4_binding, dict):
            errors.append("c4_binding 必须是对象")
        else:
            expected_level = DOC_TYPE_LEVEL_MAP.get(doc_type)
            actual_level = c4_binding.get("level")
            if actual_level != expected_level:
                errors.append(
                    f"c4_binding.level 不匹配: 期望 {expected_level}, 实际 {actual_level}"
                )
            for field in template.required_binding_fields:
                if field not in c4_binding:
                    missing_fields.append(f"c4_binding.{field}")
                    errors.append(f"c4_binding 缺少: {field}")

        return ValidationResult(
            passed=len(errors) == 0,
            doc_type=doc_type,
            missing_fields=missing_fields,
            errors=errors,
        )

    def get_template(self, doc_type: str) -> TemplateDef | None:
        """Return template definition."""
        return self._templates.get(doc_type)

    def register_template(self, doc_type: str, schema: TemplateDef) -> None:
        """Register a new document type template."""
        self._templates[doc_type] = schema

    @staticmethod
    def _extract_frontmatter(content: str) -> dict[str, Any] | None:
        match = re.search(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if not match:
            return None
        try:
            return cast(dict[str, Any] | None, yaml.safe_load(match.group(1)))
        except yaml.YAMLError:
            return None
