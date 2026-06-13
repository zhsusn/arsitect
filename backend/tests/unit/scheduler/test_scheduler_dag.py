"""Tests for DAGScheduler."""

from __future__ import annotations

from typing import Any

from app.scheduler.dag_scheduler import DAGDefinition, DAGScheduler


class FakeNode:
    """Lightweight plan node stand-in."""

    def __init__(
        self,
        node_id: str,
        skill_id: str,
        stage_id: str,
        order_index: int,
        node_type: str = "primary",
    ) -> None:
        self.node_id = node_id
        self.skill_id = skill_id
        self.stage_id = stage_id
        self.order_index = order_index
        self.node_type = node_type


class TestDAGScheduler:
    """Unit tests for DAG parsing and scheduling."""

    def test_topological_sort_linear(self) -> None:
        """Linear dependency: A -> B -> C."""
        dag = DAGDefinition(project_id="test")
        dag.nodes["A"] = self._make_node("A", [], ["B"])
        dag.nodes["B"] = self._make_node("B", ["A"], ["C"])
        dag.nodes["C"] = self._make_node("C", ["B"], [])

        layers = dag.topological_layers()
        assert len(layers) == 3
        assert layers[0] == ["A"]
        assert layers[1] == ["B"]
        assert layers[2] == ["C"]

    def test_topological_sort_parallel(self) -> None:
        """Parallel dependency: A -> B, A -> C."""
        dag = DAGDefinition(project_id="test")
        dag.nodes["A"] = self._make_node("A", [], ["B", "C"])
        dag.nodes["B"] = self._make_node("B", ["A"], [])
        dag.nodes["C"] = self._make_node("C", ["A"], [])

        layers = dag.topological_layers()
        assert len(layers) == 2
        assert layers[0] == ["A"]
        assert set(layers[1]) == {"B", "C"}

    def test_parse_yaml(self) -> None:
        """YAML DAG parsing."""
        yaml_content = """
skills:
  - id: setup
    name: Setup
    file: setup.py
    outputs: [config.yaml]
  - id: build
    name: Build
    file: build.py
    inputs: [config.yaml]
    depends_on: [setup]
"""
        dag = DAGScheduler.parse_yaml(yaml_content, "test")
        assert len(dag.nodes) == 2
        assert dag.nodes["build"].dependencies == ["setup"]
        assert dag.nodes["setup"].dependents == ["build"]

    def test_from_execution_plan(self) -> None:
        """Building a DAG from existing plan nodes."""
        nodes: list[Any] = [
            FakeNode("n1", "setup", "stage-1", 0),
            FakeNode("n2", "build", "stage-1", 1, "auxiliary"),
            FakeNode("n3", "deploy", "stage-2", 2),
        ]
        dag = DAGScheduler.from_execution_plan("proj-1", nodes)

        assert len(dag.nodes) == 3
        assert "build" in dag.nodes["setup"].dependents
        assert "deploy" in dag.nodes["setup"].dependents

    @staticmethod
    def _make_node(
        skill_id: str,
        dependencies: list[str],
        dependents: list[str],
    ) -> Any:
        """Create a minimal DAGNode-like object."""
        node: Any = type("N", (), {})()
        node.skill_id = skill_id
        node.dependencies = dependencies
        node.dependents = dependents
        return node
