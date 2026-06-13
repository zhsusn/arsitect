"""DocForge — Document standardization engine."""
from .doc_migration_engine import (
    C4RegistryResult,
    C4TagResult,
    DependencyResult,
    MigrationResult,
    extract_c4_entities,
    fill_dependencies,
    inject_c4_tags,
    migrate_legacy_docs,
)

__all__ = [
    "C4RegistryResult",
    "C4TagResult",
    "DependencyResult",
    "MigrationResult",
    "extract_c4_entities",
    "fill_dependencies",
    "inject_c4_tags",
    "migrate_legacy_docs",
]
