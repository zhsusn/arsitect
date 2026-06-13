---
doc_type: "PRD"
fragment_id: "prd-ai-cli-terminal-001"
title: "AI CLI 终端 - 需求清单"
version: "1.0.0"
version_type: "BASELINE"
base_version: ""
change_type: ""
change_summary: ""
author: "agent-product"
tags: ["prd", "ai-cli", "p0"]
status: "DRAFT"
iteration: "ai-cli-terminal"
dependencies:
  - fragment_id: "prd-ai-cli-terminal-000"
    version: "1.0.0"
c4_binding:
  level: "L1"
  actors: ["developer", "tech-lead"]
  external_systems: ["kimi-api", "git-provider"]
---

# AI CLI 终端 - 需求清单

## 1. 范围与边界 {#sec-scope}

### 1.1 In-Scope

- AI CLI 终端页面与类终端交互体验。
- Bug 修复模式：异常解析、AI 分析、修复方案、用户确认、执行修复、记录保存。
- 架构治理模式：项目扫描、治理项列表、治理方案、用户确认、执行重构、ADR 记录。
- WebSocket 会话管理与消息持久化。
- Bug 记录、架构问题记录、会话记录数据模型。

### 1.2 Out-of-Scope

- OCR 截图识别。
- Docker 沙箱执行。
- 自动 PR 创建与合并。
- 多 AI Provider 适配。
- 复杂分布式架构治理。

### 1.3 Non-goals

- 本期不替代 IDE 终端。
- 本期不实现零确认全自动修复。
- 本期不解决复杂分布式架构治理。

## 2. 业务术语表 {#sec-terminology}

| 术语 | 定义 |
|------|------|
| AI CLI 终端 | 平台内嵌的类终端交互界面，用于与 AI Agent 交互 |
| Bug 模式 | 针对代码异常修复的 CLI 工作模式 |
| Arch 模式 | 针对架构治理的 CLI 工作模式 |
| 修复方案卡片 | 在终端流中嵌入的可交互 HTML 组件，展示 Diff 与操作按钮 |
| 治理项卡片 | 在终端流中嵌入的可交互 HTML 组件，展示架构问题与治理方案 |
| Exec Service | 执行引擎，负责在临时工作区执行代码变更与验证 |
| AI Gateway | 统一封装 Kimi API 调用的服务层 |

## 3. 用户故事与验收标准 {#sec-user-stories}

### US-001：创建 AI CLI 会话

**作为** 开发者，**我想** 在平台内打开一个 AI CLI 终端会话，**以便** 与 AI Agent 交互。

- AC1 (Happy): Given 用户已登录，When 点击"打开 AI CLI"，Then 系统创建新会话并显示终端界面。
- AC2 (Negative): Given 用户未登录，When 访问 AI CLI 页面，Then 系统跳转登录页。
- AC3 (Edge): Given 网络异常，When 创建会话，Then 系统提示"连接失败，请重试"。

### US-002：在 Bug 模式下粘贴异常并获取分析

**作为** 开发者，**我想** 粘贴异常堆栈到终端，**以便** AI 分析根因。

- AC1 (Happy): Given 会话处于 Bug 模式，When 粘贴异常堆栈，Then 终端显示 AI 流式分析结论。
- AC2 (Negative): Given 粘贴内容为空，When 提交，Then 系统提示"请输入异常信息"。
- AC3 (Edge): Given 异常签名与历史 Bug 匹配，When 提交，Then 系统提示"发现历史同类问题"并可查看。

### US-003：查看并确认修复方案

**作为** 开发者，**我想** 查看 AI 生成的修复方案 Diff，**以便** 决定是否执行。

- AC1 (Happy): Given AI 已生成修复方案，When 终端渲染修复卡片，Then 用户可点击"执行修复"、"忽略"或"编辑后执行"。
- AC2 (Negative): Given 用户无写入权限，When 点击"执行修复"，Then 系统提示"权限不足"。
- AC3 (Edge): Given 修复风险为 high，When 点击"执行修复"，Then 系统提示"高风险，建议生成 PR"。

### US-004：在 Arch 模式下扫描项目

**作为** Tech Lead，**我想** 一键扫描项目架构问题，**以便** 发现代码库坏味道。

- AC1 (Happy): Given 会话处于 Arch 模式，When 点击"扫描架构"，Then 终端显示治理项列表。
- AC2 (Negative): Given 项目路径无效，When 扫描，Then 系统提示"项目路径不存在"。
- AC3 (Edge): Given 未发现任何问题，When 扫描完成，Then 系统提示"未检测到架构问题"。

### US-005：执行架构治理并记录 ADR

**作为** 架构师，**我想** 确认治理方案后执行重构，**以便** 代码库质量提升并留下决策记录。

- AC1 (Happy): Given 治理方案已展示，When 点击"执行重构"，Then 系统在临时工作区执行变更并记录 ADR。
- AC2 (Negative): Given 验证失败，When 执行重构，Then 系统自动回滚并提示失败原因。
- AC3 (Edge): Given 用户取消确认，When 关闭卡片，Then 系统记录"用户跳过"状态。

## 4. 功能需求清单 {#sec-requirements}

| 编号 | 需求 | 优先级 | 验收标准 | 状态 |
|------|------|--------|----------|------|
| REQ-P0-001 | 创建并管理 AI CLI 会话 | P0 | US-001 AC1-3 | NOT_STARTED |
| REQ-P0-002 | Bug 模式异常解析与 AI 分析 | P0 | US-002 AC1-3 | NOT_STARTED |
| REQ-P0-003 | 修复方案卡片展示与用户确认 | P0 | US-003 AC1-3 | NOT_STARTED |
| REQ-P0-004 | Arch 模式项目扫描与治理项列表 | P0 | US-004 AC1-3 | NOT_STARTED |
| REQ-P0-005 | 架构治理执行与 ADR 记录 | P0 | US-005 AC1-3 | NOT_STARTED |
| REQ-P1-006 | 会话历史查询与恢复 | P1 | 可查看最近 10 条消息 | NOT_STARTED |
| REQ-P1-007 | 历史 Bug 同类推荐 | P1 | 匹配度 >= 80% 时推荐 | NOT_STARTED |
| REQ-P2-008 | OCR 截图识别异常 | P2 | 截图上传后识别文字 | NOT_STARTED |

## 5. 业务规则 {#sec-business-rules}

### 5.1 规则清单

| 编号 | 规则 | 优先级 | 冲突仲裁 |
|------|------|--------|----------|
| BR-001 | 所有自动修复必须用户显式确认 | P0 | 任何绕过确认的逻辑视为 Bug |
| BR-002 | 高风险修复必须生成 PR，禁止直推主分支 | P0 | 高风险判定标准见修复方案 risk 字段 |
| BR-003 | 架构扫描规则默认关闭高误报规则 | P1 | 用户可手动开启 |
| BR-004 | 会话消息保留最近 100 条，超期自动归档 | P1 | 归档策略可配置 |
| BR-005 | 执行引擎必须在临时 Git 工作区运行 | P0 | 禁止直接修改用户原始工作区 |

### 5.2 冲突仲裁

- 当用户权限与修复执行冲突时，BR-001 与 BR-002 优先于用户体验。
- 当扫描性能与全面性冲突时，默认采用保守规则（BR-003）。

## 6. 需求追溯矩阵（RTM） {#sec-rtm}

| 用户故事 | 功能需求 | 需求描述 | 优先级 | 验收标准 | 状态 |
|----------|----------|----------|--------|----------|------|
| US-001 | REQ-P0-001 | 创建并管理 AI CLI 会话 | P0 | AC1-3 | NOT_STARTED |
| US-002 | REQ-P0-002 | Bug 模式异常解析与 AI 分析 | P0 | AC1-3 | NOT_STARTED |
| US-003 | REQ-P0-003 | 修复方案卡片展示与用户确认 | P0 | AC1-3 | NOT_STARTED |
| US-004 | REQ-P0-004 | Arch 模式项目扫描与治理项列表 | P0 | AC1-3 | NOT_STARTED |
| US-005 | REQ-P0-005 | 架构治理执行与 ADR 记录 | P0 | AC1-3 | NOT_STARTED |
