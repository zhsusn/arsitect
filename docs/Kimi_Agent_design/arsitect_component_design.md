# Arsitect 平台 — 基础组件设计方案

> 基于 AI Code v3.2 PRD、C4 平台设计文档、Sketch 设计思路、架构核心文档、数据流文档、需求规格书等 9 份材料的系统性分析

---

## 一、产品全景理解

### 1.1 产品定位

Arsitect 是一个 **AI-Native 软件研发全生命周期管理平台**，面向"超级个体"（独立开发者/全栈自由职业者）和小型团队，将 AI Skill 编排执行、C4 架构治理、产物管理、HITL 人工审批融为一体的可视化驾驶舱。

### 1.2 核心创新点

| 创新点 | 描述 |
|--------|------|
| **Draft/Active 双态模型** | 预立项轻量分析 → 正式执行完整流程，降低项目启动门槛 |
| **复杂度路由** | 五维度评估自动分流 Trivial/Light/Standard/Deep 四级路径 |
| **PocketFlow 三阶段执行** | prep → exec → post 标准化 Skill 生命周期，统一所有 Skill 行为 |
| **C4 Architecture as Code** | 架构设计唯一真相源，自动正向渲染 + 反向代码定位 |
| **产物审查迭代** | REVIEW_PENDING → 行内批注 → 重新生成 → diff 对比 |
| **渐进式冻结** | 前期鼓励推翻，后期基线化 + Stale 传播 |
| **同源双渲染** | 一份源数据驱动两个渲染引擎（架构图 + 交互原型），避免信息不同步 |
| **旅程画布** | 无边际空间，项目本身就是白板，双箭头 = 业务流程+数据流向 |

### 1.3 技术栈（从材料提取）

**前端**：React 19 + Vite 6 + Zustand 5 + React Flow 12
**后端**：FastAPI 0.115 + SQLAlchemy 2.0 + Pydantic 2
**数据**：SQLite(MVP) → PostgreSQL(P1)，文件系统 + Git 快照
**AI 执行**：Kimi CLI（子进程 STDIO）+ PocketFlow 执行引擎
**MVP 规模**：前端 ~7,500 行，后端 ~6,000 行，50 个独立组件

---

## 二、基础能力分析（从需求推导）

### 2.1 第一层：核心执行能力

| 能力名称 | 需求来源 | 能力描述 |
|----------|----------|----------|
| **Skill 编排执行** | REQ-P0-006, BR-016 | 一键调用 Kimi CLI，注入输入产物，捕获输出和日志，遵循 PocketFlow prep-exec-post 三阶段 |
| **DAG 调度引擎** | REQ-P0-014, BR-018 | YAML 驱动 DAG 构建、拓扑排序、并行调度（模块内无依赖 Skill 并行）、条件分支、错误处理 |
| **状态机管理** | REQ-P0-007, §6.2 状态机 | Skill 级 9 状态 + Project 级 4 状态 + Artifact 级 4 状态，状态变更事件驱动 |
| **HITL 人工审批** | REQ-P0-008~009, BR-009 | Gate 自检摘要、快速确认/驳回/重试、旁路审批、历史追溯 |

### 2.2 第二层：数据与产物管理能力

| 能力名称 | 需求来源 | 能力描述 |
|----------|----------|----------|
| **产物多模态渲染** | REQ-P0-010 | Markdown/Mermaid/Swagger/YAML/JSON 格式渲染与预览 |
| **产物编辑与冲突检测** | REQ-P0-011, BR-006 | 平台内编辑产物，保存时检测外部变更冲突（哈希校验） |
| **产物版本管理** | REQ-P0-012 | Git 快照自动提交、版本历史、diff 对比、一键回滚 |
| **产物审查迭代** | REQ-P0-034~038 | 行内批注、全局修改建议、参考资料注入、基于反馈重新生成 |
| **文件系统监听** | R-006 缓解策略 | watchdog 监听产物目录变更，检测外部修改触发 STALE 状态 |

### 2.3 第三层：架构治理能力

| 能力名称 | 需求来源 | 能力描述 |
|----------|----------|----------|
| **C4 DSL 管理** | REQ-P0-019~021 | 自动生成 L1/L2/L3/L4 DSL、手动编辑覆盖、层级穿透下钻 |
| **C4 正向渲染** | REQ-P0-019 | DSL → Mermaid/SVG 架构图渲染 |
| **C4 反向定位** | REQ-P0-033 | Component/Code 级节点 → 本地代码文件定位 |
| **架构漂移检测** | REQ-P1-005~006 | 设计架构 vs 实际代码扫描架构对比（P1） |
| **线框图生成** | REQ-P0-030~031 | DomainMapper → LayoutPlanner → NavigationLinker 三阶段流水线 |
| **原型验证** | REQ-P0-028~029 | OpenUI 提示词生成与服务调用、可交互原型预览 |
| **原型-架构双向绑定** | REQ-P0-032 | 接口缺失检测、一键回写 C4 DSL |
| **需求草图生成** | REQ-P0-040 | PageSpec 规则解析、低保真草图生成 |

### 2.4 第四层：项目治理能力

| 能力名称           | 需求来源                   | 能力描述                                                    |
| -------------- | ---------------------- | ------------------------------------------------------- |
| **项目双态管理**     | REQ-P0-001, BR-001~003 | Draft/Active/Archived/Cancelled 状态流转，Draft 仅允许分析型 Skill |
| **复杂度路由**      | REQ-P0-016, REQ-P0-018 | 五维度规模评估（Triage/Calibrate）、四级路径可视化对比、人工覆盖                |
| **模板引擎**       | REQ-P0-002, BR-004     | Trivial/Light/Standard/Deep 四级模板管理、弱关联、偏离记录             |
| **Timebox 管理** | REQ-P0-017             | 里程碑时间盒配置、到期预警、超时处理                                      |
| **范围锚定**       | BR-019                 | 模块清单锁定、新增模块触发重估、Stale 传播                                |
| **Skill 注册管理** | REQ-P0-013~015         | 手动导入、Frontmatter 解析、DAG 自动解析 + 手动调整                     |

### 2.5 第五层：可视化与交互能力

| 能力名称 | 需求来源 | 能力描述 |
|----------|----------|----------|
| **拓扑画布** | REQ-P0-003~005 | 动态渲染 Skill 节点和依赖连线、缩放/拖拽/筛选、三视图切换 |
| **阶段详情面板** | REQ-P0-039 | 右侧面板展示 Skill 快照、产物、日志、质量门禁、审查 Tab |
| **审批中心** | REQ-P0-008~009 | 待确认队列、AI 自检摘要、快速确认/驳回/重试 |
| **历史回溯** | REQ-P1-001~003 | 已完成项目时间线、阶段耗时对比、返工热力图（P1） |
| **实时推送** | REQ-P0-007 | WebSocket/SSE 推送状态变更、Gate 等待通知 |

### 2.6 第六层：基础设施能力

| 能力名称 | 需求来源 | 能力描述 |
|----------|----------|----------|
| **数据库访问** | ASM-005 | SQLAlchemy ORM、SQLite → PostgreSQL 迁移兼容 |
| **Git 集成** | REQ-P0-012 | GitPython 封装、产物自动提交、diff/历史查询 |
| **CLI 适配** | ADR-004 | 抽象 CLIAdapter，当前 KimiCLIAdapter，预留 MCPAdapter |
| **配置管理** | — | 环境配置、全局参数、模板配置 |
| **日志与审计** | — | 结构化日志、Gate 决策审计、human-decisions.md |
| **降级与容错** | A-004 | OpenUI 不可用时 Wireframe 降级、CLI 失败重试 |



---

## 三、基础组件清单

### 3.1 执行引擎域

| 组件名称 | 职责 | 对应能力 | 优先级 |
|----------|------|----------|--------|
| **PocketFlowEngine** | Skill 执行三阶段编排（prep→exec→post），子进程生命周期管理，输入注入，输出捕获，日志收集 | Skill 编排执行 | P0 |
| **DAGScheduler** | YAML DAG 解析、拓扑排序、并行调度、条件评估、超时监控、错误处理 | DAG 调度引擎 | P0 |
| **StateMachineManager** | Skill/Project/Artifact 三级状态机定义、状态流转校验、事件驱动 | 状态机管理 | P0 |
| **GateController** | Gate 等待队列管理、AI 自检摘要触发、审批决策记录、旁路审批授权 | HITL 人工审批 | P0 |

### 3.2 产物管理域

| 组件名称 | 职责 | 对应能力 | 优先级 |
|----------|------|----------|--------|
| **ArtifactRenderer** | Markdown(react-markdown)/Mermaid(mermaid.js)/Swagger(swagger-ui)/YAML/JSON 多模态渲染 | 产物多模态渲染 | P0 |
| **ArtifactEditor** | 平台内产物编辑、保存时外部哈希校验、冲突检测弹窗 | 产物编辑与冲突检测 | P0 |
| **ArtifactVersionManager** | Git 快照自动提交、版本历史列表、diff 对比、一键回滚 | 产物版本管理 | P0 |
| **ReviewManager** | 行内批注存储、全局修改建议、参考资料注入、重新生成触发 | 产物审查迭代 | P0 |
| **FileSystemWatcher** | watchdog 监听产物目录、文件变更事件、STALE 状态标记 | 文件系统监听 | P0 |

### 3.3 架构治理域

| 组件名称 | 职责 | 对应能力 | 优先级 |
|----------|------|----------|--------|
| **C4DSLManager** | C4 DSL 文件的读写、版本管理、手动编辑覆盖标记 | C4 DSL 管理 | P0 |
| **C4AutoGenerator** | 解析概要设计文档，自动生成 L1/L2/L3/L4 DSL | C4 DSL 管理 | P0 |
| **C4Renderer** | DSL → Mermaid/SVG 渲染、层级穿透下钻、面包屑导航 | C4 正向渲染 | P0 |
| **C4ReverseLocator** | Component/Code 节点 → 本地代码文件路径映射 | C4 反向定位 | P0 |
| **DriftDetector** | 设计架构 vs 实际架构对比、差异报告生成（P1） | 架构漂移检测 | P1 |
| **WireframeEngine** | DomainMapper→LayoutPlanner→NavigationLinker 三阶段线框生成 | 线框图生成 | P0 |
| **OpenUIClient** | OpenUI Docker HTTP API 调用、提示词组装、HTML 原型获取 | 原型验证 | P0 |
| **PrototypeArchBinder** | 原型接口缺失检测、C4 DSL 自动回写、变更标记 | 原型-架构双向绑定 | P0 |
| **SketchGenerator** | PageSpec 规则解析、低保真草图 HTML 生成（同源双渲染） | 需求草图生成 | P0 |
| **JourneyCanvasEngine** | 旅程画布布局计算、节点/边渲染、页面层级关系管理 | 需求草图生成 | P0 |

### 3.4 项目治理域

| 组件名称 | 职责 | 对应能力 | 优先级 |
|----------|------|----------|--------|
| **ProjectGovernance** | Project CRUD、Draft/Active 状态流转、7天自动清理 | 项目双态管理 | P0 |
| **ComplexityRouter** | 五维度信号采集、Triage/Calibrate 评估、四级路径推荐 | 复杂度路由 | P0 |
| **TemplateEngine** | 四级模板定义、阶段-Skill 绑定推荐、偏离记录 | 模板引擎 | P0 |
| **TimeboxManager** | 里程碑时间盒设置、到期预警、超时处理 | Timebox 管理 | P0 |
| **ScopeAnchor** | 模块清单锁定、新增触发重估、Stale 传播计算 | 范围锚定 | P0 |
| **SkillRegistry** | Skill 导入、Frontmatter 解析、DAG 边自动提取、手动调整 | Skill 注册管理 | P0 |

### 3.5 可视化域

| 组件名称 | 职责 | 对应能力 | 优先级 |
|----------|------|----------|--------|
| **FlowCanvas** | React Flow 封装、拓扑图/泳道/列表三视图、节点状态着色 | 拓扑画布 | P0 |
| **StageDetailPanel** | 右侧滑出面板、Skill 快照/产物/日志/审查 Tab 展示 | 阶段详情面板 | P0 |
| **GateCenter** | 审批浮层、待审队列、AI 摘要展示、快速操作 | 审批中心 | P0 |
| **HistoryViewer** | 时间线渲染、阶段耗时对比图表、返工热力图（P1） | 历史回溯 | P1 |
| **RealtimePush** | SSE 连接管理、状态变更推送、Gate 通知 | 实时推送 | P0 |

### 3.6 基础设施域

| 组件名称 | 职责 | 对应能力 | 优先级 |
|----------|------|----------|--------|
| **DatabaseAdapter** | SQLAlchemy ORM 封装、AsyncSession 管理、数据库迁移兼容 | 数据库访问 | P0 |
| **GitAdapter** | GitPython 封装、自动 commit、diff/history 查询 | Git 集成 | P0 |
| **CLIAdapter** | 抽象 CLI 适配器、KimiCLIAdapter 实现、MCPAdapter 预留接口 | CLI 适配 | P0 |
| **ConfigManager** | 环境变量/配置文件管理、全局参数热加载 | 配置管理 | P0 |
| **AuditLogger** | 结构化审计日志、human-decisions.md 写入、Gate 决策记录 | 日志与审计 | P0 |
| **FallbackManager** | 服务降级策略（OpenUI→Wireframe）、重试退避、断路器 | 降级与容错 | P0 |

---

## 四、开源方案调研与选型

### 4.1 调研方法说明

针对每个组件，调研开源生态中的成熟方案，评估维度：
- **功能匹配度**：是否满足业务需求
- **生态成熟度**：社区活跃度、文档质量、GitHub Stars
- **集成难度**：与现有技术栈（React 19 + FastAPI）的兼容
- **扩展性**：是否支持未来需求演进
- **维护成本**：学习曲线、部署复杂度

### 4.2 调研结果汇总

#### (1) DAG 调度引擎 / 工作流编排

| 方案 | Stars | 核心定位 | 功能匹配 | 集成难度 | 评估结论 |
|------|-------|----------|----------|----------|----------|
| **自研调度器** | — | 为 Arsitect 量身定制 | ★★★★★ | ★★★★☆ | **推荐**：MVP 阶段自研更轻量 |
| LangGraph | 30K+ | AI Agent 图编排 + 持久化 | ★★★★☆ | ★★★☆☆ | HITL/Checkpointer 非常成熟，但过于重量 |
| Prefect | 25K+ | 数据工作流编排 | ★★★☆☆ | ★★★☆☆ | Python-native DAG，但面向数据管道 |
| Celery | 25K+ | 分布式任务队列 | ★★★☆☆ | ★★☆☆☆ | 复杂度过高，需要 Broker |
| RQ | 9.9K | 轻量 Redis 队列 | ★★★☆☆ | ★★★★☆ | 轻量但功能有限 |
| Airflow | 50K+ | 企业级批处理调度 | ★★☆☆☆ | ★☆☆☆☆ | 太重，不适合单机 |

> **结论**：Arsitect 的 DAG 调度具有独特业务语义（PocketFlow 三阶段、Gate 审批、产物驱动），通用引擎难以直接满足。MVP 阶段**自研轻量调度器**，P1 阶段可引入 LangGraph 的 Checkpointer 思想增强持久化能力。

#### (2) 状态机管理

| 方案 | 定位 | 功能匹配 | 评估结论 |
|------|------|----------|----------|
| **自研 + SQLAlchemy** | 数据库级状态持久化 | ★★★★★ | **推荐**：状态与业务强耦合，自研更灵活 |
| `python-transitions` | 通用状态机库 | ★★★★☆ | 支持 HierarchicalGraphMachine，但异步支持弱 |
| `vention-state-machine` | transitions 的异步包装 | ★★★★☆ | 基于 HierarchicalGraphMachine，支持恢复、超时 |
| XState (JS) | 前端状态机 | ★★★☆☆ | 前端状态机不适合后端业务 |

> **结论**：Skill 级 9 状态 + Project 级 4 状态 + Artifact 级 4 状态构成复杂状态矩阵，通用状态机难以表达跨实体状态传播。采用**自研状态管理**，配合 SQLAlchemy 事务保证持久化。

#### (3) 产物多模态渲染（前端）

| 方案 | 用途 | 功能匹配 | 评估结论 |
|------|------|----------|----------|
| **react-markdown + remark-gfm** | Markdown 渲染 | ★★★★★ | **推荐**：React 生态标准方案 |
| **mermaid.js** | Mermaid 图表渲染 | ★★★★★ | **推荐**：C4 DSL 默认渲染方式 |
| **@mermaid-js/mermaid-cli** | Mermaid 服务端渲染 | ★★★★☆ | 用于后端生成静态 SVG |
| **swagger-ui-react** | OpenAPI 文档渲染 | ★★★★★ | **推荐**：Swagger 文档可视化 |
| **react-json-view** / **@microlink/json-view** | JSON 渲染 | ★★★★★ | **推荐**：JSON 折叠/复制 |
| **@stoplight/json-schema-viewer** | JSON Schema 渲染 | ★★★★☆ | OpenAPI schema 展示 |

> **结论**：各格式使用对应生态标准库组合，通过统一的 **ArtifactRenderer** 组件封装。

#### (4) 文件系统监听

| 方案 | 定位 | 功能匹配 | 评估结论 |
|------|------|----------|----------|
| **watchdog** | Python 跨平台文件监控 | ★★★★★ | **推荐**：业界标准，支持 inotify/FSEvents/ReadDirectoryChangesW |
| `watchfiles` (Rust) | 高性能文件监控 | ★★★★☆ | uvicorn 内置，但纯监控场景不如 watchdog 灵活 |

> **结论**：使用 **watchdog**，跨平台一致性好，Observer + EventHandler 模式与 Arsitect 事件驱动架构契合。

#### (5) C4 架构工具链

| 方案 | 定位 | 功能匹配 | 评估结论 |
|------|------|----------|----------|
| **Structurizr DSL** | C4 官方 DSL | ★★★★★ | **参考标准**：DSL 语法设计参考 |
| **Structurizr Lite** | C4 本地渲染 | ★★★★☆ | Docker 运行，可作为验证参考 |
| **mermaid.js** | Mermaid C4 插件 | ★★★★★ | **推荐**：实际渲染方案 |
| **C4-PlantUML** | PlantUML C4 扩展 | ★★★☆☆ | 可选渲染后端 |
| **自研 C4DSLManager** | 自定义 DSL 管理 | ★★★★★ | **必须自研**：需要支持 DSL 与架构图双向绑定 |

> **结论**：DSL 语法参考 Structurizr，渲染使用 Mermaid，管理层自研实现双向绑定。

#### (6) Git 集成

| 方案 | 定位 | 功能匹配 | 评估结论 |
|------|------|----------|----------|
| **GitPython** | Python Git 操作封装 | ★★★★★ | **推荐**：功能完整，API 直观 |
| **dulwich** | 纯 Python Git 实现 | ★★★★☆ | 无 git 依赖，但功能有限 |
| **pygit2** | libgit2 绑定 | ★★★★☆ | 高性能，但安装复杂 |

> **结论**：使用 **GitPython**，功能完整且文档丰富。MVP 阶段完全满足，P1 如性能瓶颈可迁移至 pygit2。

#### (7) 实时推送

| 方案 | 定位 | 功能匹配 | 评估结论 |
|------|------|----------|----------|
| **SSE (Server-Sent Events)** | 单向服务器推送 | ★★★★★ | **推荐**：单向推送足够，HTTP 兼容，无额外协议 |
| **WebSocket** | 双向实时通信 | ★★★★☆ | 过重，客户端无需向服务器推送 |
| **Long Polling** | 兼容降级方案 | ★★★☆☆ | 可作为 SSE 不可用的降级 |

> **结论**：使用 **SSE (FastAPI StreamingResponse)**，足够满足状态变更推送需求。

#### (8) 任务调度（Timebox 预警）

| 方案 | 定位 | 功能匹配 | 评估结论 |
|------|------|----------|----------|
| **APScheduler** | Python 任务调度 | ★★★★★ | **推荐**：AsyncIO 原生支持，内存/数据库存储 |
| `asyncio.Task` | 原生异步任务 | ★★★☆☆ | 无持久化，重启丢失 |
| Celery Beat | 定时任务 | ★★★☆☆ | 过重，需要 Broker |

> **结论**：使用 **APScheduler (AsyncIOScheduler)**，轻量且支持持久化。

#### (9) 拓扑画布自动布局

| 方案 | 定位 | 功能匹配 | 评估结论 |
|------|------|----------|----------|
| **@xyflow/layout (dagre)** | React Flow 官方布局 | ★★★★★ | **推荐**：官方维护，DAG 布局 |
| **ELK (eclipse-layout-kernel)** | 专业图布局算法 | ★★★★★ | 布局质量最高，但集成复杂 |
| **@xyflow/layout (elkjs)** | React Flow ELK 封装 | ★★★★★ | **推荐**：质量与易用平衡 |

> **结论**：MVP 使用 **dagre**（简单快速），P1 引入 **elkjs**（更专业布局）。

### 4.3 技术选型总览

| 组件 | 选型方案 | 关键依赖 |
|------|----------|----------|
| DAGScheduler | **自研** | asyncio, topological-sort |
| StateMachineManager | **自研** | SQLAlchemy, asyncio.Event |
| PocketFlowEngine | **自研** | asyncio.subprocess, aioshutil |
| ArtifactRenderer | **组合方案** | react-markdown, mermaid, swagger-ui-react |
| ArtifactVersionManager | **GitPython** | gitpython, Git CLI |
| FileSystemWatcher | **watchdog** | watchdog |
| C4DSLManager | **自研** | pyyaml, jinja2 |
| C4Renderer | **mermaid.js** | @mermaid-js/mermaid |
| FlowCanvas 布局 | **dagre → elkjs** | dagre / elkjs |
| RealtimePush | **SSE** | FastAPI StreamingResponse |
| TimeboxManager | **APScheduler** | apscheduler |
| GateController | **自研** | 状态机 + SSE |
| DatabaseAdapter | **SQLAlchemy 2.0** | sqlalchemy, aiosqlite → asyncpg |



---

## 五、核心组件详细设计方案

### 5.1 DAGScheduler (自研)

#### 5.1.1 设计目标
- YAML 驱动 DAG 构建与执行
- 模块内 Skill 并行调度 (无依赖时)
- 条件分支支持 (仅 CLI 执行超时回退模式)
- 状态驱动: 等待依赖完成 -> 调度 -> 执行 -> 等待 Gate/完成
- 超时监控 (90s 超时 + 30s SIGKILL)

#### 5.1.2 核心数据结构

```python
# backend/scheduler/models.py
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any

class SkillStatus(Enum):
    PENDING = auto()       # 等待执行
    EXECUTING = auto()     # 正在执行
    GATE_WAITING = auto()  # 等待用户确认
    COMPLETED = auto()     # 正常完成
    ERROR = auto()         # 执行失败
    SKIPPED = auto()       # 被跳过 (旁路)
    TIMEOUT = auto()       # 超时失败
    REVIEW_PENDING = auto()  # 审查等待
    APPROVED = auto()      # 审查通过

@dataclass
class SkillNode:
    """DAG 中的 Skill 节点"""
    id: str
    name: str
    file_path: str
    phase: str  # setup/analysis/design/develop/verify/deploy
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    status: SkillStatus = SkillStatus.PENDING
    parallel_group: Optional[str] = None
```

#### 5.1.3 调度器核心 API

```python
# backend/scheduler/dag_scheduler.py
class DAGScheduler:
    """
    DAG 调度器 - 核心职责:
    1. 解析 YAML 定义构建 DAG
    2. 拓扑排序确定执行顺序
    3. 按层调度, 同层无依赖 Skill 并行执行
    4. 超时监控与处理 (90s SIGTERM + 30s SIGKILL)
    5. Gate 等待与恢复
    6. 错误处理 (rollback/retry/skip)
    """

    def __init__(self, engine, gate, max_parallel=3, timeout=90.0, kill_timeout=30.0):
        self.engine = engine      # PocketFlowEngine
        self.gate = gate          # GateController
        self.max_parallel = max_parallel
        self.timeout = timeout
        self.kill_timeout = kill_timeout
        self._callbacks = {}      # 事件回调注册表
        self._running = {}        # 正在执行的任务

    async def execute_dag(self, dag: DAGDefinition) -> Dict[str, Any]:
        """执行完整 DAG"""
        layers = dag.topological_sort()  # 返回按层分组的节点
        results = {}

        for layer in layers:
            # 过滤出就绪节点
            ready = [n for n in layer if self._can_execute(n, results)]
            # 并行执行
            tasks = [self._execute_node(n, dag.project_id) for n in ready]
            layer_results = await asyncio.gather(*tasks, return_exceptions=True)
            # 处理结果
            for node, result in zip(ready, layer_results):
                if isinstance(result, Exception):
                    await self._handle_error(node, result, dag)
                else:
                    results[node.id] = result
            self._emit("layer_completed", {"layer": [n.id for n in ready]})
        return results

    async def _execute_node(self, node: SkillNode, project_id: str) -> Dict:
        """执行单个 Skill 节点"""
        # 1. 状态: PENDING -> EXECUTING
        await self._update_status(node, SkillStatus.EXECUTING)

        # 2. 调用 PocketFlowEngine
        result = await self.engine.execute(skill=node, project_id=project_id)

        # 3. 检查 Gate (如需)
        if result.get("requires_gate"):
            await self._update_status(node, SkillStatus.GATE_WAITING)
            gate_result = await self.gate.wait_for_approval(node, result)
            if not gate_result["approved"]:
                raise GateRejectedError(f"Gate rejected for {node.id}")

        # 4. 检查审查 (如需)
        if result.get("has_artifacts"):
            await self._update_status(node, SkillStatus.REVIEW_PENDING)
            # 审查异步处理, 不阻塞调度

        # 5. 状态: EXECUTING -> COMPLETED
        await self._update_status(node, SkillStatus.COMPLETED)
        return result

    def _can_execute(self, node, results) -> bool:
        """检查所有依赖是否已完成或跳过"""
        return all(
            dep in results and results[dep].get("status") 
                in (SkillStatus.COMPLETED, SkillStatus.SKIPPED)
            for dep in node.dependencies
        )
```

#### 5.1.4 关键设计决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 并行策略 | 按层并行 | 拓扑排序后同层无依赖, 天然可并行 |
| 超时处理 | 90s SIGTERM + 30s SIGKILL | 给 Skill 优雅退出机会 |
| 错误策略 | 三级: rollback/retry/skip | 满足不同 Skill 容错需求 |
| 持久化 | 数据库实时写入 | 崩溃后可恢复执行状态 |
| Gate 阻塞 | 异步等待, 不阻塞事件循环 | 支持多个 Gate 并发等待 |

---

### 5.2 StateMachineManager (自研)

#### 5.2.1 三级状态机定义

**Skill 级 (9 状态)**:
```
PENDING -> SCHEDULED -> EXECUTING -> COMPLETED
                              |-> GATE_WAITING -> EXECUTING
                              |-> REVIEW_PENDING -> APPROVED -> COMPLETED
                              |-> FAILED (可重试 -> SCHEDULED)
SCHEDULED -> SKIPPED
```

**Project 级 (4 状态)**:
```
DRAFT -> ACTIVE -> ARCHIVED
  |         |
  +---> CANCELLED <---+
```

**Artifact 级 (4 状态)**:
```
GENERATED -> EDITED -> REVIEWING -> ACCEPTED
      |          ^          |
      +----------+----------+
      (编辑触发 stale 传播)
```

#### 5.2.2 核心 API

```python
class StateMachineManager:
    """
    状态机管理器 - 核心职责:
    1. 管理 Skill/Project/Artifact 三级状态机
    2. 校验状态转换合法性 (基于 TRANSITIONS 定义)
    3. 触发状态变更事件 (SSE 推送)
    4. 持久化到数据库 (原子操作)
    5. 崩溃恢复
    """

    async def transition(self, entity_type, entity_id, 
                         from_state, to_state, context=None) -> bool:
        """执行状态转换"""
        # 1. 校验转换合法性
        if to_state not in TRANSITIONS[entity_type].get(from_state, set()):
            raise InvalidTransitionError(f"{from_state} -> {to_state} invalid")
        # 2. 执行前置校验器
        # 3. 数据库原子更新
        # 4. 触发事件 -> SSE 推送
        # 5. 记录审计日志

    async def recover_after_crash(self):
        """崩溃恢复: EXECUTING/GATE_WAITING 状态重置为 PENDING"""
        # 扫描数据库中"执行中"的 Skill
        # 重置为 PENDING, 等待重新调度
```

---

### 5.3 PocketFlowEngine (自研)

#### 5.3.1 三阶段执行模型

```
+-------+     +-------+     +-------+
| PREP  | --> | EXEC  | --> | POST  |
+-------+     +-------+     +-------+
  准备输入      调用 CLI       捕获输出
  验证产物      超时管理       触发 Gate
  计算哈希      日志收集       验证产物
```

#### 5.3.2 核心 API

```python
@dataclass
class ExecutionResult:
    skill_id: str
    status: str           # success | error | timeout | killed
    exit_code: int
    stdout: str
    stderr: str
    output_artifacts: List[str]
    log_path: str
    duration_ms: int
    requires_gate: bool = False
    gate_summary: Optional[str] = None

class PocketFlowEngine:
    async def execute(self, skill: SkillNode, project_id: str) -> ExecutionResult:
        """完整三阶段执行"""
        prep = await self._prep_phase(skill, project_id)
        exec_result = await self._exec_phase(skill, project_id)
        return await self._post_phase(skill, project_id, exec_result)

    async def _prep_phase(self, skill, project_id):
        """PREP: 验证输入产物, 计算哈希, 准备工作目录"""

    async def _exec_phase(self, skill, project_id):
        """EXEC: 子进程调用 + 超时管理"""
        process = await asyncio.create_subprocess_exec(...)
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=90.0)
        except asyncio.TimeoutError:
            process.terminate()  # SIGTERM
            await asyncio.wait_for(process.wait(), timeout=30.0)
            # 仍不退出则 process.kill()  # SIGKILL

    async def _post_phase(self, skill, project_id, exec_result):
        """POST: 扫描输出产物, 验证完整性, 生成 Gate 摘要"""
```

---

### 5.4 GateController (自研)

#### 5.4.1 职责
- Gate 等待队列管理
- AI 自检摘要触发
- 审批决策记录 (确认/驳回/重试)
- 旁路审批授权 (ADMIN 角色)
- human-decisions.md 审计日志

#### 5.4.2 核心 API

```python
class GateController:
    """审批控制器"""

    async def wait_for_approval(self, skill, exec_result, timeout=None):
        """等待用户审批, 返回 {approved, decision, reason}"""
        # 1. 将 Gate 加入等待队列
        # 2. 通过 SSE 通知前端
        # 3. 等待用户响应 (asyncio.Event)
        # 4. 记录决策到 human-decisions.md

    async def approve(self, gate_id, user_id, notes=None):
        """确认审批"""

    async def reject(self, gate_id, user_id, reason):
        """驳回, 触发 rollback"""

    async def bypass(self, gate_id, admin_id, reason):
        """旁路审批 (需 ADMIN 权限)"""

    def get_pending_gates(self) -> List[GateItem]:
        """获取待审批队列 (GateCenter 展示)"""
```

---

### 5.5 ArtifactRenderer (前端)

#### 5.5.1 组件架构

```
ArtifactRenderer (统一入口)
  |-- MarkdownRenderer    -> react-markdown + remark-gfm
  |-- MermaidRenderer     -> mermaid.js (动态渲染)
  |-- SwaggerRenderer     -> swagger-ui-react
  |-- YAMLRenderer        -> react-syntax-highlighter
  |-- JSONRenderer        -> @microlink/json-view
  |-- DiffRenderer        -> react-diff-viewer-continued
```

#### 5.5.2 核心 Props

```typescript
interface ArtifactRendererProps {
  artifact: {
    path: string;        // 产物路径
    content: string;     // 产物内容
    format: "md" | "mmd" | "yaml" | "json" | "swagger" | "txt";
    version?: string;    // 版本号 (用于 diff)
    previousContent?: string; // 上一版本内容
  };
  mode: "preview" | "edit" | "diff";  // 渲染模式
  onEdit?: (content: string) => void;
  onReviewComment?: (line: number, comment: string) => void;
}
```

---

### 5.6 FileSystemWatcher

#### 5.6.1 基于 watchdog 的实现

```python
# backend/watcher/fs_watcher.py
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

class ArtifactEventHandler(FileSystemEventHandler):
    """产物目录事件处理器"""

    def __init__(self, project_id, artifact_manager):
        self.project_id = project_id
        self.manager = artifact_manager
        self._debounce_timers = {}  # 防抖计时器

    def on_modified(self, event):
        if event.is_directory:
            return
        # 防抖处理 (500ms 内多次变更合并)
        self._debounce(event.src_path, self._handle_modify, event)

    async def _handle_modify(self, event):
        # 1. 计算新哈希
        new_hash = compute_hash(event.src_path)
        # 2. 与数据库中存储的哈希对比
        stored = await self.manager.get_hash(self.project_id, event.src_path)
        if new_hash != stored:
            # 3. 标记产物为 STALE
            await self.manager.mark_stale(self.project_id, event.src_path)
            # 4. 通过 SSE 通知前端
            await self.manager.notify_stale(self.project_id, event.src_path)

class FileSystemWatcher:
    """文件系统监听器"""

    def __init__(self):
        self.observer = Observer()
        self._handlers = {}

    def watch_project(self, project_id: str, path: str):
        """开始监听项目产物目录"""
        handler = ArtifactEventHandler(project_id, self.artifact_manager)
        self.observer.schedule(handler, path, recursive=True)
        self._handlers[project_id] = handler

    def unwatch_project(self, project_id: str):
        """停止监听"""
        ...
```

---

### 5.7 C4DSLManager + C4Renderer (自研)

#### 5.7.1 DSL 设计 (参考 Structurizr)

```yaml
# workspace.dsl
workspace "项目名称" "描述" {
    model {
        user = person "用户" "描述"
        system = softwareSystem "系统名称" "描述" {
            webapp = container "Web App" "React" {
                component "HomePage" "页面组件"
                component "APIClient" "API 调用"
            }
            api = container "API" "FastAPI" {
                component "ProjectController" "项目控制器"
            }
        }
    }
    views {
        systemContext {
            description "系统上下文"
            include user, system
        }
        container {
            description "容器视图"
            include user, system
        }
        component system.webapp {
            description "Web App 组件"
        }
    }
}
```

#### 5.7.2 C4Renderer 渲染流程

```typescript
// 前端: C4Renderer.tsx
const C4Renderer = ({ dslContent, viewLevel }: Props) => {
  // 1. 解析 DSL 为 AST
  const ast = parseDSL(dslContent);
  // 2. 根据 viewLevel 提取对应视图
  const view = extractView(ast, viewLevel);
  // 3. 转换为 Mermaid 语法
  const mermaidCode = toMermaid(view);
  // 4. 渲染 (mermaid.js)
  return <MermaidRenderer code={mermaidCode} />;
};
```

#### 5.7.3 反向定位

```python
# backend: C4ReverseLocator
class C4ReverseLocator:
    """C4 反向定位: Component/Code 节点 -> 本地代码文件"""

    async def locate_code(self, dsl_node_id: str, project_id: str) -> str:
        """根据 C4 DSL 节点 ID 定位到本地代码文件路径"""
        # 1. 查询映射表
        mapping = await self.db.get_code_mapping(project_id, dsl_node_id)
        # 2. 验证文件存在
        if not os.path.exists(mapping.file_path):
            raise FileNotFoundError(f"Code file not found: {mapping.file_path}")
        return mapping.file_path

    async def locate_component(self, file_path: str, project_id: str) -> str:
        """反向: 代码文件 -> C4 DSL 节点"""
        ...
```

---

### 5.8 RealtimePush (SSE)

#### 5.8.1 FastAPI 后端

```python
# backend/api/sse.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
import json

router = APIRouter()

class SSEManager:
    """SSE 连接管理器"""

    def __init__(self):
        self._clients: Dict[str, asyncio.Queue] = {}  # project_id -> queue

    async def connect(self, project_id: str):
        """建立 SSE 连接"""
        queue = asyncio.Queue()
        self._clients[project_id] = queue
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
        finally:
            del self._clients[project_id]

    async def push(self, project_id: str, event_type: str, data: dict):
        """推送事件到指定项目"""
        if project_id in self._clients:
            await self._clients[project_id].put({
                "type": event_type,
                "data": data,
                "timestamp": time.time()
            })

sse_manager = SSEManager()

@router.get("/projects/{project_id}/events")
async def project_events(project_id: str):
    """SSE 端点"""
    return StreamingResponse(
        sse_manager.connect(project_id),
        media_type="text/event-stream"
    )
```

#### 5.8.2 React 前端

```typescript
// frontend/hooks/useSSE.ts
export function useSSE(projectId: string) {
  const [events, setEvents] = useState<SSEEvent[]>([]);

  useEffect(() => {
    const source = new EventSource(`/api/projects/${projectId}/events`);
    source.onmessage = (e) => {
      const event = JSON.parse(e.data);
      setEvents(prev => [...prev, event]);
      // 根据事件类型分发到对应 store
      if (event.type === "skill_state_changed") {
        useSkillStore.getState().updateSkill(event.data);
      }
    };
    return () => source.close();
  }, [projectId]);

  return events;
}
```

---

### 5.9 DatabaseAdapter

#### 5.9.1 SQLAlchemy 2.0 异步架构

```python
# backend/db/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# MVP: SQLite (aiosqlite)
# P1: PostgreSQL (asyncpg)
DATABASE_URL = "sqlite+aiosqlite:///./arsitect.db"  # MVP
# DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/arsitect"  # P1

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class DatabaseAdapter:
    """数据库适配器"""

    async def get_session(self) -> AsyncSession:
        async with async_session() as session:
            yield session

    async def init_db(self):
        """初始化数据库 (建表)"""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def migrate_to_postgres(self):
        """P1: SQLite -> PostgreSQL 迁移"""
        # 使用 alembic 管理迁移
        ...
```

#### 5.9.2 核心模型

```python
# backend/db/models.py
class Project(Base):
    __tablename__ = "projects"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    state = Column(Enum(ProjectState), default=ProjectState.DRAFT)
    complexity_route = Column(String(20))  # trivial/light/standard/deep
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SkillExecution(Base):
    __tablename__ = "skill_executions"
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"))
    skill_id = Column(String(100), nullable=False)
    phase = Column(String(50))
    status = Column(Enum(SkillStatus), default=SkillStatus.PENDING)
    stdout = Column(Text)
    stderr = Column(Text)
    log_path = Column(String(500))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_ms = Column(Integer)
    gate_decision = Column(String(20))  # approved/rejected/bypassed
    gate_decider = Column(String(100))
    gate_notes = Column(Text)
```



---

## 六、补充公共组件 (从整体架构分析)

在完成核心组件设计后, 从整体架构视角审视, 还需以下公共组件来支撑平台完整运转:

### 6.1 新增公共组件清单

| 组件名称 | 所属域 | 职责 | 优先级 | 触发补充的原因 |
|----------|--------|------|--------|----------------|
| **EventBus** | 基础设施 | 统一事件总线, 解耦组件间通信 (发布/订阅模式) | P0 | DAGScheduler、StateMachine、GateController、FileSystemWatcher 都需要事件通知机制 |
| **ProjectContext** | 项目治理 | 项目级上下文管理器, 管理全局参数、产物目录、Git 仓库句柄 | P0 | 所有组件操作都需知道"当前项目"的上下文 |
| **ArtifactStore** | 产物管理 | 产物存储抽象层, 统一文件读写 + 哈希缓存 + Git 自动提交 | P0 | ArtifactVersionManager 和 FileSystemWatcher 都需要统一的产物访问层 |
| **PermissionManager** | 基础设施 | 权限管理 (OWNER/ADMIN/MEMBER/VISITOR), Gate 旁路审批鉴权 | P0 | GateController 的旁路审批需要角色校验 |
| **CacheManager** | 基础设施 | 多级缓存 (内存 + SQLite), DSL AST 缓存、产物内容缓存 | P1 | C4 大文件 DSL 解析和产物频繁读取需要缓存 |
| **HealthChecker** | 基础设施 | 依赖服务健康检查 (Docker/OpenUI/Git CLI), 降级决策数据源 | P0 | FallbackManager 需要实时知道 OpenUI 是否可用 |
| **MetricsCollector** | 基础设施 | 指标收集 (执行耗时、Gate 等待时间、重试次数), 为历史回溯提供数据 | P1 | HistoryViewer 的返工热力图和耗时对比需要数据源 |
| **ImportExportManager** | 项目治理 | 项目导入/导出 (.arsitect 格式), 支持迁移和备份 | P1 | 用户可能需要备份项目或在不同机器间迁移 |
| **SearchEngine** | 产物管理 | 全产物内容搜索 (文件名 + 内容), 支持过滤和快速跳转 | P1 | 大型项目产物多时需要搜索能力 |
| **NotificationManager** | 基础设施 | 多渠道通知 (SSE/邮件/Webhook), Timebox 到期提醒 | P1 | 用户离线时需要通知机制 |

### 6.2 公共组件详细设计

#### 6.2.1 EventBus (核心公共组件)

```python
# backend/common/event_bus.py
import asyncio
from typing import Dict, List, Callable, Any
from dataclasses import dataclass

@dataclass
class DomainEvent:
    """领域事件"""
    event_type: str           # 事件类型 (如: skill.state_changed)
    aggregate_id: str         # 聚合根 ID (如: project_id)
    payload: Dict[str, Any]   # 事件载荷
    timestamp: float          # 发生时间
    source: str               # 事件来源组件

class EventBus:
    """
    异步事件总线

    核心职责:
    1. 组件间解耦通信 (发布/订阅)
    2. 事件持久化 (可选, 用于重放)
    3. 错误隔离 (处理器失败不影响发布者)

    使用场景:
    - DAGScheduler 发布 skill 状态变更
    - FileSystemWatcher 发布文件变更事件
    - GateController 发布审批决策
    - StateMachineManager 发布状态转换通知
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False

    async def start(self):
        """启动事件分发循环"""
        self._running = True
        while self._running:
            event = await self._event_queue.get()
            await self._dispatch(event)

    def subscribe(self, event_type: str, handler: Callable):
        """订阅事件"""
        self._subscribers.setdefault(event_type, []).append(handler)

    def publish(self, event: DomainEvent):
        """发布事件 (非阻塞)"""
        asyncio.create_task(self._event_queue.put(event))

    async def _dispatch(self, event: DomainEvent):
        """分发事件到所有订阅者"""
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                # 事件处理器错误不应影响其他处理器
                print(f"Event handler error for {event.event_type}: {e}")
```

#### 6.2.2 ProjectContext

```python
# backend/common/project_context.py
from contextvars import ContextVar
from pathlib import Path

# 线程安全的项目上下文
project_ctx: ContextVar[str] = ContextVar("project_id")

class ProjectContext:
    """
    项目上下文管理器

    管理内容:
    - 项目 ID (ContextVar)
    - 产物目录路径
    - Git 仓库句柄 (GitPython Repo)
    - 全局参数 (项目级配置)
    - 当前复杂度路由

    使用 with 语句确保上下文正确清理:
    with ProjectContext(project_id) as ctx:
        # 所有操作都在该项目上下文中
        await engine.execute(skill)
    """

    def __init__(self, project_id: str, base_dir: str = "./projects"):
        self.project_id = project_id
        self.base_dir = Path(base_dir)
        self.artifacts_dir = self.base_dir / project_id / "artifacts"
        self.logs_dir = self.base_dir / project_id / "logs"
        self._token = None

    def __enter__(self):
        self._token = project_ctx.set(self.project_id)
        return self

    def __exit__(self, *args):
        project_ctx.reset(self._token)

    @property
    def repo(self):
        """延迟加载 Git 仓库"""
        from git import Repo
        return Repo(self.base_dir / self.project_id)
```

#### 6.2.3 ArtifactStore (产物存储抽象)

```python
# backend/common/artifact_store.py
import hashlib
from pathlib import Path
from typing import Optional, Dict
import aiofiles

class ArtifactStore:
    """
    产物存储抽象层

    核心职责:
    1. 统一文件读写接口
    2. 自动哈希计算与缓存
    3. Git 自动提交 (可配置)
    4. 变更检测 (基于哈希)

    这是 FileSystemWatcher 和 ArtifactVersionManager 的底层依赖。
    """

    def __init__(self, project_ctx: ProjectContext, git_adapter: 'GitAdapter'):
        self.ctx = project_ctx
        self.git = git_adapter
        self._hash_cache: Dict[str, str] = {}  # path -> hash 缓存

    async def read(self, relative_path: str) -> str:
        """读取产物内容"""
        full_path = self.ctx.artifacts_dir / relative_path
        async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
            return await f.read()

    async def write(self, relative_path: str, content: str, auto_commit=True):
        """写入产物, 自动计算哈希, 可选 Git 提交"""
        full_path = self.ctx.artifacts_dir / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(full_path, 'w', encoding='utf-8') as f:
            await f.write(content)

        # 更新哈希缓存
        new_hash = self._compute_hash(content)
        old_hash = self._hash_cache.get(relative_path)
        self._hash_cache[relative_path] = new_hash

        # 冲突检测
        if old_hash and old_hash != new_hash:
            # 文件被外部修改
            pass

        # Git 自动提交
        if auto_commit:
            await self.git.commit_file(
                self.ctx.project_id, 
                relative_path, 
                f"Update {relative_path}"
            )

    async def get_hash(self, relative_path: str) -> str:
        """获取产物哈希 (优先缓存)"""
        if relative_path not in self._hash_cache:
            content = await self.read(relative_path)
            self._hash_cache[relative_path] = self._compute_hash(content)
        return self._hash_cache[relative_path]

    @staticmethod
    def _compute_hash(content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
```

#### 6.2.4 HealthChecker

```python
# backend/common/health_checker.py
import asyncio
import aiohttp
from typing import Dict, Callable
from dataclasses import dataclass
from enum import Enum

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNAVAILABLE = "unavailable"

@dataclass
class HealthResult:
    service: str
    status: ServiceStatus
    latency_ms: float
    message: str

class HealthChecker:
    """
    依赖服务健康检查器

    检查对象:
    - Docker Daemon (OpenUI 运行依赖)
    - OpenUI 服务 HTTP 端口
    - Git CLI 可用性
    - Kimi CLI 可用性

    结果驱动 FallbackManager 的降级决策。
    """

    def __init__(self, check_interval: float = 30.0):
        self.check_interval = check_interval
        self._checks: Dict[str, Callable] = {}
        self._results: Dict[str, HealthResult] = {}

    def register(self, name: str, check_fn: Callable):
        """注册健康检查项"""
        self._checks[name] = check_fn

    async def start_monitoring(self):
        """启动持续监控"""
        while True:
            for name, check_fn in self._checks.items():
                try:
                    result = await asyncio.wait_for(check_fn(), timeout=5.0)
                    self._results[name] = result
                except asyncio.TimeoutError:
                    self._results[name] = HealthResult(
                        name, ServiceStatus.UNAVAILABLE, 5000, "Timeout"
                    )
            await asyncio.sleep(self.check_interval)

    def get_status(self, service: str) -> ServiceStatus:
        """获取服务状态"""
        result = self._results.get(service)
        return result.status if result else ServiceStatus.UNAVAILABLE

    def is_available(self, service: str) -> bool:
        return self.get_status(service) == ServiceStatus.HEALTHY
```

---

## 七、Demo 版迁移方案

### 7.1 现状分析

根据 AI_Code_v3.2.md 的描述, Demo 版现状:

```
前端: React + Vite + Zustand + React Flow (手工编排节点)
后端: FastAPI + SQLAlchemy + SQLite (基础 CRUD)
规模: 前端 ~7,500 行 / 后端 ~6,000 行 / 50 个组件
已具备: 拓扑画布、产物展示、基础路由、Gate 原型
缺失: DAG 调度、状态机、产物版本、审查迭代、SSE、watchdog、HITL 完整流程
```

### 7.2 迁移策略: 渐进式重构

采用**绞杀者模式 (Strangler Fig Pattern)**, 逐个组件替换, 而非一次性重写。

#### 阶段一: 基础设施层 (Week 1-2)

```
新增组件:
  [EventBus] ---------- 新文件, 无依赖
  [ProjectContext] ---- 新文件, 替换 scattered path 计算
  [DatabaseAdapter] --- 扩展现有 SQLAlchemy 代码, 添加 AsyncSession
  [ConfigManager] ----- 新文件, 替换硬编码配置

迁移动作:
  1. 将现有同步 SQLAlchemy 改为异步 (create_async_engine)
  2. 引入 EventBus, 将 React Flow 节点状态更新改为事件驱动
  3. 添加 ProjectContext, 统一项目路径管理
  4. 风险: 低 (仅基础设施, 不影响业务逻辑)
```

#### 阶段二: 执行引擎层 (Week 3-4)

```
新增组件:
  [PocketFlowEngine] -- 替换现有的 subprocess 直接调用
  [StateMachineManager] - 新文件, 接管所有状态管理
  [DAGScheduler] ------ 新文件, 替换手工编排

迁移动作:
  1. 将现有的 subprocess 调用封装到 PocketFlowEngine
  2. 添加 Skill 状态机 (9 状态), 替换现有的简单状态字段
  3. 实现 YAML DAG 解析, 支持现有手工编排的导出
  4. 保持手工编排作为 DAG 编辑器的 fallback
  5. 风险: 中 (核心执行逻辑, 需充分测试)
```

#### 阶段三: Gate + 产物管理层 (Week 5-6)

```
新增组件:
  [GateController] -------- 替换现有 Gate 原型
  [ArtifactStore] --------- 新文件, 统一产物读写
  [ArtifactVersionManager] -- 基于 GitPython 的版本管理
  [FileSystemWatcher] ------ 基于 watchdog 的监听

迁移动作:
  1. 重构 Gate 流程: 自检摘要 -> 等待 -> 决策记录
  2. 添加 human-decisions.md 审计日志
  3. 产物读写改为 ArtifactStore 接口
  4. 自动 Git 提交 + 历史记录
  5. 启动 watchdog 监听产物目录
  6. 风险: 中 (用户交互流程变更)
```

#### 阶段四: 可视化 + 架构治理层 (Week 7-8)

```
新增组件:
  [ArtifactRenderer] -- 替换现有产物展示 (添加 Mermaid/Swagger 渲染)
  [C4DSLManager] ------ 新文件
  [C4Renderer] -------- 新文件
  [C4ReverseLocator] --- 新文件
  [RealtimePush] ------ SSE 实时推送

迁移动作:
  1. 产物展示组件升级为 ArtifactRenderer (多模态)
  2. 添加 C4 DSL 编辑器 + Mermaid 渲染
  3. 实现 SSE 推送, 替换前端轮询
  4. 添加架构图反向定位功能
  5. 风险: 低-Med (主要为新增功能)
```

#### 阶段五: 公共组件 + 打磨 (Week 9-10)

```
新增组件:
  [PermissionManager] --- 角色权限管理
  [HealthChecker] ------- 服务健康检查
  [FallbackManager] ----- 降级策略 (OpenUI -> Wireframe)
  [MetricsCollector] ---- 指标收集

迁移动作:
  1. 添加 Gate 旁路审批鉴权
  2. 实现 OpenUI 不可用时自动降级 Wireframe
  3. 添加项目指标收集
  4. 性能优化 + Bug 修复
  5. 风险: 低
```

### 7.3 迁移风险与缓解

| 风险 | 影响 | 缓解策略 |
|------|------|----------|
| 异步改造引入 Bug | 高 | 保持现有 API 接口不变, 内部逐步异步化; 充分单元测试 |
| 状态机升级导致状态丢失 | 高 | 迁移脚本: 现有简单状态 -> 新状态机状态映射 |
| Gate 流程变更用户不适应 | 中 | 保留快速确认入口, 默认不强制详细审批 |
| watchdog 误报 (IDE 保存触发) | 中 | 500ms 防抖 + .gitignore 过滤 |
| 性能下降 (新增抽象层) | 低 | 缓存 + 延迟加载; 性能基准测试对比 |

### 7.4 兼容性保障

```
1. API 兼容: 保持 REST API 路径和响应格式不变, 内部实现替换
2. 数据兼容: 数据库迁移脚本 (alembic), 旧数据自动升级
3. 配置兼容: 现有配置自动导入 ConfigManager
4. UI 兼容: 新增功能默认隐藏 (feature flag), 用户手动开启
5. 产物兼容: 现有产物目录结构不变, ArtifactStore 适配
```

### 7.5 迁移验证清单

```
[ ] 现有手工编排项目可正常打开和执行
[ ] Gate 流程: 自检 -> 确认 -> 日志记录
[ ] 产物编辑保存后 Git 自动提交
[ ] 外部修改产物触发 STALE 标记
[ ] SSE 实时推送状态变更
[ ] C4 DSL 编辑后架构图自动更新
[ ] OpenUI 不可用时自动降级 Wireframe
[ ] 项目导出/导入功能正常
[ ] 性能: DAG 执行速度 >= Demo 版
[ ] 崩溃恢复: 重启后继续执行未完成的 Skill
```




---

## 八、总结与关键决策

### 8.1 组件全景图

```
+===============================================================+
|                        Arsitect 平台架构                        |
+===============================================================+
|                                                               |
|  +------------------+  +------------------+  +--------------+  |
|  |   FlowCanvas     |  | StageDetailPanel |  |  GateCenter  |  |
|  |  (React Flow)    |  |                  |  |              |  |
|  +--------+---------+  +--------+---------+  +------+-------+  |
|           |                     |                   |          |
|  +--------v---------+  +--------v---------+  +------v-------+  |
|  |   RealtimePush   |  | ArtifactRenderer |  | HistoryViewer|  |
|  |     (SSE)        |  | (Markdown/Mermaid|  |   (P1)       |  |
|  +------------------+  |  /Swagger/JSON)  |  +--------------+  |
|                        +--------+---------+                   |
|                                 |                             |
+=================================|==============================+
                                  | REST API + SSE
+=================================|==============================+
|                                 |                             |
|  +------------------+  +--------v---------+  +--------------+  |
|  | DAGScheduler     |  | StateMachineMgr  |  |PocketFlowEng |  |
|  | (拓扑排序/并行)   |  | (3级状态机)       |  |(CLI 三阶段)  |  |
|  +--------+---------+  +--------+---------+  +------+-------+  |
|           |                     |                   |          |
|  +--------v---------+  +--------v---------+  +------v-------+  |
|  | GateController   |  | EventBus         |  |CLIAdapter    |  |
|  | (审批队列)        |  | (事件总线)        |  |(Kimi/MCP)   |  |
|  +------------------+  +------------------+  +--------------+  |
|                                                               |
|  +------------------+  +------------------+  +--------------+  |
|  | ArtifactStore    |  | C4DSLManager     |  | C4Renderer   |  |
|  | (产物存储抽象)    |  | (DSL 管理)        |  | (Mermaid)    |  |
|  +--------+---------+  +--------+---------+  +--------------+  |
|           |                     |                             |
|  +--------v---------+  +--------v---------+  +--------------+  |
|  | ArtifactVerMgr   |  | C4AutoGenerator  |  |WireframeEng  |  |
|  | (GitPython)      |  | (AI 生成 DSL)     |  | (线框图)     |  |
|  +------------------+  +------------------+  +--------------+  |
|                                                               |
|  +------------------+  +------------------+  +--------------+  |
|  | FileSystemWatcher|  | OpenUIClient     |  |SketchGen     |  |
|  | (watchdog)       |  | (Docker HTTP)    |  | (草图生成)    |  |
|  +------------------+  +------------------+  +--------------+  |
|                                                               |
+=======================+============+===========================+
                        |            |
            +-----------v----+  +----v-----------+
            | DatabaseAdapter |  |   GitAdapter   |
            | (SQLAlchemy 2)  |  |  (GitPython)   |
            +-----------------+  +----------------+
                        |
            +-----------v-----------+
            |   公共基础设施组件       |
            | EventBus/ProjectCtx   |
            | ArtifactStore/Health  |
            | ConfigMgr/AuditLogger |
            +-----------------------+
```

### 8.2 关键设计决策汇总

| 决策点 | 选择 | 理由 |
|--------|------|------|
| DAG 调度 | 自研轻量调度器 | 业务语义独特, 通用引擎难以满足 |
| 状态机 | 自研 + SQLAlchemy | 三级状态矩阵复杂, 通用库难以表达 |
| 产物渲染 | 组合生态标准库 | 各格式用对应最佳方案 |
| Git 集成 | GitPython | 功能完整, MVP 阶段足够 |
| 实时推送 | SSE (非 WebSocket) | 单向推送足够, HTTP 兼容 |
| Timebox | APScheduler | AsyncIO 原生, 轻量 |
| 布局算法 | dagre -> elkjs | MVP 快速, P1 专业 |
| 文件监听 | watchdog | 跨平台标准方案 |
| 缓存策略 | 内存 + SQLite | 渐进引入, P1 完善 |

### 8.3 自研 vs 引入外部方案总结

| 组件 | 方案 | 原因 |
|------|------|------|
| DAGScheduler | 自研 | PocketFlow 三阶段 + Gate + 产物驱动 = 独特业务语义 |
| StateMachineManager | 自研 | 跨实体的状态传播 (Stale) 无法由通用状态机表达 |
| PocketFlowEngine | 自研 | CLI 子进程生命周期管理 + 三阶段 = 核心业务逻辑 |
| GateController | 自研 | HITL 审批流程 + 旁路 + 审计 = 业务核心 |
| C4DSLManager | 自研 | DSL <-> 代码双向绑定 = 独特需求 |
| ArtifactStore | 自研 | 哈希缓存 + Git 自动提交 + 冲突检测 = 组合需求 |
| EventBus | 自研 | 简单发布/订阅, 无需引入重量级消息队列 |
| ArtifactRenderer | 组合引入 | react-markdown, mermaid, swagger-ui 均为标准方案 |
| FileSystemWatcher | 引入 watchdog | 跨平台文件监控是通用能力, watchdog 成熟稳定 |
| GitAdapter | 引入 GitPython | Git 操作是通用能力, GitPython 功能完整 |

### 8.4 MVP 开发优先级建议

**P0 (必须, 阻塞发布)**:
1. DAGScheduler + PocketFlowEngine + StateMachineManager (核心执行)
2. GateController (审批流程)
3. ArtifactStore + ArtifactRenderer (产物管理)
4. EventBus + RealtimePush (实时通信)
5. DatabaseAdapter + ProjectContext (基础设施)

**P1 (重要, 可后续迭代)**:
1. FileSystemWatcher (外部变更检测)
2. C4DSLManager + C4Renderer (架构治理)
3. ArtifactVersionManager (Git 版本管理)
4. ReviewManager (审查迭代)
5. HealthChecker + FallbackManager (降级容错)

**P2 (增强体验)**:
1. HistoryViewer + MetricsCollector (历史回溯)
2. ComplexityRouter UI (复杂度路由可视化)
3. ImportExportManager (导入导出)
4. SearchEngine (搜索)
5. NotificationManager (多渠道通知)

### 8.5 技术债务预警

| 债务项 | 影响 | 偿还时机 |
|--------|------|----------|
| SQLite -> PostgreSQL 迁移 | 并发性能 | P1 阶段 |
| dagre -> elkjs 布局升级 | 画布体验 | P1 阶段 |
| LangGraph Checkpointer 引入 | 执行持久化 | P1-P2 阶段 |
| 前端状态管理 Zustand 扩展 | 大规模项目性能 | 按需 |
| 单元测试覆盖率不足 | 质量风险 | 持续 |

---

> **文档信息**
> - 基于材料: AI_Code_v3.2.md, DocForge_C4_Platform_Design.docx, sketch.txt, 00-design-overview.md, 01-architecture-core.md, 02-data-flow.md, 00-requirements-overview.md, 01-requirements-list.md, 02-functional-requirements.md
> - 调研时间: 2026-06-10
> - 覆盖组件: 34 个核心组件 + 10 个公共组件
> - 开源方案评估: 20+ 个项目
