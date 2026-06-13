---
doc_type: "PRD"
fragment_id: "prd-ai-cli-terminal-dr-002-io"
title: "Bug 修复 - 输入输出表"
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

# Bug 修复 - 输入输出表 {#sec-io-table}

## 1. 外部输入 {#sec-external-input}

| 编号 | 输入项 | 来源 | 类型 | 必填 | 说明 |
|------|--------|------|------|------|------|
| I2-001 | errorInput | 用户粘贴 | string | 是 | 原始异常堆栈或错误描述 |
| I2-002 | sessionId | CLI 会话 | string | 是 | 当前会话标识 |
| I2-003 | projectId | 项目上下文 | string | 是 | 当前项目标识 |
| I2-004 | userAction | 卡片按钮 | enum | 否 | `execute` / `ignore` / `edit` |
| I2-005 | editedDiff | 编辑器 | string | 否 | 用户编辑后的 Diff |
| I2-006 | writePermission | 权限模块 | boolean | 是 | 是否有代码写入权限 |

## 2. 外部输出 {#sec-external-output}

| 编号 | 输出项 | 目标 | 类型 | 说明 |
|------|--------|------|------|------|
| O2-001 | analysis stream | 终端 | WebSocket text | 根因、定位、风险等流式文本 |
| O2-002 | fix proposal card | 终端 | WebSocket card | 包含 Diff 与操作按钮 |
| O2-003 | execution progress | 终端 | WebSocket progress | 执行进度百分比与日志 |
| O2-004 | result message | 终端 | WebSocket text | 成功/失败/忽略结果 |
| O2-005 | bugRecordId | 前端/记录页 | string | 保存后的记录编号 |

## 3. 数据存储 {#sec-data-storage}

| 编号 | 数据项 | 实体 | 读写方向 | 说明 |
|------|--------|------|----------|------|
| D2-001 | bug record | BugRecord | 写入 | 错误签名、根因、Diff、状态 |
| D2-002 | similar bugs | BugRecord | 读取 | 按错误签名匹配历史记录 |
| D2-003 | session messages | CliMessage | 写入 | 分析与执行过程消息 |

## 4. 接口映射 {#sec-api-mapping}

| 编号 | 接口 | 方法 | 用途 |
|------|------|------|------|
| API2-001 | `/api/bugs` | POST | 保存 Bug 记录 |
| API2-002 | `/api/bugs?signature={sig}` | GET | 查询同类历史 Bug |
| API2-003 | `/ws/cli/{sessionId}` | WebSocket | 流式分析、卡片、进度 |
| API2-004 | `/api/cli/sessions/{id}/abort` | POST | 中止当前 AI 任务 |
