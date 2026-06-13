# 批次三详细设计文档：编排调度 + HITL + 实时推送

> **批次编号**: Batch-03
> **目标**: 能编排执行 DAG，有人工审批，实时状态同步
> **周期**: 3 周
> **组件数**: 6 个
> **前置依赖**: Batch-02（PocketFlowEngine）
> **验收标准**: 见附录 A

---

## 目录

1. [设计概览](#一设计概览)
2. [DAGScheduler](#二dagscheduler)
3. [StateMachineManager](#三statemachinemanager)
4. [GateController](#四gatecontroller)
5. [RealtimePush](#五realtimepush)
6. [FlowCanvas](#六flowcanvas)
7. [StageDetailPanel](#七stagedetailpanel)
8. [API 接口总览](#八api-接口总览)
9. [测试策略](#九测试策略)
10. [附录 A：验收标准](#附录-a验收标准)

---

## 一、设计概览

### 1.1 批次架构图

```
================================================================================
                          前端 (React 19 + Vite 6)
================================================================================
  +------------------+  +------------------+  +------------------+
  | FlowCanvas       |  | StageDetailPanel |  | GateCenter       |
  | (拓扑画布)        |  | (阶段详情)        |  | (审批中心)       |
  |                  |  |                  |  |                  |
  | React Flow       |  | 产物/日志/审查    |  | 待审队列         |
  | 拓扑/泳道/列表    |  | 质量门禁         |  | 确认/驳回/重试   |
  +--------+---------+  +--------+---------+  +--------+---------+
           |                     |                      |
           +----------+----------+                      |
                      |                                 |
================================================================================
                          后端 (FastAPI 0.115)
================================================================================
                      |                                 |
  +-------------------v---------+  +------------------v---------+
  | DAGScheduler (DS-01)        |  | StateMachineManager         |
  |                             |  | (SM-01)                     |
  | YAML DAG 解析               |  |                             |
  | 拓扑排序                     |  | Skill/Project/Artifact      |
  | 按层并行调度                 |  | 三级状态机                   |
  | 超时监控                     |  | 状态流转校验                 |
  +------------+--------+-------+  +------------------+---------+
               |        |                             |
               |        |                             |
  +------------v--+   +v----------------+  +---------v-----------+
  | PocketFlowEng |   | GateController  |  | RealtimePush        |
  | (Batch-02)    |   | (GC-01)         |  | (RP-01)             |
  +---------------+   | 审批队列管理     |  | SSE 推送            |
                      | AI自检摘要       |  | 状态变更通知        |
                      | 决策记录         |  | Gate 通知           |
                      +-----------------+  +---------------------+
```

### 1.2 核心数据流

```
流 1: DAG 编排执行
  YAML DAG 定义 → DAGScheduler.parse() → 拓扑排序 → 按层并行执行
  → PocketFlowEngine.execute() → StateMachineManager.transition()
  → 完成/错误处理

流 2: HITL 审批
  Skill 执行完成 → GateController.create_gate()
  → SSE 推送通知 → GateCenter 展示
  → 用户确认/驳回 → GateController.resolve()
  → 决策记录 → 继续/回滚

流 3: 状态同步
  任何状态变更 → StateMachineManager.transition()
  → EventBus.publish() → RealtimePush.broadcast()
  → 前端 SSE 接收 → UI 更新
```

### 1.3 批次时间线

```
Week 1: DAG 调度 + 状态机
  ├─ Day 1-2:  DAGScheduler（YAML 解析 + 拓扑排序 + 并行调度）
  ├─ Day 3-4:  StateMachineManager（三级状态机定义 + 流转校验）
  └─ Day 5-7:  集成 + 单元测试

Week 2: HITL 审批
  ├─ Day 8-10: GateController（审批队列 + 决策记录）
  ├─ Day 11-12: GateCenter 前端（审批浮层）
  └─ Day 13-14: HITL 集成测试

Week 3: 实时推送 + 可视化
  ├─ Day 15-17: RealtimePush（SSE 实现）
  ├─ Day 18-19: FlowCanvas + StageDetailPanel 前端
  └─ Day 20-21: 端到端集成测试
```



---

## 二、DAGScheduler (DS-01)

**文件**: `backend/app/scheduler/dag_scheduler.py`
**依赖**: PocketFlowEngine, StateMachineManager, GateController
**被依赖**: FlowCanvas（展示执行状态）

### 2.1 设计目标

- YAML 驱动 DAG 构建与执行
- 拓扑排序确定执行顺序
- 按层并行调度（同层无依赖 Skill 并行）
- 超时监控（90s + 30s）
- 错误处理（rollback/retry/skip）

### 2.2 核心实现

```python
# backend/app/scheduler/dag_scheduler.py
import asyncio
from collections import defaultdict, deque
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from app.engine.pocketflow_engine import PocketFlowEngine, SkillConfig, ExecutionResult
from app.scheduler.state_machine import StateMachineManager, SkillState
from app.scheduler.gate_controller import GateController

class ExecutionStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class DAGNode:
    """DAG 节点"""
    skill_id: str
    skill_config: SkillConfig
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    status: ExecutionStatus = ExecutionStatus.RUNNING
    result: Optional[ExecutionResult] = None
    layer: int = 0  # 拓扑层号

@dataclass
class DAGDefinition:
    """DAG 定义"""
    project_id: str
    nodes: Dict[str, DAGNode] = field(default_factory=dict)

    def topological_layers(self) -> List[List[str]]:
        """返回按层分组的拓扑排序结果"""
        in_degree = {nid: 0 for nid in self.nodes}
        for node in self.nodes.values():
            for dep in node.dependencies:
                if dep in self.nodes:
                    in_degree[nid] += 1

        # Kahn 算法
        layers = []
        current = [nid for nid, deg in in_degree.items() if deg == 0]

        while current:
            layers.append(current)
            next_layer = []
            for nid in current:
                for dependent_id in self.nodes[nid].dependents:
                    in_degree[dependent_id] -= 1
                    if in_degree[dependent_id] == 0:
                        next_layer.append(dependent_id)
            current = next_layer

        return layers

class DAGScheduler:
    """
    DAG 调度器

    核心职责:
    1. YAML DAG 解析与构建
    2. 拓扑排序
    3. 按层并行执行
    4. 超时监控
    5. 错误处理
    """

    def __init__(
        self,
        engine: PocketFlowEngine,
        state_machine: StateMachineManager,
        gate_controller: Optional[GateController] = None,
        max_parallel: int = 3,
    ):
        self.engine = engine
        self.state_machine = state_machine
        self.gate = gate_controller
        self.max_parallel = max_parallel
        self._event_handlers: List[Callable] = []

    def on_event(self, handler: Callable):
        """注册事件处理器"""
        self._event_handlers.append(handler)

    def _emit(self, event_type: str, data: Dict):
        """触发事件"""
        for handler in self._event_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(event_type, data))
                else:
                    handler(event_type, data)
            except Exception:
                pass

    # ============================================================
    # YAML 解析
    # ============================================================
    @staticmethod
    def parse_yaml(yaml_content: str, project_id: str) -> DAGDefinition:
        """从 YAML 解析 DAG"""
        import yaml
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
                timeout=skill_data.get("timeout", 90.0),
            )
            node = DAGNode(
                skill_id=skill_id,
                skill_config=config,
                dependencies=skill_data.get("depends_on", []),
            )
            dag.nodes[skill_id] = node

        # 建立 dependents 关系
        for node in dag.nodes.values():
            for dep in node.dependencies:
                if dep in dag.nodes:
                    dag.nodes[dep].dependents.append(node.skill_id)

        return dag

    # ============================================================
    # DAG 执行
    # ============================================================
    async def execute(self, dag: DAGDefinition) -> Dict[str, Any]:
        """
        执行完整 DAG

        流程:
        1. 拓扑排序得到执行层
        2. 逐层执行
        3. 层内并行（受 max_parallel 限制）
        4. 收集结果
        """
        layers = dag.topological_layers()
        self._emit("dag_started", {"project_id": dag.project_id, "layers": len(layers)})

        all_results = {}

        for layer_idx, layer in enumerate(layers):
            self._emit("layer_started", {"layer": layer_idx, "skills": layer})

            # 并行执行层内节点（限制并发数）
            semaphore = asyncio.Semaphore(self.max_parallel)

            async def run_with_limit(skill_id: str) -> ExecutionResult:
                async with semaphore:
                    return await self._execute_node(dag, skill_id)

            tasks = [run_with_limit(sid) for sid in layer]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for skill_id, result in zip(layer, results):
                if isinstance(result, Exception):
                    self._emit("skill_failed", {"skill_id": skill_id, "error": str(result)})
                    all_results[skill_id] = {"status": "error", "error": str(result)}
                else:
                    all_results[skill_id] = {
                        "status": result.status.value,
                        "duration_ms": result.duration_ms,
                    }

            self._emit("layer_completed", {"layer": layer_idx})

        self._emit("dag_completed", {"project_id": dag.project_id, "results": all_results})
        return all_results

    async def _execute_node(self, dag: DAGDefinition, skill_id: str) -> ExecutionResult:
        """执行单个节点"""
        node = dag.nodes[skill_id]

        # 1. 更新状态为 EXECUTING
        await self.state_machine.transition(
            entity_id=skill_id,
            from_state=SkillState.SCHEDULED,
            to_state=SkillState.EXECUTING,
        )
        self._emit("skill_executing", {"skill_id": skill_id})

        # 2. 执行 Skill
        result = await self.engine.execute(node.skill_config)

        # 3. 更新状态
        if result.status.value == "success":
            await self.state_machine.transition(
                entity_id=skill_id,
                from_state=SkillState.EXECUTING,
                to_state=SkillState.COMPLETED,
            )
        else:
            await self.state_machine.transition(
                entity_id=skill_id,
                from_state=SkillState.EXECUTING,
                to_state=SkillState.FAILED,
            )

        node.result = result
        return result

    # ============================================================
    # 取消
    # ============================================================
    async def cancel(self, dag: DAGDefinition):
        """取消 DAG 执行"""
        for node in dag.nodes.values():
            if node.status == ExecutionStatus.RUNNING:
                node.status = ExecutionStatus.CANCELLED
        self._emit("dag_cancelled", {"project_id": dag.project_id})
```



---

## 三、StateMachineManager (SM-01)

**文件**: `backend/app/scheduler/state_machine.py`
**依赖**: DatabaseAdapter, EventBus
**被依赖**: DAGScheduler, GateController, ArtifactEditor

### 3.1 设计目标

- 管理三级状态机：Skill / Project / Artifact
- 状态转换合法性校验
- 事件驱动状态变更
- 持久化到数据库

### 3.2 状态定义

```python
# backend/app/scheduler/state_machine.py
from enum import Enum, auto
from typing import Dict, Set, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

# ============================================================
# Skill 级状态机（9 状态）
# ============================================================
class SkillState(str, Enum):
    PENDING = "pending"              # 初始状态
    SCHEDULED = "scheduled"          # 已调度
    EXECUTING = "executing"          # 正在执行
    GATE_WAITING = "gate_waiting"    # 等待 Gate 审批
    COMPLETED = "completed"          # 正常完成
    FAILED = "failed"                # 执行失败
    SKIPPED = "skipped"              # 被跳过
    REVIEW_PENDING = "review_pending"  # 等待审查
    APPROVED = "approved"            # 审查通过

# 允许的状态转换
SKILL_TRANSITIONS: Dict[SkillState, Set[SkillState]] = {
    SkillState.PENDING: {SkillState.SCHEDULED},
    SkillState.SCHEDULED: {SkillState.EXECUTING, SkillState.SKIPPED},
    SkillState.EXECUTING: {
        SkillState.COMPLETED, SkillState.FAILED,
        SkillState.GATE_WAITING, SkillState.REVIEW_PENDING,
    },
    SkillState.GATE_WAITING: {SkillState.EXECUTING, SkillState.SKIPPED, SkillState.FAILED},
    SkillState.REVIEW_PENDING: {SkillState.APPROVED, SkillState.EXECUTING},
    SkillState.APPROVED: {SkillState.COMPLETED},
    SkillState.FAILED: {SkillState.SCHEDULED},  # 重试
    SkillState.SKIPPED: set(),
    SkillState.COMPLETED: set(),
}

# ============================================================
# Project 级状态机（4 状态）
# ============================================================
class ProjectState(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"

PROJECT_TRANSITIONS: Dict[ProjectState, Set[ProjectState]] = {
    ProjectState.DRAFT: {ProjectState.ACTIVE, ProjectState.CANCELLED},
    ProjectState.ACTIVE: {ProjectState.ARCHIVED, ProjectState.CANCELLED},
    ProjectState.ARCHIVED: set(),
    ProjectState.CANCELLED: set(),
}

# ============================================================
# Artifact 级状态机（4 状态）
# ============================================================
class ArtifactState(str, Enum):
    GENERATED = "generated"   # AI 生成
    EDITED = "edited"         # 人工编辑
    REVIEWING = "reviewing"   # 审查中
    ACCEPTED = "accepted"     # 已接受

ARTIFACT_TRANSITIONS: Dict[ArtifactState, Set[ArtifactState]] = {
    ArtifactState.GENERATED: {ArtifactState.EDITED, ArtifactState.REVIEWING, ArtifactState.ACCEPTED},
    ArtifactState.EDITED: {ArtifactState.REVIEWING, ArtifactState.GENERATED},
    ArtifactState.REVIEWING: {ArtifactState.ACCEPTED, ArtifactState.EDITED},
    ArtifactState.ACCEPTED: {ArtifactState.EDITED},
}

# ============================================================
# 状态机管理器
# ============================================================
@dataclass
class StateTransition:
    entity_type: str       # skill / project / artifact
    entity_id: str
    from_state: str
    to_state: str
    timestamp: datetime
    triggered_by: Optional[str] = None  # 触发者

class StateMachineManager:
    """
    状态机管理器

    职责:
    1. 管理三级状态机
    2. 转换合法性校验
    3. 持久化状态
    4. 触发事件通知
    """

    TRANSITION_MAPS = {
        "skill": SKILL_TRANSITIONS,
        "project": PROJECT_TRANSITIONS,
        "artifact": ARTIFACT_TRANSITIONS,
    }

    def __init__(self, db, event_bus=None):
        self.db = db
        self.event_bus = event_bus

    async def transition(
        self,
        entity_type: str,
        entity_id: str,
        from_state: Enum,
        to_state: Enum,
        triggered_by: Optional[str] = None,
    ) -> bool:
        """
        执行状态转换

        流程:
        1. 校验转换合法性
        2. 更新数据库
        3. 触发事件
        """
        # 1. 校验
        transitions = self.TRANSITION_MAPS.get(entity_type)
        if not transitions:
            raise ValueError(f"Unknown entity type: {entity_type}")

        allowed = transitions.get(from_state, set())
        if to_state not in allowed:
            raise InvalidTransitionError(
                f"Invalid transition: {from_state.value} -> {to_state.value} "
                f"for {entity_type}"
            )

        # 2. 更新数据库
        await self._persist_state(entity_type, entity_id, to_state.value)

        # 3. 触发事件
        transition = StateTransition(
            entity_type=entity_type,
            entity_id=entity_id,
            from_state=from_state.value,
            to_state=to_state.value,
            timestamp=datetime.utcnow(),
            triggered_by=triggered_by,
        )

        if self.event_bus:
            self.event_bus.publish(f"{entity_type}.state_changed", {
                "entity_id": entity_id,
                "from": from_state.value,
                "to": to_state.value,
            })

        return True

    async def get_state(self, entity_type: str, entity_id: str) -> Optional[str]:
        """获取当前状态"""
        return await self._query_state(entity_type, entity_id)

    async def recover_after_crash(self, project_id: str):
        """
        崩溃恢复
        将 EXECUTING/GATE_WAITING 状态的 Skill 重置为 PENDING
        """
        # 查询所有异常状态的 Skill
        crashed = await self._query_crashed_skills(project_id)
        for skill_id in crashed:
            await self._persist_state("skill", skill_id, SkillState.PENDING.value)
            if self.event_bus:
                self.event_bus.publish("skill.recovered", {"skill_id": skill_id})

    async def _persist_state(self, entity_type: str, entity_id: str, state: str):
        """持久化状态到数据库"""
        from app.db.models import SkillExecution
        await self.db.execute(
            update(SkillExecution)
            .where(SkillExecution.id == entity_id)
            .values(status=state)
        )

    async def _query_state(self, entity_type: str, entity_id: str) -> Optional[str]:
        from app.db.models import SkillExecution
        result = await self.db.execute(
            select(SkillExecution.status).where(SkillExecution.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def _query_crashed_skills(self, project_id: str) -> List[str]:
        from app.db.models import SkillExecution
        result = await self.db.execute(
            select(SkillExecution.id)
            .where(SkillExecution.project_id == project_id)
            .where(SkillExecution.status.in_([
                SkillState.EXECUTING.value, SkillState.GATE_WAITING.value
            ]))
        )
        return [r[0] for r in result.all()]

class InvalidTransitionError(Exception):
    pass

from sqlalchemy import select, update
```

---

## 四、GateController (GC-01)

**文件**: `backend/app/scheduler/gate_controller.py`
**依赖**: StateMachineManager, EventBus
**被依赖**: GateCenter（前端审批中心）

### 4.1 设计目标

- Gate 等待队列管理
- AI 自检摘要触发
- 审批决策记录（确认/驳回/重试）
- 旁路审批授权
- human-decisions.md 审计日志

### 4.2 核心实现

```python
# backend/app/scheduler/gate_controller.py
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.scheduler.state_machine import StateMachineManager, SkillState
from app.common.event_bus import EventBus

class GateDecision(str, Enum):
    APPROVED = "approved"      # 确认
    REJECTED = "rejected"      # 驳回
    RETRY = "retry"            # 重试
    BYPASSED = "bypassed"      # 旁路

@dataclass
class GateItem:
    """审批项"""
    gate_id: str
    skill_id: str
    project_id: str
    summary: str               # AI 自检摘要
    created_at: datetime
    decision: Optional[str] = None
    decider: Optional[str] = None
    notes: Optional[str] = None
    resolved_at: Optional[datetime] = None

class GateController:
    """
    审批控制器

    职责:
    1. Gate 等待队列管理
    2. AI 自检摘要生成
    3. 审批决策（确认/驳回/重试/旁路）
    4. 审计日志
    5. 与状态机联动
    """

    def __init__(
        self,
        state_machine: StateMachineManager,
        event_bus: Optional[EventBus] = None,
    ):
        self.state_machine = state_machine
        self.event_bus = event_bus
        self._pending_gates: Dict[str, GateItem] = {}  # gate_id -> GateItem
        self._wait_events: Dict[str, asyncio.Event] = {}  # gate_id -> Event

    # ============================================================
    # 创建 Gate
    # ============================================================
    async def create_gate(
        self, skill_id: str, project_id: str, exec_result: dict
    ) -> str:
        """
        创建审批 Gate

        流程:
        1. 生成 AI 自检摘要
        2. 更新 Skill 状态为 GATE_WAITING
        3. 加入等待队列
        4. 通知前端
        """
        gate_id = f"gate-{skill_id}-{int(datetime.utcnow().timestamp())}"

        # 1. 生成摘要
        summary = await self._generate_summary(skill_id, exec_result)

        # 2. 创建 GateItem
        gate = GateItem(
            gate_id=gate_id,
            skill_id=skill_id,
            project_id=project_id,
            summary=summary,
            created_at=datetime.utcnow(),
        )
        self._pending_gates[gate_id] = gate
        self._wait_events[gate_id] = asyncio.Event()

        # 3. 更新状态
        await self.state_machine.transition(
            entity_type="skill",
            entity_id=skill_id,
            from_state=SkillState.EXECUTING,
            to_state=SkillState.GATE_WAITING,
        )

        # 4. 通知
        if self.event_bus:
            self.event_bus.publish("gate.created", {
                "gate_id": gate_id,
                "skill_id": skill_id,
                "summary": summary,
            })

        return gate_id

    # ============================================================
    # 等待审批
    # ============================================================
    async def wait_for_approval(self, gate_id: str, timeout: Optional[float] = None) -> Dict:
        """
        异步等待审批决策

        Returns:
            {"decision": "approved|rejected|retry", "notes": "..."}
        """
        event = self._wait_events.get(gate_id)
        if not event:
            return {"decision": "error", "notes": "Gate not found"}

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            return {"decision": "timeout", "notes": "Approval timed out"}

        gate = self._pending_gates.get(gate_id)
        if not gate or not gate.decision:
            return {"decision": "error", "notes": "No decision recorded"}

        return {
            "decision": gate.decision,
            "notes": gate.notes or "",
            "decider": gate.decider or "",
        }

    # ============================================================
    # 审批决策
    # ============================================================
    async def approve(self, gate_id: str, user_id: str, notes: str = "") -> bool:
        """确认审批"""
        return await self._resolve(gate_id, GateDecision.APPROVED, user_id, notes)

    async def reject(self, gate_id: str, user_id: str, reason: str = "") -> bool:
        """驳回"""
        return await self._resolve(gate_id, GateDecision.REJECTED, user_id, reason)

    async def retry(self, gate_id: str, user_id: str, notes: str = "") -> bool:
        """重试"""
        return await self._resolve(gate_id, GateDecision.RETRY, user_id, notes)

    async def bypass(self, gate_id: str, admin_id: str, reason: str = "") -> bool:
        """
        旁路审批（需 ADMIN 权限）
        """
        # TODO: 权限校验
        return await self._resolve(gate_id, GateDecision.BYPASSED, admin_id, reason)

    async def _resolve(
        self, gate_id: str, decision: GateDecision, user_id: str, notes: str
    ) -> bool:
        """处理审批决策"""
        gate = self._pending_gates.get(gate_id)
        if not gate:
            return False

        # 1. 记录决策
        gate.decision = decision.value
        gate.decider = user_id
        gate.notes = notes
        gate.resolved_at = datetime.utcnow()

        # 2. 写审计日志
        self._write_audit_log(gate)

        # 3. 更新状态机
        if decision == GateDecision.APPROVED:
            await self.state_machine.transition(
                entity_type="skill", entity_id=gate.skill_id,
                from_state=SkillState.GATE_WAITING, to_state=SkillState.EXECUTING,
                triggered_by=user_id,
            )
        elif decision == GateDecision.REJECTED:
            await self.state_machine.transition(
                entity_type="skill", entity_id=gate.skill_id,
                from_state=SkillState.GATE_WAITING, to_state=SkillState.FAILED,
                triggered_by=user_id,
            )
        elif decision == GateDecision.RETRY:
            await self.state_machine.transition(
                entity_type="skill", entity_id=gate.skill_id,
                from_state=SkillState.GATE_WAITING, to_state=SkillState.SCHEDULED,
                triggered_by=user_id,
            )

        # 4. 通知等待者
        event = self._wait_events.get(gate_id)
        if event:
            event.set()

        # 5. 广播事件
        if self.event_bus:
            self.event_bus.publish("gate.resolved", {
                "gate_id": gate_id, "decision": decision.value,
                "skill_id": gate.skill_id, "decider": user_id,
            })

        return True

    # ============================================================
    # 查询
    # ============================================================
    def get_pending_gates(self, project_id: Optional[str] = None) -> List[GateItem]:
        """获取待审批队列"""
        gates = self._pending_gates.values()
        if project_id:
            gates = [g for g in gates if g.project_id == project_id]
        return [g for g in gates if g.decision is None]

    def get_gate(self, gate_id: str) -> Optional[GateItem]:
        """获取单个 Gate"""
        return self._pending_gates.get(gate_id)

    # ============================================================
    # AI 自检摘要
    # ============================================================
    async def _generate_summary(self, skill_id: str, exec_result: dict) -> str:
        """生成 Gate 自检摘要"""
        # MVP: 规则模板
        # P1: 调用 LLM 分析
        stdout = exec_result.get("stdout", "")[:500]
        stderr = exec_result.get("stderr", "")[:500]
        artifacts = exec_result.get("output_artifacts", [])

        return f"""Skill: {skill_id}
Status: {exec_result.get("status", "unknown")}
Duration: {exec_result.get("duration_ms", 0)}ms
Exit Code: {exec_result.get("exit_code", "N/A")}
Output Artifacts: {', '.join(artifacts) if artifacts else 'None'}
Stderr Preview: {stderr[:200]}
"""

    # ============================================================
    # 审计日志
    # ============================================================
    def _write_audit_log(self, gate: GateItem):
        """写入 human-decisions.md"""
        import os
        log_path = os.path.join("./projects", gate.project_id, "human-decisions.md")

        entry = f"""
## {gate.resolved_at.isoformat()} - {gate.decision.upper()}
- Gate: {gate.gate_id}
- Skill: {gate.skill_id}
- Decider: {gate.decider}
- Notes: {gate.notes or "N/A"}

"""
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry)
```



---

## 五、RealtimePush (RP-01)

**文件**: `backend/app/common/realtime_push.py`
**依赖**: EventBus
**被依赖**: FlowCanvas, GateCenter, StageDetailPanel

### 5.1 设计目标

- SSE (Server-Sent Events) 实时推送
- 状态变更事件广播
- Gate 审批通知
- 多客户端支持

### 5.2 核心实现

```python
# backend/app/common/realtime_push.py
import asyncio
import json
from typing import Dict, Set, Optional
from dataclasses import dataclass, asdict

from fastapi import Request
from fastapi.responses import StreamingResponse

from app.common.event_bus import EventBus

class RealtimePush:
    """
    实时推送服务（SSE）

    职责:
    1. 管理 SSE 客户端连接
    2. 订阅 EventBus 事件
    3. 广播到所有连接的客户端
    """

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._clients: Dict[str, Set[asyncio.Queue]] = {}  # project_id -> queues
        self._subscribed = False

    async def subscribe_events(self):
        """订阅 EventBus 事件"""
        if self._subscribed:
            return
        self._subscribed = True

        self.event_bus.subscribe("skill.state_changed", self._on_skill_state_change)
        self.event_bus.subscribe("gate.created", self._on_gate_created)
        self.event_bus.subscribe("gate.resolved", self._on_gate_resolved)
        self.event_bus.subscribe("dag.started", self._on_dag_event)
        self.event_bus.subscribe("dag.completed", self._on_dag_event)
        self.event_bus.subscribe("layer.started", self._on_dag_event)
        self.event_bus.subscribe("layer.completed", self._on_dag_event)

    def _on_skill_state_change(self, event: dict):
        """Skill 状态变更"""
        self._broadcast(event.get("project_id", ""), {
            "type": "skill_state_changed",
            "data": event,
        })

    def _on_gate_created(self, event: dict):
        """Gate 创建"""
        self._broadcast(event.get("project_id", ""), {
            "type": "gate_created",
            "data": event,
        })

    def _on_gate_resolved(self, event: dict):
        """Gate 解决"""
        self._broadcast(event.get("project_id", ""), {
            "type": "gate_resolved",
            "data": event,
        })

    def _on_dag_event(self, event: dict):
        """DAG 事件"""
        self._broadcast(event.get("project_id", ""), {
            "type": "dag_event",
            "data": event,
        })

    def _broadcast(self, project_id: str, message: dict):
        """广播到项目的所有客户端"""
        if project_id not in self._clients:
            return

        dead_queues = set()
        message_str = f"data: {json.dumps(message)}\n\n"

        for queue in self._clients[project_id]:
            try:
                queue.put_nowait(message_str)
            except asyncio.QueueFull:
                dead_queues.add(queue)

        # 清理失效连接
        for dq in dead_queues:
            self._clients[project_id].discard(dq)

    async def connect(self, project_id: str, request: Request):
        """
        建立 SSE 连接

        使用 FastAPI StreamingResponse
        """
        queue = asyncio.Queue(maxsize=100)

        if project_id not in self._clients:
            self._clients[project_id] = set()
        self._clients[project_id].add(queue)

        async def event_generator():
            try:
                while True:
                    if await request.is_disconnected():
                        break
                    try:
                        message = await asyncio.wait_for(queue.get(), timeout=30.0)
                        yield message
                    except asyncio.TimeoutError:
                        yield ": heartbeat\n\n"
            finally:
                self._clients[project_id].discard(queue)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
```

---

## 六、FlowCanvas (FC-01)

**文件**: `frontend/src/components/FlowCanvas.tsx`
**依赖**: React Flow 12, RealtimePush (SSE)

### 6.1 设计目标

- React Flow 拓扑画布封装
- 三视图切换（拓扑图/泳道/列表）
- 节点状态着色（PENDING/SCHEDULED/EXECUTING/COMPLETED/FAILED）
- 实时状态同步（SSE）

### 6.2 核心实现

```tsx
// frontend/src/components/FlowCanvas.tsx
import { useCallback, useEffect, useState } from "react";
import {
  ReactFlow, Controls, Background, MiniMap,
  useNodesState, useEdgesState, addEdge,
  Node, Edge, Connection,
} from "reactflow";
import "reactflow/dist/style.css";

type ViewMode = "topology" | "swimlane" | "list";

interface SkillNodeData {
  label: string;
  status: string;  // pending/scheduled/executing/completed/failed
  phase: string;
  duration?: number;
}

const STATUS_COLORS: Record<string, string> = {
  pending: "#999",
  scheduled: "#4a90d9",
  executing: "#f5a623",
  completed: "#5cb85c",
  failed: "#d9534f",
  gate_waiting: "#9b59b6",
};

interface FlowCanvasProps {
  projectId: string;
  dag: { nodes: DAGNodeDef[]; edges: DAGEdgeDef[] };
}

interface DAGNodeDef { id: string; label: string; phase: string; status: string; }
interface DAGEdgeDef { source: string; target: string; label?: string; }

export function FlowCanvas({ projectId, dag }: FlowCanvasProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("topology");
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // 初始化节点和边
  useEffect(() => {
    const flowNodes: Node[] = dag.nodes.map((n, i) => ({
      id: n.id,
      type: "default",
      position: { x: (i % 5) * 200, y: Math.floor(i / 5) * 100 },
      data: { label: n.label, status: n.status, phase: n.phase },
      style: {
        border: `2px solid ${STATUS_COLORS[n.status] || "#999"}`,
        background: `${STATUS_COLORS[n.status] || "#999"}22`,
      },
    }));

    const flowEdges: Edge[] = dag.edges.map((e, i) => ({
      id: `e${i}`,
      source: e.source,
      target: e.target,
      label: e.label,
      animated: true,
    }));

    setNodes(flowNodes);
    setEdges(flowEdges);
  }, [dag]);

  // SSE 实时更新
  useEffect(() => {
    const source = new EventSource(`/api/v1/events/${projectId}`);
    source.onmessage = (e) => {
      const event = JSON.parse(e.data);
      if (event.type === "skill_state_changed") {
        const { entity_id, to } = event.data;
        setNodes((nds) =>
          nds.map((n) =>
            n.id === entity_id
              ? {
                  ...n,
                  data: { ...n.data, status: to },
                  style: {
                    border: `2px solid ${STATUS_COLORS[to] || "#999"}`,
                    background: `${STATUS_COLORS[to] || "#999"}22`,
                  },
                }
              : n
          )
        );
      }
    };
    return () => source.close();
  }, [projectId]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  return (
    <div className="flow-canvas" style={{ width: "100%", height: "600px" }}>
      {/* 视图切换 */}
      <div className="view-toggle">
        {(["topology", "swimlane", "list"] as const).map((mode) => (
          <button
            key={mode}
            className={viewMode === mode ? "active" : ""}
            onClick={() => setViewMode(mode)}
          >
            {mode === "topology" && "Topology"}
            {mode === "swimlane" && "Swimlane"}
            {mode === "list" && "List"}
          </button>
        ))}
      </div>

      {/* 图例 */}
      <div className="legend">
        {Object.entries(STATUS_COLORS).map(([status, color]) => (
          <span key={status} className="legend-item">
            <span className="dot" style={{ background: color }} />
            {status}
          </span>
        ))}
      </div>

      {viewMode === "topology" && (
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
        >
          <Controls />
          <MiniMap />
          <Background variant="dots" gap={12} size={1} />
        </ReactFlow>
      )}

      {viewMode === "list" && (
        <div className="node-list">
          <table>
            <thead>
              <tr><th>ID</th><th>Name</th><th>Phase</th><th>Status</th></tr>
            </thead>
            <tbody>
              {nodes.map((n) => (
                <tr key={n.id}>
                  <td>{n.id}</td>
                  <td>{n.data.label}</td>
                  <td>{n.data.phase}</td>
                  <td style={{ color: STATUS_COLORS[n.data.status] }}>{n.data.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
```

---

## 七、StageDetailPanel (SP-01)

**文件**: `frontend/src/components/StageDetailPanel.tsx`
**依赖**: ArtifactRenderer, ArtifactEditor

### 7.1 设计目标

- 右侧滑出面板展示 Skill 详情
- 产物/日志/审查 Tab 切换
- 与 FlowCanvas 联动（点击节点展开）

### 7.2 核心实现

```tsx
// frontend/src/components/StageDetailPanel.tsx
import { useState } from "react";
import { ArtifactRenderer } from "./ArtifactRenderer";
import { ArtifactEditor } from "./ArtifactEditor";

type Tab = "artifacts" | "logs" | "review";

interface SkillDetail {
  skillId: string;
  name: string;
  status: string;
  phase: string;
  duration?: number;
  artifacts: Artifact[];
  logs: string;
}

interface Artifact {
  path: string;
  content: string;
  format: "md" | "yaml" | "json" | "svg" | "html";
}

interface StageDetailPanelProps {
  skill: SkillDetail | null;
  onClose: () => void;
}

export function StageDetailPanel({ skill, onClose }: StageDetailPanelProps) {
  const [activeTab, setActiveTab] = useState<Tab>("artifacts");
  const [editMode, setEditMode] = useState(false);

  if (!skill) return null;

  return (
    <div className="stage-detail-panel">
      {/* 头部 */}
      <div className="panel-header">
        <h3>{skill.name}</h3>
        <button onClick={onClose}>×</button>
      </div>

      {/* 元信息 */}
      <div className="skill-meta">
        <span className={`status status-${skill.status}`}>{skill.status}</span>
        <span className="phase">{skill.phase}</span>
        {skill.duration && <span className="duration">{skill.duration}ms</span>}
      </div>

      {/* Tab 切换 */}
      <div className="tabs">
        {(["artifacts", "logs", "review"] as const).map((tab) => (
          <button
            key={tab}
            className={activeTab === tab ? "active" : ""}
            onClick={() => setActiveTab(tab)}
          >
            {tab === "artifacts" && `Artifacts (${skill.artifacts.length})`}
            {tab === "logs" && "Logs"}
            {tab === "review" && "Review"}
          </button>
        ))}
      </div>

      {/* Tab 内容 */}
      <div className="tab-content">
        {activeTab === "artifacts" && (
          <div className="artifacts-tab">
            <div className="toolbar">
              <button onClick={() => setEditMode(!editMode)}>
                {editMode ? "Preview" : "Edit"}
              </button>
            </div>
            {skill.artifacts.map((artifact) => (
              <div key={artifact.path} className="artifact-item">
                <div className="artifact-path">{artifact.path}</div>
                {editMode ? (
                  <ArtifactEditor
                    projectId=""
                    artifactPath={artifact.path}
                    initialContent={artifact.content}
                    initialHash=""
                    format={artifact.format}
                  />
                ) : (
                  <ArtifactRenderer artifact={artifact} />
                )}
              </div>
            ))}
          </div>
        )}

        {activeTab === "logs" && (
          <div className="logs-tab">
            <pre className="logs-content">{skill.logs || "No logs available."}</pre>
          </div>
        )}

        {activeTab === "review" && (
          <div className="review-tab">
            <p>Review functionality coming in Batch-04.</p>
          </div>
        )}
      </div>
    </div>
  );
}
```

---

## 八、API 接口总览

```python
# backend/app/api/v1/scheduler.py
from fastapi import APIRouter, Depends, BackgroundTasks

from app.scheduler.dag_scheduler import DAGScheduler, DAGDefinition
from app.scheduler.state_machine import StateMachineManager
from app.scheduler.gate_controller import GateController
from app.db.database import get_db

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])

# ============================================================
# DAG 执行
# ============================================================
@router.post("/dag/execute")
async def execute_dag(
    background_tasks: BackgroundTasks,
    project_id: str,
    yaml_content: str,
):
    """解析 YAML 并执行 DAG"""
    dag = DAGScheduler.parse_yaml(yaml_content, project_id)

    # 后台执行
    background_tasks.add_task(_execute_dag_async, dag)

    return {"dag_id": project_id, "layers": len(dag.topological_layers())}

async def _execute_dag_async(dag: DAGDefinition):
    """异步执行 DAG"""
    from app.engine.pocketflow_engine import PocketFlowEngine, KimiCLIAdapter
    from app.common.project_context import ProjectContext

    with ProjectContext(dag.project_id) as ctx:
        engine = PocketFlowEngine(KimiCLIAdapter(), ctx)
        state_machine = StateMachineManager(None)
        scheduler = DAGScheduler(engine, state_machine)
        await scheduler.execute(dag)

# ============================================================
# Gate 审批
# ============================================================
@router.get("/gates/pending")
async def get_pending_gates(
    project_id: Optional[str] = None,
    gate_controller: GateController = Depends(),
):
    """获取待审批队列"""
    gates = gate_controller.get_pending_gates(project_id)
    return {"gates": [
        {"gate_id": g.gate_id, "skill_id": g.skill_id, "summary": g.summary}
        for g in gates
    ]}

@router.post("/gates/{gate_id}/approve")
async def approve_gate(gate_id: str, user_id: str, notes: str = ""):
    """确认审批"""
    controller = GateController(None)
    success = await controller.approve(gate_id, user_id, notes)
    return {"success": success}

@router.post("/gates/{gate_id}/reject")
async def reject_gate(gate_id: str, user_id: str, reason: str = ""):
    """驳回"""
    controller = GateController(None)
    success = await controller.reject(gate_id, user_id, reason)
    return {"success": success}


# backend/app/api/v1/events.py
from fastapi import APIRouter, Request

from app.common.realtime_push import RealtimePush
from app.common.event_bus import get_event_bus

router = APIRouter(prefix="/events", tags=["Events"])

@router.get("/{project_id}")
async def events(project_id: str, request: Request):
    """SSE 事件流"""
    push = RealtimePush(get_event_bus())
    await push.subscribe_events()
    return await push.connect(project_id, request)
```

---

## 九、测试策略

```python
# tests/test_dag_scheduler.py
import pytest
from app.scheduler.dag_scheduler import DAGScheduler, DAGDefinition

class TestDAGScheduler:
    def test_topological_sort_linear(self):
        """线性依赖: A -> B -> C"""
        dag = DAGDefinition(project_id="test")
        dag.nodes["A"] = type("N", (), {"skill_id": "A", "dependencies": [], "dependents": ["B"]})
        dag.nodes["B"] = type("N", (), {"skill_id": "B", "dependencies": ["A"], "dependents": ["C"]})
        dag.nodes["C"] = type("N", (), {"skill_id": "C", "dependencies": ["B"], "dependents": []})

        layers = dag.topological_layers()
        assert len(layers) == 3
        assert layers[0] == ["A"]
        assert layers[1] == ["B"]
        assert layers[2] == ["C"]

    def test_topological_sort_parallel(self):
        """并行依赖: A -> B, A -> C"""
        dag = DAGDefinition(project_id="test")
        dag.nodes["A"] = type("N", (), {"skill_id": "A", "dependencies": [], "dependents": ["B", "C"]})
        dag.nodes["B"] = type("N", (), {"skill_id": "B", "dependencies": ["A"], "dependents": []})
        dag.nodes["C"] = type("N", (), {"skill_id": "C", "dependencies": ["A"], "dependents": []})

        layers = dag.topological_layers()
        assert len(layers) == 2
        assert layers[0] == ["A"]
        assert set(layers[1]) == {"B", "C"}

    def test_parse_yaml(self):
        """YAML DAG 解析"""
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


# tests/test_state_machine.py
import pytest
from app.scheduler.state_machine import StateMachineManager, SkillState, InvalidTransitionError

class TestStateMachine:
    def test_valid_transition(self):
        """合法转换"""
        sm = StateMachineManager(None)
        # PENDING -> SCHEDULED 是合法的
        transitions = sm.TRANSITION_MAPS["skill"]
        assert SkillState.SCHEDULED in transitions[SkillState.PENDING]

    def test_invalid_transition(self):
        """非法转换"""
        sm = StateMachineManager(None)
        # COMPLETED -> EXECUTING 是非法的
        transitions = sm.TRANSITION_MAPS["skill"]
        assert SkillState.EXECUTING not in transitions.get(SkillState.COMPLETED, set())

    def test_all_skill_states_have_transitions(self):
        """所有 Skill 状态都有转换定义"""
        sm = StateMachineManager(None)
        for state in SkillState:
            assert state in sm.TRANSITION_MAPS["skill"]


# tests/test_gate_controller.py
import pytest
import asyncio
from app.scheduler.gate_controller import GateController, GateDecision

class TestGateController:
    @pytest.mark.asyncio
    async def test_create_and_approve_gate(self):
        """创建并审批 Gate"""
        gc = GateController(None)

        # 创建 Gate
        gate_id = await gc.create_gate("skill-1", "proj-1", {
            "status": "success", "stdout": "", "stderr": "", "output_artifacts": ["a.md"]
        })

        # 验证待审批队列
        pending = gc.get_pending_gates("proj-1")
        assert len(pending) == 1
        assert pending[0].gate_id == gate_id

        # 审批
        await gc.approve(gate_id, "user-1", "Looks good")

        # 验证已解决
        gate = gc.get_gate(gate_id)
        assert gate.decision == GateDecision.APPROVED.value
        assert gate.decider == "user-1"

    @pytest.mark.asyncio
    async def test_wait_for_approval(self):
        """异步等待审批"""
        gc = GateController(None)
        gate_id = await gc.create_gate("skill-2", "proj-1", {"status": "success"})

        # 异步在 100ms 后审批
        async def delayed_approve():
            await asyncio.sleep(0.1)
            await gc.approve(gate_id, "user-1", "")

        asyncio.create_task(delayed_approve())

        result = await gc.wait_for_approval(gate_id, timeout=5.0)
        assert result["decision"] == "approved"

    @pytest.mark.asyncio
    async def test_wait_timeout(self):
        """等待超时"""
        gc = GateController(None)
        gate_id = await gc.create_gate("skill-3", "proj-1", {"status": "success"})

        result = await gc.wait_for_approval(gate_id, timeout=0.1)
        assert result["decision"] == "timeout"
```

---

## 附录 A：验收标准

### A.1 功能验收

| # | 组件 | 验收项 | 验证方法 |
|---|------|--------|----------|
| 1 | DAGScheduler | YAML 解析 + 拓扑排序 + 并行执行 | 单元测试 |
| 2 | StateMachineManager | 三级状态机 + 转换校验 | 单元测试 |
| 3 | GateController | 创建/等待/审批/超时 | 单元测试 + 集成测试 |
| 4 | RealtimePush | SSE 连接 + 事件广播 | 手动测试 |
| 5 | FlowCanvas | 三视图 + 状态着色 + SSE 更新 | 前端手动测试 |
| 6 | StageDetailPanel | Tab 切换 + 编辑/预览 | 前端手动测试 |

### A.2 端到端验收

```
[ ] E2E-01: YAML DAG 定义 → DAGScheduler 解析 → 拓扑排序 → 按层并行执行
[ ] E2E-02: Skill 执行 → Gate 创建 → SSE 通知 → 用户审批 → 继续执行
[ ] E2E-03: 状态变更 → EventBus → RealtimePush → 前端 SSE → UI 更新
[ ] E2E-04: FlowCanvas 点击节点 → StageDetailPanel 展开 → 产物预览 → 编辑保存
```

### A.3 性能验收

| 指标 | 目标 |
|------|------|
| DAG 拓扑排序 | < 10ms / 100 节点 |
| 并行执行 | 按 max_parallel 限制 |
| Gate 审批延迟 | < 100ms（用户操作到状态更新）|
| SSE 推送延迟 | < 50ms |
| 崩溃恢复 | < 1s 重置所有异常状态 |

---

> **文档结束**
>
> 批次：Batch-03（编排调度 + HITL + 实时推送）
> 组件数：6 个
> 预计周期：3 周

