---
doc_type: "PRD"
fragment_id: "prd-ai-cli-terminal-dr-001-io"
title: "CLI 会话管理 - 输入输出表"
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

# CLI 会话管理 - 输入输出表 {#sec-io-table}

## 1. 外部输入 {#sec-external-input}

| 编号 | 输入项 | 来源 | 类型 | 必填 | 说明 |
|------|--------|------|------|------|------|
| I1-001 | userId | 认证模块 | string | 是 | 当前登录用户标识 |
| I1-002 | projectId | 项目上下文 | string | 是 | 当前项目标识 |
| I1-003 | mode | 用户选择 | enum | 是 | `bug` / `arch` |
| I1-004 | sessionId | 系统生成/URL | string | 否 | 恢复会话时使用 |
| I1-005 | command | 键盘/快捷按钮 | string | 否 | 内置命令或用户输入 |

## 2. 外部输出 {#sec-external-output}

| 编号 | 输出项 | 目标 | 类型 | 说明 |
|------|--------|------|------|------|
| O1-001 | sessionId | 前端/URL | string | 新建会话后返回 |
| O1-002 | message stream | 前端终端 | WebSocket 消息 | 用户/AI/系统/卡片消息 |
| O1-003 | connection status | 前端状态栏 | enum | `online` / `reconnecting` / `offline` |
| O1-004 | mode indicator | 前端 Tab | enum | 当前激活模式 |
| O1-005 | history list | 前端弹窗 | array | 最近会话摘要列表 |

## 3. 数据存储 {#sec-data-storage}

| 编号 | 数据项 | 实体 | 读写方向 | 说明 |
|------|--------|------|----------|------|
| D1-001 | session metadata | CliSession | 写入 | userId, projectId, mode, status |
| D1-002 | message list | CliMessage | 写入/读取 | 最多保留 100 条 |
| D1-003 | last active time | CliSession | 更新 | 用于会话恢复排序 |

## 4. 接口映射 {#sec-api-mapping}

| 编号 | 接口 | 方法 | 用途 |
|------|------|------|------|
| API1-001 | `/api/cli/sessions` | POST | 创建新会话 |
| API1-002 | `/api/cli/sessions/{id}/history` | GET | 获取历史消息 |
| API1-003 | `/ws/cli/{sessionId}` | WebSocket | 双向消息通道 |
| API1-004 | `/api/cli/sessions/{id}` | DELETE | 关闭会话 |
