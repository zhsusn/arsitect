"""Tests for Skill ORM model."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.infrastructure.database.session import AsyncSessionLocal
from app.models.skill import Skill


class TestSkillModel:
    """Test Skill ORM model and constraints."""

    @pytest.mark.asyncio
    async def test_create_skill(self) -> None:
        """Can insert and retrieve a Skill row."""
        async with AsyncSessionLocal() as session:
            skill = Skill(
                skill_id="skill-001",
                skill_name="brainstorming",
                version="1.0.0",
                pattern="generator",
                directory_path=".agents/skills/brainstorming",
            )
            session.add(skill)
            await session.commit()

            result = await session.execute(select(Skill).where(Skill.skill_id == "skill-001"))
            fetched = result.scalar_one()
            assert fetched.skill_name == "brainstorming"
            assert fetched.parse_status == "PARSED"

    @pytest.mark.asyncio
    async def test_unique_name_version(self) -> None:
        """Duplicate (skill_name, version) raises IntegrityError."""
        from sqlalchemy.exc import IntegrityError

        async with AsyncSessionLocal() as session:
            s1 = Skill(
                skill_id="skill-002",
                skill_name="test-skill",
                version="1.0.0",
                pattern="generator",
                directory_path="/tmp/s1",
            )
            session.add(s1)
            await session.commit()

            s2 = Skill(
                skill_id="skill-003",
                skill_name="test-skill",
                version="1.0.0",
                pattern="pipeline",
                directory_path="/tmp/s2",
            )
            session.add(s2)
            with pytest.raises(IntegrityError):
                await session.commit()
