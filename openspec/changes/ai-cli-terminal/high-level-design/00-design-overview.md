---
doc_type: "ARCH"
fragment_id: "arch-ai-cli-terminal-000"
title: "AI CLI 终端 - 设计总览"
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
c4_binding:
  level: "L1"
  system: "ai-cli-terminal"
  actors: ["developer", "tech-lead", "architect"]
  external_systems: ["kimi-api", "git-provider"]
---

# AI CLI 终端 - 设计总览

## 1. 执行摘要 {#sec-executive-summary}

| 项目 | 内容 |
|------|------|
| **变更名称** | AI CLI 终端（AI CLI Terminal） |
| **设计范围** | 在 Arsitect 平台内嵌类终端交互页面，支持 Bug 修复与架构治理两种模式 |
| **核心架构** | 前端终端页 + WebSocket 网关 + CLI/Bug/Arch/Exec 四大服务 + AI Gateway + 统一存储 |
| **关键技术** | React 19 + xterm.js + python-socketio + FastAPI + SQLAlchemy 2.0 + SQLite/PostgreSQL |
| **关键决策** | 采用 WebSocket 替代 SSE 以支持双向流式交互；MVP 使用 SQLite，P1 迁移至 PostgreSQL |
| **目标状态** | 通过 Gate 2 评审后进入 detailed-design 与 interface-first-dev 阶段 |

## 2. 范围与边界 {#sec-scope}

### 2.1 In-Scope {#sec-in-scope}

- AI CLI 终端页面及其类终端交互体验。
- WebSocket 会话连接、消息路由与上下文保持。
- Bug 修复模式：异常解析、历史查询、AI 分析、修复方案卡片、用户确认、执行修复、记录保存。
- 架构治理模式：项目扫描、治理项列表、治理方案卡片、用户确认、执行重构、ADR 记录。
- CLI 会话、消息、Bug 记录、架构问题记录的数据持久化策略。
- 与 Kimi API 的流式集成，以及后续多 AI Provider 的扩展接口预留。

### 2.2 Out-of-Scope {#sec-out-of-scope}

- OCR 截图识别（P2 引入）。
- Docker 沙箱执行（P2 引入，MVP 使用临时 Git 工作区）。
- 自动 PR 创建与合并（P2 引入）。
- Claude/Cursor/GPT 等多 Provider 适配（P2 引入）。
- 复杂分布式架构治理（本期聚焦单仓库代码级坏味道）。

### 2.3 设计边界 {#sec-design-boundary}

| 维度 | 本期覆盖 | 本期不覆盖 |
|------|----------|------------|
| 系统分层 | 表现层、网关层、应用服务层、AI 适配层、存储层 | 模块内部类设计、具体 ORM 映射 |
| 数据定义 | 核心实体与关系、存储策略 | 字段类型、DDL、索引设计 |
| 通信协议 | WebSocket 消息类型与路由策略 | 具体消息 Schema、重连算法细节 |
| 部署 | 本地单体运行拓扑 | K8s、容器编排、CI/CD 流水线 |
| 安全 | 权限校验、沙箱执行、审计策略 | 具体鉴权实现、密钥管理 |

## 3. 术语与缩写 {#sec-terminology}

| 术语 | 定义 | 来源 |
|------|------|------|
| **AI CLI 终端** | 平台内嵌的类终端交互界面 | PRD-001 |
| **Bug 模式** | 针对代码异常修复的 CLI 工作模式 | PRD-001 |
| **Arch 模式** | 针对架构治理的 CLI 工作模式 | PRD-001 |
| **修复方案卡片** | 终端流中嵌入的可交互组件，展示 Diff 与操作按钮 | PRD-002 |
| **治理项卡片** | 终端流中嵌入的可交互组件，展示架构问题与治理方案 | PRD-002 |
| **CLI Service** | 负责会话管理与消息路由的应用服务 | 本设计 |
| **Bug Service** | 负责 Bug 分析、方案生成与执行的应用服务 | 本设计 |
| **Arch Service** | 负责架构扫描、治理方案与重构执行的应用服务 | 本设计 |
| **Exec Service** | 负责在临时工作区执行代码变更与验证的应用服务 | 本设计 |
| **AI Gateway** | 统一封装 Kimi API 调用与流式输出的适配层 | 本设计 |
| **WebSocket Gateway** | 前后端双向实时通信网关 | 本设计 |
| **ADR** | Architecture Decision Record，架构决策记录 | PRD-002 |
| **HITL** | Human-in-the-Loop，人工介入关键决策 | PRD-000 |

## 4. 参考资料 {#sec-references}

| 编号 | 文档 | 版本 | 用途 |
|------|------|------|------|
| REF-001 | `high-level-requirements/00-requirements-overview.md` | v1.0.0 | 产品范围、NFR、里程碑、风险 |
| REF-002 | `high-level-requirements/01-requirements-list.md` | v1.0.0 | 需求清单、业务规则、RTM |
| REF-003 | `high-level-requirements/02-functional-requirements.md` | v1.0.0 | 功能架构、用户旅程、状态机 |
| REF-004 | `docs/aicli.txt` | v1.0 | 原始设计输入与交互原型参考 |
| REF-005 | `openspec/config.yaml` | v2.1 | 阶段定义、门控规则、技术栈基线 |
| REF-006 | `AGENTS.md` | - | 项目整体架构与代码规范 |

## 5. 设计索引与检查清单 {#sec-design-index}

| 主题文件 | 核心决策点 | 风险等级 | 检查状态 |
|----------|------------|----------|----------|
| 01-architecture-core.md | 系统分层、服务划分、技术选型、C4 绑定 | 高 | 待评审 |
| 02-data-flow.md | Bug 修复与架构治理端到端数据流 | 高 | 待评审 |
| 03-runtime-behavior.md | 状态机、消息路由、流式输出、异常恢复 | 中 | 待评审 |
| 04-quality-attributes.md | 性能、安全、可维护、可观测策略 | 中 | 待评审 |
| 05-ops-governance.md | 部署拓扑、监控告警、回滚方案 | 中 | 待评审 |

## 6. 关键架构决策索引 {#sec-adr-index}

| 编号 | 决策 | 候选方案 | 选定方案 | 理由 |
|------|------|----------|----------|------|
| ADR-001 | 前后端实时通信协议 | SSE / WebSocket | WebSocket | 双向交互、卡片确认、命令回车场景更自然 |
| ADR-002 | MVP 数据库 | SQLite / PostgreSQL | SQLite | 与现有 Arsitect MVP 一致，零配置启动 |
| ADR-003 | 终端渲染引擎 | 自研 / xterm.js | xterm.js | 成熟稳定，支持 ANSI、自定义 Decoration、社区活跃 |
| ADR-004 | 执行沙箱 | Docker / 临时 Git 工作区 | 临时 Git 工作区 | 降低部署复杂度，P2 引入 Docker 沙箱 |

