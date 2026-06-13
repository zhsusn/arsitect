---
doc_type: "PRD"
fragment_id: "prd-ai-cli-terminal-dr-001-spec"
title: "CLI 会话管理 - 模块规格"
version: "1.0.0"
status: "DRAFT"
iteration: "ai-cli-terminal"
dependencies:
  - fragment_id: "prd-ai-cli-terminal-000"
    version: "1.0.0"
  - fragment_id: "prd-ai-cli-terminal-001"
    version: "1.0.0"
  - fragment_id: "prd-ai-cli-terminal-002"
    version: "1.0.0"
---

# CLI 会话管理 - 模块规格 {#sec-spec}

## 1. 模块定位 {#sec-module-position}

本模块为 AI CLI 终端提供会话生命周期管理能力，是 Bug 修复与架构治理两个业务模式的公共底座。模块负责会话的创建、恢复、模式切换、连接保持以及消息持久化，确保用户在不同工作模式间切换时上下文不丢失。

## 2. 功能边界 {#sec-functional-scope}

### 2.1 In-Scope {#sec-in-scope}

- 新建 AI CLI 会话并分配唯一 sessionId。
- 恢复最近关闭的会话及其最近 100 条消息。
- 在 Bug 模式与架构治理模式之间切换。
- WebSocket 连接建立、心跳保活与断线重连。
- 用户消息、AI 消息、系统消息、卡片消息的持久化。
- 会话关闭与显式清理。

### 2.2 Out-of-Scope {#sec-out-of-scope}

- 多 AI Provider 的会话隔离（P2）。
- 会话级别的权限细粒度控制（P2）。
- 消息全文检索与高级筛选（P2）。

## 3. 用户场景 {#sec-user-scenarios}

### 3.1 场景一：首次进入终端 {#sec-scenario-new-session}

用户从项目仪表盘点击"打开 AI CLI"，系统创建新会话，默认进入 Bug 模式，终端显示欢迎语与输入提示。

### 3.2 场景二：切换工作模式 {#sec-scenario-mode-switch}

用户在 Bug 模式下处理完一个异常后，点击顶部 Tab 切换到架构治理模式，系统保留当前会话，清空模式专属上下文，显示治理模式提示。

### 3.3 场景三：页面刷新后恢复 {#sec-scenario-recovery}

用户刷新浏览器后，前端通过 sessionId 请求历史消息，后端按时间倒序返回最近 100 条，终端逐条重新渲染。

## 4. 验收标准 {#sec-acceptance-criteria}

| 编号 | 场景 | 验收标准 | 优先级 |
|------|------|----------|--------|
| AC1-001 | 创建会话 | 已登录用户点击入口后 1s 内显示可用终端 | P0 |
| AC1-002 | 未登录拦截 | 未登录用户访问页面时跳转登录页 | P0 |
| AC1-003 | 模式切换 | 切换模式后终端保留公共消息，上下文重置不超过 500ms | P0 |
| AC1-004 | 断线重连 | 网络闪断 5s 内自动恢复连接并补发未送达消息 | P1 |
| AC1-005 | 历史恢复 | 刷新页面后 2s 内恢复最近 100 条消息 | P1 |

## 5. 依赖与约束 {#sec-dependencies}

- 依赖用户认证模块提供当前 userId。
- 依赖项目模块提供当前 projectId。
- 依赖后端 WebSocket Gateway 提供连接管理能力。
- 单会话消息保留上限为 100 条，超出后按时间顺序归档。
