"""Tests for SkillResolver."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.skill import Skill
from app.services.skill_resolver import SkillResolver


class TestSkillResolver:
    """Tests for SkillResolver."""

    @pytest.fixture
    def resolver(self) -> SkillResolver:
        """Create a resolver pointing at the real skill directory."""
        return SkillResolver()

    @pytest.mark.asyncio
    async def test_resolve_sync_local_skill(self, resolver: SkillResolver) -> None:
        """Sync resolution finds a real skill by directory name."""
        path = resolver.resolve_sync("brainstorming")
        assert Path(path).name == "SKILL.md"
        assert "brainstorming" in path

    @pytest.mark.asyncio
    async def test_resolve_async_local_skill(self, resolver: SkillResolver) -> None:
        """Async resolution falls back to local file system without session."""
        path = await resolver.resolve("brainstorming")
        assert Path(path).name == "SKILL.md"
        assert "brainstorming" in path

    @pytest.mark.asyncio
    async def test_resolve_from_database(self) -> None:
        """Database directory_path takes precedence over local fallback."""
        async with AsyncSessionLocal() as session:
            existing = (
                await session.execute(
                    select(Skill).where(Skill.skill_name == "__test_resolver__")
                )
            ).scalar_one_or_none()
            if existing is not None:
                await session.delete(existing)
                await session.commit()

            directory = (
                Path(__file__).resolve().parents[4]
                / ".agents"
                / "skills"
                / "brainstorming"
            )
            skill = Skill(
                skill_id="test-resolver-001",
                skill_name="__test_resolver__",
                version="1.0.0",
                pattern="generator",
                directory_path=str(directory),
                description="Resolver test skill",
            )
            session.add(skill)
            await session.commit()

            resolver = SkillResolver(session=session)
            path = await resolver.resolve("__test_resolver__")
            assert Path(path).name == "SKILL.md"
            assert "brainstorming" in path

    @pytest.mark.asyncio
    async def test_resolve_missing_skill_raises(self, resolver: SkillResolver) -> None:
        """Missing skill raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            await resolver.resolve("nonexistent-skill-xyz")

    def test_to_dict(self) -> None:
        """Resolver description is serializable."""
        resolver = SkillResolver(base_dir="/tmp/skills")
        desc = resolver.to_dict()
        assert Path(desc["base_dir"]) == Path("/tmp/skills")
        assert desc["has_session"] is False
