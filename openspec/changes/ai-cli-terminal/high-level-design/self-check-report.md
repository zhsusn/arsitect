---
doc_type: "ARCH"
fragment_id: "arch-ai-cli-terminal-006"
title: "AI CLI 终端 - 概要设计自检报告"
version: "1.0.0"
status: "DRAFT"
iteration: "ai-cli-terminal"
dependencies:
  - fragment_id: "arch-ai-cli-terminal-000"
    version: "1.0.0"
  - fragment_id: "arch-ai-cli-terminal-001"
    version: "1.0.0"
  - fragment_id: "arch-ai-cli-terminal-002"
    version: "1.0.0"
  - fragment_id: "arch-ai-cli-terminal-003"
    version: "1.0.0"
  - fragment_id: "arch-ai-cli-terminal-004"
    version: "1.0.0"
  - fragment_id: "arch-ai-cli-terminal-005"
    version: "1.0.0"
c4_binding:
  level: "L2"
  system: "ai-cli-terminal"
---

# AI CLI 终端 - 概要设计自检报告

## 1. 自检结论总览 {#sec-summary}

| 检查项 | 结论等级 | 说明 |
|--------|----------|------|
| 技术栈覆盖度 | ✅ | React 19 + Vite 6 + xterm.js + FastAPI + SQLAlchemy 2.0 + SQLite/PostgreSQL 覆盖全部需求 |
| 架构-需求一致性 | ✅ | 01-architecture-core 中的服务划分与 02-functional-requirements 中的模块-功能点树完全对应 |
| 数据流-状态机一致性 | ✅ | 03-runtime-behavior 中的状态机与 02-data-flow 中的时序图状态一致 |
| 异常-回滚联动 | ✅ | 04-quality-attributes 中的异常分类与 05-ops-governance 中的回滚方案三级联动 |
| 安全-业务规则一致性 | ✅ | BR-001/BR-002/BR-005 在架构、运行时、运维文档中均有落实 |
| 性能-部署匹配 | ✅ | P95 < 200ms、首屏 < 3s 目标与本地单进程部署拓扑匹配 |
| ADR 溯源 | ✅ | ADR-001 ~ ADR-006 均可在 PRD、AGENTS.md 与原始设计输入中找到支撑 |
| 模块遗漏检查 | ✅ | CLI/Bug/Arch/Exec/AI Gateway/WebSocket Gateway/Storage 全部覆盖 |
| Mermaid 规范合规 | ✅ | 全部图表使用语义化节点、subgraph 分组、虚线回流 |
| 边界红线检查 | ✅ | 未发现字段类型、DDL、具体代码、框架特定模式越界 |

**最终结论：无 ❌ 阻断项，无 ⚠️ 警告项。满足 Gate 2 进入条件。**

## 2. 详细检查记录 {#sec-detailed-checks}

### 2.1 技术栈覆盖度 {#sec-tech-coverage}

**检查逻辑**：验证 01 §2.1 技术栈清单是否覆盖需求文档中的全部技术约束。

| 需求约束 | 来源 | 技术栈支撑 | 匹配 |
|----------|------|------------|------|
| React 19 + Vite 6 + TypeScript | PRD-000 §9 | 前端采用 React 19 + Vite 6 + TypeScript | ✅ |
| FastAPI + SQLAlchemy 2.0 | PRD-000 §9 | 后端采用 FastAPI 0.115 + SQLAlchemy 2.0 | ✅ |
| SQLite（MVP） | PRD-000 §9 | MVP 使用 SQLite | ✅ |
| python-socketio | PRD-000 §9 | WebSocket 采用 python-socketio | ✅ |
| xterm.js | docs/aicli.txt | 终端渲染采用 xterm.js | ✅ |
| WebSocket 双向通信 | PRD-000 NFR | 采用 WebSocket 替代 SSE | ✅ |

**结论**：✅ 通过。全部技术约束均有对应组件支撑。

### 2.2 架构-需求一致性 {#sec-arch-req}

**检查逻辑**：验证 01 §3.3 服务职责矩阵是否覆盖 02-functional-requirements §2 中的全部模块-功能点。

| 模块 | 功能点 | 处理服务 | 匹配 |
|------|--------|----------|------|
| cli-session | 创建/恢复/关闭会话 | CLI Service | ✅ |
| cli-session | 模式切换 | CLI Service | ✅ |
| cli-session | 消息持久化与历史查询 | CLI Service + Storage | ✅ |
| bug-fix | 异常解析与签名生成 | Bug Service | ✅ |
| bug-fix | 历史 Bug 同类查询 | Bug Service + Storage | ✅ |
| bug-fix | AI 根因分析与修复方案生成 | Bug Service + AI Gateway | ✅ |
| bug-fix | 修复方案卡片渲染与确认 | Bug Service + 前端 | ✅ |
| bug-fix | 临时工作区执行修复与验证 | Bug Service + Exec Service | ✅ |
| arch-governance | 项目扫描与规则匹配 | Arch Service | ✅ |
| arch-governance | 治理项列表与优先级排序 | Arch Service | ✅ |
| arch-governance | AI 治理方案生成 | Arch Service + AI Gateway | ✅ |
| arch-governance | 重构执行与 ADR 记录 | Arch Service + Exec Service + Storage | ✅ |

**结论**：✅ 通过。全部功能点均有明确服务处理方。

### 2.3 数据流-状态机一致性 {#sec-flow-state}

**检查逻辑**：验证 03-runtime-behavior 中的状态机与 02-data-flow 中的时序图状态是否一致。

| 状态机 | 02-data-flow 对应 | 一致性 |
|--------|-------------------|--------|
| CLI 会话：active → paused → active | Bug/Arch 流程中的卡片确认阶段 | ✅ |
| Bug：pending → executed → verified | Bug 修复时序图中的执行与验证 | ✅ |
| Bug：pending → ignored | 用户点击忽略 | ✅ |
| Bug：executed → failed → pending | 验证失败后重新生成方案 | ✅ |
| Arch：detected → planned → executed → closed | 架构治理时序图中的扫描→方案→执行→ADR | ✅ |
| Arch：executed → failed → planned | 验证失败后重新规划 | ✅ |

**结论**：✅ 通过。状态机与时序图完全对应。

### 2.4 安全-业务规则一致性 {#sec-security-rules}

**检查逻辑**：验证 01-requirements-list §5.1 中的业务规则是否在架构、运行时、运维文档中落实。

| 规则 | 来源 | 落实位置 | 匹配 |
|------|------|----------|------|
| BR-001：所有自动修复必须用户显式确认 | PRD-001 | 03 §5.1 确认流程、04 §3.2 安全策略 | ✅ |
| BR-002：高风险修复必须生成 PR | PRD-001 | 01 §3.3 Bug Service、04 §3.2 高风险拦截 | ✅ |
| BR-005：执行引擎必须在临时 Git 工作区运行 | PRD-001 | 01 §2.3 ADR-004、04 §3.2 临时工作区隔离 | ✅ |

**结论**：✅ 通过。关键业务规则均有对应设计落地。

### 2.5 异常-回滚联动 {#sec-exception-rollback}

**检查逻辑**：验证 04-quality-attributes §7.1 中的异常分类是否在 05-ops-governance §6 中有回滚对应。

| 异常 | 触发条件 | 回滚层级 | 匹配 |
|------|----------|----------|------|
| 前端构建产物异常 | 发布后发现 | 层级 A | ✅ |
| 后端代码缺陷 | 发布后发现 | 层级 A/C | ✅ |
| 数据迁移脚本异常 | 升级后 | 层级 B | ✅ |
| 严重功能缺陷 | 线上 | 层级 C | ✅ |
| 安全漏洞 | 线上 | 层级 C | ✅ |

**结论**：✅ 通过。异常场景均有回滚策略覆盖。

### 2.6 ADR 溯源 {#sec-adr-trace}

**检查逻辑**：验证 01 §2.2/2.3 中的 ADR 是否有明确来源支撑。

| ADR | 来源 | 支撑依据 |
|-----|------|----------|
| ADR-001 WebSocket | PRD-000 §9、NFR、docs/aicli.txt | 双向交互需求明确 |
| ADR-002 SQLite | PRD-000 §9、AGENTS.md §2.1 | 与现有 MVP 一致 |
| ADR-003 xterm.js | docs/aicli.txt §2.2 | 原始设计明确要求 |
| ADR-004 临时 Git 工作区 | PRD-000 Out-of-Scope、PRD-001 BR-005 | Docker 沙箱 P2 引入 |
| ADR-005 房间隔离 | 高并发需求 | 避免消息串扰 |
| ADR-006 异步服务层 | 流式输出需求 | FastAPI 原生支持 |

**结论**：✅ 通过。全部 ADR 均有来源支撑。

## 3. 待确认项 {#sec-open-items}

| 编号 | 事项 | 建议处理阶段 | 风险 |
|------|------|--------------|------|
| OI-001 | WebSocket 长轮询降级方案的具体实现 | P1 详细设计 | 低 |
| OI-002 | PostgreSQL 迁移的 Alembic 脚本规划 | P1 详细设计 | 低 |
| OI-003 | 高风险修复 PR 创建流程与 Git Provider 集成 | P2 概要设计 | 中 |
| OI-004 | Docker 沙箱执行引擎的接口设计 | P2 概要设计 | 中 |
| OI-005 | 多 AI Provider 适配的抽象接口 | P2 概要设计 | 中 |
| OI-006 | 企业防火墙 WebSocket 限制的实际影响 | MVP 验证 | 中 |

## 4. 最终结论 {#sec-final-conclusion}

本次 AI CLI 终端概要设计严格遵循 Arsitect 项目规范，完成了 6 份主题文件与 1 份自检报告：

- `00-design-overview.md`
- `01-architecture-core.md`
- `02-data-flow.md`
- `03-runtime-behavior.md`
- `04-quality-attributes.md`
- `05-ops-governance.md`
- `self-check-report.md`

设计覆盖了 Bug 修复与架构治理两条核心链路，明确了前端、网关、应用服务、AI 适配、存储五层架构，包含 WebSocket vs SSE 与 SQLite vs PostgreSQL 两项关键 ADR，并在运维文档中给出了三级回滚方案。自检未发现阻断项，建议提交 Gate 2 评审。

