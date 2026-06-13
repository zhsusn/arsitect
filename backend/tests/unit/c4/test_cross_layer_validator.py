"""Tests for CrossLayerValidator."""

from __future__ import annotations

from app.c4.cross_layer_validator import (
    CrossLayerValidator,
    RuleId,
    Severity,
)


class TestCrossLayerValidator:
    """CrossLayerValidator unit tests covering VAL-001~008."""

    # ============================================================
    # VAL-003: container归属一致性
    # ============================================================
    def test_val003_unknown_container_ref(self) -> None:
        """Component referencing unknown container raises ERROR."""
        workspace = {
            "workspace": {
                "model": {
                    "containers": [{"id": "WebApp"}],
                    "components": [
                        {"id": "Ctrl", "properties": {"container_id": "NonExistent"}}
                    ],
                }
            }
        }
        validator = CrossLayerValidator(None, None)
        issues = validator._check_val003_container_refs(workspace)

        assert len(issues) == 1
        assert issues[0].rule_id == RuleId.VAL_003
        assert issues[0].severity == Severity.ERROR
        assert "NonExistent" in issues[0].message

    def test_val003_valid_container_ref(self) -> None:
        """Component referencing existing container passes."""
        workspace = {
            "workspace": {
                "model": {
                    "containers": [{"id": "WebApp"}],
                    "components": [
                        {"id": "Ctrl", "properties": {"container_id": "WebApp"}}
                    ],
                }
            }
        }
        validator = CrossLayerValidator(None, None)
        issues = validator._check_val003_container_refs(workspace)
        assert len(issues) == 0

    # ============================================================
    # VAL-004: 组件归属一致性
    # ============================================================
    def test_val004_missing_container_id(self) -> None:
        """Component without container_id raises WARNING."""
        workspace = {
            "workspace": {
                "model": {
                    "containers": [{"id": "API"}],
                    "components": [{"id": "Ctrl", "properties": {}}],
                }
            }
        }
        validator = CrossLayerValidator(None, None)
        issues = validator._check_val004_component_containers(workspace)

        assert len(issues) == 1
        assert issues[0].rule_id == RuleId.VAL_004
        assert issues[0].severity == Severity.WARNING
        assert "no container_id" in issues[0].message

    def test_val004_undefined_container(self) -> None:
        """Component belonging to undefined container raises ERROR."""
        workspace = {
            "workspace": {
                "model": {
                    "containers": [{"id": "API"}],
                    "components": [
                        {"id": "Ctrl", "properties": {"container_id": "Missing"}}
                    ],
                }
            }
        }
        validator = CrossLayerValidator(None, None)
        issues = validator._check_val004_component_containers(workspace)

        assert len(issues) == 1
        assert issues[0].rule_id == RuleId.VAL_004
        assert issues[0].severity == Severity.ERROR
        assert "undefined container" in issues[0].message

    def test_val004_valid_container(self) -> None:
        """Component with valid container_id passes."""
        workspace = {
            "workspace": {
                "model": {
                    "containers": [{"id": "API"}],
                    "components": [
                        {"id": "Ctrl", "properties": {"container_id": "API"}}
                    ],
                }
            }
        }
        validator = CrossLayerValidator(None, None)
        issues = validator._check_val004_component_containers(workspace)
        assert len(issues) == 0

    # ============================================================
    # VAL-001: 外部系统引用一致性
    # ============================================================
    def test_val001_unreferenced_external_system(self) -> None:
        """External system not referenced by any container raises WARNING."""
        workspace = {
            "workspace": {
                "model": {
                    "containers": [{"id": "App"}],
                    "externalSystems": [{"id": "LegacyDB"}],
                    "relationships": [],
                }
            }
        }
        validator = CrossLayerValidator(None, None)
        issues = validator._check_val001_external_systems(workspace)

        assert len(issues) == 1
        assert issues[0].rule_id == RuleId.VAL_001
        assert issues[0].severity == Severity.WARNING
        assert "LegacyDB" in issues[0].message

    def test_val001_referenced_external_system(self) -> None:
        """Referenced external system passes."""
        workspace = {
            "workspace": {
                "model": {
                    "containers": [{"id": "App"}],
                    "externalSystems": [{"id": "LegacyDB"}],
                    "relationships": [
                        {"source": "App", "target": "LegacyDB", "description": "uses"}
                    ],
                }
            }
        }
        validator = CrossLayerValidator(None, None)
        issues = validator._check_val001_external_systems(workspace)
        assert len(issues) == 0

    # ============================================================
    # VAL-006: 实体-表映射一致性
    # ============================================================
    def test_val006_undefined_entity_mapping(self) -> None:
        """Table mapping to undefined entity raises ERROR."""
        workspace = {
            "workspace": {
                "model": {
                    "entities": [{"id": "User"}],
                    "tables": [
                        {
                            "id": "users",
                            "properties": {"mapped_entity": "NonExistent"},
                        }
                    ],
                }
            }
        }
        validator = CrossLayerValidator(None, None)
        issues = validator._check_val006_entity_table_mapping(workspace)

        assert len(issues) == 1
        assert issues[0].rule_id == RuleId.VAL_006
        assert issues[0].severity == Severity.ERROR
        assert "NonExistent" in issues[0].message

    def test_val006_valid_entity_mapping(self) -> None:
        """Table mapping to existing entity passes."""
        workspace = {
            "workspace": {
                "model": {
                    "entities": [{"id": "User"}],
                    "tables": [
                        {"id": "users", "properties": {"mapped_entity": "User"}}
                    ],
                }
            }
        }
        validator = CrossLayerValidator(None, None)
        issues = validator._check_val006_entity_table_mapping(workspace)
        assert len(issues) == 0

    # ============================================================
    # VAL-002: 实体定义一致性
    # ============================================================
    def test_val002_missing_dto_field(self) -> None:
        """DTO field not found in entity raises WARNING."""
        workspace = {
            "workspace": {
                "model": {
                    "entities": [
                        {
                            "id": "User",
                            "properties": {"attributes": ["name"]},
                        }
                    ],
                    "interfaces": [
                        {
                            "id": "UserAPI",
                            "properties": {
                                "dto_fields": ["name", "email"],
                                "related_entity": "User",
                            },
                        }
                    ],
                }
            }
        }
        validator = CrossLayerValidator(None, None)
        issues = validator._check_val002_entity_definition(workspace)

        assert len(issues) == 1
        assert issues[0].rule_id == RuleId.VAL_002
        assert "email" in issues[0].message

    def test_val002_valid_dto_field(self) -> None:
        """All DTO fields found in entity passes."""
        workspace = {
            "workspace": {
                "model": {
                    "entities": [
                        {
                            "id": "User",
                            "properties": {"attributes": ["name", "email"]},
                        }
                    ],
                    "interfaces": [
                        {
                            "id": "UserAPI",
                            "properties": {
                                "dto_fields": ["name", "email"],
                                "related_entity": "User",
                            },
                        }
                    ],
                }
            }
        }
        validator = CrossLayerValidator(None, None)
        issues = validator._check_val002_entity_definition(workspace)
        assert len(issues) == 0

    # ============================================================
    # VAL-005: 接口归属一致性
    # ============================================================
    def test_val005_missing_interface_contract(self) -> None:
        """Component declares interface without contract raises WARNING."""
        workspace = {
            "workspace": {
                "model": {
                    "interfaces": [{"id": "GetUser"}],
                    "components": [
                        {
                            "id": "Ctrl",
                            "properties": {"interfaces": ["MissingAPI"]},
                        }
                    ],
                }
            }
        }
        validator = CrossLayerValidator(None, None)
        issues = validator._check_val005_interface_contract(workspace)

        assert len(issues) == 1
        assert issues[0].rule_id == RuleId.VAL_005
        assert "MissingAPI" in issues[0].message

    # ============================================================
    # VAL-007: 属性-字段映射一致性
    # ============================================================
    def test_val007_unknown_column(self) -> None:
        """Table column not in entity attributes raises WARNING."""
        workspace = {
            "workspace": {
                "model": {
                    "entities": [
                        {
                            "id": "User",
                            "properties": {"attributes": ["name"]},
                        }
                    ],
                    "tables": [
                        {
                            "id": "users",
                            "properties": {
                                "mapped_entity": "User",
                                "columns": ["name", "age"],
                            },
                        }
                    ],
                }
            }
        }
        validator = CrossLayerValidator(None, None)
        issues = validator._check_val007_attribute_field_mapping(workspace)

        assert len(issues) == 1
        assert issues[0].rule_id == RuleId.VAL_007
        assert "age" in issues[0].message

    # ============================================================
    # VAL-008: 页面类型推断一致性
    # ============================================================
    def test_val008_page_type_conflict(self) -> None:
        """PageType differs from inferred type raises INFO."""
        workspace = {
            "workspace": {
                "model": {
                    "pages": [
                        {
                            "id": "HomePage",
                            "properties": {
                                "page_type": "Dashboard",
                                "inferred_type": "List",
                            },
                        }
                    ],
                }
            }
        }
        validator = CrossLayerValidator(None, None)
        issues = validator._check_val008_page_type_inference(workspace)

        assert len(issues) == 1
        assert issues[0].rule_id == RuleId.VAL_008
        assert issues[0].severity == Severity.INFO

    def test_val008_no_conflict(self) -> None:
        """Matching page_type and inferred_type passes."""
        workspace = {
            "workspace": {
                "model": {
                    "pages": [
                        {
                            "id": "HomePage",
                            "properties": {
                                "page_type": "Dashboard",
                                "inferred_type": "Dashboard",
                            },
                        }
                    ],
                }
            }
        }
        validator = CrossLayerValidator(None, None)
        issues = validator._check_val008_page_type_inference(workspace)
        assert len(issues) == 0

    # ============================================================
    # Full validation flow
    # ============================================================
    def test_generate_summary(self) -> None:
        """Summary generation formats correctly."""
        summary = CrossLayerValidator._generate_summary("proj-1", 2, 3, 1)
        assert "FAILED" in summary
        assert "2 errors" in summary
        assert "3 warnings" in summary
        assert "1 infos" in summary

        summary_pass = CrossLayerValidator._generate_summary("proj-2", 0, 1, 0)
        assert "PASSED" in summary_pass
