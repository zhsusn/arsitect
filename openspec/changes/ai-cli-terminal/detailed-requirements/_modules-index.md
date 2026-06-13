---
doc_type: "PRD"
fragment_id: "prd-ai-cli-terminal-dr-index"
title: "AI CLI 终端 - 详细需求模块索引"
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

# AI CLI 终端 - 详细需求模块索引 {#sec-modules-index}

## 1. 变更概述 {#sec-overview}

本索引汇总 `ai-cli-terminal` 变更下的详细需求模块，覆盖 CLI 会话管理、Bug 修复、架构治理三大模块。每个模块均按统一结构输出 6 份文件：模块需求（聚合）、规格、原型、输入输出表、业务逻辑、交互规格。

## 2. 模块清单 {#sec-module-list}

| 模块编号 | 模块名称 | 目录 | 对应高层需求 | 优先级 | 状态 |
|----------|----------|------|--------------|--------|------|
| DR-001 | CLI 会话管理 | `feature-01-cli-session/` | REQ-P0-001, US-001 | P0 | DRAFT |
| DR-002 | Bug 修复 | `feature-02-bug-fix/` | REQ-P0-002, REQ-P0-003, US-002, US-003 | P0 | DRAFT |
| DR-003 | 架构治理 | `feature-03-arch-governance/` | REQ-P0-004, REQ-P0-005, US-004, US-005 | P0 | DRAFT |

## 3. 文件清单 {#sec-file-list}

### 3.1 CLI 会话管理 {#sec-files-cli-session}

| 文件 | 类型 | fragment_id |
|------|------|-------------|
| `feature-01-cli-session/module-requirements.md` | 聚合 | `prd-ai-cli-terminal-dr-001` |
| `feature-01-cli-session/spec.md` | 规格 | `prd-ai-cli-terminal-dr-001-spec` |
| `feature-01-cli-session/prototype.md` | 原型 | `prd-ai-cli-terminal-dr-001-prototype` |
| `feature-01-cli-session/io-table.md` | 输入输出表 | `prd-ai-cli-terminal-dr-001-io` |
| `feature-01-cli-session/logic.md` | 业务逻辑 | `prd-ai-cli-terminal-dr-001-logic` |
| `feature-01-cli-session/interaction-spec.md` | 交互规格 | `prd-ai-cli-terminal-dr-001-interaction` |

### 3.2 Bug 修复 {#sec-files-bug-fix}

| 文件 | 类型 | fragment_id |
|------|------|-------------|
| `feature-02-bug-fix/module-requirements.md` | 聚合 | `prd-ai-cli-terminal-dr-002` |
| `feature-02-bug-fix/spec.md` | 规格 | `prd-ai-cli-terminal-dr-002-spec` |
| `feature-02-bug-fix/prototype.md` | 原型 | `prd-ai-cli-terminal-dr-002-prototype` |
| `feature-02-bug-fix/io-table.md` | 输入输出表 | `prd-ai-cli-terminal-dr-002-io` |
| `feature-02-bug-fix/logic.md` | 业务逻辑 | `prd-ai-cli-terminal-dr-002-logic` |
| `feature-02-bug-fix/interaction-spec.md` | 交互规格 | `prd-ai-cli-terminal-dr-002-interaction` |

### 3.3 架构治理 {#sec-files-arch-governance}

| 文件 | 类型 | fragment_id |
|------|------|-------------|
| `feature-03-arch-governance/module-requirements.md` | 聚合 | `prd-ai-cli-terminal-dr-003` |
| `feature-03-arch-governance/spec.md` | 规格 | `prd-ai-cli-terminal-dr-003-spec` |
| `feature-03-arch-governance/prototype.md` | 原型 | `prd-ai-cli-terminal-dr-003-prototype` |
| `feature-03-arch-governance/io-table.md` | 输入输出表 | `prd-ai-cli-terminal-dr-003-io` |
| `feature-03-arch-governance/logic.md` | 业务逻辑 | `prd-ai-cli-terminal-dr-003-logic` |
| `feature-03-arch-governance/interaction-spec.md` | 交互规格 | `prd-ai-cli-terminal-dr-003-interaction` |

## 4. 需求追溯矩阵 {#sec-rtm}

| 用户故事 | 功能需求 | 详细需求模块 | 验收标准 |
|----------|----------|--------------|----------|
| US-001 | REQ-P0-001 | DR-001 | AC1-001 ~ AC1-005 |
| US-002 | REQ-P0-002 | DR-002 | AC2-001 ~ AC2-003 |
| US-003 | REQ-P0-003 | DR-002 | AC2-004 ~ AC2-007 |
| US-004 | REQ-P0-004 | DR-003 | AC3-001 ~ AC3-004 |
| US-005 | REQ-P0-005 | DR-003 | AC3-005 ~ AC3-007 |

## 5. 优先级与迭代计划 {#sec-priority-plan}

| 阶段 | 模块 | 交付目标 |
|------|------|----------|
| Phase 1 | DR-001 | 基础 CLI 页面 + WebSocket 连接 + 会话管理 |
| Phase 2 | DR-002 | Bug 修复完整流程 + Bug 记录库 |
| Phase 3 | DR-003 | 架构治理扫描 + 治理项执行 + ADR 记录 |
