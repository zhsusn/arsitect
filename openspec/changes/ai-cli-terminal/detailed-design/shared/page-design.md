---
doc_type: "DETAIL_DESIGN"
fragment_id: "dd-ai-cli-terminal-page"
title: "AI CLI 终端 - 共享页面设计"
version: "1.0.0"
status: "DRAFT"
iteration: "ai-cli-terminal"
dependencies:
  - fragment_id: "dd-ai-cli-terminal-shared"
    version: "1.0.0"
c4_binding:
  level: "L3"
  container: "ai-cli-terminal"
  component: "frontend-page"
---

# AI CLI 终端 - 共享页面设计 {#sec-page-design}

## 1. 页面布局 {#sec-layout}

### 1.1 整体结构 {#sec-structure}

```
┌─────────────────────────────────────────────────────────────┐
│  [Logo]  AI CLI 终端                    [Bug模式] [架构模式] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  xterm.js 终端渲染区域                               │    │
│  │  (占满剩余高度，支持 ANSI 颜色与自定义 Decoration)   │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  [快捷操作 1] [快捷操作 2] [快捷操作 3] [清空终端]           │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 顶部模式 Tab {#sec-mode-tab}

- **Bug 模式**：默认模式，输入提示为 `$ 粘贴异常信息或输入错误描述...`
- **架构模式**：输入提示为 `$ 输入架构问题或选择治理项...`
- 切换时通过 WebSocket 发送 `session.mode_switch` 事件，服务端更新 `cli_sessions.mode`。

### 1.3 快捷操作栏 {#sec-shortcuts}

| 模式 | 按钮 | 动作 |
|------|------|------|
| Bug | 粘贴异常 | 读取剪贴板并发送到终端 |
| Bug | 查看历史 Bug | 打开侧边抽屉展示历史记录 |
| Bug | 清空终端 | 调用 `xterm.clear()` |
| Arch | 扫描当前项目 | 发送 `scan arch` 命令 |
| Arch | 查看架构图 | 打开 Mermaid 架构图弹窗 |
| Arch | 治理规则配置 | 打开规则配置抽屉 |

## 2. 终端渲染层 {#sec-terminal}

### 2.1 xterm.js 集成 {#sec-xterm-integration}

- 使用 `xterm.js` + `xterm-addon-fit` + `xterm-addon-web-links`。
- 通过 `terminal.onData()` 捕获用户输入，回车时组装为 `CliRequest` 发送。
- 通过 `terminal.write()` 输出服务端文本，支持 ANSI 颜色码。

### 2.2 消息样式 {#sec-message-style}

| 类型 | 前缀 | ANSI 颜色 | CSS 类 |
|------|------|-----------|--------|
| user | `$` | 白色 | `.msg-user` |
| ai | `[AI]` | 蓝色 `\x1b[36m` | `.msg-ai` |
| system | `[系统]` | 灰色 `\x1b[90m` | `.msg-system` |
| error | `[错误]` | 红色 `\x1b[31m` | `.msg-error` |
| success | `[成功]` | 绿色 `\x1b[32m` | `.msg-success` |
| diff | `[Diff]` | 黄色 `\x1b[33m` | `.msg-diff` |
| prompt | `[?]` | 紫色 `\x1b[35m` | `.msg-prompt` |

### 2.3 交互卡片嵌入 {#sec-card-decoration}

- 使用 `xterm.js` 的 `registerDecoration` API 在指定行插入 HTML Overlay。
- 卡片类型：`bug-report`、`fix-proposal`、`arch-decision`、`progress`、`confirm`。
- 按钮点击后自动向终端输入对应命令（如 `Y`、`N`、`edit`）。

```typescript
interface CliCard {
  type: 'bug-report' | 'fix-proposal' | 'arch-decision' | 'progress' | 'confirm';
  data: Record<string, any>;
  actions: Array<{
    label: string;
    command: string;
    style: 'primary' | 'danger' | 'default';
  }>;
}
```

## 3. 状态管理 {#sec-state}

- 使用 Zustand 管理全局 CLI 状态：
  - `currentSessionId`
  - `mode`
  - `socketStatus: 'connecting' | 'open' | 'closed' | 'error'`
  - `pendingConfirm: boolean`
  - `lastCommand`
- 本地终端状态由 `xterm.js` 自身维护。

## 4. 用户旅程 {#sec-user-journey}

### 4.1 进入页面 {#sec-enter}

1. 用户点击导航"AI CLI"。
2. 前端调用 `POST /api/v1/cli/sessions` 创建会话。
3. 建立 WebSocket 连接 `/api/v1/cli/ws/{sessionId}`。
4. 终端显示欢迎语与模式提示。

### 4.2 异常处理 {#sec-error-handling}

- 连接失败：显示"连接失败，请重试"，自动重试 3 次。
- 会话失效：提示"会话已失效，请重新创建"，清空当前会话并重新创建。
- 网络闪断：前端自动重连，恢复最近 10 条消息。

## 5. 可访问性 {#sec-a11y}

- 终端区域支持键盘聚焦（`tabIndex=0`）。
- 快捷操作按钮提供 `aria-label`。
- 颜色对比度满足 WCAG 2.1 AA。
