"""Tests for TemplateEngine."""

from __future__ import annotations

import pytest

from app.governance.template_engine import TemplateEngine


class TestTemplateEngine:
    """TemplateEngine tests."""

    @pytest.fixture
    def engine(self) -> TemplateEngine:
        """Return a fresh template engine."""
        return TemplateEngine()

    def test_list_routes(self, engine: TemplateEngine) -> None:
        """All four complexity routes are available."""
        routes = engine.list_routes()
        assert set(routes) == {"trivial", "light", "standard", "deep"}

    @pytest.mark.parametrize(
        ("route", "expected_stage_count", "expected_strategy"),
        [
            ("trivial", 3, "full_auto"),
            ("light", 5, "full_auto"),
            ("standard", 9, "semi_auto"),
            ("deep", 10, "full_manual"),
        ],
    )
    def test_stage_counts(
        self,
        engine: TemplateEngine,
        route: str,
        expected_stage_count: int,
        expected_strategy: str,
    ) -> None:
        """Each route has the expected number of presented stages."""
        template = engine.get_template(route)
        assert template is not None
        assert len(template.stages) == expected_stage_count
        assert template.execution_strategy == expected_strategy

    def test_business_stage_keys_are_set(self, engine: TemplateEngine) -> None:
        """Every stage has a non-empty business_stage_key."""
        for route in engine.list_routes():
            template = engine.get_template(route)
            assert template is not None
            for stage in template.stages:
                assert stage.business_stage_key
                assert stage.stage_name
                assert stage.primary_skill_id

    def test_merge_policy_groups(self, engine: TemplateEngine) -> None:
        """Merge policies match the complexity route design."""
        trivial = engine.get_merge_policy("trivial")
        assert trivial is not None
        assert len(trivial["groups"]) == 3

        light = engine.get_merge_policy("light")
        assert light is not None
        assert len(light["groups"]) == 5

        standard = engine.get_merge_policy("standard")
        assert standard is not None
        assert len(standard["groups"]) == 9

        deep = engine.get_merge_policy("deep")
        assert deep is not None
        assert len(deep["groups"]) == 10

    def test_base_stage_lookup(self, engine: TemplateEngine) -> None:
        """Base stage definitions can be looked up by business key."""
        stage = engine.get_base_stage("build")
        assert stage is not None
        assert stage.primary_skill_id == "executing-plans"
        assert "unit-test-generator" in stage.auxiliary_skill_ids

    def test_list_available_skills(self, engine: TemplateEngine) -> None:
        """list_available_skills returns primary + auxiliary skills."""
        skills = engine.list_available_skills("standard", "build")
        assert "executing-plans" in skills
        assert "unit-test-generator" in skills
