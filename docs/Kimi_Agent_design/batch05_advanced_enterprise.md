# 批次五详细设计文档：高级功能 + 企业级

> **批次编号**: Batch-05
> **目标**: 历史分析、权限、搜索、通知等企业级功能
> **周期**: 4 周
> **组件数**: 8 个
> **前置依赖**: Batch-04
> **验收标准**: 见附录 A

---

## 目录

1. [设计概览](#一设计概览)
2. [HistoryViewer](#二historyviewer)
3. [PermissionManager](#三permissionmanager)
4. [PrototypeArchBinder](#四prototypearchbinder)
5. [DriftDetector](#五driftdetector)
6. [MetricsCollector](#六metricscollector)
7. [SearchEngine](#七searchengine)
8. [NotificationManager](#八notificationmanager)
9. [ImportExportManager](#九importexportmanager)
10. [API 接口总览](#十api-接口总览)
11. [测试策略](#十一测试策略)
12. [附录 A：验收标准](#附录-a验收标准)

---

## 一、设计概览

### 1.1 批次架构图

```
================================================================================
                          前端 (React 19 + Vite 6)
================================================================================
  +------------------+  +------------------+  +------------------+
  | HistoryViewer    |  | AdminPanel       |  | GlobalSearch     |
  | (历史回溯)        |  | (权限管理)        |  | (全局搜索)       |
  +--------+---------+  +--------+---------+  +--------+---------+
           |                     |                      |
================================================================================
                          后端 (FastAPI 0.115)
================================================================================
           |                     |                      |
  +--------v---------+  +--------v---------+  +--------v---------+
  | HistoryViewer    |  | PermissionManager|  | SearchEngine      |
  | (HV-01)          |  | (PM-01)          |  | (SE-02)           |
  |                  |  |                  |  |                   |
  | 时间线           |  | RBAC             |  | 全文搜索           |
  | 耗时对比         |  | OWNER/ADMIN/     |  | 文件名+内容        |
  | 返工热力图       |  | MEMBER/VISITOR   |  | 过滤+跳转          |
  +------------------+  +------------------+  +------------------+
           |                     |
  +--------v---------+  +--------v---------+  +------------------+
  | MetricsCollector |  |PrototypeArchBinder|  | NotificationMgr  |
  | (MC-01)          |  | (PA-01)          |  | (NM-01)          |
  |                  |  |                  |  |                  |
  | 指标收集         |  | 双向绑定         |  | SSE/邮件/Webhook |
  | 数据源           |  | 接口缺失检测     |  | Timebox 提醒     |
  +------------------+  +------------------+  +------------------+
           |                     |                      |
  +--------v---------+  +--------v---------+  +--------v---------+
  | DriftDetector    |  | ImportExportMgr  |  | (其他)            |
  | (DD-01)          |  | (IE-01)          |  |                  |
  |                  |  |                  |  |                  |
  | 架构漂移检测      |  | 导入/导出        |  |                  |
  | 设计vs实际        |  | .arsitect 格式   |  |                  |
  +------------------+  +------------------+  +------------------+
```

### 1.2 批次时间线

```
Week 1: 历史 + 权限
  ├─ Day 1-3:  HistoryViewer（时间线 + 返工热力图）
  ├─ Day 4-5:  PermissionManager（RBAC）
  └─ Day 6-7:  集成测试

Week 2: 双向绑定 + 漂移
  ├─ Day 8-10: PrototypeArchBinder（接口缺失检测）
  ├─ Day 11-12: DriftDetector（架构漂移）
  └─ Day 13-14: 集成测试

Week 3: 指标 + 搜索
  ├─ Day 15-17: MetricsCollector（指标收集）
  ├─ Day 18-19: SearchEngine（全文搜索）
  └─ Day 20-21: 集成测试

Week 4: 通知 + 导入导出
  ├─ Day 22-24: NotificationManager（多渠道通知）
  ├─ Day 25-26: ImportExportManager（.arsitect 格式）
  └─ Day 27-28: 端到端测试
```



---

## 二、HistoryViewer (HV-01)

**文件**: `frontend/src/components/HistoryViewer.tsx` + `backend/app/advanced/history_viewer.py`
**依赖**: MetricsCollector, DatabaseAdapter
**被依赖**: 前端历史页面

### 2.1 设计目标

- 已完成项目时间线渲染
- 阶段耗时对比图表
- 返工热力图（P1 增强）
- Skill 执行成功率统计

### 2.2 后端实现

```python
# backend/app/advanced/history_viewer.py
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ExecutionRecord:
    skill_id: str
    skill_name: str
    phase: str
    status: str           # completed/failed/skipped
    duration_ms: int
    started_at: datetime
    completed_at: Optional[datetime]
    retry_count: int

@dataclass
class ProjectTimeline:
    project_id: str
    project_name: str
    stages: List[Dict]     # [{name, start, end, skills_count}]
    total_duration_ms: int
    skill_records: List[ExecutionRecord]

class HistoryViewer:
    """
    历史查看器

    职责:
    1. 查询已完成项目的执行历史
    2. 阶段耗时统计
    3. 返工率计算
    """

    def __init__(self, db):
        self.db = db

    async def get_project_timeline(self, project_id: str) -> Optional[ProjectTimeline]:
        """获取项目时间线"""
        from app.db.models import Project, SkillExecution

        # 查询项目
        project_result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            return None

        # 查询执行记录
        exec_result = await self.db.execute(
            select(SkillExecution)
            .where(SkillExecution.project_id == project_id)
            .order_by(SkillExecution.started_at)
        )
        records = exec_result.scalars().all()

        skill_records = [
            ExecutionRecord(
                skill_id=r.skill_id,
                skill_name=r.skill_id,  # 可扩展查询名称
                phase=r.phase,
                status=r.status,
                duration_ms=r.duration_ms or 0,
                started_at=r.started_at,
                completed_at=r.completed_at,
                retry_count=getattr(r, "retry_count", 0),
            )
            for r in records
        ]

        # 按阶段分组
        stages = self._group_by_phase(skill_records)

        total_duration = sum(r.duration_ms for r in skill_records)

        return ProjectTimeline(
            project_id=project_id,
            project_name=project.name,
            stages=stages,
            total_duration_ms=total_duration,
            skill_records=skill_records,
        )

    def _group_by_phase(self, records: List[ExecutionRecord]) -> List[Dict]:
        """按阶段分组"""
        from collections import defaultdict
        phases = defaultdict(list)
        for r in records:
            phases[r.phase].append(r)

        result = []
        for phase_name, phase_records in sorted(phases.items()):
            durations = [r.duration_ms for r in phase_records]
            result.append({
                "name": phase_name,
                "skill_count": len(phase_records),
                "total_duration_ms": sum(durations),
                "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
                "success_rate": len([r for r in phase_records if r.status == "completed"]) / len(phase_records) if phase_records else 0,
                "start": min((r.started_at for r in phase_records), default=None),
                "end": max((r.completed_at for r in phase_records if r.completed_at), default=None),
            })
        return result

    async def get_rework_heatmap(self, project_id: str) -> Dict:
        """
        返工热力图数据

        计算每个 Skill 的重试次数，生成热力图
        """
        timeline = await self.get_project_timeline(project_id)
        if not timeline:
            return {}

        heatmap = {}
        for record in timeline.skill_records:
            key = f"{record.phase}.{record.skill_id}"
            heatmap[key] = {
                "skill_id": record.skill_id,
                "phase": record.phase,
                "retry_count": record.retry_count,
                "intensity": min(record.retry_count / 3, 1.0),  # 3次=最大强度
            }

        return heatmap

    async def list_completed_projects(self, limit: int = 20) -> List[Dict]:
        """列出已完成项目"""
        from app.db.models import Project

        result = await self.db.execute(
            select(Project)
            .where(Project.state == "archived")
            .order_by(Project.updated_at.desc())
            .limit(limit)
        )
        return [
            {"id": p.id, "name": p.name, "completed_at": p.updated_at}
            for p in result.scalars().all()
        ]

from sqlalchemy import select
```

### 2.3 前端实现

```tsx
// frontend/src/components/HistoryViewer.tsx
import { useState, useEffect } from "react";

interface TimelineStage {
  name: string;
  skill_count: number;
  total_duration_ms: number;
  avg_duration_ms: number;
  success_rate: number;
}

interface HistoryViewerProps {
  projectId: string;
}

export function HistoryViewer({ projectId }: HistoryViewerProps) {
  const [timeline, setTimeline] = useState<TimelineStage[]>([]);
  const [heatmap, setHeatmap] = useState<Record<string, any>>({});

  useEffect(() => {
    fetch(`/api/v1/history/${projectId}/timeline`)
      .then((r) => r.json())
      .then((d) => setTimeline(d.stages));

    fetch(`/api/v1/history/${projectId}/heatmap`)
      .then((r) => r.json())
      .then((d) => setHeatmap(d));
  }, [projectId]);

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  return (
    <div className="history-viewer">
      <h3>Execution Timeline</h3>

      {/* 阶段耗时对比 */}
      <div className="timeline-chart">
        {timeline.map((stage) => (
          <div key={stage.name} className="stage-bar">
            <div className="stage-label">{stage.name}</div>
            <div className="stage-bar-container">
              <div
                className="stage-bar-fill"
                style={{
                  width: `${Math.min(stage.success_rate * 100, 100)}%`,
                  background: stage.success_rate > 0.8 ? "#5cb85c" : stage.success_rate > 0.5 ? "#f5a623" : "#d9534f",
                }}
              />
            </div>
            <div className="stage-stats">
              {stage.skill_count} skills | {formatDuration(stage.total_duration_ms)} | {(stage.success_rate * 100).toFixed(0)}%
            </div>
          </div>
        ))}
      </div>

      {/* 返工热力图 */}
      <h3>Rework Heatmap</h3>
      <div className="heatmap-grid">
        {Object.entries(heatmap).map(([key, data]) => (
          <div
            key={key}
            className="heatmap-cell"
            style={{
              background: `rgba(217, 83, 79, ${data.intensity})`,
              color: data.intensity > 0.5 ? "white" : "#333",
            }}
            title={`${data.skill_id}: ${data.retry_count} retries`}
          >
            {data.skill_id}
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 三、PermissionManager (PM-01)

**文件**: `backend/app/advanced/permission_manager.py`
**依赖**: DatabaseAdapter
**被依赖**: AdminPanel（前端）

### 3.1 设计目标

- RBAC 权限管理
- 四角色：OWNER/ADMIN/MEMBER/VISITOR
- Gate 旁路审批鉴权
- 项目级权限隔离

### 3.2 核心实现

```python
# backend/app/advanced/permission_manager.py
from enum import Enum
from typing import List, Dict, Optional, Set
from dataclasses import dataclass

class Role(str, Enum):
    OWNER = "owner"       # 全部权限
    ADMIN = "admin"       # 管理权限（含旁路审批）
    MEMBER = "member"     # 成员权限
    VISITOR = "visitor"   # 只读权限

class Permission(str, Enum):
    PROJECT_READ = "project:read"
    PROJECT_WRITE = "project:write"
    PROJECT_DELETE = "project:delete"
    SKILL_EXECUTE = "skill:execute"
    SKILL_EDIT = "skill:edit"
    GATE_APPROVE = "gate:approve"
    GATE_BYPASS = "gate:bypass"
    DSL_EDIT = "dsl:edit"
    SETTINGS_READ = "settings:read"
    SETTINGS_WRITE = "settings:write"

# 角色权限映射
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.OWNER: set(Permission),  # 全部权限
    Role.ADMIN: {
        Permission.PROJECT_READ, Permission.PROJECT_WRITE,
        Permission.SKILL_EXECUTE, Permission.SKILL_EDIT,
        Permission.GATE_APPROVE, Permission.GATE_BYPASS,
        Permission.DSL_EDIT,
        Permission.SETTINGS_READ, Permission.SETTINGS_WRITE,
    },
    Role.MEMBER: {
        Permission.PROJECT_READ, Permission.PROJECT_WRITE,
        Permission.SKILL_EXECUTE,
        Permission.GATE_APPROVE,
        Permission.DSL_EDIT,
        Permission.SETTINGS_READ,
    },
    Role.VISITOR: {
        Permission.PROJECT_READ,
        Permission.SETTINGS_READ,
    },
}

@dataclass
class ProjectMember:
    user_id: str
    project_id: str
    role: Role

class PermissionManager:
    """
    权限管理器

    职责:
    1. 角色管理
    2. 权限校验
    3. 项目级权限隔离
    """

    def __init__(self, db):
        self.db = db

    def has_permission(self, user_id: str, project_id: str, permission: Permission) -> bool:
        """检查用户是否有某权限"""
        # TODO: 查询数据库获取角色
        # 简化实现：OWNER 有全部权限
        role = self._get_user_role(user_id, project_id)
        if not role:
            return False
        return permission in ROLE_PERMISSIONS.get(role, set())

    def can_bypass_gate(self, user_id: str, project_id: str) -> bool:
        """检查是否可以旁路审批"""
        return self.has_permission(user_id, project_id, Permission.GATE_BYPASS)

    def _get_user_role(self, user_id: str, project_id: str) -> Optional[Role]:
        """获取用户在项目中的角色"""
        # TODO: 从数据库查询
        # 简化：单用户模式默认 OWNER
        return Role.OWNER

    async def assign_role(self, project_id: str, user_id: str, role: Role):
        """分配角色"""
        # TODO: 持久化到数据库
        pass

    async def list_members(self, project_id: str) -> List[ProjectMember]:
        """列出项目成员"""
        # TODO: 查询数据库
        return []
```

---

## 四、PrototypeArchBinder (PA-01)

**文件**: `backend/app/advanced/prototype_arch_binder.py`
**依赖**: C4BaselineStore, InterfaceContractStore
**被依赖**: 前端双向绑定面板

### 4.1 设计目标

- 原型接口缺失检测
- C4 DSL 自动回写
- 变更标记

### 4.2 核心实现

```python
# backend/app/advanced/prototype_arch_binder.py
from typing import List, Dict, Optional
from dataclasses import dataclass

from app.c4.baseline_store import C4BaselineStore
from app.c4.interface_contract_store import InterfaceContractStore

@dataclass
class InterfaceGap:
    """接口差异"""
    contract_id: str
    endpoint_path: str
    method: str
    gap_type: str       # "missing_in_proto" | "missing_in_contract"
    suggestion: str

class PrototypeArchBinder:
    """
    原型-架构双向绑定

    职责:
    1. 检测原型中实现但契约未定义的接口
    2. 检测契约定义但原型未实现的接口
    3. 一键回写 C4 DSL
    """

    def __init__(
        self,
        baseline_store: C4BaselineStore,
        contract_store: InterfaceContractStore,
    ):
        self.baseline = baseline_store
        self.contracts = contract_store

    async def detect_gaps(self, project_id: str, proto_interfaces: List[Dict]) -> List[InterfaceGap]:
        """
        检测接口差异

        Args:
            project_id: 项目 ID
            proto_interfaces: 原型中发现的接口列表 [{path, method}]

        Returns:
            List[InterfaceGap]: 差异列表
        """
        gaps = []

        # 1. 获取契约中的接口
        contract_interfaces = await self.contracts.list_by_project(project_id)
        contract_set = {
            (c.endpoint_path, c.method)
            for c in contract_interfaces
        }

        # 2. 获取原型中的接口
        proto_set = {
            (p["path"], p["method"])
            for p in proto_interfaces
        }

        # 3. 契约中有但原型中没有
        for c in contract_interfaces:
            if (c.endpoint_path, c.method) not in proto_set:
                gaps.append(InterfaceGap(
                    contract_id=c.contract_id,
                    endpoint_path=c.endpoint_path,
                    method=c.method,
                    gap_type="missing_in_proto",
                    suggestion=f"Implement {c.method} {c.endpoint_path} in prototype",
                ))

        # 4. 原型中有但契约中没有
        for p in proto_interfaces:
            if (p["path"], p["method"]) not in contract_set:
                gaps.append(InterfaceGap(
                    contract_id="",
                    endpoint_path=p["path"],
                    method=p["method"],
                    gap_type="missing_in_contract",
                    suggestion=f"Add {p['method']} {p['path']} to interface contract",
                ))

        return gaps

    async def sync_to_dsl(self, project_id: str, gaps: List[InterfaceGap]) -> bool:
        """将缺失的接口回写到 C4 DSL"""
        # 1. 读取当前 DSL
        baseline = await self.baseline.read_current(project_id)
        if not baseline:
            return False

        import yaml
        dsl_data = yaml.safe_load(baseline.dsl_content)

        # 2. 添加缺失的接口
        model = dsl_data.setdefault("workspace", {}).setdefault("model", {})
        interfaces = model.setdefault("interfaces", [])

        for gap in gaps:
            if gap.gap_type == "missing_in_contract":
                interfaces.append({
                    "id": f"{gap.method}_{gap.endpoint_path.replace('/', '_').strip('_')}",
                    "method": gap.method,
                    "path": gap.endpoint_path,
                })

        # 3. 写回
        new_dsl = yaml.dump(dsl_data, allow_unicode=True)
        # TODO: 通过 C4DSLManager 写入新版本

        return True
```

---

## 五、DriftDetector (DD-01)

**文件**: `backend/app/advanced/drift_detector.py`
**依赖**: C4BaselineStore, BindingRegistry
**被依赖**: 前端漂移报告

### 5.1 设计目标

- 设计架构 vs 实际代码扫描架构对比
- 差异报告生成

### 5.2 核心实现

```python
# backend/app/advanced/drift_detector.py
from typing import List, Dict, Optional
from dataclasses import dataclass

from app.c4.baseline_store import C4BaselineStore

@dataclass
class DriftReport:
    project_id: str
    checked_at: str
    additions: List[Dict]    # 代码中有但 DSL 中没有
    deletions: List[Dict]   # DSL 中有但代码中没有
    modifications: List[Dict]  # 两者都有但定义不同

class DriftDetector:
    """
    架构漂移检测器

    职责:
    1. 扫描代码目录提取实际架构
    2. 与 C4 DSL 对比
    3. 生成差异报告

    P1 功能，MVP 可简化
    """

    def __init__(self, baseline_store: C4BaselineStore):
        self.baseline = baseline_store

    async def detect(self, project_id: str, code_dir: str) -> DriftReport:
        """
        检测架构漂移

        流程:
        1. 加载 C4 DSL（设计架构）
        2. 扫描代码目录（实际架构）
        3. 对比差异
        """
        # 1. 加载设计架构
        baseline = await self.baseline.read_current(project_id)
        design_components = self._extract_design_components(baseline.dsl_content if baseline else "")

        # 2. 扫描实际架构（简化：扫描文件名）
        actual_components = self._scan_code_directory(code_dir)

        # 3. 对比
        additions = [c for c in actual_components if c["id"] not in {d["id"] for d in design_components}]
        deletions = [c for c in design_components if c["id"] not in {a["id"] for a in actual_components}]

        return DriftReport(
            project_id=project_id,
            checked_at=datetime.utcnow().isoformat(),
            additions=additions,
            deletions=deletions,
            modifications=[],
        )

    def _extract_design_components(self, dsl_content: str) -> List[Dict]:
        """从 DSL 提取组件定义"""
        import yaml
        try:
            data = yaml.safe_load(dsl_content)
            model = data.get("workspace", {}).get("model", {})
            return model.get("components", [])
        except yaml.YAMLError:
            return []

    def _scan_code_directory(self, code_dir: str) -> List[Dict]:
        """扫描代码目录提取组件（简化实现）"""
        from pathlib import Path
        components = []
        path = Path(code_dir)

        # 扫描常见的控制器/服务文件
        for pattern in ["**/*controller*.py", "**/*service*.py", "**/*handler*.py"]:
            for file in path.rglob(pattern.replace("**/*", "").replace("*.py", ".py")):
                components.append({
                    "id": file.stem,
                    "name": file.stem,
                    "type": "code_file",
                    "path": str(file),
                })

        return components

from datetime import datetime
```

---

## 六、MetricsCollector (MC-01)

**文件**: `backend/app/advanced/metrics_collector.py`
**依赖**: DatabaseAdapter
**被依赖**: HistoryViewer

### 6.1 设计目标

- 指标收集（执行耗时、Gate 等待时间、重试次数）
- 为历史回溯提供数据

### 6.2 核心实现

```python
# backend/app/advanced/metrics_collector.py
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SkillMetrics:
    skill_id: str
    project_id: str
    execution_count: int
    total_duration_ms: int
    avg_duration_ms: float
    success_count: int
    fail_count: int
    retry_count: int
    avg_gate_wait_ms: int

class MetricsCollector:
    """
    指标收集器

    职责:
    1. 收集执行指标
    2. 聚合统计
    3. 为 HistoryViewer 提供数据
    """

    def __init__(self, db):
        self.db = db

    async def record_execution(
        self, skill_id: str, project_id: str,
        duration_ms: int, success: bool, retry_count: int = 0,
    ):
        """记录执行指标"""
        from app.db.models import SkillMetrics as MetricsModel

        # 查询或创建记录
        result = await self.db.execute(
            select(MetricsModel)
            .where(MetricsModel.skill_id == skill_id)
            .where(MetricsModel.project_id == project_id)
        )
        metrics = result.scalar_one_or_none()

        if not metrics:
            metrics = MetricsModel(
                skill_id=skill_id,
                project_id=project_id,
                execution_count=0,
                total_duration_ms=0,
                success_count=0,
                fail_count=0,
                retry_count=0,
            )
            self.db.add(metrics)

        metrics.execution_count += 1
        metrics.total_duration_ms += duration_ms
        if success:
            metrics.success_count += 1
        else:
            metrics.fail_count += 1
        metrics.retry_count += retry_count

        await self.db.flush()

    async def get_skill_metrics(self, skill_id: str, project_id: str) -> Optional[SkillMetrics]:
        """获取 Skill 指标"""
        from app.db.models import SkillMetrics as MetricsModel

        result = await self.db.execute(
            select(MetricsModel)
            .where(MetricsModel.skill_id == skill_id)
            .where(MetricsModel.project_id == project_id)
        )
        m = result.scalar_one_or_none()
        if not m:
            return None

        return SkillMetrics(
            skill_id=m.skill_id,
            project_id=m.project_id,
            execution_count=m.execution_count,
            total_duration_ms=m.total_duration_ms,
            avg_duration_ms=m.total_duration_ms / m.execution_count if m.execution_count else 0,
            success_count=m.success_count,
            fail_count=m.fail_count,
            retry_count=m.retry_count,
            avg_gate_wait_ms=0,  # TODO: 记录 Gate 等待时间
        )

from sqlalchemy import select
```

---

## 七、SearchEngine (SE-02)

**文件**: `backend/app/advanced/search_engine.py`
**依赖**: ArtifactStore, C4BaselineStore, FragmentRegistry
**被依赖**: GlobalSearch（前端）

### 7.1 设计目标

- 全产物内容搜索（文件名 + 内容）
- 支持过滤和快速跳转

### 7.2 核心实现

```python
# backend/app/advanced/search_engine.py
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class SearchResult:
    type: str           # artifact / c4_node / fragment
    id: str
    title: str
    preview: str        # 匹配内容预览
    path: str           # 跳转路径
    score: float        # 匹配度

class SearchEngine:
    """
    搜索引擎

    职责:
    1. 全文搜索产物内容
    2. 搜索 C4 节点
    3. 搜索文档片段

    MVP 实现：线性扫描（P1 可引入 Elasticsearch）
    """

    def __init__(self, artifact_store, baseline_store, fragment_registry):
        self.artifacts = artifact_store
        self.baseline = baseline_store
        self.fragments = fragment_registry

    async def search(
        self, project_id: str, query: str, filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        全文搜索

        Args:
            project_id: 项目 ID
            query: 搜索关键词
            filters: {type: "artifact|c4|fragment", format: "md|yaml|json"}

        Returns:
            List[SearchResult]: 搜索结果按匹配度排序
        """
        results = []
        query_lower = query.lower()

        # 1. 搜索产物
        if not filters or filters.get("type") in (None, "artifact"):
            artifact_results = await self._search_artifacts(project_id, query_lower)
            results.extend(artifact_results)

        # 2. 搜索 C4 节点
        if not filters or filters.get("type") in (None, "c4"):
            c4_results = await self._search_c4(project_id, query_lower)
            results.extend(c4_results)

        # 3. 搜索文档片段
        if not filters or filters.get("type") in (None, "fragment"):
            fragment_results = await self._search_fragments(project_id, query_lower)
            results.extend(fragment_results)

        # 按匹配度排序
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:50]  # 最多 50 条

    async def _search_artifacts(self, project_id: str, query: str) -> List[SearchResult]:
        """搜索产物"""
        results = []
        # TODO: 遍历产物目录
        # 简化实现
        return results

    async def _search_c4(self, project_id: str, query: str) -> List[SearchResult]:
        """搜索 C4 节点"""
        results = []
        baseline = await self.baseline.read_current(project_id)
        if not baseline:
            return results

        import yaml
        try:
            data = yaml.safe_load(baseline.dsl_content)
            model = data.get("workspace", {}).get("model", {})

            for container in model.get("containers", []):
                if query in container.get("name", "").lower() or query in container.get("id", "").lower():
                    results.append(SearchResult(
                        type="c4_node",
                        id=container["id"],
                        title=f"Container: {container.get('name', container['id'])}",
                        preview=f"Technology: {container.get('technology', 'N/A')}",
                        path=f"/c4?node={container['id']}",
                        score=1.0,
                    ))

            for component in model.get("components", []):
                if query in component.get("name", "").lower() or query in component.get("id", "").lower():
                    results.append(SearchResult(
                        type="c4_node",
                        id=component["id"],
                        title=f"Component: {component.get('name', component['id'])}",
                        preview=f"",
                        path=f"/c4?node={component['id']}",
                        score=1.0,
                    ))
        except yaml.YAMLError:
            pass

        return results

    async def _search_fragments(self, project_id: str, query: str) -> List[SearchResult]:
        """搜索文档片段"""
        results = []
        fragments = await self.fragments.list_by_project(project_id)
        for frag in fragments:
            if query in frag.title.lower() or query in frag.content.lower()[:1000]:
                score = 0.5
                if query in frag.title.lower():
                    score = 1.0
                results.append(SearchResult(
                    type="fragment",
                    id=frag.id,
                    title=frag.title,
                    preview=frag.content[:200],
                    path=f"/documents/{frag.id}",
                    score=score,
                ))
        return results
```



---

## 八、NotificationManager (NM-01)

**文件**: `backend/app/advanced/notification_manager.py`
**依赖**: EventBus
**被依赖**: 前端通知中心

### 8.1 设计目标

- 多渠道通知（SSE/Webhook）
- Timebox 到期提醒
- Gate 审批通知

### 8.2 核心实现

```python
# backend/app/advanced/notification_manager.py
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class NotificationChannel(str, Enum):
    SSE = "sse"           # Server-Sent Events
    WEBHOOK = "webhook"   # HTTP Webhook

@dataclass
class Notification:
    id: str
    type: str             # gate/timeout/system
    title: str
    message: str
    project_id: str
    channels: List[str]
    created_at: datetime
    read: bool = False

class NotificationManager:
    """
    通知管理器

    职责:
    1. 多渠道通知发送
    2. 通知历史管理
    3. Timebox 提醒
    """

    def __init__(self, event_bus):
        self.event_bus = event_bus
        self._notifications: Dict[str, List[Notification]] = {}  # project_id -> notifications
        self._handlers: Dict[str, Callable] = {}

        self._register_default_handlers()

    def _register_default_handlers(self):
        """注册默认通知处理器"""
        self.event_bus.subscribe("gate.created", self._on_gate_created)
        self.event_bus.subscribe("timebox.warning", self._on_timebox_warning)

    def _on_gate_created(self, event: dict):
        """Gate 创建通知"""
        self.send(
            type="gate",
            title="Approval Required",
            message=f"Skill '{event.get('skill_id')}' requires approval",
            project_id=event.get("project_id", ""),
            channels=[NotificationChannel.SSE],
        )

    def _on_timebox_warning(self, event: dict):
        """Timebox 警告通知"""
        self.send(
            type="timeout",
            title="Timebox Warning",
            message=f"Milestone '{event.get('milestone')}' approaching deadline",
            project_id=event.get("project_id", ""),
            channels=[NotificationChannel.SSE],
        )

    def send(
        self, type: str, title: str, message: str,
        project_id: str, channels: List[str],
    ):
        """发送通知"""
        notification = Notification(
            id=f"notif-{int(datetime.utcnow().timestamp())}",
            type=type,
            title=title,
            message=message,
            project_id=project_id,
            channels=channels,
            created_at=datetime.utcnow(),
        )

        # 存储
        if project_id not in self._notifications:
            self._notifications[project_id] = []
        self._notifications[project_id].append(notification)

        # 通过各渠道发送
        for channel in channels:
            handler = self._handlers.get(channel)
            if handler:
                handler(notification)

    def register_channel_handler(self, channel: str, handler: Callable):
        """注册渠道处理器"""
        self._handlers[channel] = handler

    def get_unread(self, project_id: str) -> List[Notification]:
        """获取未读通知"""
        notifications = self._notifications.get(project_id, [])
        return [n for n in notifications if not n.read]

    def mark_read(self, project_id: str, notification_id: str):
        """标记已读"""
        notifications = self._notifications.get(project_id, [])
        for n in notifications:
            if n.id == notification_id:
                n.read = True
                break
```

---

## 九、ImportExportManager (IE-01)

**文件**: `backend/app/advanced/import_export_manager.py`
**依赖**: ProjectContext, ArtifactStore
**被依赖**: 前端导入导出界面

### 9.1 设计目标

- 项目导出（.arsitect 格式）
- 项目导入
- 支持迁移和备份

### 9.2 核心实现

```python
# backend/app/advanced/import_export_manager.py
import json
import zipfile
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ExportManifest:
    version: str = "1.0"
    exported_at: str = ""
    project_id: str = ""
    project_name: str = ""
    includes: List[str] = None  # dsl/artifacts/config/history

class ImportExportManager:
    """
    导入导出管理器

    职责:
    1. 项目导出为 .arsitect 文件
    2. 从 .arsitect 文件导入
    3. 备份和恢复
    """

    def __init__(self, project_ctx):
        self.ctx = project_ctx

    async def export_project(self, project_id: str, output_path: str) -> str:
        """
        导出项目

        生成 .arsitect 文件（ZIP 格式）:
        - manifest.json
        - dsl/arsitect.aac.yml
        - artifacts/*.md, *.yaml, *.json
        - config/project.json
        """
        manifest = ExportManifest(
            exported_at=datetime.utcnow().isoformat(),
            project_id=project_id,
            includes=["dsl", "artifacts", "config"],
        )

        zip_path = Path(output_path) / f"{project_id}.arsitect"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # manifest
            zf.writestr("manifest.json", json.dumps(manifest.__dict__, indent=2, default=str))

            # DSL
            dsl_path = self.ctx.get_dsl_path()
            if dsl_path.exists():
                zf.write(dsl_path, "dsl/arsitect.aac.yml")

            # Artifacts
            artifacts_dir = self.ctx.artifacts_dir
            if artifacts_dir.exists():
                for artifact in artifacts_dir.rglob("*"):
                    if artifact.is_file():
                        arcname = f"artifacts/{artifact.relative_to(artifacts_dir)}"
                        zf.write(artifact, arcname)

        return str(zip_path)

    async def import_project(self, arsitect_path: str, target_dir: str) -> str:
        """
        导入项目

        从 .arsitect 文件解压并恢复项目
        """
        import shutil

        target = Path(target_dir)
        target.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(arsitect_path, "r") as zf:
            # 读取 manifest
            manifest_data = json.loads(zf.read("manifest.json"))

            # 解压所有文件
            zf.extractall(target)

            # 移动 DSL 到正确位置
            dsl_src = target / "dsl" / "arsitect.aac.yml"
            if dsl_src.exists():
                dsl_dst = target / "dsl" / "arsitect.aac.yml"
                dsl_dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(dsl_src), str(dsl_dst))

        return manifest_data.get("project_id", "")
```

---

## 十、API 接口总览

```python
# backend/app/api/v1/advanced.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/advanced", tags=["Advanced"])

# HistoryViewer
@router.get("/history/{project_id}/timeline")
async def get_timeline(project_id: str):
    ...

@router.get("/history/{project_id}/heatmap")
async def get_heatmap(project_id: str):
    ...

# SearchEngine
@router.get("/search")
async def global_search(project_id: str, q: str, type: Optional[str] = None):
    ...

# NotificationManager
@router.get("/notifications")
async def get_notifications(project_id: str, unread_only: bool = False):
    ...

@router.post("/notifications/{notif_id}/read")
async def mark_notification_read(project_id: str, notif_id: str):
    ...

# ImportExportManager
@router.post("/projects/{project_id}/export")
async def export_project(project_id: str):
    ...

@router.post("/projects/import")
async def import_project(file: UploadFile):
    ...

# DriftDetector
@router.post("/projects/{project_id}/drift")
async def detect_drift(project_id: str, code_dir: str):
    ...

# PrototypeArchBinder
@router.post("/projects/{project_id}/gaps")
async def detect_gaps(project_id: str, proto_interfaces: List[Dict]):
    ...
```

---

## 十一、测试策略

```python
# tests/test_search_engine.py
import pytest
from app.advanced.search_engine import SearchEngine

class TestSearchEngine:
    @pytest.mark.asyncio
    async def test_search_c4_containers(self):
        """搜索 C4 容器"""
        # Mock baseline_store
        search = SearchEngine(None, MockBaselineStore(), None)
        results = await search.search("proj-1", "web")

        container_results = [r for r in results if r.type == "c4_node"]
        assert len(container_results) > 0


# tests/test_permission_manager.py
import pytest
from app.advanced.permission_manager import PermissionManager, Role, Permission

class TestPermissionManager:
    def test_owner_has_all_permissions(self):
        pm = PermissionManager(None)
        assert pm.has_permission("user-1", "proj-1", Permission.GATE_BYPASS)
        assert pm.has_permission("user-1", "proj-1", Permission.PROJECT_DELETE)

    def test_bypass_gate_requires_admin(self):
        pm = PermissionManager(None)
        # OWNER 可以旁路
        assert pm.can_bypass_gate("user-1", "proj-1")


# tests/test_import_export.py
import pytest
from app.advanced.import_export_manager import ImportExportManager

class TestImportExport:
    @pytest.mark.asyncio
    async def test_export_manifest(self):
        manager = ImportExportManager(MockContext())
        path = await manager.export_project("test-proj", "/tmp")
        assert path.endswith(".arsitect")
```

---

## 附录 A：验收标准

### A.1 功能验收

| # | 组件 | 验收项 |
|---|------|--------|
| 1 | HistoryViewer | 时间线 + 返工热力图 |
| 2 | PermissionManager | RBAC + 旁路鉴权 |
| 3 | PrototypeArchBinder | 接口缺失检测 + DSL 回写 |
| 4 | DriftDetector | 设计 vs 实际对比 |
| 5 | MetricsCollector | 指标收集 + 聚合 |
| 6 | SearchEngine | 全文搜索 + 过滤 |
| 7 | NotificationManager | 多渠道通知 |
| 8 | ImportExportManager | .arsitect 导入导出 |

### A.2 端到端验收

```
[ ] E2E-01: 完成项目 → 历史查看 → 阶段耗时对比 → 返工热力图
[ ] E2E-02: 原型生成 → 接口缺失检测 → 一键回写 DSL → 验证一致性
[ ] E2E-03: 全局搜索关键词 → 结果过滤 → 点击跳转
[ ] E2E-04: 项目导出 .arsitect → 删除项目 → 导入恢复 → 验证完整
```

---

> **文档结束**
>
> 批次：Batch-05（高级功能 + 企业级）
> 组件数：8 个
> 预计周期：4 周

