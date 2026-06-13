"""Seed script for pre-defined templates and their stages."""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from pathlib import Path

# Add project root to PYTHONPATH so 'app' can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.infrastructure.database.session import AsyncSessionLocal, init_db
from app.models.template import Template
from app.models.template_stage import TemplateStage

TEMPLATES = [
    {
        "template_id": "Trivial",
        "template_name": "极简模板",
        "description": "1-2 个阶段，适用于脚本/工具类微型项目",
        "stage_count": 2,
        "estimated_skill_count": 4,
        "applicable_complexity": "low",
        "config_json": {},
    },
    {
        "template_id": "Light",
        "template_name": "轻量模板",
        "description": "3-5 个阶段，适用于 MVP/原型项目",
        "stage_count": 5,
        "estimated_skill_count": 10,
        "applicable_complexity": "low-medium",
        "config_json": {},
    },
    {
        "template_id": "Standard",
        "template_name": "标准模板",
        "description": "6-9 个阶段，适用于常规功能开发",
        "stage_count": 9,
        "estimated_skill_count": 22,
        "applicable_complexity": "medium",
        "config_json": {},
    },
    {
        "template_id": "Deep",
        "template_name": "深度模板",
        "description": "10-12 个阶段，适用于大型/核心系统重构",
        "stage_count": 12,
        "estimated_skill_count": 35,
        "applicable_complexity": "high",
        "config_json": {},
    },
]

STAGES = [
    # Trivial stages
    ("Trivial", 1, "编码实现", "executing-plans", False),
    ("Trivial", 2, "收尾归档", "finish", False),
    # Light stages
    ("Light", 1, "需求分析", "requirement-analysis", False),
    ("Light", 2, "概要设计", "high-level-design", False),
    ("Light", 3, "编码实现", "executing-plans", False),
    ("Light", 4, "单元测试", "unit-test", False),
    ("Light", 5, "收尾归档", "finish", False),
    # Standard stages
    ("Standard", 1, "需求探索", "brainstorming", False),
    ("Standard", 2, "概要需求", "prd-generation", False),
    ("Standard", 3, "详细需求", "detailed-requirements", False),
    ("Standard", 4, "概要设计", "high-level-design", False),
    ("Standard", 5, "详细设计", "detailed-design", False),
    ("Standard", 6, "接口契约", "interface-first-dev", False),
    ("Standard", 7, "编码实现", "executing-plans", False),
    ("Standard", 8, "单元测试", "unit-test", False),
    ("Standard", 9, "收尾归档", "finish", False),
    # Deep stages
    ("Deep", 1, "需求探索", "brainstorming", False),
    ("Deep", 2, "概要需求", "prd-generation", False),
    ("Deep", 3, "详细需求", "detailed-requirements", False),
    ("Deep", 4, "概要设计", "high-level-design", False),
    ("Deep", 5, "详细设计", "detailed-design", False),
    ("Deep", 6, "接口契约", "interface-first-dev", False),
    ("Deep", 7, "编码实现", "executing-plans", False),
    ("Deep", 8, "单元测试", "unit-test", False),
    ("Deep", 9, "集成测试", "integration-test", False),
    ("Deep", 10, "代码审查", "code-review-pipeline", False),
    ("Deep", 11, "UAT", "uat-verification", False),
    ("Deep", 12, "收尾归档", "finish", False),
]


async def seed() -> None:
    """Insert templates and stages."""
    await init_db()
    async with AsyncSessionLocal() as session:
        for tpl_data in TEMPLATES:
            existing = await session.get(Template, tpl_data["template_id"])
            if existing:
                print(f"Template {tpl_data['template_id']} already exists, skipping")
                continue
            data = {**tpl_data}
            if isinstance(data.get("config_json"), dict):
                data["config_json"] = json.dumps(data["config_json"])
            tpl = Template(**data)
            session.add(tpl)
            print(f"Added template {tpl_data['template_id']}")

        for template_id, order_index, stage_name, skill_id, skippable in STAGES:
            stage = TemplateStage(
                stage_id=str(uuid.uuid4()),
                stage_name=stage_name,
                order_index=order_index,
                template_id=template_id,
                primary_skill_id=skill_id,
                skippable=skippable,
                is_present_in=template_id,
            )
            session.add(stage)
            print(f"Added stage {stage_name} for {template_id}")

        await session.commit()
        print("Seed completed.")


if __name__ == "__main__":
    asyncio.run(seed())
