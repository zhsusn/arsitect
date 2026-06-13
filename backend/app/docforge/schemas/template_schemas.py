"""Document template and validation schemas."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TemplateDef:
    """Template definition for a doc_type."""

    required_frontmatter: list[str] = field(default_factory=list)
    required_binding_fields: list[str] = field(default_factory=list)
    required_c4_tags: list[str] = field(default_factory=list)
    optional_c4_tags: list[str] = field(default_factory=list)
    required_sections: list[str] = field(default_factory=list)
    expected_level: str = "L1"


DEFAULT_TEMPLATES: dict[str, TemplateDef] = {
    "PRD": TemplateDef(
        required_frontmatter=["c4_binding", "title", "version"],
        required_binding_fields=["system_id", "actors"],
        required_c4_tags=["@C4-System", "@C4-Actor"],
        optional_c4_tags=["@C4-External-System"],
        required_sections=["## 背景", "## 目标", "## 范围"],
        expected_level="L1",
    ),
    "DOMAIN_MODEL": TemplateDef(
        required_frontmatter=["c4_binding", "domain"],
        required_binding_fields=["container_id", "entities"],
        required_c4_tags=["@C4-Entity", "@C4-Relationship"],
        optional_c4_tags=["@C4-Attribute", "@C4-Enum"],
        required_sections=["## 领域概述", "## 实体定义"],
        expected_level="L2",
    ),
    "ARCH": TemplateDef(
        required_frontmatter=["c4_binding", "architecture_style"],
        required_binding_fields=["containers"],
        required_c4_tags=["@C4-Container", "@C4-Technology"],
        optional_c4_tags=["@C4-Relation"],
        required_sections=["## 架构概述", "## 容器定义"],
        expected_level="L2",
    ),
    "DETAIL_DESIGN": TemplateDef(
        required_frontmatter=["c4_binding", "module"],
        required_binding_fields=["container_id", "components"],
        required_c4_tags=["@C4-Component", "@C4-Code-Path"],
        optional_c4_tags=["@C4-Interface", "@C4-Page-Type"],
        required_sections=["## 模块概述", "## 组件设计"],
        expected_level="L3",
    ),
    "API_DESIGN": TemplateDef(
        required_frontmatter=["c4_binding", "base_url"],
        required_binding_fields=["component_id", "interfaces"],
        required_c4_tags=["@C4-Interface", "@C4-Method"],
        optional_c4_tags=["@C4-Request", "@C4-Response"],
        required_sections=["## 接口概述", "## 接口清单"],
        expected_level="L3",
    ),
    "DB_DESIGN": TemplateDef(
        required_frontmatter=["c4_binding", "storage"],
        required_binding_fields=["container_id", "tables"],
        required_c4_tags=["@C4-Table", "@C4-Column"],
        optional_c4_tags=["@C4-Index", "@C4-Constraint"],
        required_sections=["## 存储概述", "## 表结构"],
        expected_level="L2",
    ),
}


DOC_TYPE_LEVEL_MAP: dict[str, str] = {
    "PRD": "L1",
    "DOMAIN_MODEL": "L2",
    "ARCH": "L2",
    "DETAIL_DESIGN": "L3",
    "API_DESIGN": "L3",
    "DB_DESIGN": "L2",
}
