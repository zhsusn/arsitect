---
doc_type: "PRD"
fragment_id: "prd-ai-cli-terminal-dr-consistency"
title: "AI CLI 终端 - 详细需求一致性报告"
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

# AI CLI 终端 - 详细需求一致性报告 {#sec-consistency-report}

## 1. 检查范围 {#sec-check-scope}

本报告对 `ai-cli-terminal` 变更下的 3 个详细需求模块（DR-001 ~ DR-003）进行内部一致性与高层需求追溯检查。

## 2. 与高层需求的一致性 {#sec-high-level-consistency}

| 检查项 | 高层需求来源 | 详细需求体现 | 状态 |
|--------|--------------|--------------|------|
| Bug 修复闭环 | `02-functional-requirements.md` §3.1 / §5.1 | DR-002 覆盖解析、分析、方案、确认、执行、记录 | ✅ 一致 |
| 架构治理闭环 | `02-functional-requirements.md` §3.2 / §5.2 | DR-003 覆盖扫描、列表、方案、确认、重构、ADR | ✅ 一致 |
| 会话与模式管理 | `02-functional-requirements.md` §2 / §6.1 | DR-001 覆盖会话创建、恢复、模式切换、重连 | ✅ 一致 |
| 显式确认规则 | `01-requirements-list.md` BR-001 | DR-002 / DR-003 均要求用户确认后执行 | ✅ 一致 |
| 高风险方案 PR 规则 | `01-requirements-list.md` BR-002 | DR-002 明确 high 风险二次确认 / PR 引导 | ✅ 一致 |
| 临时工作区规则 | `01-requirements-list.md` BR-005 | DR-002 / DR-003 均声明在临时工作区执行 | ✅ 一致 |
| 消息持久化 | `00-requirements-overview.md` §4.1 | DR-001 声明保留最近 100 条消息 | ✅ 一致 |

## 3. 模块间接口一致性 {#sec-inter-module-consistency}

| 接口/数据 | DR-001 | DR-002 | DR-003 | 一致性 |
|-----------|--------|--------|--------|--------|
| sessionId | 生成并管理 | 复用 | 复用 | ✅ 一致 |
| projectId | 上下文来源 | 上下文来源 | 上下文来源 | ✅ 一致 |
| WebSocket 消息类型 | user/ai/system/card | text/card/progress | progress/card/text | ✅ 一致，类型覆盖 |
| 卡片操作语义 | 模式切换相关 | execute/ignore/edit | execute/skip/false_positive | ✅ 不冲突 |
| 临时工作区执行 | 不涉及 | 修复执行 | 重构执行 | ✅ 均依赖 Exec Service |
| 状态枚举 | active/paused/closed | pending/executed/verified/... | detected/planned/closed/... | ✅ 各自独立 |

## 4. 待确认问题 {#sec-open-issues}

| 编号 | 问题 | 影响模块 | 建议处理方式 |
|------|------|----------|--------------|
| Q-001 | 消息保留 100 条后归档策略未定义存储位置 | DR-001 | 概要设计阶段确定归档表或文件 |
| Q-002 | Bug 修复"编辑后执行"的 Diff 编辑器范围（Monaco / 简易文本） | DR-002 | 概要设计阶段结合前端技术栈决定 |
| Q-003 | 架构扫描引擎具体规则实现方式（AST / 正则 / tree-sitter） | DR-003 | 概要设计阶段确定扫描器选型 |
| Q-004 | Exec Service 临时工作区的生命周期与清理策略 | DR-002 / DR-003 | 概要设计阶段统一设计 |
| Q-005 | 高风险方案"生成 PR"在 MVP 中是否为占位功能 | DR-002 | 明确 P2 实现，MVP 仅提示 |

## 5. 风险与假设复核 {#sec-risk-assumption}

| 高层风险/假设 | 详细需求中的缓解/依赖 | 状态 |
|---------------|------------------------|------|
| R-001 误改代码 | DR-002 / DR-003 均要求临时工作区 + 验证 + 回滚 | ✅ 已覆盖 |
| R-002 WebSocket 断连 | DR-001 定义重连与消息补全机制 | ✅ 已覆盖 |
| R-003 架构扫描误报 | DR-003 默认关闭高误报规则 + 支持标记误报 | ✅ 已覆盖 |
| A-001 类终端交互接受度 | DR-001 提供模式切换与命令补全 | ✅ 已覆盖 |
| A-002 Kimi API 流式稳定 | DR-002 / DR-003 依赖 AI Gateway 流式能力 | ⚠️ 依赖外部能力 |
| A-003 项目已纳入 Git | DR-002 / DR-003 执行前依赖临时工作区 | ⚠️ 需 Exec Service 保证 |

## 6. 结论 {#sec-conclusion}

三个详细需求模块在功能边界、验收标准、关键业务规则上与高层需求保持一致。模块间通过 `sessionId`、`projectId`、WebSocket 消息通道、Exec Service 等公共能力衔接，未发现直接冲突。待确认问题需在概要设计阶段进一步细化技术方案。
