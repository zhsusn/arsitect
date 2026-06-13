---
doc_type: "PRD"
fragment_id: "prd-ai-cli-terminal-dr-001-interaction"
title: "CLI 会话管理 - 交互规格"
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

# CLI 会话管理 - 交互规格 {#sec-interaction-spec}

## 1. 键盘交互 {#sec-keyboard-interaction}

| 按键 | 场景 | 行为 |
|------|------|------|
| Enter | 输入行有内容 | 发送当前输入 |
| ↑ / ↓ | 输入行聚焦 | 切换历史命令 |
| Tab | 输入行聚焦 | 补全内置命令 |
| Ctrl+L | 任意时刻 | 清空终端渲染区 |
| Ctrl+V | 输入行聚焦 | 粘贴剪贴板内容 |
| Esc | 存在待确认卡片 | 取消当前卡片操作 |

## 2. 内置命令 {#sec-built-in-commands}

| 命令 | 功能 | 示例 |
|------|------|------|
| `help` | 显示可用命令 | `$ help` |
| `clear` | 清空本地终端 | `$ clear` |
| `history` | 展示最近会话列表 | `$ history` |
| `mode bug` | 切换到 Bug 模式 | `$ mode bug` |
| `mode arch` | 切换到 Arch 模式 | `$ mode arch` |
| `reconnect` | 手动触发重连 | `$ reconnect` |

## 3. 错误提示 {#sec-error-messages}

| 场景 | 提示文案 | 恢复方式 |
|------|----------|----------|
| 未登录 | `[错误] 请先登录后使用 AI CLI` | 跳转登录页 |
| 连接失败 | `[错误] 连接失败，正在尝试重连...` | 自动重连 |
| 切换模式时存在待确认 | `[系统] 当前有未确认操作，请先处理` | 处理卡片后继续 |
| 会话已过期 | `[错误] 会话已过期，请重新创建` | 创建新会话 |

## 4. 滚动与聚焦 {#sec-scroll-focus}

- 新消息到达时，若用户未主动向上滚动，则自动滚动到底部。
- 用户向上滚动超过 200px 后，新消息到达不自动滚动，显示"有新消息"提示。
- 页面加载完成后，输入行自动获得焦点。

## 5. 连接状态展示 {#sec-connection-status}

- 在线：顶部状态圆点为绿色，hover 显示"连接正常"。
- 重连中：圆点为黄色并旋转，显示"正在重连..."
- 离线：圆点为红色，显示"已离线，请检查网络"。
