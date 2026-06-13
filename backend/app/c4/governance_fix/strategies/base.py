"""Base class for governance fix strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.c4.governance_fix.llm_gateway import LLMGateway, get_llm_gateway
from app.c4.governance_fix.models import ChangeSet, GovernanceIssue


class FixStrategy(ABC):
    """Base class for a fix strategy.

    Each strategy knows how to handle a specific (rule_id, root_cause) pair
    and returns a list of concrete ChangeSets.
    """

    def __init__(self) -> None:
        self._llm: LLMGateway | None = None

    @property
    def llm(self) -> LLMGateway:
        """Lazy-load the configured LLM gateway."""
        if self._llm is None:
            self._llm = get_llm_gateway()
        return self._llm

    @abstractmethod
    async def plan(
        self,
        issue: GovernanceIssue,
        project_id: str,
        context: dict[str, Any],
    ) -> list[ChangeSet]:
        """Return ChangeSets that would fix the given issue."""
        raise NotImplementedError

    def supports(self, issue: GovernanceIssue) -> bool:
        """Return True if this strategy can handle the issue."""
        return False
