---
doc_type: "PRD"
fragment_id: "prd-ai-cli-terminal-dr-003-io"
title: "架构治理 - 输入输出表"
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

# 架构治理 - 输入输出表 {#sec-io-table}

## 1. 外部输入 {#sec-external-input}

| 编号 | 输入项 | 来源 | 类型 | 必填 | 说明 |
|------|--------|------|------|------|------|
| I3-001 | projectId | 项目上下文 | string | 是 | 当前项目标识 |
| I3-002 | sessionId | CLI 会话 | string | 是 | 当前会话标识 |
| I3-003 | scanRules | 默认配置/用户配置 | array | 否 | 扫描规则列表，默认使用系统规则 |
| I3-004 | issueId | 用户选择 | string | 否 | 选中的治理项标识 |
| I3-005 | userAction | 卡片按钮 | enum | 否 | `execute` / `skip` / `false_positive` |
| I3-006 | adrReason | 用户输入 | string | 否 | ADR 决策原因补充 |
| I3-007 | adrImpact | 用户输入 | string | 否 | ADR 影响补充 |

## 2. 外部输出 {#sec-external-output}

| 编号 | 输出项 | 目标 | 类型 | 说明 |
|------|--------|------|------|------|
| O3-001 | scan progress | 终端 | WebSocket progress | 扫描进度与当前文件 |
| O3-002 | issue list card | 终端 | WebSocket card | 治理项汇总列表 |
| O3-003 | governance plan card | 终端 | WebSocket card | 单个治理项方案 |
| O3-004 | refactor progress | 终端 | WebSocket progress | 重构执行进度 |
| O3-005 | ADR draft | 终端/ADR 页面 | object | 生成的架构决策记录草稿 |
| O3-006 | result message | 终端 | WebSocket text | 成功/跳过/误标结果 |

## 3. 数据存储 {#sec-data-storage}

| 编号 | 数据项 | 实体 | 读写方向 | 说明 |
|------|--------|------|----------|------|
| D3-001 | arch issue | ArchIssue | 写入/更新 | 治理项描述、方案、状态 |
| D3-002 | scan config | ScanRule | 读取 | 扫描规则定义 |
| D3-003 | ADR record | ADR | 写入 | 架构决策记录 |
| D3-004 | session messages | CliMessage | 写入 | 扫描与重构过程消息 |

## 4. 接口映射 {#sec-api-mapping}

| 编号 | 接口 | 方法 | 用途 |
|------|------|------|------|
| API3-001 | `/api/arch/scan` | POST | 触发架构扫描（异步） |
| API3-002 | `/api/arch/issues` | POST | 保存/更新治理项 |
| API3-003 | `/api/arch/issues/{id}/plan` | GET | 获取治理方案 |
| API3-004 | `/api/adr` | POST | 保存 ADR 记录 |
| API3-005 | `/ws/cli/{sessionId}` | WebSocket | 流式扫描、卡片、进度 |
