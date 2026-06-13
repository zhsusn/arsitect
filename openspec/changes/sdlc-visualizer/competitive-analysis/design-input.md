# 设计输入 — 供 high-level-design Skill 消费

> 来源：`competitive-analysis.md`（technical 模式）
> 生成日期：2026-05-31
> 目标读者：`high-level-design` Skill

---

## 1. 技术选型约束

| 组件类别 | 竞品主流方案 | 推荐方案 | 理由 | 置信度 |
|----------|-------------|---------|------|--------|
| 前端框架 | Next.js (Dify), React (LangSmith) | **React 19 + Vite 6** | PRD 已锁定，Vite HMR 极速，React 19 并发特性利于画布性能 | H |
| 画布组件 | 自研 (Dify/LangGraph) | **React Flow 12** | 原生 React 集成，支持分组/泳道，TypeScript 友好，社区活跃 | H |
| 前端状态管理 | Redux (Dify), 无 (LangSmith) | **Zustand 5** | API 极简，无样板代码，适合画布+服务器状态分离 | H |
| 后端框架 | Flask (Dify), Python 库 (LangGraph/CrewAI) | **FastAPI 0.115** | PRD 已锁定，异步原生，Pydantic 集成，适合 subprocess 管理 | H |
| ORM | SQLAlchemy (Dify), 无直接 ORM | **SQLAlchemy 2.0** | PRD 已锁定，Mapped[] 类型注解，selectinload 解决 N+1 | H |
| 数据库（MVP） | PostgreSQL + Weaviate (Dify), SQLite/PostgreSQL (LangGraph) | **SQLite** | PRD 已锁定，零运维，10 并发项目上限内性能充足 | H |
| 数据库（P1+） | PostgreSQL | **PostgreSQL 15+** | PRD 演进路线已规划，支持高并发和复杂查询 | H |
| WS 服务端 | 未公开 (Dify), LangSmith 实时 | **python-socketio 5** | PRD 已锁定，Room 模型成熟，支持命名空间和广播 | M |
| AI 调用方式 | 多模型 API (Dify), LangChain 封装 (LangGraph/CrewAI) | **asyncio subprocess + Kimi CLI** | CLI 是唯一可行调用方式，asyncio 统一异步接口 | H |
| 产物存储 | 对象存储/数据库 BLOB (Dify), State 序列化 (LangGraph) | **本地文件系统** | 产物需被 IDE/Git 直接访问，openspec 目录兼容 | H |
| 进程管理 | 无（云端 API） | **asyncio + subprocess** | 标准库，统一 async 接口，适合 CLI 调用 | H |
| 可观测性 | LangSmith (LangGraph), Langfuse (CrewAI) | **自建指标 + SQLite 审计日志** | MVP 阶段不引入外部依赖，P1 评估 OpenTelemetry | M |
| 部署 | Docker/K8s/SaaS (Dify) | **本地单机可执行** | PRD 约束，零运维，P3 评估容器化 | H |

---

## 2. 核心组件选型评分表（汇总）

### 2.1 画布组件

| 候选方案 | 扩展性(25%) | 成本(20%) | 团队熟悉度(20%) | 生态成熟度(20%) | 契合度(15%) | 加权总分 | 决策 |
|----------|------------|-----------|----------------|----------------|------------|---------|------|
| React Flow 12 | 5 | 5 | 4 | 5 | 5 | **4.80** | ★ 推荐 |
| AntV X6 | 5 | 5 | 3 | 4 | 4 | 4.25 | 备选 |
| LogicFlow | 4 | 5 | 3 | 3 | 3 | 3.65 | 备选 |
| 自研 Canvas | 2 | 2 | 2 | 1 | 2 | 1.85 | 不推荐 |

### 2.2 前端状态管理

| 候选方案 | 扩展性 | 成本 | 熟悉度 | 成熟度 | 契合度 | 加权总分 | 决策 |
|----------|--------|------|--------|--------|--------|---------|------|
| Zustand 5 | 4 | 5 | 4 | 4 | 5 | **4.40** | ★ 推荐 |
| Redux Toolkit | 5 | 3 | 4 | 5 | 4 | 4.25 | 备选 |
| Jotai | 4 | 5 | 3 | 3 | 4 | 3.80 | 备选 |

### 2.3 数据库（MVP）

| 候选方案 | 扩展性 | 成本 | 熟悉度 | 成熟度 | 契合度 | 加权总分 | 决策 |
|----------|--------|------|--------|--------|--------|---------|------|
| SQLite | 2 | 5 | 5 | 5 | 5 | **4.10** | ★ 推荐（MVP） |
| PostgreSQL | 5 | 4 | 4 | 5 | 4 | 4.45 | ★ 推荐（P1+） |

### 2.4 CLI 调用方式

| 候选方案 | 扩展性 | 成本 | 熟悉度 | 成熟度 | 契合度 | 加权总分 | 决策 |
|----------|--------|------|--------|--------|--------|---------|------|
| asyncio subprocess | 3 | 5 | 5 | 5 | 5 | **4.55** | ★ 推荐 |
| HTTP API | 4 | 4 | 4 | 4 | 2 | 3.60 | 不推荐 |
| MCP 协议 | 4 | 3 | 2 | 2 | 3 | 2.90 | 未来（P3） |

### 2.5 产物存储

| 候选方案 | 扩展性 | 成本 | 熟悉度 | 成熟度 | 契合度 | 加权总分 | 决策 |
|----------|--------|------|--------|--------|--------|---------|------|
| 本地文件系统 | 2 | 5 | 5 | 5 | 5 | **4.10** | ★ 推荐 |
| SQLite BLOB | 3 | 5 | 4 | 4 | 2 | 3.55 | 不推荐 |
| MinIO | 5 | 3 | 3 | 4 | 3 | 3.80 | P2 评估 |

---

## 3. 架构模式参考

| 模式 | 来源竞品 | 描述 | 本系统适用性 | 风险 |
|------|---------|------|-------------|------|
| **BaaS + LLMOps** | Dify | 后端即服务 + 运维监控一体化 | 部分适用 — 本系统后端提供服务化 API，但不做模型管理 | 过度抽象可能增加复杂度 |
| **图状态机编排** | LangGraph | StateGraph 定义节点和边，State 在节点间传递 | 参考 — 本系统 YAML DAG 可视为简化版图模型，但不需要循环和递归 | 不宜直接引入 LangGraph，避免过度设计 |
| **事件驱动 Flow 编排** | CrewAI Flow | @start/@listen/@router 装饰器定义执行图 | 参考 — YAML 条件分支和并行调度逻辑相似 | CrewAI 的 Python 装饰器模型与本系统的声明式 YAML 有范式差异 |
| **Event-sourced Run Lifecycle** | JoySafeter | Run → Event → Snapshot 统一生命周期 | **高度适用** — 本系统 SkillExecution 可借鉴事件溯源模式记录执行轨迹 | 需平衡追溯完整性与存储成本 |
| **插件/扩展市场** | Dify v1.0 | 模型、工具、策略插件化 | 参考 — 本系统 Skill 动态注册是简化版插件机制 | MVP 阶段不需要完整插件市场 |
| **Checkpointer 状态持久化** | LangGraph | 任意步骤暂停/恢复，系统重启不丢失 | **部分适用** — 本系统异常恢复机制（孤儿进程扫描）可借鉴 | MVP 单机场景下 Checkpointer 优先级低 |
| **三级伪状态 + 增量监听** | 本系统原创 | 已触发/运行中/产物生成中 + chokidar 监听 | **核心创新** — 缓解 Kimi CLI 无实时中间状态的问题 | 若产物生成间隔 > 30s，用户体验仍可能受损 |

---

## 4. 接口设计约束

| 维度 | 竞品实践 | 本系统约束 |
|------|---------|-----------|
| **API 风格** | Dify: RESTful + WebSocket; LangGraph: Python 库调用 | **RESTful (FastAPI) + WebSocket (Socket.IO)** |
| **实时推送** | LangSmith: 追踪数据实时流式推送 | **WebSocket Room 模型**：项目级 Room，状态变更广播 |
| **产物访问** | Dify: API 下载; LangGraph: State 序列化 | **HTTP 静态文件服务 + Markdown/YAML 实时渲染** |
| **CLI 交互** | 无（均为库/服务调用） | **subprocess stdin/stdout/stderr 管道 + 退出码捕获** |
| **扩展接口** | Dify: 插件 API; LangGraph: 自定义 Node | **Skill 注册接口**：目录路径 + Frontmatter 解析 |
| **错误处理** | 各平台有统一的异常封装 | **CLI 退出码映射 + stderr 正则提取 + 超时熔断** |

---

## 5. 数据模型参考

### 5.1 竞品模型借鉴

| 本系统实体 | 借鉴来源 | 借鉴点 | 差异化 |
|-----------|---------|--------|--------|
| **Project** | Dify App | 顶层容器概念 | 增加 Draft/Active 双态和规模等级 |
| **Phase** | CrewAI Flow Step | 里程碑/阶段概念 | CrewAI 的 Flow 是通用步骤，本系统的 Phase 是 SDLC 特定语义（Clarify/Align/Contract/Build/Verify/Release） |
| **SkillExecution** | LangGraph Thread + Node | 执行实例 + 节点状态 | LangGraph 的 Thread 是图执行上下文，本系统的 SkillExecution 是单 Skill 调用实例，更轻量 |
| **Artifact** | Dify Document | 产物/文档概念 | Dify 的 Document 用于 RAG，本系统的 Artifact 是 SDLC 产物，需多模态渲染 |
| **HITLRecord** | CrewAI Feedback Pause | 人工干预记录 | CrewAI 是简单的 feedback，本系统是结构化 Gate 审批（摘要/决策/评语/时间戳） |
| **TracingSpan** | LangGraph Trace + JoySafeter Trace | 执行链路追踪 | 本系统追踪 Kimi CLI 进程级调用，非 LLM API 调用级追踪 |

### 5.2 关键设计决策

| 决策 | 推荐方案 | 理由 |
|------|---------|------|
| 项目级状态与节点级状态分离 | **双轨状态机** | 项目状态（Draft→Active→Completed）生命周期长、变更少；节点状态（IN_PROGRESS→BLOCKED）变化频繁。分离降低锁竞争和并发冲突 |
| 产物元数据与产物内容分离 | **SQLite 存元数据 + 文件系统存内容** | 元数据（路径、哈希、创建时间）适合关系查询；内容（Markdown/YAML）适合文件系统直接访问 |
| Skill 定义静态化 | **SKILL.md Frontmatter + meta.json** | 运行时只读解析，不写入。Skill 版本变更通过重新导入实现 |
| Gate 审批记录独立表 | **HITLRecord 实体** | 审计需求，需长期保留，独立表避免与 ExecutionLog 混淆 |

---

## 6. 差异化空间（Blue Ocean ERRC）

| 维度 | 动作 | 具体内容 |
|------|------|----------|
| **Eliminate（剔除）** | 剔除多人会签 | 竞品（Dify 无，CrewAI 有简单 feedback）均未覆盖；本系统聚焦超级个体，取消传统 RACI 会签，改为 AI 摘要 + 单人快速确认 |
| **Eliminate（剔除）** | 剔除 LLM 模型管理 | Dify/LangGraph/CrewAI 均内置多模型支持；本系统不管理模型，只调用 Kimi CLI，降低复杂度 |
| **Reduce（减少）** | 减少配置复杂度 | Dify 的低代码画布需要大量节点配置；本系统的 Skill Flow 基于 YAML 模板，标准 SDLC 模板开箱即用 |
| **Reduce（减少）** | 减少通用 AI 编排抽象 | LangGraph 的图状态机强大但学习曲线陡；本系统只做 SDLC 特定的 DAG 调度，无循环/递归 |
| **Raise（提升）** | 提升软件工程纪律可视化深度 | 竞品均无 Draft/Active 双态、四道 Gate、产物基线化、Stale 传播等软件工程概念 |
| **Raise（提升）** | 提升产物阅读体验 | 竞品产物浏览体验差（Dify 是对话历史，LangGraph 是 JSON State）；本系统提供 Markdown/Mermaid/Swagger 多模态渲染 |
| **Create（创造）** | 创造 AI 辅助开发全生命周期管理 | 从需求探索到线上监控的端到端可视化，产物版本追溯，历史项目分析 |
| **Create（创造）** | 创造自检确认模式 | AI 自动生成 Gate 摘要（风险点 + 待补充项），用户 30 秒内完成确认，非传统人工审查 |

---

## 7. 风险提示

| 风险 ID | 风险描述 | 来源竞品/趋势 | 观测指标 | 缓解策略 |
|---------|---------|--------------|----------|----------|
| CA-R001 | Dify 增加项目模板和审批节点，进入 SDLC 管理领域 | Dify 产品演进 | Dify 发布日志中出现 "project template" / "approval" 关键词 | 加速 SDLC 语义层深度建设，建立品类心智 |
| CA-R002 | Cursor/Windsurf 内置 AI 开发进度面板 | IDE 演进 | IDE 更新日志中出现 "AI project tracking" / "SDLC visualization" | 强化 Arsitect 规范社区影响力，成为 IDE 插件的数据源标准 |
| CA-R003 | Kimi CLI 官方推出 Web UI | Moonshot AI | Kimi CLI 发布 Web 端或桌面端 | 聚焦差异化（Gate 审批、产物管理、历史分析），不与官方工具竞争基础功能 |
| CA-R004 | LangGraph Checkpointer 模式被本系统误用导致过度设计 | 技术选型 | 概要设计文档中出现"引入 LangGraph 作为编排引擎" | 明确约束：本系统为传统 Web 应用 + 外部 AI 工具代理，不引入 Agent 框架 |
| CA-R005 | React Flow 12 在 50+ 节点场景下性能不足 | 技术实现 | 性能测试帧率 < 30fps | 预研虚拟滚动 + 节点懒加载，或降级为列表视图 |
| CA-R006 | SQLite 在并发写入场景下成为瓶颈 | 技术实现 | 10 并发项目下 WAL 模式锁等待 > 500ms | P1 前完成 PostgreSQL 迁移方案设计 |

---

## 8. 下游衔接说明

本文件由 `competitive-analysis` Skill（mode=technical）生成，供 `high-level-design` Skill 直接消费。

`high-level-design` 使用本文件时应注意：
1. **技术选型约束表** 中的方案已获 PRD 锁定或竞品分析验证，如无充分理由不建议推翻。
2. **架构模式参考** 中的"参考"和"部分适用"项需根据 MVP 资源约束判断是否引入，禁止过度设计。
3. **风险提示** 中的 CA-R004 是硬性约束：本系统不引入 LangGraph/CrewAI/Dify 等 Agent 框架作为编排引擎。
4. **数据模型参考** 中的差异化设计点需在 `high-level-design/01-architecture-core.md` 中明确体现。
