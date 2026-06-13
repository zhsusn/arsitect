"""Root cause classifier for governance issues."""

from __future__ import annotations

from typing import Any

from app.c4.governance_fix.models import GovernanceIssue, RootCause


class RootCauseClassifier:
    """Classify an issue into a root cause and decide auto-fixability."""

    # Frontend / backend primitive suffixes that are legitimately standalone.
    _PRIMITIVE_SUFFIXES = (
        "button", "input", "badge", "popover", "mask", "handle", "layer",
        "view", "panel", "overlay", "card", "item", "state", "directions",
        "header", "steps", "menu", "menuitem", "tab", "row", "btn", "block",
        "path", "tag", "chip", "icon", "avatar", "divider", "spacer",
        "adapter", "manager", "handler", "controller", "validator",
    )

    def __init__(self, context: dict[str, Any]) -> None:
        self.context = context
        self.registry = context.get("registry") or {}
        self.components = self.registry.get("components", {})
        self.code_entities = context.get("code_entities", [])
        self.workspace_model = context.get("workspace_model") or {}
        model = self.workspace_model.get("workspace", {}).get("model", self.workspace_model.get("model", {}))
        self.containers = {c.get("id", "") for c in model.get("containers", [])}

    def classify(self, issue: GovernanceIssue) -> GovernanceIssue:
        """Populate root_cause / auto_fixable / confidence on the issue."""
        root_cause = self._classify(issue)
        issue.root_cause = root_cause
        issue.auto_fixable = self._is_auto_fixable(issue, root_cause)
        issue.confidence = self._confidence(issue, root_cause)
        return issue

    def _classify(self, issue: GovernanceIssue) -> str:
        rule = issue.rule_id

        # Structural analyzer rules
        if rule == "C4-ORPHAN-001":
            return self._classify_orphan(issue)
        if rule == "C4-ORPHAN-002":
            return RootCause.INTENTIONAL_DESIGN
        if rule in ("C4-CYCLE-001", "C4-CYCLE-002"):
            return RootCause.NEEDS_HUMAN_DECISION
        if rule == "C4-NAME-001":
            return RootCause.DOC_NON_COMPLIANT
        if rule == "C4-LEVEL-001":
            return RootCause.DOC_NON_COMPLIANT
        if rule == "C4-DISCONN-001":
            return RootCause.RELATIONSHIP_MISSING

        # Consistency checker rules
        if rule == "CON-C2M-001":
            return self._classify_container_missing_module(issue)
        if rule == "CON-M2C-001":
            return RootCause.DOC_INCOMPLETE
        if rule == "CON-C2F-001":
            return self._classify_component_missing_function(issue)
        if rule == "CON-F2C-001":
            return RootCause.DOC_INCOMPLETE
        if rule.startswith("CON-SYS-"):
            return RootCause.DOC_INCOMPLETE

        # Cross-layer validator rules
        if rule == "VAL-001":
            return RootCause.RELATIONSHIP_MISSING
        if rule in ("VAL-002", "VAL-006", "VAL-007"):
            return RootCause.DOC_INCOMPLETE
        if rule in ("VAL-003", "VAL-004"):
            return RootCause.DOC_NON_COMPLIANT
        if rule == "VAL-005":
            return RootCause.DOC_INCOMPLETE
        if rule == "VAL-008":
            return RootCause.NEEDS_HUMAN_DECISION

        # Doc linter
        if rule.startswith("VAL-DOC-"):
            return RootCause.DOC_NON_COMPLIANT

        return RootCause.UNKNOWN

    def _classify_orphan(self, issue: GovernanceIssue) -> str:
        node_ids = issue.node_ids or []
        if not node_ids:
            return RootCause.RELATIONSHIP_MISSING

        # If all nodes are primitive / intentional helpers, treat as intentional.
        if all(self._is_intentional_primitive(nid) for nid in node_ids):
            return RootCause.INTENTIONAL_DESIGN

        # If any node has a code implementation but no edge, relationship extraction missed.
        for nid in node_ids:
            info = self.components.get(nid, {})
            if info.get("implemented") or self._has_code_entity(info.get("name", nid)):
                return RootCause.RELATIONSHIP_MISSING

        # Otherwise the node is documented but not implemented.
        return RootCause.CODE_MISSING

    def _classify_container_missing_module(self, issue: GovernanceIssue) -> str:
        cid = issue.c4_node_id or ""
        # If a code directory matches by name, it's a naming mismatch.
        if self._has_code_directory(cid):
            return RootCause.DOC_CODE_MISMATCH
        # If the container name looks like a conceptual/P1 module, intentional.
        if self._is_likely_conceptual(cid):
            return RootCause.INTENTIONAL_DESIGN
        return RootCause.CODE_MISSING

    def _classify_component_missing_function(self, issue: GovernanceIssue) -> str:
        comp_id = issue.c4_node_id or ""
        comp = self.components.get(comp_id, {})
        name = comp.get("name", comp_id)
        if self._has_code_entity(name):
            return RootCause.DOC_CODE_MISMATCH
        if self._is_likely_conceptual(comp_id):
            return RootCause.INTENTIONAL_DESIGN
        return RootCause.CODE_MISSING

    def _is_intentional_primitive(self, node_id: str) -> bool:
        info = self.components.get(node_id, {})
        name = (info.get("name") or node_id).lower()
        if name in {"react", "app"}:
            return True
        return any(name.endswith(s) for s in self._PRIMITIVE_SUFFIXES)

    def _is_likely_conceptual(self, text: str) -> bool:
        """Heuristic for P1 / placeholder names."""
        lower = text.lower()
        return any(
            frag in lower
            for frag in ("p1", "future", "todo", "placeholder", "concept", "draft")
        )

    def _has_code_entity(self, name: str) -> bool:
        if not name:
            return False
        name_lower = name.lower().replace("-", "_")
        for e in self.code_entities:
            e_name = e.get("name", "").lower().replace("-", "_")
            if e_name == name_lower or name_lower in e_name or e_name in name_lower:
                return True
        return False

    def _has_code_directory(self, container_id: str) -> bool:
        if not container_id:
            return False
        cid = container_id.lower().replace("-", "_").replace(" ", "_")
        for e in self.code_entities:
            fp = e.get("file_path", "").lower().replace("-", "_")
            if cid in fp:
                return True
        return False

    def _is_auto_fixable(self, issue: GovernanceIssue, root_cause: str) -> bool:
        if root_cause == RootCause.NEEDS_HUMAN_DECISION:
            return False
        if root_cause == RootCause.UNKNOWN:
            return False
        # Naming fixes and container_id fixes are safe and deterministic.
        if issue.rule_id in ("C4-NAME-001", "C4-LEVEL-001"):
            return True
        if root_cause == RootCause.INTENTIONAL_DESIGN:
            return True
        if root_cause == RootCause.RELATIONSHIP_MISSING and issue.rule_id == "C4-ORPHAN-001":
            return True
        # Doc linter auto-fixable issues are safe; everything else needs confirmation.
        return issue.rule_id.startswith("VAL-DOC-")

    def _confidence(self, issue: GovernanceIssue, root_cause: str) -> str:
        if issue.rule_id in ("C4-NAME-001", "C4-LEVEL-001"):
            return "HIGH"
        if root_cause == RootCause.INTENTIONAL_DESIGN:
            return "HIGH"
        if root_cause == RootCause.RELATIONSHIP_MISSING:
            return "HIGH"
        if root_cause in (RootCause.DOC_NON_COMPLIANT, RootCause.DOC_INCOMPLETE):
            return "MEDIUM"
        return "LOW"
