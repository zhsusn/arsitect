"""C4BaselineStore — versioned arsitect.aac.yml storage."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import yaml
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.docforge.c4_assembler import C4Assembler, C4Workspace
from app.models.application import Application
from app.models.c4_baseline import C4Baseline
from app.models.project import Project


@dataclass
class BaselineDTO:
    """Baseline data transfer object."""

    baseline_id: str
    project_id: str
    version: str
    dsl_content: str
    dsl_hash: str
    level: str
    is_current: bool
    created_at: datetime


class C4BaselineStore:
    """C4 DSL versioned baseline repository.

    Responsibilities:
    1. Write DSL with versioning.
    2. Read current or specific version.
    3. Diff between versions.
    4. Rollback to version.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def write(
        self,
        workspace: C4Workspace,
        dsl_content: str,
        compiled_from: list[str] | None = None,
    ) -> str:
        """Write new baseline version.

        Returns:
            New version string.
        """
        await self.db.execute(
            update(C4Baseline)
            .where(C4Baseline.project_id == workspace.project_id)
            .values(is_current=False)
        )

        latest = await self._get_latest(workspace.project_id)
        if latest:
            parts = latest.version.split(".")
            new_version = f"{parts[0]}.{int(parts[1]) + 1}.0"
        else:
            new_version = "1.0.0"

        dsl_hash = hashlib.sha256(dsl_content.encode()).hexdigest()
        baseline = C4Baseline(
            project_id=workspace.project_id,
            version=new_version,
            dsl_content=dsl_content,
            dsl_hash=dsl_hash,
            level="L1-L4",
            is_current=True,
            compiled_from=json.dumps(compiled_from or []),
        )
        self.db.add(baseline)
        await self.db.flush()
        return new_version

    async def read_current(self, project_id: str) -> BaselineDTO | None:
        result = await self.db.execute(
            select(C4Baseline)
            .where(C4Baseline.project_id == project_id)
            .where(C4Baseline.is_current.is_(True))
        )
        baseline = result.scalar_one_or_none()
        if baseline:
            return self._to_dto(baseline)
        # Fallback: auto-sync from filesystem baseline
        synced = await self.sync_from_filesystem(project_id)
        return synced

    async def sync_from_filesystem(self, project_id: str) -> BaselineDTO | None:
        """Read baseline files from disk and write to DB."""
        import traceback

        try:
            baseline_dir = settings.project_root / "openspec" / "changes" / project_id / "baseline"
            registry_path = baseline_dir / "_c4-registry.yaml"
            if not registry_path.exists():
                return None

            registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))

            # Ensure project (and its application) exist to satisfy FK constraints
            proj_result = await self.db.execute(
                select(Project).where(Project.project_id == project_id)
            )
            project = proj_result.scalar_one_or_none()
            if not project:
                app_result = await self.db.execute(
                    select(Application).where(Application.application_id == project_id)
                )
                app = app_result.scalar_one_or_none()
                if not app:
                    app = Application(
                        application_id=project_id,
                        application_name=project_id,
                        local_path=str(settings.project_root / "openspec" / "changes" / project_id),
                        workspace_id="default",
                    )
                    self.db.add(app)
                    await self.db.flush()
                project = Project(
                    project_id=project_id,
                    project_name=project_id,
                    project_status="Draft",
                    application_id=app.application_id,
                    template_level="Standard",
                    progress_percent=0,
                    risk_level="None",
                )
                self.db.add(project)
                await self.db.flush()

            workspace = C4Workspace(project_id=project_id)

            systems = registry.get("systems", {})
            if systems:
                first_key = next(iter(systems))
                first_sys = systems[first_key]
                workspace.system = {"id": first_key, "name": first_sys.get("name", first_key)}

            for eid, info in registry.get("actors", {}).items():
                workspace.actors.append({"id": eid, "name": info.get("name", eid)})

            for eid, info in registry.get("containers", {}).items():
                workspace.containers.append({
                    "id": eid,
                    "name": info.get("name", eid),
                    "technology": ", ".join(info.get("aliases", [])),
                })

            for eid, info in registry.get("components", {}).items():
                workspace.components.append({
                    "id": eid,
                    "name": info.get("name", eid),
                    "properties": {
                        "container_id": info.get("container_id", "default"),
                        "intentional_orphan": bool(info.get("intentional_orphan", False)),
                    },
                })

            for iface in registry.get("interfaces", []):
                workspace.interfaces.append({
                    "id": iface["id"],
                    "name": f"{iface['method']} {iface['path']}",
                    "properties": {"method": iface["method"], "path": iface["path"]},
                })

            # System → container containment
            if workspace.system:
                for c in workspace.containers:
                    workspace.relationships.append({
                        "source": workspace.system["id"],
                        "target": c["id"],
                        "description": "contains",
                    })

            # Relationships from registry
            for rel in registry.get("relationships", []):
                workspace.relationships.append({
                    "source": rel.get("source", ""),
                    "target": rel.get("target", ""),
                    "description": rel.get("description", ""),
                })

            assembler = C4Assembler()
            dsl_content = assembler.serialize_to_yaml(workspace)
            new_hash = hashlib.sha256(dsl_content.encode()).hexdigest()

            # Skip if DB already has identical content
            latest = await self._get_latest(project_id)
            if latest and latest.dsl_hash == new_hash:
                return self._to_dto(latest)

            version = await self.write(workspace, dsl_content, compiled_from=["filesystem_sync"])
            await self.db.commit()

            # Re-read to return fresh DTO
            result = await self.db.execute(
                select(C4Baseline)
                .where(C4Baseline.project_id == project_id)
                .where(C4Baseline.version == version)
            )
            baseline = result.scalar_one_or_none()
            return self._to_dto(baseline) if baseline else None
        except Exception as e:
            print(f"[C4BaselineStore] sync_from_filesystem error: {e}")
            traceback.print_exc()
            return None

    async def read_version(self, project_id: str, version: str) -> BaselineDTO | None:
        result = await self.db.execute(
            select(C4Baseline)
            .where(C4Baseline.project_id == project_id)
            .where(C4Baseline.version == version)
        )
        baseline = result.scalar_one_or_none()
        return self._to_dto(baseline) if baseline else None

    async def list_versions(self, project_id: str) -> list[BaselineDTO]:
        result = await self.db.execute(
            select(C4Baseline)
            .where(C4Baseline.project_id == project_id)
            .order_by(C4Baseline.created_at.desc())
        )
        return [self._to_dto(b) for b in result.scalars().all()]

    async def diff(
        self, project_id: str, version1: str, version2: str
    ) -> dict[str, Any]:
        b1 = await self.read_version(project_id, version1)
        b2 = await self.read_version(project_id, version2)
        if not b1 or not b2:
            return {"error": "Version not found"}

        lines1 = set(b1.dsl_content.split("\n"))
        lines2 = set(b2.dsl_content.split("\n"))
        return {
            "added": sorted(lines2 - lines1),
            "removed": sorted(lines1 - lines2),
            "version1": version1,
            "version2": version2,
        }

    async def rollback(self, project_id: str, version: str) -> str:
        await self.db.execute(
            update(C4Baseline)
            .where(C4Baseline.project_id == project_id)
            .values(is_current=False)
        )
        result = await self.db.execute(
            update(C4Baseline)
            .where(C4Baseline.project_id == project_id)
            .where(C4Baseline.version == version)
            .values(is_current=True)
        )
        if result.rowcount == 0:
            raise ValueError(f"Version {version} not found")
        return version

    async def get_l2_entities(self, project_id: str) -> list[dict[str, Any]]:
        """Return L2 entities (containers + domain entities) for WireframeEngine."""
        baseline = await self.read_current(project_id)
        if not baseline:
            return []
        try:
            data = yaml.safe_load(baseline.dsl_content)
            model = data.get("workspace", {}).get("model", {})
        except yaml.YAMLError:
            return []

        entities: list[dict[str, Any]] = []
        for container in model.get("containers", []):
            entities.append(
                {
                    "id": container["id"],
                    "name": container.get("name", container["id"]),
                    "type": "Container",
                    "technology": container.get("technology", ""),
                }
            )
        for entity in model.get("entities", []):
            entities.append(
                {
                    "id": entity["id"],
                    "name": entity.get("name", entity["id"]),
                    "type": "Entity",
                }
            )
        return entities

    async def _get_latest(self, project_id: str) -> C4Baseline | None:
        result = await self.db.execute(
            select(C4Baseline)
            .where(C4Baseline.project_id == project_id)
            .order_by(C4Baseline.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _to_dto(baseline: C4Baseline) -> BaselineDTO:
        return BaselineDTO(
            baseline_id=baseline.baseline_id,
            project_id=baseline.project_id,
            version=baseline.version,
            dsl_content=baseline.dsl_content,
            dsl_hash=baseline.dsl_hash,
            level=baseline.level,
            is_current=baseline.is_current,
            created_at=baseline.created_at,
        )
