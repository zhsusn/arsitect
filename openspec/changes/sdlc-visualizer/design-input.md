# SDLC Visualizer — 设计输入文档

> **文档定位**：供 `high-level-design` Skill 直接消费的技术架构设计输入（Design Input）。
> **编制日期**：2026-06-01
> **目标读者**：AI 架构师（high-level-design Skill）
> **项目阶段**：概要设计（HLD）前置输入

---

## 1. 技术选型约束

| 组件 | 竞品主流方案 | 推荐方案 | 理由 | 置信度 |
|------|-------------|----------|------|--------|
| 前端框架 | Next.js (Dify)、Vue 3 (ChatDev DevAll)、React (CrewAI/LangGraph 生态) | **React 19 + Vite 6** | 团队对 React 生态最熟悉；React Flow 12 原生绑定 React；Vite 6 冷启动快、HMR 极致，适合本地单机工具场景；Next.js 对本地单机应用过重，SSR 无意义 | ⭐⭐⭐⭐⭐ |
| 状态管理 | Redux Toolkit / Zustand (Dify 用 Redux)、Pinia (Vue) | **Zustand 5** | 学习曲线极低、无样板代码、支持持久化中间件（localStorage/sessionStorage）、与 React 19 concurrent features 兼容性好；Redux 对单机工具过度工程化 | ⭐⭐⭐⭐⭐ |
| 画布引擎 | React Flow (Dify/LangGraph)、自定义 Canvas (CrewAI) | **React Flow 12** | 竞品已验证的拓扑图标准；支持节点/边自定义、布局引擎（@xyflow/elk）、子流程（Subflows）、内置 MiniMap/Controls；与 React 19 兼容；社区活跃 | ⭐⭐⭐⭐⭐ |
| 后端框架 | Flask (Dify/ChatDev)、FastAPI (DevAll) | **FastAPI 0.115** | Python 异步原生支持（uvloop + httptools）、自动 OpenAPI 文档生成、Pydantic 2 深度集成；Flask 同步模型在 CLI 流式输出场景下需额外线程管理 | ⭐⭐⭐⭐⭐ |
| ORM | SQLAlchemy 1.4 (Dify)、Django ORM | **SQLAlchemy 2.0** | 与 FastAPI + Pydantic 2 类型系统无缝衔接；声明式模型 + 异步 Session（AsyncSession）；2.0 版本 API 统一，避免 1.4 兼容层混乱 | ⭐⭐⭐⭐⭐ |
| 数据库 | PostgreSQL (Dify)、SQLite (CrewAI/LangGraph 轻量场景) | **SQLite (MVP)** | 本地单机零运维的核心诉求；无需独立进程、即开即用；10 Project 上限数据量极小；SQLAlchemy 2.0 支持 aiosqlite 异步驱动；未来可透明迁移至 PostgreSQL | ⭐⭐⭐⭐ |
| CLI 集成 | 自定义 Python SDK (OpenHands)、子进程调用 (ChatDev) | **Kimi CLI 子进程 + STDIO** | 项目定位明确绑定 Kimi CLI（MVP 阶段）；通过 Node.js `child_process` / Python `subprocess` 调用 Kimi CLI，捕获 STDOUT/STDERR 流；未来可通过 MCP 协议扩展 | ⭐⭐⭐⭐ |
| Git 操作 | PyGit2 (OpenHands)、GitPython (ChatDev)、isomorphic-git (JS) | **Node.js `simple-git` + 服务端 `GitPython`** | 前端展示层用 `simple-git`（轻量 Promise API）；后端复杂操作（diff/blame/history）用 `GitPython`；双端互补，避免单一库能力盲区 | ⭐⭐⭐⭐ |

---

## 2. 核心组件选型评分表

**评分权重**：扩展性 25% | 成本 20% | 团队熟悉度 20% | 生态成熟度 20% | 契合度 15%
**评分标准**：1~5 分，5 分为最优

| 组件类别 | 候选方案 | 扩展性 | 成本 | 团队熟悉度 | 生态成熟度 | 契合度 | 加权总分 | 推荐决策 |
|----------|---------|--------|------|-----------|-----------|--------|---------|---------|
| 前端框架 | React 19 + Vite 6 | 4 | 5 | 5 | 5 | 5 | **4.70** | ✅ 推荐 |
| 前端框架 | Next.js 14 | 5 | 3 | 3 | 5 | 2 | **3.80** | — |
| 前端框架 | Vue 3 + Vite | 4 | 5 | 3 | 5 | 3 | **4.10** | — |
| 状态管理 | Zustand 5 | 4 | 5 | 4 | 4 | 5 | **4.35** | ✅ 推荐 |
| 状态管理 | Redux Toolkit | 4 | 3 | 3 | 5 | 3 | **3.65** | — |
| 状态管理 | Jotai | 4 | 5 | 2 | 3 | 4 | **3.65** | — |
| 画布引擎 | React Flow 12 | 5 | 5 | 3 | 5 | 5 | **4.70** | ✅ 推荐 |
| 画布引擎 | AntV X6 | 4 | 4 | 2 | 3 | 3 | **3.35** | — |
| 画布引擎 | 自研 Canvas | 2 | 1 | 1 | 1 | 2 | **1.40** | ❌ 否决 |
| 后端框架 | FastAPI 0.115 | 5 | 5 | 4 | 5 | 5 | **4.80** | ✅ 推荐 |
| 后端框架 | Flask 2.x | 3 | 5 | 4 | 5 | 3 | **3.90** | — |
| 后端框架 | Django 5.x | 4 | 3 | 3 | 5 | 2 | **3.55** | — |
| ORM | SQLAlchemy 2.0 | 5 | 5 | 4 | 5 | 5 | **4.80** | ✅ 推荐 |
| ORM | Peewee | 2 | 5 | 2 | 3 | 3 | **2.90** | — |
| ORM | Prisma (Python 实验性) | 3 | 2 | 1 | 2 | 2 | **2.15** | ❌ 否决 |
| 数据库 | SQLite (MVP) | 2 | 5 | 5 | 5 | 5 | **4.15** | ✅ 推荐 (MVP) |
| 数据库 | PostgreSQL 16 | 5 | 3 | 4 | 5 | 3 | **4.10** | 未来迁移 |
| CLI 集成 | Kimi CLI STDIO | 3 | 5 | 4 | 3 | 5 | **3.80** | ✅ 推荐 (MVP) |
| CLI 集成 | Kimi MCP 协议 | 5 | 3 | 2 | 2 | 4 | **3.35** | 未来扩展 |
| Git 操作 | simple-git + GitPython | 4 | 5 | 4 | 4 | 4 | **4.20** | ✅ 推荐 |
| Git 操作 | isomorphic-git (纯 JS) | 3 | 5 | 2 | 3 | 3 | **3.25** | — |

---

## 3. 架构模式参考

| 模式 | 来源竞品 | 适用性 | 风险 |
|------|---------|--------|------|
| **事件溯源状态机** | OpenHands (模块化 SDK + 不可变配置) | 高 — Skill 执行编排天然适合事件流建模；每个 Gate 审批、节点状态变更均可事件化 | 事件存储增长快，SQLite 下需定期 compact；实现复杂度高于 CRUD |
| **图状态机 (Graph State Machine)** | LangGraph (条件边 + 并行执行) | 高 — SDLC 12 阶段链路本身就是有向图，React Flow 画布与图状态机同构 | 状态爆炸风险（阶段 × 门控 × 任务状态）；需定义清晰的快照/恢复机制 |
| **角色化 Agent 编排** | CrewAI (角色 + 任务 + 工具)、ChatDev (ChatChain) | 中 — 适合 Kimi CLI 侧的多 Skill 协作，但 Visualizer 本身是"编排器"而非"Agent" | 过度抽象可能增加认知负担；MVP 阶段建议扁平化执行器 |
| **插件化扩展架构** | Dify (120+ 插件 + MCP) | 中 — 长期需要支持多 CLI（Kimi / Claude / Cursor），但 MVP 仅 Kimi | 插件接口过早设计会导致 breaking change；建议预留接口，MVP 硬编码 Kimi 适配器 |
| **三阶段生命周期 (PocketFlow)** | Arsitect 自有规范 | 高 — 核心差异化卖点：Draft / Active / Archived 三态驱动所有产物 | 需确保所有 Skill 产出物都能映射到三态；状态转换需审计日志 |
| **瀑布模型流水线** | ChatDev (ChatChain) | 低 — 传统瀑布与 AI 辅助的快速迭代特性冲突 | 可能降低用户体验灵活性；不建议采纳 |

---

## 4. 接口设计约束

| 维度 | 竞品做法 | 建议 |
|------|---------|------|
| **API 风格** | Dify: REST + WebSocket (实时); ChatDev: REST + Socket.IO; OpenHands: 事件总线 | **RESTful HTTP + Server-Sent Events (SSE)** — SSE 比 WebSocket 更适合单向 CLI 流式输出（progress / log），实现简单、自动重连、与 HTTP 基础设施兼容；双向控制用 REST |
| **认证授权** | Dify: OAuth + API Key; ChatDev: Session Cookie; OpenHands: JWT | **本地单机免认证 (MVP)** — 无服务端多租户场景；如需扩展，采用简单的本地 token（如 UUID 存储于 localStorage） |
| **CLI 通信协议** | ChatDev: 子进程 stdio; OpenHands: 内部 SDK 调用; Dify: 外部服务集成 | **STDIO 管道 + 结构化 JSON 行 (JSON Lines)** — Kimi CLI 输出通过 `--format json` 或自定义解析器转为 JSON Lines；前后端通过 SSE 透传 |
| **文件系统访问** | OpenHands: DockerWorkspace 隔离; ChatDev: 直接文件系统 | **Node.js `fs` API (渲染进程) + FastAPI `UploadFile` (后端)** — Electron/Chromium 本地文件选择器 + 后端文件服务；避免过度封装，保持与本地开发环境一致 |
| **实时同步** | Dify: WebSocket broadcast; LangGraph: 状态订阅 | **Zustand 持久化中间件 + SSE 推送** — 前端状态为 SSOT，后端推送增量事件；离线场景下前端可独立运行（本地 SQLite 已同步） |
| **OpenAPI 契约** | Dify: 自动生成 Swagger; FastAPI 原生支持 | **强制要求 FastAPI 自动生成的 `/docs` 作为接口基线** — 所有前后端接口必须通过 Pydantic Schema 定义；接口变更时同步更新 frontend API client |

---

## 5. 数据模型参考

| 实体 | 竞品设计 | 本方案决策 |
|------|---------|-----------|
| **Project** | Dify: App (名称/模式/状态/配置); ChatDev: Project (仓库/角色/阶段) | `Project` — id, name, description, local_path, status (draft/active/archived), created_at, updated_at; **10 Project 上限在应用层 enforcement** |
| **Workflow / Chain** | LangGraph: Graph (nodes + edges + state_schema); CrewAI: Flow (tasks + agents); ChatDev: ChatChain (阶段序列) | `Workflow` — id, project_id, name, stages (JSON: 12 SDLC 阶段定义), react_flow_nodes, react_flow_edges, current_stage_id, status; **画布布局与业务逻辑解耦** |
| **Stage / Phase** | ChatDev: Phase (类型/角色/消息历史); OpenHands: Event (timestamp/action/source) | `Stage` — id, workflow_id, name, sdlc_phase (enum: 需求→监控), gate_status (pending/passed/rejected), input_artifacts (JSON), output_artifacts (JSON), ordering; **Gate 审批内嵌于 Stage** |
| **Skill Execution** | Dify: NodeExecution (状态/输入/输出/耗时); OpenHands: Action (action/args/observation) | `SkillExecution` — id, stage_id, skill_name (对应 .agents/skills/{name}), trigger_context (JSON), stdout_log (text), stderr_log (text), exit_code, started_at, ended_at, artifacts (JSON); **完整捕获 CLI 执行现场** |
| **Artifact** | Dify: 文档/知识库分段; OpenHands: 不可变配置快照 | `Artifact` — id, project_id, stage_id, artifact_type (spec/design/code/test/review), file_path, content_hash, version, status (draft/active/archived), created_at; **内容寻址 + 版本化** |
| **Human Decision** | Arsitect: human-decisions.md (审计日志) | `HumanDecision` — id, stage_id, gate_name (enum: Gate1/Gate2.5/Gate2/Gate3), decision (approve/reject/hold), comment, decided_by (用户标识), decided_at; **结构化审计，支持导出 Markdown** |
| **Code Review** | ChatDev: ReviewRecord (问题/修复/验证) | `CodeReview` — id, project_id, skill_execution_id, review_type (self/peer/auto), axis_scores (JSON: 五轴评分), issues (JSON array), fix_plan (JSON), status (open/fixed/verified); **与 Arsitect code-review-pipeline 对齐** |

---

## 6. 差异化空间（Blue Ocean ERRC 网格）

| 维度 | 剔除 (Eliminate) | 减少 (Reduce) | 提升 (Raise) | 创造 (Create) |
|------|-----------------|---------------|-------------|---------------|
| **部署与运维** | 服务器部署、Docker Compose、K8s 编排、云服务依赖 | 系统资源占用、第三方服务依赖数量、配置复杂度 | 开箱即用体验、5 分钟 onboarding、离线工作能力 | **本地单机零运维** 的完整工具链 |
| **协作模型** | 多租户 RBAC、团队权限矩阵、Org/Workspace 层级 | 用户角色种类（MVP 仅单超级个体）、审批流程层级 | 个人工作流自动化程度、AI 辅助密度、上下文连续性 | **"我 + AI" 的超级个体工作模式** 专用优化 |
| **功能广度** | 通用 Low-Code 平台、非 SDLC 流程（如 CRM/ERP） | 支持的 AI CLI 数量（MVP 仅 Kimi）、项目管理维度 | SDLC 12 阶段的覆盖深度、门控与审查的自动化衔接、产物一致性校验 | **PocketFlow 三态生命周期** 的可视化编排（Draft/Active/Archived） |
| **技术栈复杂度** | 微服务拆分、消息队列中间件、独立缓存层、反向代理 | 后端服务进程数、数据库运维负担、前端构建时间 | 技术栈现代度（React 19 / FastAPI 0.115 / Pydantic 2）、类型安全覆盖度 | **React Flow 画布与 SDLC 阶段** 的实时双向绑定（画布即架构） |
| **可视化深度** | 通用 BI 图表、3D 可视化、VR/AR | 非技术 stakeholder 的交互复杂度 | C4 模型浏览体验、代码审查 diff 可视化、UAT 证据链展示 | **C4 架构浏览器** 与 OpenUI/Wireframe 原型的同屏验证 |
| **生态锁定** | 强制云存储、强制 SaaS 订阅、专有模型绑定 | 对外部 API 的硬性依赖（本地_fallback 策略） | 与 Arsitect Skill 框架的紧密度、与 Kimi CLI 的集成深度 | **Arsitect 规范原生支持**：自动产出 OpenSpec 合规产物 |

---

## 7. 风险提示

| 风险 | 来源 | 观测指标 |
|------|------|---------|
| **React Flow 12 与 React 19 兼容性坑** | React 19 为全新 major 版本，React Flow 12 虽声明支持但边缘 case 未完全暴露 | 画布渲染异常率、节点拖拽卡顿、边连接失败率、控制台 warning 数量 |
| **Kimi CLI 输出格式不稳定** | Kimi CLI 为外部依赖，无正式机器可读协议承诺；--format json 为实验性 | CLI 解析失败率、JSON Lines 非法率、需要 fallback 正则解析的频率 |
| **SQLite 并发写瓶颈** | 本地单机但前后端分离，FastAPI 多 worker + 前端多标签页可能导致 WAL 锁竞争 | 500 错误中 `database is locked` 占比、API P99 延迟、写操作重试次数 |
| **Zustand 状态与后端数据漂移** | 前端 SSOT + 后端 SSE 推送的增量同步模型存在时序/丢包风险 | 前后端状态不一致用户反馈数、SSE 重连频率、页面刷新后状态恢复失败率 |
| **PocketFlow 三态迁移的破坏性** | Draft → Active 状态变更涉及产物格式/路径的固化，设计不当会导致数据丢失 | 状态迁移失败率、产物路径不一致报错、人工回滚请求次数 |
| **10 Project 上限的存储膨胀** | 每个 Project 包含完整 Git 历史 + 产物版本 + 执行日志，长期可能超磁盘预期 | 单 Project 平均体积、总存储占用增长率、SQLite 文件大小 |
| **C4 架构图与 React Flow 性能** | 大型系统 C4 L1-L4 节点量可能达数百，React Flow 渲染性能下降 | 节点数 >100 时的 FPS、首次渲染时间、布局计算耗时 |
| **MVP 后多 CLI 扩展的架构债** | 当前 Kimi CLI 硬编码适配，未来支持 Claude/Cursor 时需重构执行器层 | 新增 CLI 适配所需代码变更行数、接口 breaking change 数量 |

---

## 附录：关键假设与前提

1. **目标用户画像**：独立开发者（超级个体），具备全栈能力，习惯命令行工具，追求效率最大化。
2. **运行环境**：开发者本地 macOS / Windows / Linux 工作站，无远程服务器依赖。
3. **MVP 边界**：仅支持 Kimi CLI；仅支持本地 SQLite；仅支持单用户（无登录）；10 Project 硬上限。
4. **非功能性预设**：首屏加载 < 3s；画布交互延迟 < 50ms；CLI 命令端到端响应 < 5s（不含 AI 生成时间）。
5. **未来扩展窗口**：预留 PostgreSQL 迁移路径、预留 MCP 协议适配接口、预留多 CLI 抽象层。
