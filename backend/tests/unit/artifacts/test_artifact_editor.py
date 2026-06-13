"""Tests for ArtifactEditor."""

from __future__ import annotations

import tempfile

import pytest

from app.artifacts.artifact_editor import ArtifactEditor
from app.common.artifact_store import ArtifactStore
from app.common.project_context import ProjectContext


class TestArtifactEditor:
    """ArtifactEditor unit tests."""

    @pytest.fixture
    def editor(self) -> ArtifactEditor:
        """Editor backed by temp ArtifactStore."""
        tmpdir = tempfile.mkdtemp()
        ctx = ProjectContext("test-art", base_dir=tmpdir)
        store = ArtifactStore(ctx, auto_git_commit=False)
        return ArtifactEditor(store)

    @pytest.mark.asyncio
    async def test_read_and_save(self, editor: ArtifactEditor) -> None:
        """Read and save artifact content."""
        await editor.store.write("design.md", "# Design")

        content = await editor.read("design.md")
        assert content == "# Design"

        result = await editor.save("design.md", "# Updated Design")
        assert result.success is True
        assert result.conflict_detected is False
        assert "Saved successfully" in result.message

        updated = await editor.read("design.md")
        assert updated == "# Updated Design"

    @pytest.mark.asyncio
    async def test_conflict_detection(self, editor: ArtifactEditor) -> None:
        """Save with stale expected_hash detects conflict."""
        await editor.store.write("spec.md", "v1")
        hash_v1 = editor.store._hash_cache.get("spec.md")

        # External modification
        full_path = editor.store.ctx.artifacts_dir / "spec.md"
        full_path.write_text("v2")

        result = await editor.save("spec.md", "v3", expected_hash=hash_v1)
        assert result.success is False
        assert result.conflict_detected is True
        assert "Conflict detected" in result.message

    @pytest.mark.asyncio
    async def test_no_conflict_when_unchanged(self, editor: ArtifactEditor) -> None:
        """Save with correct hash succeeds."""
        await editor.store.write("ok.md", "content")
        hash_val = editor.store._hash_cache.get("ok.md")

        result = await editor.save("ok.md", "new content", expected_hash=hash_val)
        assert result.success is True
        assert result.conflict_detected is False

    @pytest.mark.asyncio
    async def test_save_without_expected_hash(self, editor: ArtifactEditor) -> None:
        """Save without hash always succeeds."""
        await editor.store.write("always.md", "old")

        result = await editor.save("always.md", "new")
        assert result.success is True

    def test_compute_hash(self, editor: ArtifactEditor) -> None:
        """Hash is deterministic for same content."""
        h1 = editor.compute_hash("hello")
        h2 = editor.compute_hash("hello")
        h3 = editor.compute_hash("world")

        assert h1 == h2
        assert h1 != h3
        assert len(h1) == 64
