"""Tests for StoryPathValidator."""

from __future__ import annotations

from app.services.page_spec_resolver import ModuleSpec, NavEdge, PageSpec
from app.services.story_path_validator import StoryPathValidator


def _make_simple_spec() -> ModuleSpec:
    """Build a simple ModuleSpec with 3 pages and 2 edges."""
    spec = ModuleSpec(module_id="DR-001", module_name="Test")
    spec.pages = [
        PageSpec(page_name="主页", page_type="DASHBOARD"),
        PageSpec(page_name="列表页", page_type="LIST"),
        PageSpec(page_name="详情页", page_type="DETAIL"),
    ]
    spec.nav_edges = [
        NavEdge(source="主页", target="列表页", label="点击列表"),
        NavEdge(source="列表页", target="详情页", label="点击行"),
    ]
    return spec


class TestStoryPathValidator:
    """StoryPathValidator tests."""

    def test_full_coverage_no_gaps(self) -> None:
        spec = _make_simple_spec()
        validator = StoryPathValidator([spec])
        stories = [
            {
                "story_id": "US-001",
                "title": "查看列表",
                "page_desc": "用户在主页进入列表页，然后点击行进入详情页",
            }
        ]
        report = validator.validate(stories)
        assert report.coverage_percent == 100
        assert not report.missing_pages
        assert not report.missing_edges
        assert not report.orphan_pages

    def test_orphan_page(self) -> None:
        spec = _make_simple_spec()
        validator = StoryPathValidator([spec])
        stories = [
            {
                "story_id": "US-001",
                "title": "只看主页",
                "page_desc": "用户在主页浏览",
            }
        ]
        report = validator.validate(stories)
        assert report.coverage_percent == 33
        assert len(report.orphan_pages) == 2
        orphan_names = {g.page_name for g in report.orphan_pages}
        assert "列表页" in orphan_names
        assert "详情页" in orphan_names

    def test_missing_edge(self) -> None:
        spec = _make_simple_spec()
        validator = StoryPathValidator([spec])
        stories = [
            {
                "story_id": "US-001",
                "title": "直接跳转",
                "page_desc": "用户从主页直接进入详情页",
            }
        ]
        report = validator.validate(stories)
        # 主页 -> 详情页 is NOT in nav_edges, so it's a missing edge
        missing = [
            e for e in report.missing_edges if e.from_page == "主页" and e.to_page == "详情页"
        ]
        assert len(missing) == 1

    def test_missing_page_in_story(self) -> None:
        spec = _make_simple_spec()
        validator = StoryPathValidator([spec])
        stories = [
            {
                "story_id": "US-001",
                "title": "神秘页面",
                "page_desc": '用户进入"设置页面"进行操作',
            }
        ]
        report = validator.validate(stories)
        # "设置页面" is not in spec pages
        assert any(g.page_name == "设置页面" for g in report.missing_pages)

    def test_empty_stories(self) -> None:
        spec = _make_simple_spec()
        validator = StoryPathValidator([spec])
        report = validator.validate([])
        assert report.coverage_percent == 0
        assert len(report.orphan_pages) == 3
