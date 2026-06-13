"""Tests for SketchGenerator V2 (module-spec based)."""

from __future__ import annotations

import json

from app.services.sketch_generator import generate_sketch_from_module_specs


def test_generate_from_module_specs_basic() -> None:
    pages_data = [
        {
            "page_name": "项目工作台主页",
            "page_type": "DASHBOARD",
            "page_id": "Pg_Dashboard",
            "url_route": "/projects",
            "description": "项目列表、健康度卡片",
            "module_id": "DR-001",
            "fields": [
                {"name": "search_keyword", "type": "文本", "required": False},
            ],
            "buttons": [
                {"label": "新建项目", "trigger": "click", "target_page": "新建项目弹窗"},
            ],
            "nav_targets": ["新建项目弹窗", "项目详情侧滑面板"],
            "incoming_from": [],
            "source_md_path": "openspec/.../module-requirements.md",
        },
        {
            "page_name": "新建项目弹窗",
            "page_type": "MODAL",
            "page_id": "Pg_NewProjectModal",
            "url_route": "",
            "description": "分步向导",
            "module_id": "DR-001",
            "fields": [
                {"name": "project_name", "type": "文本", "required": True, "validation": "1-64 字符"},
                {"name": "template_level", "type": "单选", "required": True},
            ],
            "buttons": [
                {"label": "确认创建", "trigger": "click"},
                {"label": "取消", "trigger": "click"},
            ],
            "nav_targets": ["项目工作台主页"],
            "incoming_from": ["项目工作台主页"],
            "source_md_path": "openspec/.../module-requirements.md",
        },
    ]

    results = generate_sketch_from_module_specs(pages_data)
    assert len(results) == 2

    dashboard = results[0]
    assert dashboard["page_name"] == "项目工作台主页"
    assert dashboard["page_type"] == "DASHBOARD"
    assert dashboard["source_module_id"] == "DR-001"
    assert "svg" in dashboard["svg_content"].lower()
    fields = json.loads(dashboard["fields_json"])
    assert len(fields) == 1
    assert fields[0]["name"] == "search_keyword"

    modal = results[1]
    assert modal["page_name"] == "新建项目弹窗"
    assert modal["page_type"] == "MODAL"
    fields = json.loads(modal["fields_json"])
    assert len(fields) == 2
    assert fields[0]["required"] is True
    assert fields[0]["validation"] == "1-64 字符"
    # SVG should contain field labels
    assert "project_name" in modal["svg_content"]
    assert "*" in modal["svg_content"]  # required indicator


def test_generate_empty_fields_fallback() -> None:
    pages_data = [
        {
            "page_name": "空页面",
            "page_type": "FORM",
            "module_id": "DR-002",
            "fields": [],
            "buttons": [],
            "nav_targets": [],
        }
    ]
    results = generate_sketch_from_module_specs(pages_data)
    assert len(results) == 1
    assert "空页面" in results[0]["svg_content"]
