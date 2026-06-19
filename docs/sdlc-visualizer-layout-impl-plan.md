# SDLC Visualizer 前端布局重构方案（v3.0 实施版）

> **版本**: v3.0-实施  
> **日期**: 2026-06-17  
> **目标**: 根据 `sdlc-visualizer-menu-design-v3.md` 重构前端路由、导航与页面，**零后端改动**，完全复用现有接口。

---

## 1. 新旧路由映射总表

### 1.1 一级菜单：项目工作台

| 二级页面 | 新路由 | 复用页面组件 | 来源旧路由 | 备注 |
|---------|--------|------------|-----------|------|
| 应用管理 | `/project-center/application` | `AppDashboard` | `/project-center/application` | 无变化 |
| 项目管理 | `/project-center/project` | `ProjectDashboard` | `/project-center/workbench` | 路由改名 |
| 产物浏览器 | `/project-center/artifact-browser` | `ArtifactViewer` | `/artifact-verification/browser` | 从产物验证移入 |
| 审批中心 | `/project-center/approval` | `GateCenter` | `/governance/approval-center` | 从治理审批移入，合并上线审批 |

### 1.2 一级菜单：需求设计室

| 二级页面 | 新路由 | 复用/创建页面 | 来源旧路由 | 备注 |
|---------|--------|------------|-----------|------|
| 脑暴室 | `/requirement-studio/brainstorm` | **新建** `BrainstormPage` | 原 `RequirementStudio` 内嵌 | 独立为页面 |
| 需求方案 | `/requirement-studio/requirement-plan` | **新建** `RequirementPlanPage` | 合并 `/requirement-studio/requirement-outline` + `requirement-detailed` | Tab 切换概要/详细 |
| 需求草图 | `/requirement-studio/sketch` | `SketchGallery` | `/sketches` | 路由改名 |
| 需求确认 | `/requirement-studio/requirement-gate` | `GateCenter` (filter) | `/gates` 中 Gate 1/2.5 | 复用审批中心组件 |

### 1.3 一级菜单：方案设计室

| 二级页面 | 新路由 | 复用/创建页面 | 来源旧路由 | 备注 |
|---------|--------|------------|-----------|------|
| 设计方案 | `/solution-studio/design-plan` | **新建** `DesignPlanPage` | 合并 `/requirement-studio/design-outline` + `design-detailed` | Tab 切换概要/详细/DB/接口 |
| 系统结构 | `/solution-studio/system-structure` | `C4Navigator` | `/c4` | 路由改名 |
| 页面布局 | `/solution-studio/page-layout` | `WireframeCanvas` | `/wireframe` | 路由改名 |
| 交互原型 | `/solution-studio/interaction-prototype` | `OpenUIPreview` | `/open-ui` | 路由改名 |
| 接口对照 | `/solution-studio/interface-check` | `BindingPanel` | `/binding` | 路由改名 |
| 设计定稿 | `/solution-studio/design-finalization` | **新建** `DesignFinalizationPage` | 合并 `/arch-governance` + `/gates` Gate 2 | 基线化+审批合并 |

### 1.4 一级菜单：开发执行室

| 二级页面 | 新路由 | 复用/创建页面 | 来源旧路由 | 备注 |
|---------|--------|------------|-----------|------|
| 任务编排 | `/execution-studio/task-orchestration` | `TaskCenter` (增强) | `/execution/task-center` | 改名，嵌入执行监控面板 |
| 代码开发 | `/execution-studio/coding` | `CanvasPage` | `/execution/canvas` | 路由改名 |
| 测试调试 | `/execution-studio/testing` | `ExecutionIssues` (增强) | `/execution/issues` | 改名，合并执行问题 |
| AI CLI | `/execution-studio/cli` | `AiCliPage` | `/execution/cli` | **保留**（用户明确要求） |

### 1.5 一级菜单：平台管理（保留）

| 二级页面 | 新路由 | 复用页面 | 来源旧路由 | 备注 |
|---------|--------|---------|-----------|------|
| Skill 治理 | `/platform/skill-management` | `SkillRegistry` | `/platform/skill-management` | 无变化 |
| LLM 配置 | `/platform/llm-config` | `LlmConfig` | `/platform/llm-config` | 无变化 |
| 模板配置 | `/platform/template-config` | `TemplateStageConfig` | `/platform/template-config` | 无变化 |
| 文档标准化 | `/platform/doc-standard` | `DocForgeAdmin` | `/platform/doc-standard` | 无变化 |

### 1.6 被去掉的页面与路由

| 旧路由 | 旧页面 | 去向 | 重定向目标 |
|--------|--------|------|-----------|
| `/execution/monitor` | `ExecutionMonitor` | **去掉**，功能下沉 | `/execution-studio/task-orchestration` |
| `/execution/dashboard` | `MonitoringDashboard` | **去掉** | `/project-center/project` |
| `/execution/issues` | `ExecutionIssues` | 合并到测试调试 | `/execution-studio/testing` |
| `/artifact-verification/validation` | `ArchValidation` | 保留页面，但入口去掉 | `/solution-studio/design-finalization` |
| `/artifact-verification/history` | `HistoryViewer` | 保留页面，但入口去掉 | `/project-center/artifact-browser` |
| `/governance/bypass` | `BypassManager` | 合并到审批中心 | `/project-center/approval` |
| `/requirement-studio/*` (原整体) | `RequirementStudio` | 拆分 | 按子路由分别重定向 |
| `/arch-governance` | `ArchGovernance` | 合并到设计定稿 | `/solution-studio/design-finalization` |

---

## 2. 合并页面设计

### 2.1 需求方案（RequirementPlanPage）

**复用来源**: `RequirementStudio` 的 `requirement-outline` + `requirement-detailed` 阶段

**内部结构**:
- 顶部 Tab: `[概要视图]` `[详细视图]` `[版本历史]`
- 左侧: 需求目录树（按模块/用户故事组织）
- 中间: 产物渲染区（ArtifactRenderer）
- 右侧: 审查与执行面板（ReviewPanel + ExecutionPanel）

**接口复用**:
- `fetchStudioStatus(projectId)` → 获取阶段状态
- `executeStage(projectId, stageId)` → 执行阶段
- `fetchArtifacts(projectId)` → 获取产物列表
-  annotations API → 审查批注

### 2.2 设计方案（DesignPlanPage）

**复用来源**: `RequirementStudio` 的 `design-outline` + `design-detailed` 阶段

**内部结构**:
- 顶部 Tab: `[概要设计]` `[详细设计]` `[DB设计]` `[接口契约]` `[版本历史]`
- 左侧: 设计目录树
- 中间: 产物渲染区
- 右侧: 审查与执行面板

**接口复用**: 同需求方案，复用 `requirement-studio` API（阶段 ID 不同）

### 2.3 设计定稿（DesignFinalizationPage）

**复用来源**: `ArchGovernance` + `GateCenter` 的 Gate 2 审批

**内部结构**:
- 左侧: 待基线产物清单（复用 ArchGovernance 的 issue 筛选逻辑）
- 中间: 基线状态与变更影响（复用 `c4/analyze` + `baseline` API）
- 右侧: 审批面板（复用 GateCenter 的审批组件）

**接口复用**:
- `/api/v1/c4/analyze` → 架构分析
- `/api/v1/c4/governance/fix-plan` → 修复计划
- `/api/v1/gates` → Gate 审批
- `/api/v1/requirement-studio/{projectId}/governance/baseline` → 基线化
- `/api/v1/requirement-studio/{projectId}/governance/change-request` → 变更请求

### 2.4 任务编排（TaskOrchestrationPage）

**复用来源**: `TaskCenter`

**增强点**:
- 右侧滑出式"执行面板"（复用 `ExecutionPanel` + `ExecutionMonitor` 的日志流逻辑）
- 点击执行后自动展开面板，展示 PocketFlow PREP/EXEC/POST 状态
- 执行完成后展示"产物预览"按钮

**接口复用**:
- `/api/v1/execution/{projectId}/tasks` → 任务 CRUD
- `/api/v1/execution/{projectId}/tasks/{taskId}/execute` → 执行任务
- `/api/v1/skill-executions` → 执行监控（SSE 日志流）

### 2.5 测试调试（TestingPage）

**复用来源**: `ExecutionIssues`

**增强点**:
- 新增"反馈回方案设计室"按钮
- 弹窗选择关联设计产物 → 自动创建变更请求
- 测试执行时内嵌展示实时日志（复用 ExecutionMonitor 的日志流）

**接口复用**:
- `/api/v1/execution/{projectId}/issues` → 问题 CRUD
- `/api/v1/execution/{projectId}/issues/{issueId}/feedback` → 反馈回架构
- `/api/v1/requirement-studio/{projectId}/governance/change-request` → 创建变更请求

---

## 3. 后端接口兼容性声明

**本次重构为纯前端改动，后端所有接口保持原样。**

复用的后端 API 模块：

| 前端页面 | 复用后端 API 模块 | 端点前缀 |
|---------|------------------|---------|
| 需求方案 | `requirement_studio` | `/v1/requirement-studio` |
| 设计方案 | `requirement_studio` | `/v1/requirement-studio` |
| 系统结构 | `c4` | `/v1/c4` |
| 页面布局 | `wireframe` | `/v1/wireframe` |
| 交互原型 | `open_ui` | `/v1/open-ui` |
| 接口对照 | `binding` | `/v1/binding` |
| 设计定稿 | `c4` + `governance` + `requirement_studio` | `/v1/c4`, `/v1/gates`, `/v1/requirement-studio` |
| 任务编排 | `execution` + `skill_executions` | `/v1/execution`, `/v1/skill-executions` |
| 测试调试 | `execution` + `requirement_studio` | `/v1/execution`, `/v1/requirement-studio` |
| 产物浏览器 | `artifacts` | `/v1/artifacts` |
| 审批中心 | `governance` + `bypass` | `/v1/gates`, `/v1/bypass` |
| 应用管理 | `applications` | `/v1/applications` |
| 项目管理 | `projects` | `/v1/projects` |
| AI CLI | `cli` + `chat` + `config_nodes` | `/v1/cli`, `/v1/chat`, `/v1/config-nodes` |
| 平台管理 | `skills` + `templates` + `llm_*` + `docforge_admin` | `/v1/skills`, `/v1/templates`, `/v1/llm-*`, `/v1/docforge-admin` |

---

## 4. 实施步骤

### 4.1 Phase 1: 路由与导航重构（W1）

1. 修改 `App.tsx`:
   - 重定义 `navGroups` 为 4 个一级菜单（室）+ 平台管理
   - 新增/调整所有 `<Route>` 映射
   - 添加旧路由 `<Navigate>` 重定向
   - **保留 AI CLI 节点**在开发执行室

2. 创建新页面目录结构:
   - `src/pages/RequirementStudio/Brainstorm/`
   - `src/pages/RequirementStudio/RequirementPlan/`
   - `src/pages/SolutionStudio/DesignPlan/`
   - `src/pages/SolutionStudio/DesignFinalization/`
   - `src/pages/ExecutionStudio/TaskOrchestration/`
   - `src/pages/ExecutionStudio/Testing/`

3. 创建新页面入口文件（先以 wrapper + 复用现有组件的方式实现 MVP）:
   - `BrainstormPage` → 复用 `RequirementStudio` 的脑暴相关部分
   - `RequirementPlanPage` → 复用 `RequirementStudio` 的概要+详细阶段
   - `DesignPlanPage` → 复用 `RequirementStudio` 的设计阶段
   - `DesignFinalizationPage` → 复用 `ArchGovernance` + `GateCenter` 组件
   - `TaskOrchestrationPage` → 复用 `TaskCenter` + 增强执行面板
   - `TestingPage` → 复用 `ExecutionIssues` + 增强反馈功能

### 4.2 Phase 2: 合并页面增强（W2-W3）

1. 在 `RequirementPlanPage` 中实现 Tab 切换（概要/详细/版本历史）
2. 在 `DesignPlanPage` 中实现 Tab 切换（概要/详细/DB/接口）
3. 在 `DesignFinalizationPage` 中整合基线化 + 审批面板
4. 在 `TaskOrchestrationPage` 中嵌入可折叠的执行面板
5. 在 `TestingPage` 中新增"反馈回方案设计室"弹窗

### 4.3 Phase 3: 清理与验证（W4）

1. 移除旧路由的独立页面引用（但保留文件，避免破坏）
2. 验证所有旧路由 `<Navigate>` 重定向正确
3. 验证所有现有后端接口调用正常
4. 类型检查与 lint 通过

---

## 5. 旧路由重定向清单

```tsx
// 项目工作台
<Route path="/project-center/workbench" element={<Navigate to="/project-center/project" replace />} />
<Route path="/project-center/workbench/*" element={<Navigate to="/project-center/project" replace />} />

// 需求设计室（拆分）
<Route path="/requirement-studio/requirement-outline" element={<Navigate to="/requirement-studio/requirement-plan" replace />} />
<Route path="/requirement-studio/requirement-detailed" element={<Navigate to="/requirement-studio/requirement-plan" replace />} />
<Route path="/requirement-studio/design-outline" element={<Navigate to="/solution-studio/design-plan" replace />} />
<Route path="/requirement-studio/design-detailed" element={<Navigate to="/solution-studio/design-plan" replace />} />
<Route path="/requirement-studio/artifacts" element={<Navigate to="/solution-studio/design-plan" replace />} />
<Route path="/requirement-studio/governance" element={<Navigate to="/solution-studio/design-finalization" replace />} />

// 方案设计室（改名）
<Route path="/c4" element={<Navigate to="/solution-studio/system-structure" replace />} />
<Route path="/wireframe" element={<Navigate to="/solution-studio/page-layout" replace />} />
<Route path="/open-ui" element={<Navigate to="/solution-studio/interaction-prototype" replace />} />
<Route path="/binding" element={<Navigate to="/solution-studio/interface-check" replace />} />
<Route path="/arch-governance" element={<Navigate to="/solution-studio/design-finalization" replace />} />
<Route path="/sketches" element={<Navigate to="/requirement-studio/sketch" replace />} />

// 开发执行室（改名+合并）
<Route path="/execution/task-center" element={<Navigate to="/execution-studio/task-orchestration" replace />} />
<Route path="/execution/canvas" element={<Navigate to="/execution-studio/coding" replace />} />
<Route path="/execution/canvas/:projectId" element={<Navigate to="/execution-studio/coding" replace />} />
<Route path="/execution/issues" element={<Navigate to="/execution-studio/testing" replace />} />
<Route path="/execution/monitor" element={<Navigate to="/execution-studio/task-orchestration" replace />} />
<Route path="/execution/monitor/:executionId" element={<Navigate to="/execution-studio/task-orchestration" replace />} />
<Route path="/execution/cli" element={<Navigate to="/execution-studio/cli" replace />} />
<Route path="/execution/dashboard" element={<Navigate to="/project-center/project" replace />} />

// 产物验证（合并到项目工作台）
<Route path="/artifact-verification/browser" element={<Navigate to="/project-center/artifact-browser" replace />} />
<Route path="/artifact-verification/validation" element={<Navigate to="/solution-studio/design-finalization" replace />} />
<Route path="/artifact-verification/history" element={<Navigate to="/project-center/artifact-browser" replace />} />

// 治理审批（合并到项目工作台）
<Route path="/governance/approval-center" element={<Navigate to="/project-center/approval" replace />} />
<Route path="/governance/approval-center/*" element={<Navigate to="/project-center/approval" replace />} />
<Route path="/governance/bypass" element={<Navigate to="/project-center/approval" replace />} />
<Route path="/gates" element={<Navigate to="/project-center/approval" replace />} />
<Route path="/gates/*" element={<Navigate to="/project-center/approval" replace />} />

// 历史遗留（已有）
<Route path="/projects" element={<Navigate to="/project-center/project" replace />} />
<Route path="/projects/create" element={<Navigate to="/project-center/project/create" replace />} />
<Route path="/applications" element={<Navigate to="/project-center/application" replace />} />
<Route path="/executions" element={<Navigate to="/execution-studio/task-orchestration" replace />} />
<Route path="/cli" element={<Navigate to="/execution-studio/cli" replace />} />
<Route path="/monitoring" element={<Navigate to="/project-center/project" replace />} />
<Route path="/artifacts" element={<Navigate to="/project-center/artifact-browser" replace />} />
<Route path="/arch-validation" element={<Navigate to="/solution-studio/design-finalization" replace />} />
<Route path="/history" element={<Navigate to="/project-center/artifact-browser" replace />} />
<Route path="/bypass" element={<Navigate to="/project-center/approval" replace />} />
<Route path="/skills" element={<Navigate to="/platform/skill-management" replace />} />
<Route path="/settings/llm" element={<Navigate to="/platform/llm-config" replace />} />
<Route path="/template-config" element={<Navigate to="/platform/template-config" replace />} />
<Route path="/docforge" element={<Navigate to="/platform/doc-standard" replace />} />
```

---

## 6. 新导航结构（App.tsx navGroups）

```typescript
const navGroups: NavGroup[] = [
  {
    icon: '🏢',
    label: '项目工作台',
    items: [
      { label: '应用管理', path: '/project-center/application' },
      { label: '项目管理', path: '/project-center/project' },
      { label: '产物浏览器', path: '/project-center/artifact-browser' },
      { label: '审批中心', path: '/project-center/approval' },
    ],
  },
  {
    icon: '🎨',
    label: '需求设计室',
    items: [
      { label: '脑暴室', path: '/requirement-studio/brainstorm' },
      { label: '需求方案', path: '/requirement-studio/requirement-plan' },
      { label: '需求草图', path: '/requirement-studio/sketch' },
      { label: '需求确认', path: '/requirement-studio/requirement-gate' },
    ],
  },
  {
    icon: '🏗️',
    label: '方案设计室',
    items: [
      { label: '设计方案', path: '/solution-studio/design-plan' },
      { label: '系统结构', path: '/solution-studio/system-structure' },
      { label: '页面布局', path: '/solution-studio/page-layout' },
      { label: '交互原型', path: '/solution-studio/interaction-prototype' },
      { label: '接口对照', path: '/solution-studio/interface-check' },
      { label: '设计定稿', path: '/solution-studio/design-finalization' },
    ],
  },
  {
    icon: '▶️',
    label: '开发执行室',
    items: [
      { label: '任务编排', path: '/execution-studio/task-orchestration' },
      { label: '代码开发', path: '/execution-studio/coding' },
      { label: '测试调试', path: '/execution-studio/testing' },
      { label: 'AI CLI', path: '/execution-studio/cli' },
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

---

## 7. 注意事项

1. **后端零改动**: 所有前端页面仅通过路由重组和组件复用实现，不新增、不修改、不删除任何后端 API。
2. **AI CLI 保留**: 按用户要求，AI CLI 节点保留在开发执行室中，用于页面自然语言使用 LLM 能力。
3. **渐进式实现**: 新页面先以 wrapper + 复用现有组件的方式实现 MVP，后续逐步增强 UI 交互。
4. **旧文件保留**: 被合并的旧页面文件不删除，仅通过路由重定向引导到新页面，避免破坏既有代码。
5. **状态管理复用**: 现有 `useRequirementStudioStore`、`useExecutionStore`、`useGateCenterStore` 等 Zustand store 继续复用，无需新建 store。
