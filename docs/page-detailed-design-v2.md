# SDLC Visualizer 页面详细设计文档 v2.0

> **版本**: v2.0
> **日期**: 2026-06-17
> **依据**: `docs/sdlc-visualizer-ui-design-v1.md` + 现有代码现状

---

## 1. 页面架构总览

### 1.1 导航结构（6 个一级菜单）

```
├─ 项目中心
│   ├─ 项目工作台 (ProjectWorkbench)       ← 复用 ProjectDashboard，纯管理化
│   └─ 应用管理 (AppManager)               ← 复用 AppDashboard
│
├─ 需求设计室                              ← 核心新增：沉浸式工作空间
│   ├─ 概要需求 (RequirementOutline)         ← 新增：用户故事、草图、规模初估
│   ├─ 详细需求 (RequirementDetailed)        ← 新增：详细PRD、接口契约初稿
│   ├─ 概要设计 (DesignOutline)            ← 复用 C4Navigator + WireframeCanvas
│   ├─ 详细设计 (DesignDetailed)           ← 复用 OpenUIPreview + BindingPanel
│   ├─ 设计产物 (StudioArtifacts)           ← 复用 ArtifactViewer，按阶段分组
│   └─ 架构治理 (StudioGovernance)          ← 复用 ArchGovernance，移入需求设计室
│
├─ 开发执行
│   ├─ 项目画布 (ExecCanvas)               ← 复用 Canvas，聚焦 Build/Verify
│   ├─ 任务中心 (TaskCenter)               ← 新增：核心页面，任务拆解/执行/Bug修复
│   ├─ 执行问题 (ExecIssues)               ← 新增：异常记录、反馈回架构
│   ├─ 执行监控 (ExecMonitor)              ← 复用 ExecutionMonitor
│   ├─ AI CLI (ExecCli)                    ← 复用 AiCliPage
│   └─ 监控看板 (ExecDashboard)            ← 复用 MonitoringDashboard
│
├─ 产物验证
│   ├─ 产物浏览器 (ArtifactBrowser)         ← 复用 ArtifactViewer
│   ├─ 架构验证 (ArchValidation)           ← 复用 ArchValidation
│   └─ 历史回溯 (HistoryViewer)            ← 复用 HistoryViewer
│
├─ 治理审批
│   ├─ 审批中心 (ApprovalCenter)           ← 复用 GateCenter
│   └─ 旁路审批 (BypassApproval)           ← 复用 BypassManager
│
└─ 平台管理
    ├─ Skill 治理 (SkillMgmt)              ← 复用 SkillRegistry
    ├─ LLM 配置 (LlmConfig)               ← 复用 LlmConfig
    ├─ 模板配置 (TemplateConfig)           ← 复用 TemplateStageConfig
    └─ 文档标准化 (DocStandard)             ← 复用 DocForgeAdmin
```

### 1.2 页面布局体系

| 页面类型 | 布局模式 | 说明 |
|----------|----------|------|
| 管理型（项目中心、平台管理） | 列表+卡片+抽屉 | 常规管理界面 |
| 沉浸式（需求设计室） | 顶部阶段导航 + 三栏 | 左任务树 / 中产物 / 右执行面板 |
| 执行型（开发执行） | 阶段切换 + 三栏 | 左任务树 / 中任务详情 / 右执行面板 |
| 验证型（产物验证） | 树+预览+抽屉 | 全局产物查看 |
| 审批型（治理审批） | 列表+卡片+详情 | Gate 流程审批 |

---

## 2. 需求设计室 — 页面详细设计

### 2.1 总体布局框架

所有需求设计室页面共享同一布局外壳：

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 面包屑：项目中心 > 需求设计室 > 概要需求                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 顶部阶段导航条：[概要需求] [详细需求] [概要设计] [详细设计] [设计产物] [架构治理]   │
│                 ↑ 当前高亮    ↑ 已解锁   ─ 未解锁(置灰)                         │
├──────────┬──────────────────────────────────────────┬──────────────────────────┤
│          │                                          │                          │
│ 左侧面板  │              中间面板                     │         右侧面板          │
│ 阶段任务树│          产物工作区                       │      审查与执行控制台      │
│          │                                          │                          │
│  ▼ 用户故事│  ┌──────────────────────────────────┐  │  ┌────────────────────┐  │
│    ├ US-001│  │ Tab 切换：PRD | 用户故事 | 草图    │  │  审查批注面板        │  │
│    ├ US-002│  └──────────────────────────────────┘  │  │  • 行内批注列表      │  │
│    └ US-003│  ┌──────────────────────────────────┐  │  │  • 全局修改建议      │  │
│            │  │      产物渲染区 (Markdown/图表)   │  │  │  • 参考资料区        │  │
│ [执行Skill] │  │                                  │  │  │  [携带批注重生成]   │  │
│ [重新生成] │  └──────────────────────────────────┘  │  └────────────────────┘  │
│            │  ┌──────────────────────────────────┐  │  ┌────────────────────┐  │
│            │  │ 底部：版本时间线 [v1]—[v2]—[v3] │  │  执行状态面板        │  │
│            │  └──────────────────────────────────┘  │  PREP→EXEC→POST      │  │
│            │                                          │  [实时日志 ▼]       │  │
│            │                                          │  [提交审查] [Gate]   │  │
├──────────┴──────────────────────────────────────────┴──────────────────────────┤
│ 状态栏：项目: 订单系统 | 阶段: 概要需求 | 产物: PRD.md | 版本: v3              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 共享状态管理（RequirementStudioStore）

```typescript
interface RequirementStudioState {
  // 当前上下文
  projectId: string
  currentStage: 'requirement-outline' | 'requirement-detailed' | 'design-outline' | 'design-detailed' | 'artifacts' | 'governance'
  
  // 阶段状态（从后端获取）
  stageStatus: Record<string, {
    status: 'locked' | 'not_started' | 'in_progress' | 'review_pending' | 'passed'
    progress: number
    tasks: StageTask[]
  }>
  
  // 当前选中的任务/产物
  selectedTaskId: string | null
  selectedArtifactId: string | null
  
  // 产物编辑
  artifactContent: string
  artifactVersions: ArtifactVersion[]
  isEditing: boolean
  hasConflict: boolean
  
  // 审查批注
  annotations: Annotation[]
  newAnnotation: string
  
  // 执行状态
  executionStatus: 'idle' | 'prep' | 'exec' | 'post' | 'success' | 'failed'
  executionLogs: string[]
  executionProgress: number
  
  // 加载状态
  loading: boolean
  error: string | null
}
```

### 2.3 概要需求页面 (RequirementOutline)

**页面定位**：需求对齐（Align）阶段，产出用户故事、PRD（概要）、草图（PageSpec）、验收标准初稿。

**左侧任务树**：

```
▼ 概要需求阶段
  ├─ 脑暴纪要      [继承] [查看]     ← 来自 Draft 阶段，只读
  ├─ 用户故事      [NOT_STARTED] [执行 Skill]
  ├─ PRD（概要）   [NOT_STARTED] [执行 Skill]
  ├─ 草图         [NOT_STARTED] [执行 Skill]
  └─ 验收标准      [NOT_STARTED] [执行 Skill]
```

**中间产物区 Tab 内容**：

| Tab | 内容 | 渲染方式 | 操作 |
|-----|------|----------|------|
| 用户故事 | 用户故事列表（US-001 ~ US-xxx） | 表格/卡片 | 查看、编辑、删除 |
| PRD | PRD Markdown 文档 | Markdown 渲染 | 编辑、保存、版本对比 |
| 草图 | 低保真页面逻辑图（文本框+箭头） | SVG/Canvas | 查看、重新生成 |
| 验收标准 | 验收标准列表 | 表格 | 查看、编辑 |

**底部规模初估卡片**：

```
┌─────────────────────────────────┐
│ 规模初估参考（基于脑暴结果）      │
│ 模块数: 3 | 接口数: 8 | 页面数: 5 │
│ 技术复杂度: 中 | 风险等级: 低      │
│ 推荐路径: Standard（参考）        │
└─────────────────────────────────┘
```

**右侧执行面板**：
- 当点击左侧任务节点时，显示对应 Skill 指令快照
- [执行] / [重新生成] 按钮
- PocketFlow 三阶段状态显示（PREP → EXEC → POST）
- 实时日志折叠面板
- 审查提交区（批注输入 + [提交审查]）

### 2.4 详细需求页面 (RequirementDetailed)

**左侧任务树**：

```
▼ 详细需求阶段
  ├─ 详细 PRD      [NOT_STARTED] [执行 Skill]
  ├─ 验收标准      [NOT_STARTED] [执行 Skill]
  └─ 接口契约初稿  [NOT_STARTED] [执行 Skill]
```

**中间产物区 Tab 内容**：

| Tab | 内容 | 渲染方式 | 操作 |
|-----|------|----------|------|
| 详细 PRD | 详细 PRD Markdown | Markdown 渲染 | 编辑、保存 |
| 验收标准 | 详细验收标准 | 表格 | 编辑 |
| 接口契约 | OpenAPI 3.0 YAML | Swagger UI 嵌入 | YAML 编辑、Schema 校验 |

**接口契约初稿特殊交互**：
- YAML 文本编辑器（保存时触发 schema 校验）
- 校验通过 → 右侧显示 Swagger UI 嵌入式预览
- 校验失败 → 错误提示 + 行号标红

### 2.5 概要设计页面 (DesignOutline)

**左侧任务树**：

```
▼ 概要设计阶段
  ├─ HLD 文档     [NOT_STARTED] [执行 Skill]
  ├─ C4 L1/L2    [NOT_STARTED] [执行 Skill]
  └─ 线框图       [NOT_STARTED] [执行 Skill]
```

**中间产物区**：

| Tab | 内容 | 渲染方式 | 操作 |
|-----|------|----------|------|
| HLD | HLD Markdown | Markdown | 编辑、保存 |
| C4 L1 | 系统上下文图 | Mermaid.js 渲染 | 编辑 DSL、层级穿透 |
| C4 L2 | 容器图 | Mermaid.js 渲染 | 编辑 DSL、层级穿透 |
| 线框图 | 页面结构草图 | SVG | 查看 |

**C4 层级穿透交互**：
- 点击 Context 边界 → 下钻至 Container 图
- 面包屑同步更新：L1 > L2
- 手动覆盖：保存后标记 `manual_override=true`，后续不再自动覆盖

### 2.6 详细设计页面 (DesignDetailed)

**左侧任务树**：

```
▼ 详细设计阶段
  ├─ DD 文档       [NOT_STARTED] [执行 Skill]
  ├─ C4 L3/L4     [NOT_STARTED] [执行 Skill]
  ├─ OpenUI 原型   [NOT_STARTED] [执行 Skill]
  ├─ 数据绑定      [NOT_STARTED] [检查覆盖度]
  └─ DB 设计      [NOT_STARTED] [执行 Skill]
```

**中间产物区**：

| Tab | 内容 | 渲染方式 | 操作 |
|-----|------|----------|------|
| DD | DD Markdown | Markdown | 编辑、保存 |
| C4 L3 | 组件图 | Mermaid.js | 编辑 DSL、反向代码定位 |
| C4 L4 | 代码图 | Mermaid.js | 编辑 DSL |
| OpenUI | 可交互原型 | iframe 嵌入 | 刷新、降级预览 |
| 数据绑定 | 覆盖度检测报告 | 表格 + 标红 | 检查覆盖度、一键回写 |
| DB 设计 | ER 图 + 表结构 | Mermaid.js + Markdown | 编辑 |

**OpenUI 降级逻辑**：
- 服务可用 → iframe 展示可交互 HTML
- 服务不可用 → 自动降级为 Wireframe 静态预览

**数据绑定特殊交互**：
- 点击"检查覆盖度" → 系统对比页面元素与接口契约
- 缺失接口标红
- 点击"一键回写 C4 DSL" → 自动更新 `arsitect.aac.yml` 并标记变更待评审

**反向代码定位**：
- Component 节点绑定 `arsitect.codegen_target` 字段
- 点击节点 → 打开本地 IDE 对应文件（通过 VS Code URL scheme: `vscode://file/...`）

### 2.7 设计产物页面 (StudioArtifacts)

**功能定位**：需求设计室内部的产物总览与版本管理，不触发新 Skill。

**中间产物区**：

```
┌────────────────────────────────────────────────────────────┐
│ 按阶段分组产物列表                                           │
├────────────┬───────────────┬───────────┬───────────────────┤
│ 阶段       │ 产物文件       │ 当前版本   │ 状态              │
├────────────┼───────────────┼───────────┼───────────────────┤
│ 概要需求    │ prd-outline.md│ v3        │ CURRENT           │
│ 概要需求    │ user-stories.md│ v2       │ CURRENT           │
│ 详细需求    │ api-contract-v1.yaml│ v1  │ CURRENT           │
│ 概要设计    │ c4-l1.dsl.yml │ v2        │ MANUAL_OVERRIDE   │
│ 详细设计    │ openui-prototype.html│ v1 │ CURRENT           │
└────────────┴───────────────┴───────────┴───────────────────┘
```

**操作**：
- 查看：点击产物 → 按格式渲染（Markdown/Mermaid/YAML/SVG/HTML）
- 编辑：进入文本编辑器，保存时检测外部变更（BR-006），无冲突则 Git 快照
- 版本对比：选中两个版本 → 底部 diff 栏高亮增删改
- 回滚：右键版本 → "回滚到此版本" → 创建 rollback 提交

### 2.8 架构治理页面 (StudioGovernance)

**功能定位**：设计产物基线化与变更控制，从产物验证移入需求设计室。

**三栏布局**：

```
┌──────────────────────────────────────────────────────────────────────┐
│ 基线状态栏：当前基线: v3 (2026-06-15) | 基线产物: 5 | Stale: 2        │
├────────────┬────────────────────────────┬────────────────────────────┤
│ 左侧：基线产物清单 │ 中间：影响分析图             │ 右侧：操作面板             │
│            │                            │                            │
│ ├─ HLD.md  [基线]│  dd.md 变更                │ [创建基线] [解除基线]      │
│ ├─ c4-l2.dsl.yml │    ├──> 影响: OpenUI 原型   │ [提交变更请求] [回退]      │
│ ├─ api-contract  │    ├──> 影响: 任务 #12      │ 变更请求列表：             │
│ ├─ dd.md [Stale] │    └──> 影响: 接口契约      │ CR-001: 待审批 | 影响: 2  │
│ └─ db-schema [Stale]                        │                            │
└────────────┴────────────────────────────┴────────────────────────────┘
```

**功能清单**：
- 基线化：选择核心设计产物 → 标记为基线版本 → 锁定编辑
- 变更影响分析：自动计算受影响下游范围（Stale 传播）
- Stale 标记管理：查看 Stale 产物列表、影响链路、建议重跑范围
- 变更审批：基线后修改需提交变更请求（CR）
- 基线对比：基线版本 vs 当前版本 diff
- 回退控制：一键回退到基线版本，废弃后续修改

---

## 3. 开发执行 — 页面详细设计

### 3.1 总体布局框架

所有开发执行页面共享状态上下文（ExecutionContext）：

```typescript
interface ExecutionContextState {
  projectId: string
  currentView: 'canvas' | 'task-center' | 'issues' | 'monitor' | 'cli' | 'dashboard'
  
  // 任务中心数据
  tasks: ExecutionTask[]
  selectedTaskId: string | null
  taskGroups: Record<string, ExecutionTask[]>  // 按模块分组
  
  // 执行问题数据
  issues: ExecutionIssue[]
  selectedIssueId: string | null
  
  // 执行监控数据
  activeExecutions: SkillExecution[]
  executionLogs: Record<string, string[]>
  
  // 全局状态
  loading: boolean
  error: string | null
}
```

### 3.2 项目画布页面 (ExecCanvas)

**功能定位**：Build/Verify 阶段的拓扑可视化，仅展示编码、测试、Bug 修复相关节点。

**与现有 Canvas 的区别**：
- 仅展示 Build/Verify 阶段节点（移除需求分析阶段节点）
- 不直接触发 Skill，仅作为导航与状态总览
- 点击节点 → 跳转任务中心对应任务

**节点类型**：

| 节点 | 图标 | 状态 | 点击操作 |
|------|------|------|----------|
| 编码任务 | 📝 | NOT_STARTED / IN_PROGRESS / PASSED / BLOCKED | 跳转任务中心 |
| 单元测试 | 🧪 | NOT_STARTED / IN_PROGRESS / PASSED / FAILED | 跳转任务中心 |
| 集成测试 | 🔗 | NOT_STARTED / IN_PROGRESS / PASSED / FAILED | 跳转任务中心 |
| Bug 修复 | 🐛 | NOT_STARTED / IN_PROGRESS / CLOSED | 跳转任务中心 |

### 3.3 任务中心页面 (TaskCenter) — 核心页面

**页面布局**：三栏模式（开发执行的核心页面）

```
┌────────────────────────────────────────────────────────────────────────────┐
│ 顶部：开发执行 / 任务中心                                                    │
│ 阶段切换：[任务拆解] [任务执行] [Bug 修复]                                  │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ 左侧：任务/需求树            │ 中间：任务详情与产物      │ 右侧：执行面板   │
│                              │                           │                 │
│ 订单模块                     │ 任务: 订单创建接口编码      │ 触发 Skill:     │
│  ├─ 用户管理接口 [编码][待执行]│ 输入产物: HLD.md, api-   │ skill-code-gen  │
│  ├─ 订单创建接口 [编码][执行中]│   contract.yaml          │ 上下文注入:     │
│  │  ← 当前选中                │ 状态: IN_PROGRESS        │ 接口契约 + C4   │
│  └─ 订单查询接口 [测试][待执行]│ 产物: src/order/create.py │ [执行编码]     │
│ 支付模块                     │  [查看产物] [查看日志]     │ [重新生成]      │
│  ├─ 支付接口 [编码][已完成]  │  [标记完成] [标记失败]    │ [中断执行]      │
│  └─ 支付回调 [测试][失败]    │                           │ 执行日志:       │
│    ← 标红                    │                           │ > prep: ...     │
│                              │                           │ > exec: ...     │
│                              │                           │ > post: ...     │
├────────────────────────────────────────────────────────────────────────────┤
│ 快捷操作：[+ 新建任务] [批量执行] [导入任务]                                  │
└────────────────────────────────────────────────────────────────────────────┘
```

**Tab 切换**：

| Tab | 内容 |
|-----|------|
| 任务拆解 | 任务列表树 + 新建任务表单 + 自动生成任务按钮 |
| 任务执行 | 任务详情 + 执行面板 + 日志 |
| Bug 修复 | Bug 列表 + 修复表单 + 重新执行按钮 |

**任务数据结构**：

```typescript
interface ExecutionTask {
  taskId: string
  name: string
  type: 'coding' | 'test' | 'bugfix'
  inputArtifacts: string[]
  status: 'not_started' | 'in_progress' | 'passed' | 'failed' | 'blocked'
  assignedSkill: string
  parentModule: string
  outputArtifactPath: string | null
  retryCount: number
  errorLog: string | null
  createdAt: string
  updatedAt: string
}
```

**任务状态流转**：

```
NOT_STARTED → IN_PROGRESS (用户点击执行)
IN_PROGRESS → PASSED (Skill 成功 + 产物校验通过)
IN_PROGRESS → FAILED (Skill 失败 / 测试未通过)
FAILED → IN_PROGRESS (用户重试，≤3次)
FAILED → BLOCKED (用户标记为 Bug)
BLOCKED → IN_PROGRESS (Bug 修复后重新执行)
```

**新建任务表单**：
- 任务名称（输入框）
- 任务类型（单选：coding / test / bugfix）
- 所属模块（下拉选择）
- 输入产物（多选：设计产物列表）
- 分配 Skill（下拉选择）
- 描述（文本域）

### 3.4 执行问题页面 (ExecIssues)

**功能定位**：记录开发执行中的异常，并支持反馈回架构。

**页面布局**：

```
┌────────────────────────────────────────────────────────────────────────────┐
│ 顶部：开发执行 / 执行问题                                                    │
├────────────────────────────────────────────────────────────────────────────┤
│ 筛选：[全部] [编译错误] [测试失败] [架构偏差] [接口不匹配] [其他]             │
│ 搜索：[________] [状态筛选] [时间筛选]                                       │
├────────────────────────────────────────────────────────────────────────────┤
│ 左侧：问题列表                │ 右侧：问题详情与操作                          │
│                              │                                             │
│ #001 编译错误                  │ 问题类型: 编译错误                           │
│ 关联任务: 订单创建接口编码      │ 关联任务: T-001                              │
│ 状态: 已解决                    │ 错误日志:                                    │
│ 2026-06-15                      │ ```                                        │
│ #002 测试失败                  │ SyntaxError: invalid syntax...              │
│ 关联任务: 支付回调              │ ```                                        │
│ 状态: 待处理                    │ 关联产物: api-contract.yaml                 │
│ 2026-06-15                      │ 建议操作: [重试] [反馈回架构] [跳过]          │
│                                │                                             │
│                                │ [反馈回架构] → 弹窗选择关联产物               │
│                                │ → 系统标记 Stale + 创建 CR + 通知需求设计室   │
└────────────────────────────────────────────────────────────────────────────┘
```

**问题数据结构**：

```typescript
interface ExecutionIssue {
  issueId: string
  projectId: string
  taskId: string
  issueType: 'compile_error' | 'test_failure' | 'arch_mismatch' | 'interface_mismatch' | 'other'
  errorLog: string
  relatedArtifacts: string[]
  suggestedAction: 'retry' | 'feedback' | 'skip'
  feedbackToArchitecture: boolean
  targetArtifactId: string | null
  changeRequestId: string | null
  status: 'open' | 'resolved' | 'closed'
  createdAt: string
  updatedAt: string
}
```

**反馈回架构流程**：
1. 用户点击"反馈回架构" → 弹窗选择关联设计产物（如 `api-contract.yaml`）
2. 系统：
   - 在需求设计室-架构治理中标记该产物为 Stale
   - 创建变更请求（CR），描述为"接口契约与实际实现偏差"
   - 推送通知到开发执行-执行问题
3. 用户进入需求设计室修改设计 → 重新基线化 → 回到开发执行重新执行任务

### 3.5 执行监控页面 (ExecMonitor)

**复用现有 ExecutionMonitor**，路径调整为 `/execution/monitor`。

**新增功能**：
- 多任务并行监控（现有 SSE 已支持）
- 与任务中心联动：点击监控中的任务 → 跳转任务中心详情
- 实时状态面板显示 PocketFlow 三阶段进度

### 3.6 监控看板页面 (ExecDashboard)

**复用现有 MonitoringDashboard**，路径调整为 `/execution/dashboard`。

**新增功能**：
- Token 消耗统计（按项目/阶段/任务）
- 阶段耗时统计（编码阶段平均耗时、测试阶段平均耗时）
- 瓶颈识别：哪个任务类型失败率最高、哪个模块耗时最长

---

## 4. 产物验证 — 页面详细设计

### 4.1 产物浏览器 (ArtifactBrowser)

**复用现有 ArtifactViewer**，路径调整为 `/artifact-verification/browser`。

**新增功能**：
- 跨阶段查看所有产物（现有已支持）
- 按项目/阶段/任务组织目录树（现有已支持）
- 与需求设计室-设计产物的区别：产物浏览器是全局统一入口，设计产物是需求设计室内部的产物管理

### 4.2 架构验证 (ArchValidation)

**复用现有 ArchValidation**，路径调整为 `/artifact-verification/validation`。

### 4.3 历史回溯 (HistoryViewer)

**复用现有 HistoryViewer**，路径调整为 `/artifact-verification/history`。

---

## 5. 项目中心 — 页面调整

### 5.1 项目工作台 (ProjectWorkbench)

**复用现有 ProjectDashboard**，路径调整为 `/project-center/workbench`。

**调整点**：
- 移除项目画布入口（项目画布已移入开发执行）
- 移除复杂度评估入口（已下沉为概要需求阶段卡片）
- 项目卡片上新增"进入需求设计室"按钮（Draft 项目）
- 项目卡片上新增"进入开发执行"按钮（Active 项目）
- 确保项目中心不直接触发任何 Skill 执行

### 5.2 应用管理 (AppManager)

**复用现有 AppDashboard**，路径调整为 `/project-center/application`。

---

## 6. 治理审批 — 页面调整

### 6.1 审批中心 (ApprovalCenter)

**复用现有 GateCenter**，路径调整为 `/governance/approval-center`。

### 6.2 旁路审批 (BypassApproval)

**复用现有 BypassManager**，路径调整为 `/governance/bypass`。

---

## 7. 平台管理 — 页面调整

### 7.1 各页面

| 页面 | 原路径 | 新路径 | 组件 |
|------|--------|--------|------|
| Skill 治理 | `/skills` | `/platform/skill-management` | SkillRegistry |
| LLM 配置 | `/settings/llm` | `/platform/llm-config` | LlmConfig |
| 模板配置 | `/template-config` | `/platform/template-config` | TemplateStageConfig |
| 文档标准化 | `/docforge` | `/platform/doc-standard` | DocForgeAdmin |

---

## 8. 后端 API 详细设计

### 8.1 需求设计室 API

```
GET  /api/v1/requirement-studio/{projectId}/status
Response: {
  projectId: string
  currentStage: string
  stages: {
    stageId: string
    stageName: string
    status: 'locked' | 'not_started' | 'in_progress' | 'review_pending' | 'passed'
    progress: number
    canEnter: boolean
  }[]
}

GET  /api/v1/requirement-studio/{projectId}/stage/{stageId}/tasks
Response: {
  stageId: string
  tasks: {
    taskId: string
    taskName: string
    taskType: string
    status: string
    skillId: string
    outputArtifact: string
  }[]
}

POST /api/v1/requirement-studio/{projectId}/stage/{stageId}/execute
Body: { skillId: string, context: any, referenceMaterials: string[] }
Response: { executionId: string, status: string }

POST /api/v1/requirement-studio/{projectId}/stage/{stageId}/review
Body: { comments: string[], suggestions: string[], action: 'pass' | 'regenerate' }
Response: { stageId: string, status: string, nextStageId: string }

GET  /api/v1/requirement-studio/{projectId}/artifacts
Response: {
  artifacts: {
    stageId: string
    stageName: string
    files: { artifactId: string, fileName: string, version: string, status: string }[]
  }[]
}

GET  /api/v1/requirement-studio/{projectId}/artifacts/{artifactId}
Response: { content: string, versions: { version: string, createdAt: string }[] }

POST /api/v1/requirement-studio/{projectId}/artifacts/{artifactId}/edit
Body: { content: string, version: string }
Response: { artifactId: string, version: string, hasConflict: boolean }

POST /api/v1/requirement-studio/{projectId}/governance/baseline
Body: { artifactIds: string[], description: string }
Response: { baselineId: string, version: string, createdAt: string }

GET  /api/v1/requirement-studio/{projectId}/governance/stale-analysis
Response: {
  staleArtifacts: {
    artifactId: string
    artifactName: string
    version: string
    impact: { type: string, target: string, suggestion: string }[]
  }[]
}

POST /api/v1/requirement-studio/{projectId}/governance/change-request
Body: { targetArtifactId: string, changeType: string, reason: string }
Response: { changeRequestId: string, status: string }
```

### 8.2 开发执行 API

```
GET  /api/v1/execution/{projectId}/tasks
Query: { module?: string, status?: string, type?: string }
Response: {
  tasks: ExecutionTask[]
  groups: { module: string, tasks: ExecutionTask[] }[]
}

POST /api/v1/execution/{projectId}/tasks
Body: { name: string, type: string, inputArtifacts: string[], assignedSkill: string, parentModule: string }
Response: ExecutionTask

POST /api/v1/execution/{projectId}/tasks/auto-generate
Body: { designArtifactIds: string[] }
Response: { tasks: ExecutionTask[] }

GET  /api/v1/execution/{projectId}/tasks/{taskId}
Response: ExecutionTask

PATCH /api/v1/execution/{projectId}/tasks/{taskId}
Body: { status?: string, outputArtifactPath?: string, retryCount?: number }
Response: ExecutionTask

POST /api/v1/execution/{projectId}/tasks/{taskId}/execute
Response: { executionId: string, status: string }

POST /api/v1/execution/{projectId}/tasks/{taskId}/retry
Response: ExecutionTask

POST /api/v1/execution/{projectId}/tasks/{taskId}/mark-bug
Body: { errorLog: string, issueType: string }
Response: { taskId: string, issueId: string }

GET  /api/v1/execution/{projectId}/issues
Query: { issueType?: string, status?: string }
Response: { issues: ExecutionIssue[] }

POST /api/v1/execution/{projectId}/issues
Body: { taskId: string, issueType: string, errorLog: string, relatedArtifacts: string[], suggestedAction: string }
Response: ExecutionIssue

POST /api/v1/execution/{projectId}/issues/{issueId}/feedback-to-architecture
Body: { targetArtifactId: string, changeDescription: string }
Response: { issueId: string, changeRequestId: string, status: string }
```

---

## 9. 前端组件设计

### 9.1 共享组件清单

| 组件 | 位置 | 说明 |
|------|------|------|
| `StageNavBar` | `components/StageNavBar.tsx` | 顶部阶段导航条，支持锁定/解锁/高亮 |
| `TaskTree` | `components/TaskTree.tsx` | 左侧任务树，支持展开/折叠/状态图标 |
| `ArtifactRenderer` | `components/ArtifactRenderer.tsx` | 产物渲染器（Markdown/Swagger/SVG/iframe） |
| `VersionTimeline` | `components/VersionTimeline.tsx` | 底部版本时间线 + Diff |
| `ReviewPanel` | `components/ReviewPanel.tsx` | 右侧审查批注面板 |
| `ExecutionPanel` | `components/ExecutionPanel.tsx` | 右侧执行面板（PocketFlow 状态 + 日志） |
| `SizeEstimateCard` | `components/SizeEstimateCard.tsx` | 规模初估参考卡片 |
| `StatusBar` | `components/StatusBar.tsx` | 底部状态栏（项目/阶段/产物/版本） |

### 9.2 页面组件清单

| 页面 | 组件 | 说明 |
|------|------|------|
| RequirementOutline | `RequirementOutlinePage` | 概要需求，含用户故事/PRD/草图/验收标准/规模初估 |
| RequirementDetailed | `RequirementDetailedPage` | 详细需求，含详细PRD/验收标准/接口契约 |
| DesignOutline | `DesignOutlinePage` | 概要设计，含HLD/C4 L1-L2/线框图 |
| DesignDetailed | `DesignDetailedPage` | 详细设计，含DD/C4 L3-L4/OpenUI/数据绑定/DB设计 |
| StudioArtifacts | `StudioArtifactsPage` | 设计产物总览，按阶段分组 |
| StudioGovernance | `StudioGovernancePage` | 架构治理，基线化/Stale/变更请求 |
| TaskCenter | `TaskCenterPage` | 任务中心，三栏布局，含任务拆解/执行/Bug修复 |
| ExecIssues | `ExecIssuesPage` | 执行问题，列表+详情 |
| ExecCanvas | `ExecCanvasPage` | 项目画布，Build/Verify 专用 |

### 9.3 状态管理（Zustand Stores）

```typescript
// stores/requirementStudioStore.ts
interface RequirementStudioStore {
  // ... 见上文
}

// stores/executionStore.ts
interface ExecutionStore {
  // ... 见上文
}
```

---

## 10. 数据流设计

### 10.1 需求设计室数据流

```
用户进入需求设计室
  → GET /api/v1/requirement-studio/{projectId}/status
  → 渲染顶部阶段导航条（高亮当前，置灰未解锁）

用户点击阶段 Tab
  → GET /api/v1/requirement-studio/{projectId}/stage/{stageId}/tasks
  → 左侧渲染任务树
  → 右侧显示执行面板（加载 Skill 快照）

用户点击任务节点
  → GET /api/v1/requirement-studio/{projectId}/artifacts/{artifactId}
  → 中间渲染产物内容
  → 底部加载版本时间线

用户点击"执行 Skill"
  → POST /api/v1/requirement-studio/{projectId}/stage/{stageId}/execute
  → SSE 推送实时状态
  → 产物生成后自动刷新中间区

用户提交审查
  → POST /api/v1/requirement-studio/{projectId}/stage/{stageId}/review
  → 更新阶段状态，解锁下一阶段
  → 顶部导航条更新状态
```

### 10.2 开发执行数据流

```
用户进入任务中心
  → GET /api/v1/execution/{projectId}/tasks
  → 按模块分组渲染任务树

用户选择任务
  → 中间渲染任务详情（输入产物、状态、输出产物）
  → 右侧加载对应 Skill 快照

用户点击"执行编码"
  → POST /api/v1/execution/{projectId}/tasks/{taskId}/execute
  → 触发 PocketFlow
  → SSE 推送日志
  → 状态自动更新

测试失败
  → 任务状态 = FAILED
  → 用户点击"标记为 Bug"
  → POST /api/v1/execution/{projectId}/tasks/{taskId}/mark-bug
  → 创建执行问题
  → 可选：POST /api/v1/execution/{projectId}/issues/{issueId}/feedback-to-architecture
  → 标记产物 Stale，创建变更请求
```

---

## 11. 实施优先级（重新排序）

### 批次 1：共享基础组件
- `StageNavBar`（顶部阶段导航条）
- `TaskTree`（左侧任务树）
- `ArtifactRenderer`（产物渲染器）
- `ExecutionPanel`（右侧执行面板）
- `StatusBar`（底部状态栏）
- Zustand Stores（requirementStudioStore + executionStore）

### 批次 2：需求设计室（核心）
- 需求设计室外壳（布局框架）
- RequirementOutline（概要需求）
- RequirementDetailed（详细需求）
- DesignOutline（概要设计）
- DesignDetailed（详细设计）
- StudioArtifacts（设计产物）
- StudioGovernance（架构治理）

### 批次 3：开发执行（核心）
- TaskCenter（任务中心）
- ExecIssues（执行问题）
- ExecCanvas（项目画布）
- ExecMonitor（执行监控，复用）
- ExecDashboard（监控看板，复用）

### 批次 4：迁移与兼容
- 项目中心迁移（ProjectWorkbench + AppManager）
- 产物验证迁移（ArtifactBrowser + ArchValidation + HistoryViewer）
- 治理审批迁移（ApprovalCenter + BypassApproval）
- 平台管理迁移（各页面）
- 旧路由重定向

### 批次 5：测试
- 单元测试（新组件）
- 集成测试（前后端联调）
- E2E 测试（完整流程）
