---
doc_type: "DETAIL_DESIGN"
fragment_id: "dd-ai-cli-terminal-000"
title: "AI CLI 终端 - 详细设计索引"
version: "1.0.0"
status: "DRAFT"
iteration: "ai-cli-terminal"
dependencies:
  - fragment_id: "prd-ai-cli-terminal-002"
    version: "1.0.0"
c4_binding:
  level: "L2"
  container: "ai-cli-terminal"
  components:
    - "cli-session"
    - "bug-fix"
    - "arch-governance"
    - "shared-services"
---

# AI CLI 终端 - 详细设计索引 {#sec-index}

## 1. 设计目标 {#sec-goals}

本详细设计将 `ai-cli-terminal` 变更的高层级需求与技术约束转化为可直接指导编码实现的模块级设计，覆盖 CLI 会话、Bug 修复、架构治理三个核心模块及其共享基础设施。

## 2. 模块清单 {#sec-modules}

| 模块 | 目录 | 设计文件 | API 文件 | 对应需求 |
|------|------|----------|----------|----------|
| CLI 会话管理 | `feature-01-cli-session/` | `design.md` | `api-spec.md` | REQ-P0-001, US-001 |
| Bug 修复 | `feature-02-bug-fix/` | `design.md` | `api-spec.md` | REQ-P0-002, REQ-P0-003, US-002, US-003 |
| 架构治理 | `feature-03-arch-governance/` | `design.md` | `api-spec.md` | REQ-P0-004, REQ-P0-005, US-004, US-005 |
| 共享基础设施 | `shared/` | `design.md`, `db-schema.md`, `page-design.md` | `api-spec.md` | 跨模块复用 |

## 3. 阅读路线 {#sec-reading-path}

1. 先阅读 `shared/db-schema.md` 与 `shared/design.md`，理解公共数据模型与服务边界。
2. 再阅读 `feature-01-cli-session/design.md`，掌握会话生命周期与 WebSocket 网关设计。
3. 接着阅读 `feature-02-bug-fix/design.md` 与 `feature-03-arch-governance/design.md`，分别理解两条业务链路。
4. API 契约以各模块 `api-spec.md` 与 `shared/api-spec.md` 为准，后续接口优先开发需以此冻结。

## 4. 关键设计决策 {#sec-key-decisions}

| 决策 | 选择 | 原因 |
|------|------|------|
| 通信协议 | WebSocket（原生 `websockets` 库） | 双向流式交互、心跳简单、与 FastAPI 原生兼容 |
| 终端组件 | xterm.js + xterm-addon-fit + xterm-addon-web-links | 开发者心智模型成熟，支持 ANSI 与自定义 Decoration |
| 数据存储 | SQLite（MVP），预留 PostgreSQL 迁移 | 零配置启动，后期仅切换连接串 |
| 会话 ID | 服务端生成 `CLI-{uuid4}` | 可读性与全局唯一性兼顾 |
| 执行隔离 | 临时 Git 工作区（MVP） | 不直接修改用户原仓库，回滚成本低 |

## 5. 术语统一 {#sec-terminology}

| 术语 | 定义 |
|------|------|
| Session | AI CLI 一次终端会话 |
| Message | 终端内一条流式或持久化消息 |
| Card | 嵌入终端流的交互式 HTML 组件 |
| FixPlan | Bug 修复方案，含 Diff 与风险评级 |
| ArchPlan | 架构治理方案，含影响面与重构步骤 |
| ExecResult | 执行引擎返回的验证结果 |
