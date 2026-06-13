"""CrossLayerValidator — C4 architecture cross-layer consistency validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import yaml

from app.c4.baseline_store import C4BaselineStore
from app.c4.binding_registry import C4BindingRegistry


class Severity(StrEnum):
    """Validation issue severity."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class RuleId(StrEnum):
    """Validation rule identifiers."""

    VAL_001 = "VAL-001"  # 外部系统引用一致性
    VAL_002 = "VAL-002"  # 实体定义一致性
    VAL_003 = "VAL-003"  # 容器归属一致性
    VAL_004 = "VAL-004"  # 组件归属一致性
    VAL_005 = "VAL-005"  # 接口归属一致性
    VAL_006 = "VAL-006"  # 实体-表映射一致性
    VAL_007 = "VAL-007"  # 属性-字段映射一致性
    VAL_008 = "VAL-008"  # 页面类型推断一致性


@dataclass
class ValidationIssue:
    """Single validation issue."""

    rule_id: str
    severity: Severity
    message: str
    c4_node_id: str | None = None
    c4_level: str | None = None
    suggestion: str = ""


@dataclass
class ValidationReport:
    """Structured validation report."""

    project_id: str
    passed: bool
    error_count: int
    warning_count: int
    info_count: int
    issues: list[ValidationIssue] = field(default_factory=list)
    summary: str = ""


class CrossLayerValidator:
    """Cross-layer validator — C4 architecture consistency verification.

    Responsibilities:
    1. Load C4Workspace and BindingRegistry.
    2. Execute VAL-001~VAL-008 in order.
    3. Collect and classify issues.
    4. Generate structured report.
    """

    def __init__(
        self,
        baseline_store: C4BaselineStore,
        binding_registry: C4BindingRegistry,
    ) -> None:
        self.baseline = baseline_store
        self.bindings = binding_registry

    async def validate(self, project_id: str) -> ValidationReport:
        """Execute full validation.

        Args:
            project_id: Project ID.

        Returns:
            ValidationReport.
        """
        issues: list[ValidationIssue] = []

        baseline = await self.baseline.read_current(project_id)
        if not baseline:
            return ValidationReport(
                project_id=project_id,
                passed=False,
                error_count=1,
                warning_count=0,
                info_count=0,
                issues=[
                    ValidationIssue(
                        rule_id=RuleId.VAL_001,
                        severity=Severity.ERROR,
                        message="No C4 baseline found for this project",
                        suggestion="Run document extraction pipeline first",
                    )
                ],
            )

        workspace = self._parse_dsl(baseline.dsl_content)

        issues.extend(self._check_val001_external_systems(workspace))
        issues.extend(self._check_val002_entity_definition(workspace))
        issues.extend(self._check_val003_container_refs(workspace))
        issues.extend(self._check_val004_component_containers(workspace))
        issues.extend(self._check_val005_interface_contract(workspace))
        issues.extend(self._check_val006_entity_table_mapping(workspace))
        issues.extend(self._check_val007_attribute_field_mapping(workspace))
        issues.extend(self._check_val008_page_type_inference(workspace))

        errors = len([i for i in issues if i.severity == Severity.ERROR])
        warnings = len([i for i in issues if i.severity == Severity.WARNING])
        infos = len([i for i in issues if i.severity == Severity.INFO])

        passed = errors == 0
        summary = self._generate_summary(project_id, errors, warnings, infos)

        return ValidationReport(
            project_id=project_id,
            passed=passed,
            error_count=errors,
            warning_count=warnings,
            info_count=infos,
            issues=issues,
            summary=summary,
        )

    async def validate_incremental(
        self, project_id: str, changed_nodes: list[str]
    ) -> ValidationReport:
        """Incremental validation — only check changed nodes.

        Args:
            project_id: Project ID.
            changed_nodes: List of changed C4 node IDs.
        """
        baseline = await self.baseline.read_current(project_id)
        if not baseline:
            return ValidationReport(
                project_id=project_id,
                passed=False,
                error_count=0,
                warning_count=0,
                info_count=0,
            )

        workspace = self._parse_dsl(baseline.dsl_content)
        issues: list[ValidationIssue] = []

        container_ids = {c["id"] for c in workspace.get("model", {}).get("containers", [])}
        component_ids = {c["id"] for c in workspace.get("model", {}).get("components", [])}

        for node_id in changed_nodes:
            if node_id in container_ids:
                issues.extend(self._check_container_ref(workspace, node_id))
            if node_id in component_ids:
                issues.extend(self._check_component_ref(workspace, node_id))

        errors = len([i for i in issues if i.severity == Severity.ERROR])
        return ValidationReport(
            project_id=project_id,
            passed=errors == 0,
            error_count=errors,
            warning_count=0,
            info_count=0,
            issues=issues,
        )

    # ============================================================
    # VAL-001: 外部系统引用一致性
    # ============================================================
    def _check_val001_external_systems(
        self, workspace: dict[str, Any]
    ) -> list[ValidationIssue]:
        """PRD-defined external systems must have corresponding containers in ARCH."""
        issues = []
        model = self._extract_model(workspace)
        external_systems = model.get("externalSystems", [])

        for ext in external_systems:
            ext_id = ext["id"]
            found = any(
                ext_id in str(rel.get("target", ""))
                or ext_id in str(rel.get("description", ""))
                for rel in model.get("relationships", [])
            )
            if not found:
                issues.append(
                    ValidationIssue(
                        rule_id=RuleId.VAL_001,
                        severity=Severity.WARNING,
                        message=f"External system '{ext_id}' is not referenced by any container",
                        c4_node_id=ext_id,
                        c4_level="L1",
                        suggestion=f"Add a relationship from a container to {ext_id}",
                    )
                )
        return issues

    # ============================================================
    # VAL-002: 实体定义一致性
    # ============================================================
    def _check_val002_entity_definition(
        self, workspace: dict[str, Any]
    ) -> list[ValidationIssue]:
        """DTO fields in API should map to entity attributes in DOMAIN_MODEL."""
        issues = []
        model = self._extract_model(workspace)
        entities = model.get("entities", [])
        entity_attrs: dict[str, set[str]] = {}
        for e in entities:
            props = e.get("properties", {})
            attrs = set(props.get("attributes", []))
            entity_attrs[e["id"]] = attrs

        interfaces = model.get("interfaces", [])
        for iface in interfaces:
            iface_id = iface["id"]
            props = iface.get("properties", {})
            dto_fields = set(props.get("dto_fields", []))
            related_entity = props.get("related_entity")
            if related_entity and dto_fields:
                known = entity_attrs.get(related_entity, set())
                missing = dto_fields - known
                if missing:
                    issues.append(
                        ValidationIssue(
                            rule_id=RuleId.VAL_002,
                            severity=Severity.WARNING,
                            message=(
                                f"Interface '{iface_id}' DTO fields {missing} "
                                f"not found in entity '{related_entity}'"
                            ),
                            c4_node_id=iface_id,
                            c4_level="L3",
                            suggestion="Add missing attributes to domain entity or review DTO",
                        )
                    )
        return issues

    # ============================================================
    # VAL-003: 容器归属一致性
    # ============================================================
    def _check_val003_container_refs(
        self, workspace: dict[str, Any]
    ) -> list[ValidationIssue]:
        """container_id referenced by downstream docs must exist in ARCH."""
        issues = []
        model = self._extract_model(workspace)
        containers = {c["id"] for c in model.get("containers", [])}

        for component in model.get("components", []):
            container_id = component.get("properties", {}).get("container_id")
            if container_id and container_id not in containers:
                issues.append(
                    ValidationIssue(
                        rule_id=RuleId.VAL_003,
                        severity=Severity.ERROR,
                        message=(
                            f"Component '{component['id']}' references "
                            f"unknown container '{container_id}'"
                        ),
                        c4_node_id=component["id"],
                        c4_level="L3",
                        suggestion=(
                            f"Define container '{container_id}' in ARCH "
                            "document or fix the reference"
                        ),
                    )
                )
        return issues

    # ============================================================
    # VAL-004: 组件归属一致性
    # ============================================================
    def _check_val004_component_containers(
        self, workspace: dict[str, Any]
    ) -> list[ValidationIssue]:
        """Component's container must be defined in ARCH."""
        issues = []
        model = self._extract_model(workspace)
        containers = {c["id"] for c in model.get("containers", [])}

        for component in model.get("components", []):
            comp_id = component["id"]
            container_id = component.get("properties", {}).get("container_id")

            if not container_id:
                issues.append(
                    ValidationIssue(
                        rule_id=RuleId.VAL_004,
                        severity=Severity.WARNING,
                        message=f"Component '{comp_id}' has no container_id specified",
                        c4_node_id=comp_id,
                        c4_level="L3",
                        suggestion="Add container_id to the component definition",
                    )
                )
            elif container_id not in containers:
                issues.append(
                    ValidationIssue(
                        rule_id=RuleId.VAL_004,
                        severity=Severity.ERROR,
                        message=(
                            f"Component '{comp_id}' belongs to undefined "
                            f"container '{container_id}'"
                        ),
                        c4_node_id=comp_id,
                        c4_level="L3",
                        suggestion=(
                            f"Define container '{container_id}' or fix the container_id"
                        ),
                    )
                )
        return issues

    # ============================================================
    # VAL-005: 接口归属一致性
    # ============================================================
    def _check_val005_interface_contract(
        self, workspace: dict[str, Any]
    ) -> list[ValidationIssue]:
        """Interfaces declared by components must have detailed contracts in API_DESIGN."""
        issues = []
        model = self._extract_model(workspace)
        interfaces = {i["id"] for i in model.get("interfaces", [])}

        for component in model.get("components", []):
            comp_id = component["id"]
            comp_interfaces = component.get("properties", {}).get("interfaces", [])
            for iface_ref in comp_interfaces:
                if iface_ref not in interfaces:
                    issues.append(
                        ValidationIssue(
                            rule_id=RuleId.VAL_005,
                            severity=Severity.WARNING,
                            message=(
                                f"Component '{comp_id}' declares interface '{iface_ref}' "
                                "without detailed contract"
                            ),
                            c4_node_id=comp_id,
                            c4_level="L3",
                            suggestion=f"Add API contract for interface '{iface_ref}'",
                        )
                    )
        return issues

    # ============================================================
    # VAL-006: 实体-表映射一致性
    # ============================================================
    def _check_val006_entity_table_mapping(
        self, workspace: dict[str, Any]
    ) -> list[ValidationIssue]:
        """DB table mapped entity must exist in DOMAIN_MODEL."""
        issues = []
        model = self._extract_model(workspace)
        entities = {e["id"] for e in model.get("entities", [])}

        for table in model.get("tables", []):
            mapped_entity = table.get("properties", {}).get("mapped_entity")
            if mapped_entity and mapped_entity not in entities:
                issues.append(
                    ValidationIssue(
                        rule_id=RuleId.VAL_006,
                        severity=Severity.ERROR,
                        message=(
                            f"Table '{table['id']}' maps to undefined entity "
                            f"'{mapped_entity}'"
                        ),
                        c4_node_id=table["id"],
                        c4_level="L2",
                        suggestion=f"Define entity '{mapped_entity}' in DOMAIN_MODEL",
                    )
                )
        return issues

    # ============================================================
    # VAL-007: 属性-字段映射一致性
    # ============================================================
    def _check_val007_attribute_field_mapping(
        self, workspace: dict[str, Any]
    ) -> list[ValidationIssue]:
        """DB field mapped attribute must exist in corresponding entity."""
        issues = []
        model = self._extract_model(workspace)
        entity_attrs: dict[str, set[str]] = {}
        for e in model.get("entities", []):
            attrs = set(e.get("properties", {}).get("attributes", []))
            entity_attrs[e["id"]] = attrs

        for table in model.get("tables", []):
            mapped_entity = table.get("properties", {}).get("mapped_entity")
            if not mapped_entity:
                continue
            known_attrs = entity_attrs.get(mapped_entity, set())
            for col in table.get("properties", {}).get("columns", []):
                col_name = col if isinstance(col, str) else col.get("name")
                if col_name and col_name not in known_attrs:
                    issues.append(
                        ValidationIssue(
                            rule_id=RuleId.VAL_007,
                            severity=Severity.WARNING,
                            message=(
                                f"Table '{table['id']}' column '{col_name}' "
                                f"not found in entity '{mapped_entity}'"
                            ),
                            c4_node_id=table["id"],
                            c4_level="L2",
                            suggestion="Add attribute to entity or review DB mapping",
                        )
                    )
        return issues

    # ============================================================
    # VAL-008: 页面类型推断一致性
    # ============================================================
    def _check_val008_page_type_inference(
        self, workspace: dict[str, Any]
    ) -> list[ValidationIssue]:
        """PageType conflicts with DomainMapper inference; human annotation wins."""
        issues = []
        model = self._extract_model(workspace)
        for page in model.get("pages", []):
            page_id = page["id"]
            page_type = page.get("properties", {}).get("page_type")
            inferred = page.get("properties", {}).get("inferred_type")
            if page_type and inferred and page_type != inferred:
                issues.append(
                    ValidationIssue(
                        rule_id=RuleId.VAL_008,
                        severity=Severity.INFO,
                        message=(
                            f"Page '{page_id}' type '{page_type}' differs from "
                            f"inferred '{inferred}'"
                        ),
                        c4_node_id=page_id,
                        c4_level="L3",
                        suggestion="Review and confirm page type manually",
                    )
                )
        return issues

    # ============================================================
    # Incremental helpers
    # ============================================================
    def _check_container_ref(
        self, workspace: dict[str, Any], container_id: str
    ) -> list[ValidationIssue]:
        """Check reference integrity for a single container (incremental)."""
        issues = []
        model = self._extract_model(workspace)

        components = [
            c
            for c in model.get("components", [])
            if c.get("properties", {}).get("container_id") == container_id
        ]

        if not components:
            issues.append(
                ValidationIssue(
                    rule_id=RuleId.VAL_004,
                    severity=Severity.INFO,
                    message=f"Container '{container_id}' has no components defined",
                    c4_node_id=container_id,
                    c4_level="L2",
                    suggestion="Add components to this container in DETAIL_DESIGN",
                )
            )
        return issues

    def _check_component_ref(
        self, workspace: dict[str, Any], component_id: str
    ) -> list[ValidationIssue]:
        """Check component reference integrity (incremental)."""
        issues = []
        model = self._extract_model(workspace)
        containers = {c["id"] for c in model.get("containers", [])}

        for comp in model.get("components", []):
            if comp["id"] == component_id:
                container_id = comp.get("properties", {}).get("container_id")
                if container_id and container_id not in containers:
                    issues.append(
                        ValidationIssue(
                            rule_id=RuleId.VAL_003,
                            severity=Severity.ERROR,
                            message=(
                                f"Component '{component_id}' references unknown "
                                f"container '{container_id}'"
                            ),
                            c4_node_id=component_id,
                            c4_level="L3",
                            suggestion="Fix container_id or define container",
                        )
                    )
        return issues

    # ============================================================
    # Utilities
    # ============================================================
    @staticmethod
    def _parse_dsl(dsl_content: str) -> dict[str, Any]:
        """Parse DSL YAML."""
        data = yaml.safe_load(dsl_content)
        if isinstance(data, dict):
            return data
        return {}

    @staticmethod
    def _extract_model(workspace: dict[str, Any]) -> dict[str, Any]:
        """Extract model dict from workspace, handling nested workspace key."""
        if "workspace" in workspace:
            return workspace["workspace"].get("model", {})
        return workspace.get("model", {})

    @staticmethod
    def _generate_summary(
        project_id: str, errors: int, warnings: int, infos: int
    ) -> str:
        status = "PASSED" if errors == 0 else "FAILED"
        return (
            f"[{status}] Project {project_id}: "
            f"{errors} errors, {warnings} warnings, {infos} infos"
        )
