# 批次四详细设计文档：治理增强 + 降级容错 + 版本管理

> **批次编号**: Batch-04
> **目标**: 项目治理完善，降级策略，版本管理
> **周期**: 3 周
> **组件数**: 7 个
> **前置依赖**: Batch-03
> **验收标准**: 见附录 A

---

## 目录

1. [设计概览](#一设计概览)
2. [ProjectGovernance](#二projectgovernance)
3. [ComplexityRouter](#三complexityrouter)
4. [TemplateEngine](#四templateengine)
5. [ArtifactVersionManager](#五artifactversionmanager)
6. [FileSystemWatcher](#六filesystemwatcher)
7. [FallbackManager](#七fallbackmanager)
8. [HealthChecker](#八healthchecker)
9. [API 接口总览](#九api-接口总览)
10. [测试策略](#十测试策略)
11. [附录 A：验收标准](#附录-a验收标准)

---

## 一、设计概览

### 1.1 批次架构图

```
================================================================================
                          前端 (React 19 + Vite 6)
================================================================================
  +------------------+  +------------------+  +------------------+
  | ProjectDashboard |  | VersionHistory   |  | TimeboxBanner    |
  | (项目治理面板)    |  | (版本历史)        |  | (时间盒提醒)     |
  +--------+---------+  +--------+---------+  +--------+---------+
           |                     |                      |
================================================================================
                          后端 (FastAPI 0.115)
================================================================================
           |                     |                      |
  +--------v---------+  +--------v---------+  +--------v---------+
  | ProjectGovernance|  |ComplexityRouter  |  | TimeboxManager   |
  | (PG-01)          |  | (CR-02)          |  | (内嵌)           |
  |                  |  |                  |  |                  |
  | Draft/Active     |  | 五维度评估        |  | 里程碑提醒       |
  | 双态管理          |  | 四级路径          |  | 超时处理         |
  | 7天自动清理      |  | 人工覆盖          |  |                  |
  +--------+---------+  +--------+---------+  +------------------+
           |                     |
  +--------v---------+  +--------v---------+
  | TemplateEngine   |  | FallbackManager  |
  | (TE-01)          |  | (FM-01)          |
  |                  |  |                  |
  | 四级模板管理      |  | 降级策略          |
  | 偏离记录          |  | OpenUI→Wireframe |
  +------------------+  +------------------+
           |
  +--------v---------+  +------------------+
  |ArtifactVersion   |  | FileSystemWatcher|
  |Manager (AV-01)   |  | (FW-01)          |
  |                  |  |                  |
  | Git 自动提交      |  | watchdog 监听    |
  | diff/回滚        |  | STALE 传播       |
  +------------------+  +------------------+
           |
  +--------v---------+
  | HealthChecker    |
  | (HC-01)          |
  |                  |
  | 服务健康检测      |
  | 降级决策数据源    |
  +------------------+
```

### 1.2 批次时间线

```
Week 1: 项目治理
  ├─ Day 1-2:  ProjectGovernance（双态管理 + 自动清理）
  ├─ Day 3-4:  ComplexityRouter（五维度评估 + 四级路径）
  └─ Day 5-7:  TemplateEngine（模板管理 + 偏离记录）

Week 2: 版本 + 监听
  ├─ Day 8-10: ArtifactVersionManager（Git 版本管理）
  ├─ Day 11-12: FileSystemWatcher（watchdog 监听）
  └─ Day 13-14: 集成测试

Week 3: 降级 + 健康
  ├─ Day 15-17: FallbackManager（降级策略）
  ├─ Day 18-19: HealthChecker（健康检测）
  └─ Day 20-21: 端到端测试
```



---

## 二、ProjectGovernance (PG-01)

**文件**: `backend/app/governance/project_governance.py`
**依赖**: DatabaseAdapter
**被依赖**: ProjectDashboard（前端）

### 2.1 设计目标

- Project CRUD
- Draft/Active/Archived/Cancelled 状态流转
- Draft 仅允许分析型 Skill
- 7天自动清理 Draft

### 2.2 核心实现

```python
# backend/app/governance/project_governance.py
from typing import Optional, List, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from app.db.models import Project, ProjectState

@dataclass
class ProjectDTO:
    id: str
    name: str
    state: str
    complexity_route: Optional[str]
    created_at: datetime
    module_count: int = 0

class ProjectGovernance:
    """
    项目治理

    职责:
    1. Project CRUD
    2. 状态流转控制
    3. Draft 自动清理
    4. 复杂度路由管理
    """

    # Draft 自动清理期限
    DRAFT_TTL_DAYS = 7

    def __init__(self, db):
        self.db = db

    async def create(self, name: str, description: str = "") -> str:
        """创建项目（初始为 DRAFT）"""
        project = Project(
            name=name,
            description=description,
            state=ProjectState.DRAFT,
        )
        self.db.add(project)
        await self.db.flush()
        return str(project.id)

    async def get(self, project_id: str) -> Optional[ProjectDTO]:
        """获取项目"""
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            return None
        return ProjectDTO(
            id=project.id, name=project.name,
            state=project.state.value,
            complexity_route=project.complexity_route,
            created_at=project.created_at,
        )

    async def list(self, state: Optional[str] = None) -> List[ProjectDTO]:
        """列出项目"""
        query = select(Project)
        if state:
            query = query.where(Project.state == state)
        result = await self.db.execute(query.order_by(Project.created_at.desc()))
        return [
            ProjectDTO(
                id=p.id, name=p.name, state=p.state.value,
                complexity_route=p.complexity_route, created_at=p.created_at,
            )
            for p in result.scalars().all()
        ]

    # ============================================================
    # 状态流转
    # ============================================================
    async def activate(self, project_id: str, complexity_route: str) -> bool:
        """Draft → Active（正式立项）"""
        project = await self._get_entity(project_id)
        if project.state != ProjectState.DRAFT:
            raise ValueError(f"Cannot activate: state is {project.state.value}")

        project.state = ProjectState.ACTIVE
        project.complexity_route = complexity_route
        await self.db.flush()
        return True

    async def archive(self, project_id: str) -> bool:
        """Active → Archived"""
        project = await self._get_entity(project_id)
        if project.state != ProjectState.ACTIVE:
            raise ValueError("Only ACTIVE projects can be archived")
        project.state = ProjectState.ARCHIVED
        await self.db.flush()
        return True

    async def cancel(self, project_id: str) -> bool:
        """Draft/Active → Cancelled"""
        project = await self._get_entity(project_id)
        if project.state in (ProjectState.ARCHIVED, ProjectState.CANCELLED):
            raise ValueError(f"Cannot cancel: state is {project.state.value}")
        project.state = ProjectState.CANCELLED
        await self.db.flush()
        return True

    # ============================================================
    # Draft 自动清理
    # ============================================================
    async def cleanup_expired_drafts(self) -> int:
        """清理过期 Draft（7天未激活）"""
        cutoff = datetime.utcnow() - timedelta(days=self.DRAFT_TTL_DAYS)

        result = await self.db.execute(
            select(Project).where(
                Project.state == ProjectState.DRAFT,
                Project.created_at < cutoff,
            )
        )
        expired = result.scalars().all()

        for project in expired:
            project.state = ProjectState.CANCELLED

        await self.db.flush()
        return len(expired)

    async def _get_entity(self, project_id: str) -> Project:
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project not found: {project_id}")
        return project

from sqlalchemy import select
```

---

## 三、ComplexityRouter (CR-02)

**文件**: `backend/app/governance/complexity_router.py`
**依赖**: DatabaseAdapter
**被依赖**: ProjectGovernance

### 3.1 设计目标

- 五维度规模评估（代码量/外部依赖/数据模型/API 数量/业务规则）
- 四级路径推荐（Trivial/Light/Standard/Deep）
- 人工覆盖机制

### 3.2 核心实现

```python
# backend/app/governance/complexity_router.py
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class ComplexityRoute(str, Enum):
    TRIVIAL = "trivial"      # XS: < 1周
    LIGHT = "light"          # S: 1-2周
    STANDARD = "standard"    # M: 2-4周
    DEEP = "deep"            # L: > 4周

@dataclass
class ComplexityMetrics:
    """五维度评估指标"""
    code_lines: int          # 预估代码行数
    external_deps: int       # 外部依赖数
    data_models: int         # 数据模型数
    api_endpoints: int       # API 端点数
    business_rules: int      # 业务规则数

@dataclass
class ComplexityAssessment:
    route: ComplexityRoute
    confidence: float        # 0-1
    metrics: ComplexityMetrics
    reasoning: str
    manual_override: bool = False

class ComplexityRouter:
    """
    复杂度路由

    职责:
    1. 五维度评估
    2. 四级路径推荐
    3. 人工覆盖
    """

    # 阈值定义
    THRESHOLDS = {
        ComplexityRoute.TRIVIAL: {
            "code_lines": 500,
            "external_deps": 3,
            "data_models": 3,
            "api_endpoints": 5,
            "business_rules": 5,
        },
        ComplexityRoute.LIGHT: {
            "code_lines": 2000,
            "external_deps": 8,
            "data_models": 8,
            "api_endpoints": 15,
            "business_rules": 15,
        },
        ComplexityRoute.STANDARD: {
            "code_lines": 5000,
            "external_deps": 15,
            "data_models": 15,
            "api_endpoints": 30,
            "business_rules": 30,
        },
        # DEEP: 超过 STANDARD 阈值
    }

    def assess(self, metrics: ComplexityMetrics) -> ComplexityAssessment:
        """
        评估复杂度并推荐路径

        算法:
        1. 每个维度独立评级
        2. 取最高评级作为整体推荐
        3. 计算置信度
        """
        dimension_scores = self._score_dimensions(metrics)

        # 取最高评级
        max_route = max(
            dimension_scores.items(),
            key=lambda x: self._route_rank(x[1]),
        )

        route = max_route[1]

        # 计算置信度（各维度一致性）
        unique_routes = set(dimension_scores.values())
        if len(unique_routes) == 1:
            confidence = 1.0
        elif len(unique_routes) == 2:
            confidence = 0.7
        else:
            confidence = 0.4

        reasoning = self._build_reasoning(metrics, dimension_scores)

        return ComplexityAssessment(
            route=route,
            confidence=confidence,
            metrics=metrics,
            reasoning=reasoning,
        )

    def _score_dimensions(self, metrics: ComplexityMetrics) -> Dict[str, ComplexityRoute]:
        """各维度独立评级"""
        scores = {}
        scores["code_lines"] = self._route_for_metric("code_lines", metrics.code_lines)
        scores["external_deps"] = self._route_for_metric("external_deps", metrics.external_deps)
        scores["data_models"] = self._route_for_metric("data_models", metrics.data_models)
        scores["api_endpoints"] = self._route_for_metric("api_endpoints", metrics.api_endpoints)
        scores["business_rules"] = self._route_for_metric("business_rules", metrics.business_rules)
        return scores

    def _route_for_metric(self, dimension: str, value: int) -> ComplexityRoute:
        """单个维度评级"""
        t = self.THRESHOLDS
        if value <= t[ComplexityRoute.TRIVIAL][dimension]:
            return ComplexityRoute.TRIVIAL
        elif value <= t[ComplexityRoute.LIGHT][dimension]:
            return ComplexityRoute.LIGHT
        elif value <= t[ComplexityRoute.STANDARD][dimension]:
            return ComplexityRoute.STANDARD
        else:
            return ComplexityRoute.DEEP

    @staticmethod
    def _route_rank(route: ComplexityRoute) -> int:
        """路径等级（用于比较）"""
        ranks = {
            ComplexityRoute.TRIVIAL: 0,
            ComplexityRoute.LIGHT: 1,
            ComplexityRoute.STANDARD: 2,
            ComplexityRoute.DEEP: 3,
        }
        return ranks[route]

    def _build_reasoning(self, metrics: ComplexityMetrics, scores: Dict) -> str:
        """构建评估理由"""
        lines = ["Complexity Assessment:"]
        lines.append(f"  Code Lines: {metrics.code_lines} ({scores['code_lines'].value})")
        lines.append(f"  External Deps: {metrics.external_deps} ({scores['external_deps'].value})")
        lines.append(f"  Data Models: {metrics.data_models} ({scores['data_models'].value})")
        lines.append(f"  API Endpoints: {metrics.api_endpoints} ({scores['api_endpoints'].value})")
        lines.append(f"  Business Rules: {metrics.business_rules} ({scores['business_rules'].value})")
        return "\n".join(lines)

    def apply_manual_override(
        self, assessment: ComplexityAssessment, manual_route: str
    ) -> ComplexityAssessment:
        """人工覆盖"""
        assessment.route = ComplexityRoute(manual_route)
        assessment.manual_override = True
        assessment.reasoning += f"\n[MANUAL OVERRIDE] Route manually set to {manual_route}"
        return assessment
```

---

## 四、TemplateEngine (TE-01)

**文件**: `backend/app/governance/template_engine.py`
**依赖**: DatabaseAdapter
**被依赖**: ProjectGovernance

### 4.1 设计目标

- 四级模板管理（Trivial/Light/Standard/Deep）
- 阶段-Skill 绑定推荐
- 偏离记录

### 4.2 核心实现

```python
# backend/app/governance/template_engine.py
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class StageTemplate:
    """阶段模板"""
    name: str                      # setup/analysis/design/develop/verify/deploy
    required_skills: List[str]     # 必需 Skill ID 列表
    optional_skills: List[str]     # 可选 Skill ID 列表
    order: int                     # 执行顺序

@dataclass
class ProjectTemplate:
    """项目模板"""
    route: str                     # trivial/light/standard/deep
    stages: List[StageTemplate]
    description: str = ""

@dataclass
class Deviation:
    """偏离记录"""
    project_id: str
    template_route: str
    deviation_type: str            # added/removed/reordered
    detail: str

class TemplateEngine:
    """
    模板引擎

    职责:
    1. 管理四级项目模板
    2. 推荐阶段-Skill 绑定
    3. 记录偏离
    """

    def __init__(self):
        self._templates: Dict[str, ProjectTemplate] = {}
        self._init_default_templates()

    def _init_default_templates(self):
        """初始化默认模板"""
        self._templates["trivial"] = ProjectTemplate(
            route="trivial",
            description="Trivial project: single page CRUD",
            stages=[
                StageTemplate("setup", ["init-project"], [], 1),
                StageTemplate("develop", ["generate-page", "generate-api"], [], 2),
                StageTemplate("verify", ["run-tests"], [], 3),
            ],
        )
        self._templates["light"] = ProjectTemplate(
            route="light",
            description="Light project: multi-page with auth",
            stages=[
                StageTemplate("setup", ["init-project", "setup-auth"], [], 1),
                StageTemplate("analysis", ["analyze-requirements"], [], 2),
                StageTemplate("design", ["design-database", "design-api"], ["design-ui"], 3),
                StageTemplate("develop", ["generate-pages", "generate-apis"], [], 4),
                StageTemplate("verify", ["run-tests"], ["security-scan"], 5),
            ],
        )
        self._templates["standard"] = ProjectTemplate(
            route="standard",
            description="Standard project: full SDLC",
            stages=[
                StageTemplate("setup", ["init-project", "setup-ci"], [], 1),
                StageTemplate("analysis", ["analyze-requirements", "write-prd"], [], 2),
                StageTemplate("design", ["design-architecture", "design-database", "design-api"], ["design-ui"], 3),
                StageTemplate("develop", ["implement-backend", "implement-frontend"], [], 4),
                StageTemplate("verify", ["unit-tests", "integration-tests", "e2e-tests"], [], 5),
                StageTemplate("deploy", ["deploy-staging"], ["deploy-production"], 6),
            ],
        )
        self._templates["deep"] = ProjectTemplate(
            route="deep",
            description="Deep project: enterprise-grade",
            stages=[
                StageTemplate("setup", ["init-project", "setup-ci", "setup-monitoring"], [], 1),
                StageTemplate("analysis", ["analyze-requirements", "write-prd", "stakeholder-review"], [], 2),
                StageTemplate("design", ["design-architecture", "design-database", "design-api", "design-security"], ["design-ui", "design-performance"], 3),
                StageTemplate("develop", ["implement-backend", "implement-frontend", "implement-infra"], [], 4),
                StageTemplate("verify", ["unit-tests", "integration-tests", "e2e-tests", "security-audit", "performance-tests"], [], 5),
                StageTemplate("deploy", ["deploy-staging", "deploy-production", "setup-monitoring"], [], 6),
            ],
        )

    def get_template(self, route: str) -> Optional[ProjectTemplate]:
        """获取模板"""
        return self._templates.get(route)

    def list_available_skills(self, route: str, stage: str) -> List[str]:
        """获取某阶段可用的所有 Skill"""
        template = self._templates.get(route)
        if not template:
            return []
        for s in template.stages:
            if s.name == stage:
                return s.required_skills + s.optional_skills
        return []

    def record_deviation(self, deviations: List, project_id: str,
                         template_route: str, actual_stages: List[str]) -> List[Deviation]:
        """记录偏离"""
        template = self._templates.get(template_route)
        if not template:
            return []

        expected_stages = [s.name for s in template.stages]
        new_deviations = []

        # 检查新增阶段
        for stage in actual_stages:
            if stage not in expected_stages:
                new_deviations.append(Deviation(
                    project_id=project_id,
                    template_route=template_route,
                    deviation_type="added",
                    detail=f"Stage '{stage}' not in template",
                ))

        # 检查删除阶段
        for stage in expected_stages:
            if stage not in actual_stages:
                new_deviations.append(Deviation(
                    project_id=project_id,
                    template_route=template_route,
                    deviation_type="removed",
                    detail=f"Stage '{stage}' missing from execution",
                ))

        deviations.extend(new_deviations)
        return new_deviations
```



---

## 五、ArtifactVersionManager (AV-01)

**文件**: `backend/app/governance/artifact_version_manager.py`
**依赖**: GitAdapter, ArtifactStore
**被依赖**: VersionHistory（前端）

### 5.1 设计目标

- Git 自动提交产物变更
- 版本历史列表
- diff 对比
- 一键回滚

### 5.2 核心实现

```python
# backend/app/governance/artifact_version_manager.py
from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

@dataclass
class VersionRecord:
    commit_hash: str
    message: str
    author: str
    timestamp: datetime
    files_changed: List[str]

@dataclass
class DiffResult:
    file_path: str
    old_content: str
    new_content: str
    added_lines: int
    removed_lines: int

class ArtifactVersionManager:
    """
    产物版本管理器

    职责:
    1. Git 自动提交
    2. 版本历史查询
    3. Diff 对比
    4. 回滚
    """

    def __init__(self, git_adapter, project_ctx):
        self.git = git_adapter
        self.ctx = project_ctx

    async def commit_artifact(
        self, relative_path: str, message: str, author: str = "system"
    ) -> str:
        """提交产物变更"""
        full_path = self.ctx.artifacts_dir / relative_path
        commit_hash = await self.git.commit_file(
            repo_path=str(self.ctx.project_dir),
            file_path=str(full_path),
            message=message,
            author=author,
        )
        return commit_hash

    async def get_history(self, relative_path: str, limit: int = 20) -> List[VersionRecord]:
        """获取文件版本历史"""
        full_path = self.ctx.artifacts_dir / relative_path
        commits = await self.git.get_file_history(
            repo_path=str(self.ctx.project_dir),
            file_path=str(full_path),
            limit=limit,
        )
        return [
            VersionRecord(
                commit_hash=c["hash"],
                message=c["message"],
                author=c["author"],
                timestamp=c["date"],
                files_changed=c.get("files", [relative_path]),
            )
            for c in commits
        ]

    async def diff(
        self, relative_path: str, old_commit: str, new_commit: str
    ) -> DiffResult:
        """对比两个版本的差异"""
        diff_text = await self.git.diff_commits(
            repo_path=str(self.ctx.project_dir),
            file_path=relative_path,
            old_commit=old_commit,
            new_commit=new_commit,
        )

        # 解析 diff 统计
        added = diff_text.count("\n+")
        removed = diff_text.count("\n-")

        return DiffResult(
            file_path=relative_path,
            old_content="",  # 可扩展获取完整内容
            new_content="",
            added_lines=added,
            removed_lines=removed,
        )

    async def rollback(self, relative_path: str, commit_hash: str) -> bool:
        """回滚到指定版本"""
        full_path = self.ctx.artifacts_dir / relative_path
        return await self.git.checkout_file(
            repo_path=str(self.ctx.project_dir),
            file_path=str(full_path),
            commit_hash=commit_hash,
        )


class GitAdapter:
    """
    Git 操作适配器（基于 GitPython）
    """

    @staticmethod
    def commit_file(repo_path: str, file_path: str, message: str, author: str = "system") -> str:
        from git import Repo
        repo = Repo(repo_path)
        repo.git.add(file_path)
        if repo.is_dirty():
            commit = repo.index.commit(message, author=author)
            return str(commit.hexsha)
        return ""

    @staticmethod
    def get_file_history(repo_path: str, file_path: str, limit: int = 20) -> List[Dict]:
        from git import Repo
        repo = Repo(repo_path)
        commits = list(repo.iter_commits(paths=file_path, max_count=limit))
        return [
            {
                "hash": c.hexsha[:8],
                "message": c.message.strip(),
                "author": str(c.author),
                "date": datetime.fromtimestamp(c.committed_date),
                "files": list(c.stats.files.keys()),
            }
            for c in commits
        ]

    @staticmethod
    def diff_commits(repo_path: str, file_path: str, old_commit: str, new_commit: str) -> str:
        from git import Repo
        repo = Repo(repo_path)
        return repo.git.diff(f"{old_commit}..{new_commit}", "--", file_path)

    @staticmethod
    def checkout_file(repo_path: str, file_path: str, commit_hash: str) -> bool:
        from git import Repo
        repo = Repo(repo_path)
        try:
            repo.git.checkout(commit_hash, "--", file_path)
            return True
        except Exception:
            return False
```

---

## 六、FileSystemWatcher (FW-01)

**文件**: `backend/app/common/file_system_watcher.py`
**依赖**: watchdog, EventBus
**被依赖**: ArtifactStore

### 6.1 设计目标

- watchdog 监听产物目录
- 文件变更事件处理
- STALE 状态标记
- 防抖处理（500ms）

### 6.2 核心实现

```python
# backend/app/common/file_system_watcher.py
import asyncio
from pathlib import Path
from typing import Dict, Set, Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent

from app.common.event_bus import EventBus

class ArtifactEventHandler(FileSystemEventHandler):
    """产物目录事件处理器"""

    def __init__(self, project_id: str, artifact_store, event_bus: Optional[EventBus] = None):
        self.project_id = project_id
        self.store = artifact_store
        self.event_bus = event_bus
        self._debounce_timers: Dict[str, asyncio.TimerHandle] = {}

    def on_modified(self, event):
        if event.is_directory:
            return
        self._handle_change(event.src_path)

    def on_created(self, event):
        if event.is_directory:
            return
        self._handle_change(event.src_path)

    def _handle_change(self, file_path: str):
        """处理文件变更（防抖）"""
        # 取消之前的计时器
        if file_path in self._debounce_timers:
            self._debounce_timers[file_path].cancel()

        # 设置新的防抖计时器（500ms）
        loop = asyncio.get_event_loop()
        self._debounce_timers[file_path] = loop.call_later(
            0.5,  # 500ms 防抖
            lambda: asyncio.create_task(self._process_change(file_path)),
        )

    async def _process_change(self, file_path: str):
        """处理变更（防抖后）"""
        relative_path = Path(file_path).name

        # 检查是否外部变更
        changed, current_hash = self.store.check_external_change(relative_path)
        if changed:
            # 通知
            if self.event_bus:
                self.event_bus.publish("artifact.external_change", {
                    "project_id": self.project_id,
                    "file_path": relative_path,
                    "new_hash": current_hash,
                })

class FileSystemWatcher:
    """
    文件系统监听器

    职责:
    1. watchdog 监听产物目录
    2. 防抖处理
    3. 外部变更检测
    """

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus
        self._observers: Dict[str, Observer] = {}

    def watch_project(self, project_id: str, path: str, artifact_store):
        """开始监听项目目录"""
        if project_id in self._observers:
            return

        handler = ArtifactEventHandler(project_id, artifact_store, self.event_bus)
        observer = Observer()
        observer.schedule(handler, path, recursive=True)
        observer.start()

        self._observers[project_id] = observer

    def unwatch_project(self, project_id: str):
        """停止监听"""
        observer = self._observers.pop(project_id, None)
        if observer:
            observer.stop()
            observer.join()

    def stop_all(self):
        """停止所有监听"""
        for observer in self._observers.values():
            observer.stop()
        for observer in self._observers.values():
            observer.join()
        self._observers.clear()
```

---

## 七、FallbackManager (FM-01)

**文件**: `backend/app/common/fallback_manager.py`
**依赖**: HealthChecker
**被依赖**: OpenUIClient

### 7.1 设计目标

- 定义降级策略映射
- 服务不可用时自动降级
- 用户通知

### 7.2 核心实现

```python
# backend/app/common/fallback_manager.py
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from app.common.health_checker import HealthChecker, ServiceStatus

class FallbackAction(str, Enum):
    WIREFRAME = "wireframe"       # 降级为线框图
    SKIP = "skip"                 # 跳过该功能
    QUEUE = "queue"               # 排队等待重试
    NOTIFY = "notify"             # 仅通知用户

@dataclass
class FallbackRule:
    service: str                  # 依赖的服务
    action: FallbackAction        # 降级动作
    message: str                  # 用户提示

class FallbackManager:
    """
    降级管理器

    职责:
    1. 定义降级策略
    2. 根据健康状态触发降级
    3. 用户通知
    """

    def __init__(self, health_checker: HealthChecker):
        self.health = health_checker
        self._rules: Dict[str, FallbackRule] = {}
        self._init_default_rules()

    def _init_default_rules(self):
        """初始化默认降级规则"""
        self._rules = {
            "openui": FallbackRule(
                service="openui",
                action=FallbackAction.WIREFRAME,
                message="OpenUI service unavailable. Using wireframe fallback.",
            ),
            "kimi-cli": FallbackRule(
                service="kimi-cli",
                action=FallbackAction.NOTIFY,
                message="Kimi CLI unavailable. Please check your CLI installation.",
            ),
            "git": FallbackRule(
                service="git",
                action=FallbackAction.SKIP,
                message="Git unavailable. Version tracking disabled.",
            ),
        }

    def check_and_fallback(self, service: str) -> Optional[FallbackRule]:
        """
        检查服务状态，如不可用返回降级规则

        Returns:
            FallbackRule if service unavailable, None if healthy
        """
        status = self.health.get_status(service)
        if status == ServiceStatus.UNAVAILABLE:
            return self._rules.get(service)
        return None

    def get_all_fallbacks(self) -> Dict[str, FallbackRule]:
        """获取所有当前降级状态"""
        result = {}
        for service, rule in self._rules.items():
            if self.health.get_status(service) != ServiceStatus.HEALTHY:
                result[service] = rule
        return result

    def register_rule(self, service: str, rule: FallbackRule):
        """注册降级规则"""
        self._rules[service] = rule
```

---

## 八、HealthChecker (HC-01)

**文件**: `backend/app/common/health_checker.py`
**依赖**: 无
**被依赖**: FallbackManager, OpenUIClient

### 8.1 设计目标

- 依赖服务健康检查（Docker/OpenUI/Git CLI/Kimi CLI）
- 降级决策数据源
- 定期轮询

### 8.2 核心实现

```python
# backend/app/common/health_checker.py
import asyncio
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"

@dataclass
class HealthResult:
    service: str
    status: ServiceStatus
    latency_ms: float
    message: str
    last_checked: Optional[str] = None

class HealthChecker:
    """
    健康检查器

    职责:
    1. 注册健康检查项
    2. 定期检查
    3. 提供状态查询
    """

    def __init__(self, check_interval: float = 30.0):
        self.check_interval = check_interval
        self._checks: Dict[str, Callable] = {}
        self._results: Dict[str, HealthResult] = {}
        self._running = False

    def register(self, name: str, check_fn: Callable[[], Any]):
        """注册健康检查项"""
        self._checks[name] = check_fn

    async def start_monitoring(self):
        """启动持续监控"""
        self._running = True
        while self._running:
            for name, check_fn in self._checks.items():
                try:
                    import time
                    start = time.time()
                    result = await asyncio.wait_for(check_fn(), timeout=5.0)
                    latency = (time.time() - start) * 1000
                    self._results[name] = HealthResult(
                        service=name, status=ServiceStatus.HEALTHY,
                        latency_ms=latency, message="OK",
                    )
                except asyncio.TimeoutError:
                    self._results[name] = HealthResult(
                        service=name, status=ServiceStatus.UNAVAILABLE,
                        latency_ms=5000, message="Timeout",
                    )
                except Exception as e:
                    self._results[name] = HealthResult(
                        service=name, status=ServiceStatus.UNAVAILABLE,
                        latency_ms=0, message=str(e),
                    )
            await asyncio.sleep(self.check_interval)

    def stop(self):
        """停止监控"""
        self._running = False

    def get_status(self, service: str) -> ServiceStatus:
        """获取服务状态"""
        result = self._results.get(service)
        return result.status if result else ServiceStatus.UNAVAILABLE

    def is_available(self, service: str) -> bool:
        return self.get_status(service) == ServiceStatus.HEALTHY

    def get_all_statuses(self) -> Dict[str, HealthResult]:
        """获取所有服务状态"""
        return dict(self._results)

    @staticmethod
    async def check_docker() -> HealthResult:
        """检查 Docker"""
        import subprocess
        try:
            result = subprocess.run(
                ["docker", "info"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return HealthResult("docker", ServiceStatus.HEALTHY, 0, "Docker daemon running")
            return HealthResult("docker", ServiceStatus.UNAVAILABLE, 0, result.stderr)
        except Exception as e:
            return HealthResult("docker", ServiceStatus.UNAVAILABLE, 0, str(e))

    @staticmethod
    async def check_openui(base_url: str = "http://localhost:3000") -> HealthResult:
        """检查 OpenUI"""
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/health", timeout=5) as resp:
                    if resp.status == 200:
                        return HealthResult("openui", ServiceStatus.HEALTHY, 0, "OpenUI responding")
                    return HealthResult("openui", ServiceStatus.UNAVAILABLE, 0, f"HTTP {resp.status}")
        except Exception as e:
            return HealthResult("openui", ServiceStatus.UNAVAILABLE, 0, str(e))

    @staticmethod
    async def check_git() -> HealthResult:
        """检查 Git CLI"""
        import subprocess
        try:
            result = subprocess.run(
                ["git", "--version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return HealthResult("git", ServiceStatus.HEALTHY, 0, result.stdout.strip())
            return HealthResult("git", ServiceStatus.UNAVAILABLE, 0, result.stderr)
        except Exception as e:
            return HealthResult("git", ServiceStatus.UNAVAILABLE, 0, str(e))

    @staticmethod
    async def check_kimi_cli() -> HealthResult:
        """检查 Kimi CLI"""
        import subprocess
        try:
            result = subprocess.run(
                ["kimi", "--version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return HealthResult("kimi-cli", ServiceStatus.HEALTHY, 0, result.stdout.strip())
            return HealthResult("kimi-cli", ServiceStatus.UNAVAILABLE, 0, result.stderr)
        except Exception as e:
            return HealthResult("kimi-cli", ServiceStatus.UNAVAILABLE, 0, str(e))
```

---

## 九、API 接口总览

```python
# backend/app/api/v1/governance.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/governance", tags=["Governance"])

# ProjectGovernance
@router.post("/projects")
async def create_project(name: str, description: str = ""):
    ...

@router.post("/projects/{project_id}/activate")
async def activate_project(project_id: str, complexity_route: str):
    ...

@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    ...

# ComplexityRouter
@router.post("/projects/{project_id}/assess")
async def assess_complexity(project_id: str, metrics: ComplexityMetrics):
    ...

# ArtifactVersionManager
@router.get("/projects/{project_id}/artifacts/{path}/history")
async def get_artifact_history(project_id: str, path: str, limit: int = 20):
    ...

@router.post("/projects/{project_id}/artifacts/{path}/rollback")
async def rollback_artifact(project_id: str, path: str, commit_hash: str):
    ...

# HealthChecker
@router.get("/health")
async def health_check():
    ...

@router.get("/health/{service}")
async def service_health(service: str):
    ...
```

---

## 十、测试策略

```python
# tests/test_complexity_router.py
import pytest
from app.governance.complexity_router import ComplexityRouter, ComplexityMetrics, ComplexityRoute

class TestComplexityRouter:
    def test_trivial_assessment(self):
        router = ComplexityRouter()
        metrics = ComplexityMetrics(
            code_lines=300, external_deps=2,
            data_models=2, api_endpoints=3, business_rules=3,
        )
        result = router.assess(metrics)
        assert result.route == ComplexityRoute.TRIVIAL
        assert result.confidence == 1.0

    def test_mixed_assessment(self):
        router = ComplexityRouter()
        metrics = ComplexityMetrics(
            code_lines=300,      # trivial
            external_deps=10,    # light
            data_models=20,      # standard
            api_endpoints=3,     # trivial
            business_rules=3,    # trivial
        )
        result = router.assess(metrics)
        assert result.route == ComplexityRoute.STANDARD  # 最高评级
        assert result.confidence < 1.0  # 不一致

    def test_manual_override(self):
        router = ComplexityRouter()
        metrics = ComplexityMetrics(
            code_lines=300, external_deps=2,
            data_models=2, api_endpoints=3, business_rules=3,
        )
        result = router.assess(metrics)
        overridden = router.apply_manual_override(result, "deep")
        assert overridden.route == ComplexityRoute.DEEP
        assert overridden.manual_override


# tests/test_health_checker.py
import pytest
from app.common.health_checker import HealthChecker, ServiceStatus

class TestHealthChecker:
    @pytest.mark.asyncio
    async def test_check_git(self):
        result = await HealthChecker.check_git()
        assert result.status in (ServiceStatus.HEALTHY, ServiceStatus.UNAVAILABLE)

    def test_default_unavailable(self):
        hc = HealthChecker()
        assert hc.get_status("nonexistent") == ServiceStatus.UNAVAILABLE
        assert not hc.is_available("nonexistent")
```

---

## 附录 A：验收标准

### A.1 功能验收

| # | 组件 | 验收项 |
|---|------|--------|
| 1 | ProjectGovernance | Draft/Active 流转 + 7天清理 |
| 2 | ComplexityRouter | 五维度评估 + 人工覆盖 |
| 3 | TemplateEngine | 四级模板 + 偏离记录 |
| 4 | ArtifactVersionManager | Git 提交 + diff + 回滚 |
| 5 | FileSystemWatcher | watchdog 监听 + 防抖 + STALE |
| 6 | FallbackManager | 降级规则 + 自动触发 |
| 7 | HealthChecker | 定期检测 + 状态查询 |

### A.2 端到端验收

```
[ ] E2E-01: 项目创建(Draft) → 复杂度评估 → 激活(Active) → 归档
[ ] E2E-02: 产物编辑 → Git 自动提交 → 版本历史 → diff → 回滚
[ ] E2E-03: 外部修改产物 → watchdog 检测 → STALE 标记 → SSE 通知
[ ] E2E-04: OpenUI 停止 → 健康检测 → 降级 Wireframe → 用户通知
```

---

> **文档结束**
>
> 批次：Batch-04（治理增强 + 降级容错 + 版本管理）
> 组件数：7 个
> 预计周期：3 周

