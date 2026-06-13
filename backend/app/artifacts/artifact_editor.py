"""ArtifactEditor — in-platform artifact editing with conflict detection."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from app.common.artifact_store import ArtifactStore


@dataclass
class EditResult:
    """Result of artifact save operation."""

    success: bool
    new_hash: str
    conflict_detected: bool
    message: str
    previous_hash: str | None = None


class ArtifactEditor:
    """Artifact editor.

    Responsibilities:
    1. Read artifact content.
    2. Save edited content.
    3. Conflict detection on save (external modification check).
    4. Mark artifact status after edit.
    """

    def __init__(self, store: ArtifactStore) -> None:
        self.store = store

    async def read(self, relative_path: str) -> str:
        """Read artifact content."""
        return await self.store.read(relative_path)

    async def save(
        self,
        relative_path: str,
        new_content: str,
        expected_hash: str | None = None,
    ) -> EditResult:
        """Save edited artifact.

        Args:
            relative_path: Artifact relative path.
            new_content: New content.
            expected_hash: Hash known by client before editing (for conflict detection).

        Returns:
            EditResult with save outcome.
        """
        if expected_hash is not None:
            changed, current_hash = self.store.check_external_change(relative_path)
            if changed and current_hash != expected_hash:
                return EditResult(
                    success=False,
                    new_hash="",
                    conflict_detected=True,
                    message=(
                        f"Conflict detected: file was modified externally. "
                        f"Expected hash: {expected_hash[:16]}..., "
                        f"Current hash: {current_hash[:16] if current_hash else 'None'}..."
                    ),
                    previous_hash=expected_hash,
                )

        file_path, new_hash = await self.store.write(
            relative_path,
            new_content,
            commit_message=f"Edit {relative_path}",
        )

        return EditResult(
            success=True,
            new_hash=new_hash,
            conflict_detected=False,
            message=f"Saved successfully. New hash: {new_hash[:16]}...",
        )

    def compute_hash(self, content: str) -> str:
        """Compute content hash (for client preview)."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
