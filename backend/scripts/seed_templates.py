"""Seed script for pre-defined templates and their stages."""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from pathlib import Path

from sqlalchemy import select

# Add project root to PYTHONPATH so 'app' can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.governance.template_engine import TemplateEngine
from app.infrastructure.database.session import AsyncSessionLocal, init_db
from app.models.template import Template
from app.models.template_stage import TemplateStage


async def seed() -> None:
    """Insert templates and stages from TemplateEngine."""
    await init_db()
    engine = TemplateEngine()
    async with AsyncSessionLocal() as session:
        for route in engine.list_routes():
            tpl = engine.get_template(route)
            if tpl is None:
                continue
            template_id = route.capitalize()
            merge_policy = json.dumps(tpl.get_merge_policy())
            existing = await session.get(Template, template_id)
            if existing is None:
                session.add(
                    Template(
                        template_id=template_id,
                        template_name=f"{template_id} 模板",
                        description=tpl.description,
                        stage_count=len(tpl.stages),
                        estimated_skill_count=sum(
                            1 + len(s.auxiliary_skill_ids) for s in tpl.stages
                        ),
                        applicable_complexity=template_id,
                        config_json=None,
                        default_execution_strategy=tpl.execution_strategy,
                        merge_policy_json=merge_policy,
                    )
                )
                print(f"Added template {template_id}")
            else:
                existing.default_execution_strategy = tpl.execution_strategy
                existing.merge_policy_json = merge_policy
                existing.stage_count = len(tpl.stages)
                existing.estimated_skill_count = sum(
                    1 + len(s.auxiliary_skill_ids) for s in tpl.stages
                )
                session.add(existing)
                print(f"Updated template {template_id}")

            existing_stages_result = await session.execute(
                select(TemplateStage.stage_id).where(  # type: ignore[attr-defined]
                    TemplateStage.template_id == template_id
                )
            )
            existing_stage_ids = {row[0] for row in existing_stages_result.all()}

            for stage in tpl.stages:
                stage_id = str(uuid.uuid4())
                if stage_id in existing_stage_ids:
                    continue
                session.add(
                    TemplateStage(
                        stage_id=stage_id,
                        stage_name=stage.stage_name,
                        business_stage_key=stage.business_stage_key,
                        order_index=stage.order,
                        template_id=template_id,
                        primary_skill_id=stage.primary_skill_id,
                        auxiliary_skill_ids=(
                            json.dumps(stage.auxiliary_skill_ids)
                            if stage.auxiliary_skill_ids
                            else None
                        ),
                        gate_id=None,
                        skippable=False,
                        merge_group_id=None,
                        is_present_in=template_id,
                        is_gate_required=stage.is_gate_required,
                        auto_advance=stage.auto_advance,
                    )
                )
                print(f"Added stage {stage.stage_name} for {template_id}")

        await session.commit()
        print("Seed completed.")


if __name__ == "__main__":
    asyncio.run(seed())
