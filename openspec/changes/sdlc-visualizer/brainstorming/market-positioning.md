# Market Positioning - sdlc-visualizer

> 模式：positioning（市场定位）
> 分析目标：AI 辅助软件开发全生命周期可视化平台
> 生成时间：2026-05-31
> 基于：brainstorming/requirement-draft.md + 网络竞品研究

---

## 1. 竞争集合

### Primary（直接竞品 — 提供 AI 工作流可视化或编排的平台）

| 竞品 | 定位 | 核心能力 | 与本项目重叠度 | 证据层级 |
|------|------|----------|---------------|---------|
| **Dify** | 低代码 AI 应用构建平台 | 可视化 Prompt 编排、多模型支持、RAG、团队协作文档 | 中（都有可视化编排） | T1（官方文档）+ T4（行业报告） |
| **CrewAI + CrewAI Studio** | 角色化多 Agent 编排框架 | `flow.plot()` 可视化、角色定义、任务分配、Flows 事件驱动 | 中（都有流程可视化） | T1（官方文档）+ T3（框架对比分析） |
| **LangGraph + LangGraph Studio** | 图状态机编排 + 调试工具 | Time-travel 调试、状态持久化、Human-in-the-loop 中断节点、LangSmith 可观测性 | 中（都有状态可视化） | T1（官方文档）+ T3（Zylos Research 2026） |

### Secondary（相邻扩展 — 在部分场景可替代本项目的工具）

| 竞品 | 定位 | 核心能力 | 与本项目重叠度 | 证据层级 |
|------|------|----------|---------------|---------|
| **ChatDev** | 端到端 AI 软件开发 | Waterfall 多 Agent 协作（CEO/CTO/CPO/程序员/测试员）、ChatChain 可视化、全自动化闭环 | 低-中（都有 SDLC 概念） | T1（GitHub/论文）+ T5（产品页面） |
| **Jira / Linear** | 通用项目管理 | 任务跟踪、看板、报表、权限体系、敏捷/瀑布模板 | 低（管理"人"的任务 vs 管理"AI"的执行） | T1（官方文档） |
| **Notion** | 文档+数据库+看板一体化 | 灵活的数据库视图、文档协作、模板市场 | 低（产物记录 vs 过程可视化） | T1（官方文档） |
| **OutSystems Agent Workbench** | 企业级可视化 Agent 开发 | 可视化开发界面、Forge 组件、Agent 全生命周期监控、企业集成 | 低-中（都有可视化+监控） | T5（发布会/PR 稿） |
| **Flowise / n8n** | 无代码/低代码工作流编排 | 拖拽式节点编排、多集成、自托管 | 低（通用工作流 vs SDLC 专用） | T1（官方文档） |

### Non-obvious（范式威胁 — 可能从根本上改变市场格局的力量）

| 威胁源 | 描述 | 影响路径 | 证据层级 |
|--------|------|----------|---------|
| **Cursor / Windsurf / GitHub Copilot** | AI 原生 IDE，$2B ARR（Cursor 2026 初），70% Fortune 1000 采用 (T4) | IDE 内嵌 AI 执行面板，可能直接集成 SDLC 可视化，无需独立平台 | T4（行业数据）+ T5（高管声明） |
| **手动流程（现状维持）** | 命令行 + 文件管理器 + 文档编辑器 | 超级个体对工具碎片化容忍度高，若独立平台未显著降低认知负荷，用户可能回归手动 | T6（第一性原理推理） |
| **MCP 生态标准化** | Anthropic 主导的 Model Context Protocol，获 OpenAI/Google/Microsoft/AWS 支持 (T1) | 若 MCP 成为标准，Skill 编排可能下沉为 IDE/CLI 插件，独立可视化平台价值被削弱 | T1（官方协议文档）+ T3（行业分析） |
| **ADLC 成熟化** | Agentic Development Lifecycle 成为企业标准 (T3) | 企业可能直接采购端到端 ADLC 平台（如 OutSystems、ServiceNow），而非独立可视化模块 | T3（学术研究） |

---

## 2. JTBD 对比矩阵

| JTBD | 本项目 | Dify | CrewAI | LangGraph | ChatDev | Jira | Cursor |
|------|--------|------|--------|-----------|---------|------|--------|
| **J1: 管理完整软件项目生命周期** | 强（Draft->Archive 14 阶段全覆盖） | 弱（无 SDLC 语义） | 弱（通用任务编排） | 弱（底层编排框架） | 强（Waterfall 全闭环） | 强（通用项目管理） | 中（IDE 内项目管理弱） |
| **J2: 实时查看 AI 执行进度和产物** | 强（拓扑图+详情面板+产物浏览器） | 中（运行日志+输出展示） | 弱（`flow.plot()` 静态图） | 中（LangSmith Tracing） | 中（ChatChain 可视化） | 无 | 中（Inline Chat + 文件变更） |
| **J3: 快速确认关键节点风险** | 强（四道 Gate + AI 自检摘要） | 弱（无审批节点概念） | 弱（无 Gate 机制） | 中（中断节点需代码配置） | 无（全自动，无人工干预） | 弱（人工任务，非 AI 节点） | 无 |
| **J4: 沉淀历史经验优化后续项目** | 强（时间线+对比+返工热力图） | 弱（无项目历史分析） | 弱（无历史沉淀） | 弱（调试导向，非项目治理） | 弱（无跨项目分析） | 中（报表+Velocity） | 弱 |

> 评分标准：强 = 原生核心能力 / 中 = 有类似功能但非核心 / 弱 = 无或需大量定制 / 无 = 完全不相关

**未被满足的作业（Gap 识别）**：
- **J3（快速确认风险）**：当前市场无专门为"单人 AI 开发"设计的自检确认机制。LangGraph 的 HITL 需代码配置，ChatDev 完全自动，Jira 与 AI 执行脱节。
- **J4（历史沉淀）**：所有竞品均缺少"跨项目阶段耗时对比"和"返工热力图"，这是超级个体优化工作流的刚需。

---

## 3. Blue Ocean ERRC 分析

| 维度 | 具体策略 | 竞争逻辑 |
|------|----------|----------|
| **Eliminate（剔除）** | 多人审批会签、云端 SaaS 依赖、通用项目管理功能（甘特图/工时统计）、多租户 RBAC | 这些是企业级产品的标配，对超级个体是负担而非价值。剔除后可大幅降低产品复杂度。 |
| **Reduce（减少）** | 学习成本（默认模板一键启动）、配置复杂度（手动导入 Skill 但提供向导）、对外部 API 的依赖（本地 CLI 调用）、部署成本（SQLite 零运维） | 相比 Dify/LangGraph 需要理解复杂的节点/图概念，本项目以"项目"和"阶段"为心智模型，降低认知门槛。 |
| **Raise（提升）** | AI 执行过程可视化深度（三级伪状态+实时日志）、产物浏览体验（多模态渲染）、单人场景效率（30 秒 Gate 确认）、本地数据主权（零上传） | 将"可视化"从调试工具升级为项目治理工具，将"审批"从多人会签升级为 AI 辅助自检。 |
| **Create（创造）** | Draft/Active 双态管理（预立项 vs 正式执行）、四道 Gate 自检确认（单人场景专用）、Skill 动态导入（兼容任意 Skill 规范）、Arsitect 生态深度兼容 | 创造全新的"AI 辅助开发治理"品类，而非在现有 AI 编排或项目管理红海中竞争。 |

---

## 4. 颠覆向量与威胁景观

### H1（现有核心业务优化）
- **向量**：在超级个体市场中，通过极致的单人体验和本地优先策略，成为"AI 辅助开发可视化"品类的首选工具。
- **威胁**：Cursor 等 AI 原生 IDE 可能内置类似功能，直接截流用户。

### H2（邻近市场扩展）
- **向量**：从超级个体扩展到 3-5 人小团队，引入轻量协作（评论、共享产物、异步审批），切入小型创业公司市场。
- **威胁**：CrewAI Studio 或 Dify 团队版可能快速跟进小团队协作功能。

### H3（ transformative 创新）
- **向量**：成为 Arsitect 生态的"官方可视化层"，定义 AI 辅助软件开发的行业标准工作流规范（类似 Kubernetes 对容器编排的定义）。
- **威胁**：MCP 生态或 ADLC 标准化组织可能直接定义协议层，使可视化层 commoditize。

---

## 5. 战略建议（O→I→R→C→W）

| 级联 | 内容 | 优先级 |
|------|------|--------|
| **O（Objective）** | 在 12 个月内成为超级个体 AI 辅助开发可视化品类的 TOP 1 工具，月活用户 1000+ | P0 |
| **I（Insight）** | 超级个体的核心痛点不是"AI 能力不够"，而是"AI 执行过程不可见、产物难管理、关键节点易遗漏"；现有工具要么面向企业团队（Jira），要么面向通用 AI 编排（Dify），无专门面向单人 AI 软件开发的治理工具 | P0 |
| **R（Recommendation）** | 1. MVP 极致聚焦单人场景，拒绝任何多人协作功能；2. 与 Arsitect 生态深度绑定，成为官方推荐可视化工具；3. 开源核心可视化引擎，建立社区生态壁垒 | P0 |
| **C（Constraint）** | 仅支持 Kimi CLI（MVP）；本地单机部署；10 项目上限；不做通用项目管理 | P0 |
| **W（Watch）** | 1. Cursor / Windsurf 是否推出项目级 AI 执行可视化；2. MCP 生态是否出现标准 SDLC 可视化协议；3. CrewAI Studio 是否增加软件交付阶段概念 | P1 |

---

## 6. 假设登记册

| 假设 ID | 假设内容 | 支撑框架 | 置信度 | 推翻条件 | 关联决策 |
|---------|----------|----------|--------|----------|----------|
| MP-A001 | 超级个体愿意为"过程可视化"付费或采用独立工具，而非继续手动管理 | JTBD + Blue Ocean | M | 种子用户试用后留存率 < 30% | 产品定位：独立平台 vs 插件 |
| MP-A002 | Arsitect 生态将持续增长，为可视化平台提供用户基础 | Christensen 颠覆理论 | M | Arsitect 项目 6 个月内无新增 Skill 或社区停滞 | 生态绑定策略 |
| MP-A003 | Cursor 等 IDE 短期内不会推出完整的 SDLC 可视化功能 | 威胁景观 H1 | M | Cursor 在 6 个月内发布"Project Canvas"或类似功能 | 差异化聚焦策略 |
| MP-A004 | 本地优先（数据不上云）对超级个体是重要差异化卖点 | Blue Ocean | H | 种子用户调研中 < 50% 认为本地优先重要 | 部署模式：本地 vs 云端 |
| MP-A005 | "AI 辅助开发治理"是一个可独立存在的品类，而非现有工具的附加功能 | 7 Powers（差异化） | L | 市场验证表明用户更倾向在 IDE/项目管理工具中集成该功能 | 产品形态：独立平台 vs 插件 |

---

## 7. 对抗性自我批判

1. **弱点**：市场可能不够大。超级个体群体虽然增长快，但付费意愿低，且本地单机部署难以形成 SaaS 订阅收入。若无法从单人扩展到小团队，商业可持续性存疑。
   **缓解**：MVP 以免费+增值服务或一次性授权模式探索；P1 后向 3-5 人小团队扩展协作功能，打开 B 端付费空间。

2. **弱点**：Cursor 等 AI 原生 IDE 的"降维打击"风险。Cursor 已覆盖 70% Fortune 1000，若其推出项目级 AI 执行可视化，用户无需切换工具即可满足 80% 需求。
   **缓解**：聚焦 Cursor 无法覆盖的深度治理功能（Draft/Active 双态、四道 Gate、产物基线化、历史沉淀分析），与 Arsitect 生态深度绑定形成转换成本。

3. **弱点**："AI 辅助开发治理"品类教育成本高。用户可能不认为这是一个独立需求，而是希望在现有工具中解决。
   **缓解**：通过 Arsitect 社区种子用户验证需求；制作"Before/After"对比视频（命令行黑盒 vs 可视化驾驶舱），降低认知门槛；提供一键导入现有 Arsitect 项目的迁移工具。

---

## 8. 来源

### T1（直接行为数据）
- Dify 官方文档与 GitHub 仓库（129K+ stars），2026-05
- CrewAI 官方文档与 GitHub 仓库（44.3K+ stars），2026-05
- LangGraph 官方文档与 GitHub 仓库（12K+ stars），2026-05
- MCP 协议官方文档（Linux Foundation），2026-05
- Cursor 官方数据声明（$2B ARR, 70% Fortune 1000），2026-01 [POTENTIALLY STALE]

### T3（专家分析）
- Zylos Research: "AI Agent Orchestration Frameworks: LangGraph, CrewAI, AutoGen Comparison (2026)", 2026-01-12
- Brightlume: "Agent Orchestration Frameworks Compared: LangGraph vs CrewAI vs Custom", 2026-04-17
- MadAppGang: "Best AI Agent Framework 2026: How to Choose Based on Your Team's Stack", 2026-05-17
- Bryan Calabro Research: "The Inversion of the SDLC" (ADLC 论文), 2026-05-12

### T4（行业报告）
- DataCamp: "The Best AI Agents in 2026", 2025-06-16 [POTENTIALLY STALE]
- McKinsey State of AI 2025: 62% 组织实验 AI Agent，23% 规模化
- Uvik Research: "Agentic AI Frameworks in 2026", 2026-05-11
- AI Agent Market 2026: $9.14B，预计 2034 年 $139.19B

### T5（高管声明/PR）
- OutSystems Agent Workbench 发布会，2025-11-21 [POTENTIALLY STALE]
- Microsoft CEO: 20-30% 代码 AI 生成
- Google CEO: >30% 代码 AI 生成

### T6（推测）
- Cursor 推出"Project Canvas"功能的时间线预测（基于其产品迭代速度和竞争压力）
- MCP 生态对独立可视化平台价值的侵蚀路径分析
