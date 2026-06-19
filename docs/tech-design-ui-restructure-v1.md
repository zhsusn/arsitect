# SDLC Visualizer UI 重构 — 技术设计文档

> **版本**: v1.0  
> **日期**: 2026-06-17  
> **依据**: `docs/sdlc-visualizer-ui-design-v1.md`

---

## 1. 设计目标

将现有产品的前后端架构从「功能扁平导航」调整为「SDLC 阶段聚集导航」，使页面组织与真实开发流程（立项 → 脑暴 → 需求确认 → 设计 → 任务拆解 → 编码/测试/Bug 修复）对齐。

---

## 2. 现有架构 vs 新架构

### 2.1 现有导航 vs 新导航

| 现有导航 | 新导航 | 处理策略 |
|----------|--------|----------|
| 项目中心（项目工作台、项目画布、复杂度评估） | 项目中心（项目工作台、应用管理） | 移除项目画布、复杂度评估；应用管理从平台管理移入 |
| 执行中心（执行监控、AI CLI、监控看板） | 开发执行（项目画布、任务中心、执行问题、执行监控、AI CLI、监控看板） | 重命名，新增项目画布、任务中心、执行问题；项目画布从项目中心移入 |
| 架构设计（C4 架构、线框图、草图、OpenUI、数据绑定） | 需求设计室（概要需求、详细需求、概要设计、详细设计、设计产物、架构治理） | 全部页面移入需求设计室，新增阶段导航 |
| 产物验证（产物浏览器、架构验证、架构治理、历史回溯） | 产物验证（产物浏览器、架构验证、历史回溯） | 架构治理移入需求设计室 |
| 治理审批（审批中心、旁路审批） | 治理审批（审批中心、旁路审批） | 不变 |
| 平台管理（Application、Skill 治理、LLM 配置、模板配置、文档标准化） | 平台管理（Skill 治理、LLM 配置、模板配置、文档标准化） | Application 移入项目中心；模板配置降级为后台 |

### 2.2 现有路由 vs 新路由

| 现有路由 | 新路由 | 处理 |
|----------|--------|------|
| `/projects` | `/project-center/workbench` | 迁移 |
| `/applications` | `/project-center/application` | 迁移 |
| `/canvas/:projectId` | `/execution/canvas` | 迁移 |
| `/complexity-router` | — | 移除主导航，下沉为概要需求页面内卡片 |
| `/executions` | `/execution/monitor` | 迁移 |
| `/cli` | `/execution/cli` | 迁移 |
| `/monitoring` | `/execution/dashboard` | 迁移 |
| `/c4` | `/requirement-studio/design-outline` | 迁移（概要设计） |
| `/wireframe` | `/requirement-studio/design-outline` | 合并（概要设计子 Tab） |
| `/sketches` | `/requirement-studio/requirement-outline` | 合并（概要需求子 Tab） |
| `/open-ui` | `/requirement-studio/design-detailed` | 迁移（详细设计） |
| `/binding` | `/requirement-studio/design-detailed` | 合并（详细设计子 Tab） |
| `/artifacts` | `/artifact-verification/browser` | 迁移 |
| `/arch-validation` | `/artifact-verification/validation` | 迁移 |
| `/arch-governance` | `/requirement-studio/governance` | 迁移 |
| `/history` | `/artifact-verification/history` | 迁移 |
| `/gates` | `/governance/approval-center` | 迁移 |
| `/bypass` | `/governance/bypass` | 迁移 |
| `/skills` | `/platform/skill-management` | 迁移 |
| `/settings/llm` | `/platform/llm-config` | 迁移 |
| `/template-config` | `/platform/template-config` | 迁移 |
| `/docforge` | `/platform/doc-standard` | 迁移 |

### 2.3 后端 API 路由调整

| 现有 API | 新 API | 处理 |
|----------|--------|------|
| `GET /api/v1/projects/{id}/canvas/state` | `GET /api/v1/execution/{id}/canvas/state` | 迁移 |
| `POST /api/v1/projects/{id}/canvas/state` | `POST /api/v1/execution/{id}/canvas/state` | 迁移 |
| `POST /api/v1/complexity/assess` | `POST /api/v1/requirement-studio/{id}/stage/requirement-outline/size-estimate` | 迁移并收敛 |
| `GET /api/v1/complexity/templates` | `GET /api/v1/platform/template-config` | 迁移 |
| `GET /api/v1/c4` | `GET /api/v1/requirement-studio/{id}/stage/design-outline/c4` | 收敛到需求设计室 |
| `GET /api/v1/wireframe` | `GET /api/v1/requirement-studio/{id}/stage/design-outline/wireframe` | 收敛 |
| `GET /api/v1/sketch` | `GET /api/v1/requirement-studio/{id}/stage/requirement-outline/sketch` | 收敛 |
| `GET /api/v1/open-ui` | `GET /api/v1/requirement-studio/{id}/stage/design-detailed/open-ui` | 收敛 |
| `GET /api/v1/binding` | `GET /api/v1/requirement-studio/{id}/stage/design-detailed/binding` | 收敛 |
| `GET /api/v1/arch-governance` | `GET /api/v1/requirement-studio/{id}/governance` | 迁移 |
| `GET /api/v1/artifacts` | `GET /api/v1/artifact-verification/browser` | 迁移 |
| `GET /api/v1/arch-validation` | `GET /api/v1/artifact-verification/validation` | 迁移 |
| `GET /api/v1/gates` | `GET /api/v1/governance/approval-center` | 迁移 |
| `GET /api/v1/bypass` | `GET /api/v1/governance/bypass` | 迁移 |
| `GET /api/v1/skills` | `GET /api/v1/platform/skill-management` | 迁移 |
| `GET /api/v1/settings/llm` | `GET /api/v1/platform/llm-config` | 迁移 |
| `GET /api/v1/template-config` | `GET /api/v1/platform/template-config` | 迁移 |
| `GET /api/v1/docforge` | `GET /api/v1/platform/doc-standard` | 迁移 |

### 2.4 新增后端 API（按模块）

**需求设计室统一入口** (`/api/v1/requirement-studio/{projectId}`):
```
GET  /status                  → 各阶段状态聚合
GET  /stage/{stageId}/tasks   → 阶段任务树
POST /stage/{stageId}/execute → 触发阶段 Skill
POST /stage/{stageId}/review  → 提交审查批注
GET  /artifacts               → 设计产物列表（按阶段分组）
GET  /artifacts/{artifactId}  → 产物详情
POST /artifacts/{artifactId}/edit → 产物编辑
POST /governance/baseline     → 创建基线
GET  /governance/stale-analysis → Stale 分析
POST /governance/change-request → 变更请求
```

**开发执行统一入口** (`/api/v1/execution/{projectId}`):
```
GET  /tasks                   → 任务列表（按模块分组）
POST /tasks                   → 创建任务
POST /tasks/{taskId}/execute  → 执行任务
POST /tasks/{taskId}/retry    → 重试任务
POST /issues                  → 创建执行问题
GET  /issues                  → 执行问题列表
POST /issues/{issueId}/feedback-to-architecture → 反馈回架构
GET  /monitor/sse             → 执行监控 SSE
GET  /dashboard/stats         → 监控看板统计
```

---

## 3. 数据模型变更

### 3.1 新增模型

#### `ExecutionTask` — 开发执行任务
```python
class TaskType(StrEnum):
    CODING = "coding"
    TEST = "test"
    BUGFIX = "bugfix"

class TaskStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"

class ExecutionTask(Base):
    __tablename__ = "execution_tasks"
    
    task_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False)  # coding/test/bugfix
    status: Mapped[str] = mapped_column(String(16), default="not_started")
    input_artifacts: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    assigned_skill_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    parent_module: Mapped[str | None] = mapped_column(String(64), nullable=True)
    output_artifact_path: Mapped[str | None] = mapped_column(String(256), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
```

#### `ExecutionIssue` — 执行问题
```python
class IssueType(StrEnum):
    COMPILE_ERROR = "compile_error"
    TEST_FAILURE = "test_failure"
    ARCH_MISMATCH = "arch_mismatch"
    INTERFACE_MISMATCH = "interface_mismatch"
    OTHER = "other"

class ExecutionIssue(Base):
    __tablename__ = "execution_issues"
    
    issue_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), nullable=False)
    task_id: Mapped[str] = mapped_column(String(36), nullable=False)
    issue_type: Mapped[str] = mapped_column(String(32), nullable=False)
    error_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_artifacts: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    suggested_action: Mapped[str | None] = mapped_column(String(16), nullable=True)  # retry/feedback/skip
    feedback_to_architecture: Mapped[bool] = mapped_column(Boolean, default=False)
    target_artifact_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    change_request_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="open")  # open/resolved/closed
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
```

### 3.2 扩展现有模型

#### `ProjectStage` — 增加阶段类型标识
现有 `ProjectStage` 的 `stage_id` 字段已关联 `TemplateStage`，需要增加阶段分类以便需求设计室按阶段聚合展示。此改动通过 `TemplateStage` 的 `business_stage_key` 映射实现，无需修改 `ProjectStage` 表结构。

现有 `TemplateStage` 模型已有 `business_stage_key`（如 `requirement-outline`, `design-detailed` 等），新需求设计室的阶段导航直接映射到这些 key。

#### `ArtifactFile` — 增加阶段关联
现有 `ArtifactFile` 已有 `stage_id` 字段，满足需求设计室按阶段分组展示产物。

---

## 4. 服务层设计

### 4.1 新增服务

#### `RequirementStudioService` — 需求设计室统一服务
- 聚合各阶段状态（概要需求/详细需求/概要设计/详细设计/设计产物/架构治理）
- 阶段任务树管理
- 产物版本管理（查看、编辑、diff、回滚）
- 调用现有 `StageOrchestrator` 执行 Skill

#### `TaskCenterService` — 任务中心服务
- 任务 CRUD（按模块分组）
- 任务执行触发（调用 `StageOrchestrator` 或 `skill_executions`）
- 任务状态流转（NOT_STARTED → IN_PROGRESS → PASSED/FAILED → BUG_OPENED）
- 重试管理（≤3次）

#### `ExecutionIssueService` — 执行问题服务
- 问题记录 CRUD
- 反馈回架构：标记 Stale、创建变更请求、通知需求设计室
- 与 `TaskCenterService` 联动

### 4.2 复用服务

| 服务 | 复用位置 | 说明 |
|------|----------|------|
| `ProjectService` | 项目中心 | 项目 CRUD、状态流转 |
| `ApplicationService` | 项目中心-应用管理 | 应用 CRUD |
| `StageOrchestrator` | 需求设计室 + 任务中心 | 统一 Skill 执行触发 |
| `ArtifactService` | 需求设计室-设计产物 + 产物验证 | 产物查看、编辑、版本 |
| `ArchGovernanceService` | 需求设计室-架构治理 | 基线化、Stale 传播、变更分析 |
| `C4Service` | 需求设计室-概要/详细设计 | C4 生成与渲染 |
| `SketchService` | 需求设计室-概要需求 | 草图生成 |
| `WireframeService` | 需求设计室-概要设计 | 线框图生成 |
| `OpenUIService` | 需求设计室-详细设计 | OpenUI 原型生成 |
| `BindingService` | 需求设计室-详细设计 | 数据绑定检测 |
| `GateService` | 治理审批 | Gate 审批流程 |
| `BypassService` | 治理审批-旁路审批 | 旁路审批 |
| `MonitoringService` | 开发执行-监控看板 | 统计与瓶颈识别 |
| `CliService` | 开发执行-AI CLI | CLI 调试 |

---

## 5. 前端架构设计

### 5.1 路由重组

```
/project-center
  /workbench         → ProjectDashboard（现有页面，调整导航）
  /application       → AppDashboard（现有页面，从平台管理移入）

/requirement-studio
  /overview          → RequirementStudioOverview（新增：阶段导航总览）
  /requirement-outline  → RequirementOutlinePage（新增：概要需求）
  /requirement-detailed → RequirementDetailedPage（新增：详细需求）
  /design-outline    → DesignOutlinePage（新增：概要设计，复用 C4Navigator + WireframeCanvas）
  /design-detailed   → DesignDetailedPage（新增：详细设计，复用 OpenUIPreview + BindingPanel）
  /artifacts         → StudioArtifactViewer（新增：设计产物，复用 ArtifactViewer）
  /governance        → StudioGovernancePage（新增：架构治理，复用 ArchGovernance）

/execution
  /canvas          → CanvasPage（现有页面，从项目中心移入）
  /task-center     → TaskCenterPage（新增：任务中心）
  /issues          → ExecutionIssuesPage（新增：执行问题）
  /monitor         → ExecutionMonitor（现有页面，重命名路径）
  /cli             → AiCliPage（现有页面，重命名路径）
  /dashboard       → MonitoringDashboard（现有页面，重命名路径）

/artifact-verification
  /browser         → ArtifactViewer（现有页面，重命名路径）
  /validation      → ArchValidation（现有页面，重命名路径）
  /history         → HistoryViewer（现有页面，重命名路径）

/governance
  /approval-center → GateCenter（现有页面，重命名路径）
  /bypass          → BypassManager（现有页面，重命名路径）

/platform
  /skill-management → SkillRegistry（现有页面，重命名路径）
  /llm-config       → LlmConfig（现有页面，重命名路径）
  /template-config  → TemplateStageConfig（现有页面，重命名路径）
  /doc-standard     → DocForgeAdmin（现有页面，重命名路径）
```

### 5.2 导航重组

新导航树（6 个一级菜单）：

```typescript
const navGroups: NavGroup[] = [
  {
    icon: '📊',
    label: '项目中心',
    items: [
      { label: '项目工作台', path: '/project-center/workbench' },
      { label: '应用管理', path: '/project-center/application' },
    ],
  },
  {
    icon: '🎨',
    label: '需求设计室',
    items: [
      { label: '概要需求', path: '/requirement-studio/requirement-outline' },
      { label: '详细需求', path: '/requirement-studio/requirement-detailed' },
      { label: '概要设计', path: '/requirement-studio/design-outline' },
      { label: '详细设计', path: '/requirement-studio/design-detailed' },
      { label: '设计产物', path: '/requirement-studio/artifacts' },
      { label: '架构治理', path: '/requirement-studio/governance' },
    ],
  },
  {
    icon: '▶️',
    label: '开发执行',
    items: [
      { label: '项目画布', path: '/execution/canvas' },
      { label: '任务中心', path: '/execution/task-center' },
      { label: '执行问题', path: '/execution/issues' },
      { label: '执行监控', path: '/execution/monitor' },
      { label: 'AI CLI', path: '/execution/cli' },
      { label: '监控看板', path: '/execution/dashboard' },
    ],
  },
  {
    icon: '📦',
    label: '产物验证',
    items: [
      { label: '产物浏览器', path: '/artifact-verification/browser' },
      { label: '架构验证', path: '/artifact-verification/validation' },
      { label: '历史回溯', path: '/artifact-verification/history' },
    ],
  },
  {
    icon: '🛡️',
    label: '治理审批',
    items: [
      { label: '审批中心', path: '/governance/approval-center' },
      { label: '旁路审批', path: '/governance/bypass' },
    ],
  },
  {
    icon: '⚙️',
    label: '平台管理',
    items: [
      { label: 'Skill 治理', path: '/platform/skill-management' },
      { label: 'LLM 配置', path: '/platform/llm-config' },
      { label: '模板配置', path: '/platform/template-config' },
      { label: '文档标准化', path: '/platform/doc-standard' },
    ],
  },
]
```

### 5.3 新增页面组件

| 页面 | 类型 | 说明 |
|------|------|------|
| `RequirementStudioOverview` | 新增 | 需求设计室入口，展示阶段导航与项目进度 |
| `RequirementOutlinePage` | 新增 | 概要需求，含任务树、草图、规模初估卡片 |
| `RequirementDetailedPage` | 新增 | 详细需求，含详细 PRD、接口契约初稿 |
| `DesignOutlinePage` | 新增 | 概要设计，含 HLD、C4 L1/L2、线框图（复用现有组件） |
| `DesignDetailedPage` | 新增 | 详细设计，含 C4 L3/L4、OpenUI、数据绑定、DB 设计（复用现有组件） |
| `StudioArtifactViewer` | 新增 | 设计产物总览（复用 ArtifactViewer 核心组件） |
| `StudioGovernancePage` | 新增 | 架构治理（复用 ArchGovernancePage） |
| `TaskCenterPage` | 新增 | 任务中心，三栏布局：任务树/任务详情/执行面板 |
| `ExecutionIssuesPage` | 新增 | 执行问题，支持反馈回架构 |

### 5.4 复用策略

现有页面组件不删除，通过以下方式复用：

1. **提取共享组件**：将现有页面中的核心渲染组件提取到 `components/` 或 `containers/` 目录
2. **页面级包装器**：新页面作为包装器，组合现有组件 + 新增布局
3. **路由重定向**：旧路由保留重定向到新路由，兼容外部书签

---

## 6. 数据流设计

### 6.1 需求设计室数据流

```
用户进入需求设计室
  → GET /api/v1/requirement-studio/{projectId}/status
  → 返回各阶段状态 + 锁定/解锁信息
  → 前端渲染顶部阶段导航条（高亮当前阶段，置灰未解锁阶段）

用户点击阶段节点
  → GET /api/v1/requirement-studio/{projectId}/stage/{stageId}/tasks
  → 返回该阶段任务树
  → 左侧渲染任务树，中间渲染默认产物，右侧显示执行面板

用户点击"执行 Skill"
  → POST /api/v1/requirement-studio/{projectId}/stage/{stageId}/execute
  → 调用 StageOrchestrator 触发 Skill
  → SSE 推送实时状态更新
  → 产物生成后，中间区自动刷新

用户提交审查
  → POST /api/v1/requirement-studio/{projectId}/stage/{stageId}/review
  → 更新阶段状态，解锁下一阶段
```

### 6.2 任务中心数据流

```
用户进入任务中心
  → GET /api/v1/execution/{projectId}/tasks
  → 返回按模块分组任务列表
  → 左侧渲染任务树

用户选择任务
  → 中间渲染任务详情（输入产物、状态、输出产物）
  → 右侧加载对应 Skill 快照

用户点击"执行"
  → POST /api/v1/execution/{projectId}/tasks/{taskId}/execute
  → 触发 PocketFlow
  → SSE 推送日志
  → 状态自动更新

测试失败
  → 任务状态 = FAILED
  → 用户点击"标记为 Bug"
  → POST /api/v1/execution/{projectId}/issues
  → 创建执行问题
  → 可选：POST /api/v1/execution/{projectId}/issues/{issueId}/feedback-to-architecture
  → 标记产物 Stale，创建变更请求
```

---

## 7. 兼容性设计

### 7.1 向后兼容

1. **旧路由重定向**：保留旧路由 6 个月，返回 301 重定向到新路由
2. **旧 API 保留**：现有 API 继续支持，新 API 逐步迁移
3. **数据库兼容**：新增模型通过 Alembic migration 添加，不影响现有数据

### 7.2 前端迁移路径

```
Phase 1（本迭代）:
  - 调整导航和路由
  - 新增需求设计室、任务中心、执行问题页面（骨架）
  - 现有页面移动到新的导航位置
  - 旧路由添加重定向

Phase 2（后续迭代）:
  - 填充需求设计室各阶段功能
  - 填充任务中心完整功能
  - 填充执行问题反馈回架构联动
```

---

## 8. 测试策略

### 8.1 单元测试

- 后端：`TaskCenterService`, `ExecutionIssueService`, `RequirementStudioService` 的纯逻辑测试
- 前端：新增页面组件的渲染测试、状态流转测试

### 8.2 集成测试

- API 端到端测试：新路由的 CRUD 流程
- 前后端联调：导航跳转、数据加载、状态同步

### 8.3 E2E 测试

- 完整用户流程：创建项目 → 进入需求设计室 → 进入开发执行 → 任务执行 → 执行问题反馈
- 回归测试：现有功能不受影响

---

## 9. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 现有页面组件耦合度高 | 中 | 先提取共享组件，再组装新页面 |
| 数据库 migration 回滚 | 低 | Alembic 事务化 migration，测试环境先行验证 |
| 路由变更导致用户书签失效 | 低 | 保留旧路由重定向 6 个月 |
| 新服务层与现有 orchestrator 冲突 | 中 | 新服务层仅做编排，不替代现有 orchestrator 核心逻辑 |
| 阶段状态机复杂 | 中 | 复用现有 `ProjectStage.runtime_status`，新增业务层状态映射 |

---

## 10. 附录：变更清单

### 后端文件变更

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/app/models/execution_task.py` | 新增 | 任务模型 |
| `backend/app/models/execution_issue.py` | 新增 | 执行问题模型 |
| `backend/app/schemas/execution_task.py` | 新增 | 任务 Schema |
| `backend/app/schemas/execution_issue.py` | 新增 | 执行问题 Schema |
| `backend/app/services/task_center_service.py` | 新增 | 任务中心服务 |
| `backend/app/services/execution_issue_service.py` | 新增 | 执行问题服务 |
| `backend/app/services/requirement_studio_service.py` | 新增 | 需求设计室服务 |
| `backend/app/api/v1/execution.py` | 新增 | 开发执行 API 路由 |
| `backend/app/api/v1/requirement_studio.py` | 新增 | 需求设计室 API 路由 |
| `backend/app/api/v1/router.py` | 修改 | 注册新路由 |
| `backend/app/main.py` | 无修改 | 无需修改 |
| `migrations/versions/xxx_add_execution_task.py` | 新增 | Alembic migration |
| `migrations/versions/xxx_add_execution_issue.py` | 新增 | Alembic migration |

### 前端文件变更

| 文件 | 操作 | 说明 |
|------|------|------|
| `frontend/src/App.tsx` | 修改 | 导航重组 + 路由重组 |
| `frontend/src/pages/RequirementStudio/` | 新增目录 | 需求设计室页面 |
| `frontend/src/pages/Execution/` | 新增目录 | 开发执行页面 |
| `frontend/src/pages/ArtifactVerification/` | 新增目录 | 产物验证页面 |
| `frontend/src/pages/Governance/` | 新增目录 | 治理审批页面 |
| `frontend/src/pages/Platform/` | 新增目录 | 平台管理页面 |
| `frontend/src/pages/ProjectCenter/` | 新增目录 | 项目中心页面 |
| `frontend/src/services/execution.ts` | 新增 | 开发执行 API 封装 |
| `frontend/src/services/requirementStudio.ts` | 新增 | 需求设计室 API 封装 |
| `frontend/src/services/project.ts` | 修改 | 路径调整 |
| `frontend/src/services/gate.ts` | 修改 | 路径调整 |
| `frontend/src/services/api.ts` | 修改 | 新增 baseURL 或 interceptor |

