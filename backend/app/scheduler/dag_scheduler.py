"""DAG scheduler for skill orchestration."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import yaml

from app.engine.pocketflow_engine import (
    ExecutionResult,
    PocketFlowEngine,
    SkillConfig,
)
from app.scheduler.gate_controller import GateController
from app.scheduler.state_machine import SkillState, StateMachineManager


class ExecutionStatus(StrEnum):
    """DAG node execution status."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DAGNode:
    """A single node in the DAG."""

    skill_id: str
    skill_config: SkillConfig
    dependencies: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)
    status: ExecutionStatus = ExecutionStatus.RUNNING
    result: ExecutionResult | None = None
    layer: int = 0


@dataclass
class DAGDefinition:
    """DAG definition with topological utilities."""

    project_id: str
    nodes: dict[str, DAGNode] = field(default_factory=dict)

    def topological_layers(self) -> list[list[str]]:
        """Return nodes grouped by topological layer using Kahn's algorithm."""
        in_degree: dict[str, int] = dict.fromkeys(self.nodes, 0)
        for node in self.nodes.values():
            for dep in node.dependencies:
                if dep in self.nodes:
                    in_degree[node.skill_id] += 1

        layers: list[list[str]] = []
        current = [nid for nid, deg in in_degree.items() if deg == 0]

        while current:
            layers.append(current)
            next_layer: list[str] = []
            for nid in current:
                for dependent_id in self.nodes[nid].dependents:
                    in_degree[dependent_id] -= 1
                    if in_degree[dependent_id] == 0:
                        next_layer.append(dependent_id)
            current = next_layer

        return layers


class DAGScheduler:
    """YAML-driven DAG scheduler with layer-parallel execution."""

    def __init__(
        self,
        engine: PocketFlowEngine,
        state_machine: StateMachineManager,
        gate_controller: GateController | None = None,
        max_parallel: int = 3,
    ) -> None:
        """Initialize the scheduler.

        Args:
            engine: PocketFlow engine for skill execution.
            state_machine: State machine manager for skill lifecycle.
            gate_controller: Optional gate controller for HITL approvals.
            max_parallel: Maximum number of parallel skills per layer.
        """
        self.engine = engine
        self.state_machine = state_machine
        self.gate = gate_controller
        self.max_parallel = max_parallel
        self._event_handlers: list[Callable[[str, dict[str, Any]], Any]] = []

    def on_event(self, handler: Callable[[str, dict[str, Any]], Any]) -> None:
        """Register an event handler."""
        self._event_handlers.append(handler)

    def _emit(self, event_type: str, data: dict[str, Any]) -> None:
        """Emit an event to all registered handlers."""
        for handler in self._event_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(event_type, data))
                else:
                    handler(event_type, data)
            except Exception:
                pass

    # ============================================================
    # YAML parsing
    # ============================================================
    @staticmethod
    def parse_yaml(yaml_content: str, project_id: str) -> DAGDefinition:
        """Parse a DAG from YAML content."""
        data = yaml.safe_load(yaml_content)
        dag = DAGDefinition(project_id=project_id)
        skills = data.get("skills", [])

        for skill_data in skills:
            skill_id = skill_data["id"]
            config = SkillConfig(
                skill_id=skill_id,
                name=skill_data.get("name", skill_id),
                file_path=skill_data["file"],
                inputs=skill_data.get("inputs", []),
                outputs=skill_data.get("outputs", []),
                timeout=float(skill_data.get("timeout", 90.0)),
                kill_timeout=float(skill_data.get("kill_timeout", 30.0)),
            )
            node = DAGNode(
                skill_id=skill_id,
                skill_config=config,
                dependencies=skill_data.get("depends_on", []),
            )
            dag.nodes[skill_id] = node

        for node in dag.nodes.values():
            for dep in node.dependencies:
                if dep in dag.nodes:
                    dag.nodes[dep].dependents.append(node.skill_id)

        return dag

    # ============================================================
    # Execution plan migration
    # ============================================================
    @staticmethod
    def from_execution_plan(
        project_id: str,
        nodes: list[Any],
        file_path_template: str = "./agents/skills/{skill_name}/SKILL.md",
    ) -> DAGDefinition:
        """Build a DAGDefinition from existing ExecutionPlan nodes.

        This helper migrates the current database-centric execution plan model
        into the Batch-03 DAG scheduler abstraction.
        """
        dag = DAGDefinition(project_id=project_id)
        node_map: dict[str, Any] = {}

        def _get(node: Any, key: str) -> Any:
            if isinstance(node, dict):
                return node.get(key)
            return getattr(node, key, None)

        for node in nodes:
            skill_id = _get(node, "skill_id")
            node_id = _get(node, "node_id")
            node_map[node_id] = node

            config = SkillConfig(
                skill_id=skill_id,
                name=skill_id,
                file_path=file_path_template.format(skill_name=skill_id),
                inputs=[],
                outputs=[],
                timeout=90.0,
            )
            dag.nodes[skill_id] = DAGNode(
                skill_id=skill_id,
                skill_config=config,
                dependencies=[],
            )

        # Build edges based on global execution order:
        # - The first node has no dependencies.
        # - Subsequent nodes depend on the most recent primary node.
        # - Auxiliary nodes additionally depend on the current stage's primary.
        sorted_nodes = sorted(
            nodes,
            key=lambda n: _get(n, "order_index") or 0,
        )
        stage_primary: dict[str, str] = {}
        last_primary_skill_id: str | None = None
        for node in sorted_nodes:
            skill_id = _get(node, "skill_id")
            stage_id = _get(node, "stage_id")
            node_type = _get(node, "node_type")

            deps: set[str] = set()
            if last_primary_skill_id is not None:
                deps.add(last_primary_skill_id)
            if node_type == "auxiliary" and stage_id in stage_primary:
                deps.add(stage_primary[stage_id])

            dag.nodes[skill_id].dependencies = list(deps)

            if node_type == "primary":
                stage_primary[stage_id] = skill_id
                last_primary_skill_id = skill_id

        for node in dag.nodes.values():
            for dep in node.dependencies:
                if dep in dag.nodes:
                    dag.nodes[dep].dependents.append(node.skill_id)

        return dag

    # ============================================================
    # DAG execution
    # ============================================================
    async def execute(self, dag: DAGDefinition) -> dict[str, dict[str, Any]]:
        """Execute the full DAG layer by layer."""
        layers = dag.topological_layers()
        self._emit(
            "dag_started",
            {
                "project_id": dag.project_id,
                "layers": len(layers),
            },
        )

        all_results: dict[str, dict[str, Any]] = {}

        for layer_idx, layer in enumerate(layers):
            self._emit(
                "layer_started",
                {
                    "layer": layer_idx,
                    "skills": layer,
                    "project_id": dag.project_id,
                },
            )

            semaphore = asyncio.Semaphore(self.max_parallel)

            async def run_with_limit(skill_id: str, sem: asyncio.Semaphore) -> ExecutionResult:
                async with sem:
                    return await self._execute_node(dag, skill_id)

            tasks = [run_with_limit(sid, semaphore) for sid in layer]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for skill_id, result in zip(layer, results, strict=True):
                if isinstance(result, Exception):
                    self._emit(
                        "skill_failed",
                        {
                            "skill_id": skill_id,
                            "error": str(result),
                            "project_id": dag.project_id,
                        },
                    )
                    all_results[skill_id] = {
                        "status": "error",
                        "error": str(result),
                    }
                else:
                    assert isinstance(result, ExecutionResult)
                    all_results[skill_id] = {
                        "status": result.status.value,
                        "duration_ms": result.duration_ms,
                    }

            self._emit(
                "layer_completed",
                {
                    "layer": layer_idx,
                    "project_id": dag.project_id,
                },
            )

        self._emit(
            "dag_completed",
            {
                "project_id": dag.project_id,
                "results": all_results,
            },
        )
        return all_results

    async def _execute_node(self, dag: DAGDefinition, skill_id: str) -> ExecutionResult:
        """Execute a single DAG node."""
        node = dag.nodes[skill_id]

        await self.state_machine.transition(
            entity_type="skill",
            entity_id=skill_id,
            from_state=SkillState.SCHEDULED,
            to_state=SkillState.EXECUTING,
        )
        self._emit(
            "skill_executing",
            {
                "skill_id": skill_id,
                "project_id": dag.project_id,
            },
        )

        result = await self.engine.execute(node.skill_config)

        if result.status.value == "success":
            await self.state_machine.transition(
                entity_type="skill",
                entity_id=skill_id,
                from_state=SkillState.EXECUTING,
                to_state=SkillState.COMPLETED,
            )
        else:
            await self.state_machine.transition(
                entity_type="skill",
                entity_id=skill_id,
                from_state=SkillState.EXECUTING,
                to_state=SkillState.FAILED,
            )

        node.result = result
        return result

    # ============================================================
    # Cancellation
    # ============================================================
    async def cancel(self, dag: DAGDefinition) -> None:
        """Cancel the DAG execution."""
        for node in dag.nodes.values():
            if node.status == ExecutionStatus.RUNNING:
                node.status = ExecutionStatus.CANCELLED
        self._emit(
            "dag_cancelled",
            {
                "project_id": dag.project_id,
            },
        )
