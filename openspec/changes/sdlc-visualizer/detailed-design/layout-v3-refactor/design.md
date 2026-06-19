---
dr: DR-024
module: 前端布局重构 v3.0
version: v1.0
status: FROZEN
date: 2026-06-17
upstream: PRD-000 v3.0 / HLD-000 v1.0 / sdlc-visualizer-menu-design-v3.md
---

# DR-024 前端布局重构 v3.0 — 模块详细设计

> **模块编号**：DR-024  
> **模块名称**：前端布局重构 v3.0（Layout Refactor v3.0）  
> **版本**：v1.0  
> **状态**：FROZEN  
> **设计日期**：2026-06-17  
> **上游基线**：PRD-000 v3.0 / HLD-000 v1.0 / `sdlc-visualizer-menu-design-v3.md`（菜单设计方案 v3）  
> **变更性质**：纯前端重构，**后端零改动**

---

## 1. 设计目标与范围

### 1.1 目标

根据 `sdlc-visualizer-menu-design-v3.md` 提供的最新页面功能布局方案，对现有前端路由、导航、页面进行重构：
- 将原有 7 个一级菜单（项目中心/需求设计室/架构设计/开发执行/产物验证/治理审批/平台管理）合并为 **4 个一级菜单（室）+ 平台管理**
- 保留 AI CLI 节点于开发执行室中，用于页面自然语言使用 LLM 能力
- 合并概要/详细需求、概要/详细设计、架构治理/审批等页面，通过 Tab 切换
- 所有旧路由通过 `<Navigate>` 重定向兼容，**不删除旧文件**

### 1.2 范围

| In-Scope | Out-of-Scope |
|----------|--------------|
| 前端路由重组（`App.tsx`） | 后端 API 任何改动 |
| 新页面创建（6 个合并页） | 旧页面文件删除 |
| 导航侧边栏重构 | 数据库 Schema 变更 |
| 旧路由重定向（30+ 条） | 新后端接口开发 |
| 状态管理复用 | 技能（Skill）定义变更 |
| TypeScript 类型修复 | 产物存储格式变更 |

### 1.3 术语

| 术语 | 定义 |
|------|------|
| **室** | 一级菜单分组，如"需求设计室""方案设计室""开发执行室" |
| **合并页** | 将两个或以上旧页面合并为一个新页面，通过 Tab 切换 |
| **重定向** | React Router `<Navigate>`，旧 URL 自动跳转至新 URL |
| **wrapper** | 复用现有组件作为新页面的 MVP 实现方式 |

---

## 2. 架构设计

### 2.1 前端路由架构（重构后）

```
┌─────────────────────────────────────────────────────────────────┐
│                        App.tsx                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │ 项目工作台   │  │ 需求设计室   │  │ 方案设计室   │  │ 开发执行 │ │
│  │ 4 个二级页   │  │ 4 个二级页   │  │ 6 个二级页   │  │ 4 个二级│ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
│  ┌─────────────┐                                                │
│  │ 平台管理     │  4 个二级页                                    │
│  └─────────────┘                                                │
└─────────────────────────────────────────────────────────────────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
        ┌─────────┐ ┌─────────┐ ┌─────────┐
        │ 新页面  │ │ 旧页面  │ │ 重定向  │
        │ (6个)   │ │ (保留)  │ │ (30+条) │
        └─────────┘ └─────────┘ └─────────┘
```

### 2.2 导航结构（navGroups）

```typescript
const navGroups: NavGroup[] = [
  {
    icon: '🏢', label: '项目工作台',
    items: [
      { label: '应用管理', path: '/project-center/application' },
      { label: '项目管理', path: '/project-center/project' },
      { label: '产物浏览器', path: '/project-center/artifact-browser' },
      { label: '审批中心', path: '/project-center/approval' },
    ],
  },
  {
    icon: '🎨', label: '需求设计室',
    items: [
      { label: '脑暴室', path: '/requirement-studio/brainstorm' },
      { label: '需求方案', path: '/requirement-studio/requirement-plan' },
      { label: '需求草图', path: '/requirement-studio/sketch' },
      { label: '需求确认', path: '/requirement-studio/requirement-gate' },
    ],
  },
  {
    icon: '🏗️', label: '方案设计室',
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
    icon: '▶️', label: '开发执行室',
    items: [
      { label: '任务编排', path: '/execution-studio/task-orchestration' },
      { label: '代码开发', path: '/execution-studio/coding' },
      { label: '测试调试', path: '/execution-studio/testing' },
      { label: 'AI CLI', path: '/execution-studio/cli' },
    ],
  },
  {
    icon: '⚙️', label: '平台管理',
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

## 3. 路由映射详表

### 3.1 新路由（17 个二级页面）

| 一级菜单 | 二级页面 | 路由 | 复用/创建 | 来源旧路由 |
|---------|---------|------|----------|-----------|
| 项目工作台 | 应用管理 | `/project-center/application` | `AppDashboard` | 无变化 |
| 项目工作台 | 项目管理 | `/project-center/project` | `ProjectDashboard` | `/project-center/workbench` |
| 项目工作台 | 产物浏览器 | `/project-center/artifact-browser` | `ArtifactViewer` | `/artifact-verification/browser` |
| 项目工作台 | 审批中心 | `/project-center/approval` | `GateCenter` | `/governance/approval-center` |
| 需求设计室 | 脑暴室 | `/requirement-studio/brainstorm` | **新建** `BrainstormPage` | 原 `RequirementStudio` 内嵌 |
| 需求设计室 | 需求方案 | `/requirement-studio/requirement-plan` | **新建** `RequirementPlanPage` | 合并 `/requirement-studio/*` 概要+详细 |
| 需求设计室 | 需求草图 | `/requirement-studio/sketch` | `SketchGallery` | `/sketches` |
| 需求设计室 | 需求确认 | `/requirement-studio/requirement-gate` | `GateCenter` (filter) | `/gates` Gate 1/2.5 |
| 方案设计室 | 设计方案 | `/solution-studio/design-plan` | **新建** `DesignPlanPage` | 合并 `/requirement-studio/*` 设计阶段 |
| 方案设计室 | 系统结构 | `/solution-studio/system-structure` | `C4Navigator` | `/c4` |
| 方案设计室 | 页面布局 | `/solution-studio/page-layout` | `WireframeCanvas` | `/wireframe` |
| 方案设计室 | 交互原型 | `/solution-studio/interaction-prototype` | `OpenUIPreview` | `/open-ui` |
| 方案设计室 | 接口对照 | `/solution-studio/interface-check` | `BindingPanel` | `/binding` |
| 方案设计室 | 设计定稿 | `/solution-studio/design-finalization` | **新建** `DesignFinalizationPage` | 合并 `/arch-governance` + `/gates` Gate 2 |
| 开发执行室 | 任务编排 | `/execution-studio/task-orchestration` | **新建** `TaskOrchestrationPage` | `/execution/task-center` 增强 |
| 开发执行室 | 代码开发 | `/execution-studio/coding` | `CanvasPage` | `/execution/canvas` |
| 开发执行室 | 测试调试 | `/execution-studio/testing` | **新建** `TestingPage` | `/execution/issues` 增强 |
| 开发执行室 | AI CLI | `/execution-studio/cli` | `AiCliPage` | `/execution/cli` 保留 |
| 平台管理 | 4 个页面 | `/platform/*` | 无变化 | 无变化 |

### 3.2 旧路由重定向（30+ 条）

```tsx
// 项目工作台
<Route path="/project-center/workbench" element={<Navigate to="/project-center/project" replace />} />

// 需求设计室拆分
<Route path="/requirement-studio/requirement-outline" element={<Navigate to="/requirement-studio/requirement-plan" replace />} />
<Route path="/requirement-studio/requirement-detailed" element={<Navigate to="/requirement-studio/requirement-plan" replace />} />
<Route path="/requirement-studio/design-outline" element={<Navigate to="/solution-studio/design-plan" replace />} />
<Route path="/requirement-studio/design-detailed" element={<Navigate to="/solution-studio/design-plan" replace />} />
<Route path="/requirement-studio/artifacts" element={<Navigate to="/solution-studio/design-plan" replace />} />
<Route path="/requirement-studio/governance" element={<Navigate to="/solution-studio/design-finalization" replace />} />

// 方案设计室改名
<Route path="/c4" element={<Navigate to="/solution-studio/system-structure" replace />} />
<Route path="/wireframe" element={<Navigate to="/solution-studio/page-layout" replace />} />
<Route path="/open-ui" element={<Navigate to="/solution-studio/interaction-prototype" replace />} />
<Route path="/binding" element={<Navigate to="/solution-studio/interface-check" replace />} />
<Route path="/arch-governance" element={<Navigate to="/solution-studio/design-finalization" replace />} />
<Route path="/sketches" element={<Navigate to="/requirement-studio/sketch" replace />} />

// 开发执行室改名+合并
<Route path="/execution/task-center" element={<Navigate to="/execution-studio/task-orchestration" replace />} />
<Route path="/execution/canvas" element={<Navigate to="/execution-studio/coding" replace />} />
<Route path="/execution/issues" element={<Navigate to="/execution-studio/testing" replace />} />
<Route path="/execution/monitor" element={<Navigate to="/execution-studio/task-orchestration" replace />} />
<Route path="/execution/cli" element={<Navigate to="/execution-studio/cli" replace />} />
<Route path="/execution/dashboard" element={<Navigate to="/project-center/project" replace />} />

// 产物验证合并
<Route path="/artifact-verification/browser" element={<Navigate to="/project-center/artifact-browser" replace />} />
<Route path="/artifact-verification/validation" element={<Navigate to="/solution-studio/design-finalization" replace />} />
<Route path="/artifact-verification/history" element={<Navigate to="/project-center/artifact-browser" replace />} />

// 治理审批合并
<Route path="/governance/approval-center" element={<Navigate to="/project-center/approval" replace />} />
<Route path="/governance/bypass" element={<Navigate to="/project-center/approval" replace />} />
<Route path="/gates" element={<Navigate to="/project-center/approval" replace />} />

// 历史遗留
<Route path="/projects" element={<Navigate to="/project-center/project" replace />} />
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

## 4. 合并页面设计

### 4.1 需求方案（RequirementPlanPage）

**复用来源**：`RequirementStudio` 的 `requirement-outline` + `requirement-detailed` 阶段

**布局结构**（三栏 + Tab）：
```
┌──────────────────────────────────────────────────────┐
│ [概要视图] [详细视图] [版本历史]                        │  ← 顶部视图 Tab
├──────────┬──────────────────────────┬────────────────┤
│          │                          │                │
│ 任务树    │     产物渲染区            │  执行面板      │
│ (左)      │     (中)                  │  审查面板      │
│          │                          │  (右)          │
│          │                          │                │
├──────────┴──────────────────────────┴────────────────┤
│ 状态栏: 项目名 | 需求方案 | 当前产物 | v1             │
└──────────────────────────────────────────────────────┘
```

**内部 Tab（概要视图）**：`[用户故事]` `[PRD]` `[草图]` `[验收标准]`

**接口复用**：
- `GET /v1/requirement-studio/{projectId}` → 阶段状态
- `POST /v1/requirement-studio/{projectId}/stages/{stageId}/execute` → 执行阶段
- `GET /v1/requirement-studio/{projectId}/artifacts` → 产物列表
- `POST /v1/requirement-studio/{projectId}/annotations` → 审查批注

### 4.2 设计方案（DesignPlanPage）

**复用来源**：`RequirementStudio` 的 `design-outline` + `design-detailed` 阶段

**布局结构**：同需求方案三栏布局

**顶部 Tab**：`[概要设计]` `[详细设计]` `[DB 设计]` `[接口契约]` `[版本历史]`

**接口复用**：同需求方案，阶段 ID 不同（`design-outline` / `design-detailed`）

### 4.3 设计定稿（DesignFinalizationPage）

**复用来源**：`ArchGovernance` + `GateCenter` 的 Gate 2 审批

**布局结构**（三栏）：
```
┌──────────────────────────────────────────────────────┐
│ 设计定稿                                              │
├────────────────┬────────────────────┬────────────────┤
│  待基线产物清单   │  基线状态与架构分析  │  审批面板        │
│  (左)          │  (中)              │  (右)           │
│  - 复选框锁定   │  - 健康评分         │  - 待审批 Gate   │
│  - 版本标记     │  - 影响范围         │  - 通过/驳回/重试 │
│  - 一键锁定     │  - 架构 issue 筛选  │  - 历史审批      │
└────────────────┴────────────────────┴────────────────┘
```

**接口复用**：
- `GET /v1/c4/analyze?project_id={id}` → 架构分析
- `GET /v1/c4/governance/fix-plan` → 修复计划
- `GET /v1/gates` → Gate 列表
- `POST /v1/gates/{gateId}/approve` → 审批通过
- `POST /v1/gates/{gateId}/reject` → 审批驳回
- `POST /v1/requirement-studio/{projectId}/governance/baseline` → 基线化
- `POST /v1/requirement-studio/{projectId}/governance/change-request` → 变更请求

### 4.4 任务编排（TaskOrchestrationPage）

**复用来源**：`TaskCenter`

**增强点**：
- 右侧可收起"执行面板"（复用 `ExecutionPanel` + 日志流）
- 点击执行后自动展开，展示 PREP/EXEC/POST 状态
- 底部状态栏展示 Token 消耗与耗时

**接口复用**：
- `GET /v1/execution/{projectId}/tasks` → 任务列表
- `POST /v1/execution/{projectId}/tasks` → 创建任务
- `POST /v1/execution/{projectId}/tasks/{taskId}/execute` → 执行
- `POST /v1/execution/{projectId}/tasks/{taskId}/retry` → 重试
- `GET /v1/skill-executions` → 执行监控（SSE）

### 4.5 测试调试（TestingPage）

**复用来源**：`ExecutionIssues`

**增强点**：
- 顶部"运行测试"按钮，生成测试报告摘要
- 问题详情中新增"🔄 反馈回方案设计室"按钮
- 弹窗选择关联设计产物 → 自动创建变更请求

**接口复用**：
- `GET /v1/execution/{projectId}/issues` → 问题列表
- `POST /v1/execution/{projectId}/issues` → 创建问题
- `POST /v1/execution/{projectId}/issues/{issueId}/feedback` → 反馈回架构
- `POST /v1/requirement-studio/{projectId}/governance/change-request` → 变更请求

### 4.6 脑暴室（BrainstormPage）

**复用来源**：`RequirementStudio` 的脑暴阶段（内嵌）

**布局结构**：三栏布局，顶部 Tab `[脑暴纪要]` `[竞品分析]` `[规模初估]`

**接口复用**：`requirement-studio` API（阶段 ID 为 `brainstorm`）

---

## 5. 后端接口兼容性矩阵

| 前端页面 | 复用后端 API 模块 | 端点前缀 | 变更说明 |
|---------|------------------|---------|---------|
| 需求方案 | `requirement_studio` | `/v1/requirement-studio` | 无变化 |
| 设计方案 | `requirement_studio` | `/v1/requirement-studio` | 无变化 |
| 脑暴室 | `requirement_studio` | `/v1/requirement-studio` | 无变化 |
| 系统结构 | `c4` | `/v1/c4` | 无变化 |
| 页面布局 | `wireframe` | `/v1/wireframe` | 无变化 |
| 交互原型 | `open_ui` | `/v1/open-ui` | 无变化 |
| 接口对照 | `binding` | `/v1/binding` | 无变化 |
| 设计定稿 | `c4` + `governance` + `requirement_studio` | `/v1/c4`, `/v1/gates`, `/v1/requirement-studio` | 无变化 |
| 任务编排 | `execution` + `skill_executions` | `/v1/execution`, `/v1/skill-executions` | 无变化 |
| 测试调试 | `execution` + `requirement_studio` | `/v1/execution`, `/v1/requirement-studio` | 无变化 |
| 产物浏览器 | `artifacts` | `/v1/artifacts` | 无变化 |
| 审批中心 | `governance` + `bypass` | `/v1/gates`, `/v1/bypass` | 无变化 |
| 应用管理 | `applications` | `/v1/applications` | 无变化 |
| 项目管理 | `projects` | `/v1/projects` | 无变化 |
| AI CLI | `cli` + `chat` + `config_nodes` | `/v1/cli`, `/v1/chat`, `/v1/config-nodes` | 无变化 |
| 平台管理 | `skills` + `templates` + `llm_*` + `docforge_admin` | `/v1/skills`, `/v1/templates`, `/v1/llm-*`, `/v1/docforge-admin` | 无变化 |

---

## 6. 状态管理设计

### 6.1 复用现有 Store

| Store | 新页面使用 | 说明 |
|-------|----------|------|
| `useRequirementStudioStore` | 脑暴室、需求方案、设计方案 | 阶段状态、任务选择、执行日志、审查批注 |
| `useExecutionStore` | 任务编排、测试调试 | 任务列表、问题列表、执行状态 |
| `useGateCenterStore` | 设计定稿、审批中心 | Gate 列表、审批状态 |

### 6.2 无新增 Store

本次重构不新增任何 Zustand Store，所有状态通过现有 Store 复用。

---

## 7. 实施计划

### 7.1 Phase 1：路由与导航重构（W1）

1. **修改 `App.tsx`**
   - 重定义 `navGroups` 为 5 个一级菜单（4 室 + 平台管理）
   - 新增/调整所有 `<Route>` 映射
   - 添加 30+ 条旧路由 `<Navigate>` 重定向
   - **保留 AI CLI** 在开发执行室

2. **创建新页面目录**
   ```
   src/pages/RequirementStudio/Brainstorm/
   src/pages/RequirementStudio/RequirementPlan/
   src/pages/SolutionStudio/DesignPlan/
   src/pages/SolutionStudio/DesignFinalization/
   src/pages/ExecutionStudio/TaskOrchestration/
   src/pages/ExecutionStudio/Testing/
   ```

3. **创建新页面入口文件**（wrapper + 复用现有组件）
   - `BrainstormPage` → 复用 `RequirementStudio` 脑暴逻辑
   - `RequirementPlanPage` → 复用 `RequirementStudio` 概要+详细阶段
   - `DesignPlanPage` → 复用 `RequirementStudio` 设计阶段
   - `DesignFinalizationPage` → 复用 `ArchGovernance` + `GateCenter`
   - `TaskOrchestrationPage` → 复用 `TaskCenter` + 执行面板
   - `TestingPage` → 复用 `ExecutionIssues` + 反馈弹窗

### 7.2 Phase 2：合并页面增强（W2-W3）

1. `RequirementPlanPage`：实现 Tab 切换（概要/详细/版本历史）
2. `DesignPlanPage`：实现 Tab 切换（概要/详细/DB/接口）
3. `DesignFinalizationPage`：整合基线化 + 审批面板（左侧产物清单、中间架构分析、右侧审批）
4. `TaskOrchestrationPage`：嵌入可折叠执行面板（右侧滑出）
5. `TestingPage`：新增"反馈回方案设计室"弹窗（选择产物 → 创建变更请求）

### 7.3 Phase 3：清理与验证（W4）

1. 移除旧路由的独立页面引用（但保留文件，避免破坏）
2. 验证所有旧路由 `<Navigate>` 重定向正确
3. 验证所有现有后端接口调用正常
4. 类型检查 `tsc --noEmit` 通过
5. ESLint 检查通过

---

## 8. 风险与注意事项

| 风险 ID | 描述 | 等级 | 缓解策略 |
|---------|------|------|----------|
| R-LR-001 | 旧路由重定向遗漏导致用户访问 404 | 中 | 完整重定向清单覆盖所有已知旧路由；W4 全量 URL 回归测试 |
| R-LR-002 | 合并页面 Tab 切换后状态丢失（如执行日志） | 低 | Tab 切换仅切换内容渲染区，不卸载执行面板；Store 状态持久化 |
| R-LR-003 | 旧文件未删除导致 bundle 体积膨胀 | 低 | 后续版本通过 tree-shaking 优化；Vite 生产构建自动剔除未引用代码 |
| R-LR-004 | `DesignFinalizationPage` 同时依赖 `c4` + `gates` 两个 API，加载顺序错误 | 中 | 并行请求（Promise.all）；任一失败显示独立错误提示，不阻塞整体渲染 |
| R-LR-005 | 审批中心合并上线审批后，Gate 类型判断逻辑变更 | 低 | 复用 `GateCenter` 现有 filter 逻辑；新增 Gate 类型按 UI 分组显示 |

---

## 9. Gate 评审签字区

- [ ] 路由映射完整覆盖所有旧 URL（无 404 风险）
- [ ] 后端接口零改动（所有新页面复用现有 API）
- [ ] AI CLI 节点保留于开发执行室
- [ ] 合并页面 Tab 切换不丢失状态
- [ ] 类型检查 `tsc --noEmit` 通过
- [ ] 旧文件保留策略已确认（不删除，仅重定向）

**评审人**：________ **日期**：________

---

## 附录：需求可追溯性

| 需求编号 | 需求描述 | 本文件对应章节 | 验证方式 |
|---------|----------|-------------|---------|
| 菜单设计 v3-§2.1 | 项目工作台 4 个页面 | §3.1 | 路由验证 |
| 菜单设计 v3-§2.2 | 需求设计室 4 个页面 | §3.1 | 路由验证 |
| 菜单设计 v3-§2.3 | 方案设计室 6 个页面 | §3.1 | 路由验证 |
| 菜单设计 v3-§2.4 | 开发执行室 4 个页面 | §3.1 | 路由验证 |
| 菜单设计 v3-§3.1 | 需求方案合并概要+详细 | §4.1 | Tab 切换验证 |
| 菜单设计 v3-§3.2 | 设计方案合并概要+详细 | §4.2 | Tab 切换验证 |
| 菜单设计 v3-§3.3 | 设计定稿合并基线+审批 | §4.3 | 三栏布局验证 |
| 菜单设计 v3-§4.1 | AI CLI 保留 | §3.1 | 导航验证 |
| 菜单设计 v3-§5.1 | 测试调试反馈回设计室 | §4.5 | 弹窗交互验证 |
