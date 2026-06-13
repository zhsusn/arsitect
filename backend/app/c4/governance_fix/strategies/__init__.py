"""Built-in fix strategies for C4 governance issues."""

from __future__ import annotations

from app.c4.governance_fix.strategies.add_component_doc import AddComponentDocStrategy
from app.c4.governance_fix.strategies.add_container import AddContainerStrategy
from app.c4.governance_fix.strategies.add_relationship_doc import AddRelationshipDocStrategy
from app.c4.governance_fix.strategies.base import FixStrategy
from app.c4.governance_fix.strategies.create_code_skeleton import CreateCodeSkeletonStrategy
from app.c4.governance_fix.strategies.create_container_code import CreateContainerCodeStrategy
from app.c4.governance_fix.strategies.delete_orphan import DeleteOrphanStrategy
from app.c4.governance_fix.strategies.document_guidance import DocumentGuidanceStrategy
from app.c4.governance_fix.strategies.fix_container_id import FixContainerIdStrategy
from app.c4.governance_fix.strategies.mark_intentional import MarkIntentionalStrategy
from app.c4.governance_fix.strategies.reextract_registry import ReExtractRegistryStrategy
from app.c4.governance_fix.strategies.remove_relationship import RemoveRelationshipStrategy
from app.c4.governance_fix.strategies.rename_node import RenameNodeStrategy
from app.c4.governance_fix.strategies.update_component_id import UpdateComponentIdStrategy

DEFAULT_STRATEGIES: tuple[FixStrategy, ...] = (
    RenameNodeStrategy(),
    UpdateComponentIdStrategy(),
    FixContainerIdStrategy(),
    AddContainerStrategy(),
    AddComponentDocStrategy(),
    AddRelationshipDocStrategy(),
    CreateCodeSkeletonStrategy(),
    CreateContainerCodeStrategy(),
    MarkIntentionalStrategy(),
    ReExtractRegistryStrategy(),
    DeleteOrphanStrategy(),
    RemoveRelationshipStrategy(),
    DocumentGuidanceStrategy(),
)
