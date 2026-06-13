# Market Positioning — GTPlanner 六开源项目竞争分析

> **模式**：positioning（市场定位）
> **分析目标**：GTPlanner.txt 中六开源项目（C4 InterFlow、Coco Workflow、OpenHands、GTPlanner/PocketFlow、OpenUI、AI Wireframe Generator）在 AI 辅助软件工程工具链中的竞争位置
> **服务阶段**：PRD-000 需求冻结前补充输入
> **文档版本**：v1.0-draft
> **日期**：2026-06-01

---

## 1. 竞争集合

### 1.1 直接竞品（Primary）

| 项目名称 | 核心定位 | 与 SDLC Visualizer 关系 | 威胁级别 |
|---------|---------|------------------------|---------|
| **Dify** | 低代码 AI 应用构建平台 | 直接竞品（已在 PRD-000 3.2 分析） | 中 |
| **CrewAI Studio** | 角色化多 Agent 编排 + 可视化 | 直接竞品（已在 PRD-000 3.2 分析） | 中 |
| **LangGraph Studio** | 图状态机编排调试工具 | 直接竞品（已在 PRD-000 3.2 分析） | 低 |

> 六开源项目中**无直接竞品**。所有六项目均为底层基础设施/工具库，不直接提供面向超级个体的 SDLC 可视化驾驶舱。(T5) [H]

### 1.2 相邻扩展（Secondary）

| 项目名称 | 协议 | 核心能力 | 相邻维度 | 可替代/互补性 |
|---------|------|---------|---------|-------------|
| **C4 InterFlow** | MIT | 架构即代码（AaC）DSL + 反向工程 + CLI 渲染 | **产物浏览器 / C4 架构浏览**（DR-004 / DR-012） | 强互补：SDLC Visualizer 消费其渲染输出，不做自研 AaC 引擎 |
| **Coco Workflow** | MIT | 复杂度路由（Trivial/Light/Standard/Deep） | **复杂度路由面板**（DR-011） | 思想借鉴：提取路由决策表自研，不直接集成 Claude 专属插件 |
| **OpenUI** | 未明确（WandB） | 高保真原型渲染（React/Vue/Svelte） | **产物浏览器原型预览** | 互补依赖：作为 Docker 服务调用，非自研前端生成管线 |
| **AI Wireframe Generator** | MIT | 领域感知线框引擎（LangGraph StateGraph） | **原型验证层** | 算法借鉴：移植核心模式自研，确保 C4 Container 可映射到页面 |

### 1.3 范式威胁（Non-obvious）

| 项目名称 | 协议 | 威胁向量 | 分析 |
|---------|------|---------|------|
| **OpenHands** | MIT | **全自动闭环替代人机协作** | OpenHands CodeAct 架构在 SWE-bench 达到 77%，若未来集成可视化层，可能直接跳过人工审批驾驶舱模式，形成端到端全自动 SDLC (T3) [M] |
| **GTPlanner / PocketFlow** | MIT | **通用规划框架垂直化** | PocketFlow 的 prep→exec→post 三阶段是通用规划原语，若其团队扩展为软件工程专用领域，可快速构建与 Arsitect 类似的 Stage-Gate 编排能力 (T4) [M] |
| **ChatDev + 可视化插件** | — | **全自动 + 事后可视化** | ChatDev 已是全自动 Waterfall，若叠加开源可视化插件（如 LangGraph Studio 模式），可直接竞争 AI 执行可视化场景 (T5) [L] |

### 1.4 隐性替代方案

| 替代方案 | 描述 | 威胁级别 |
|---------|------|---------|
| **现状维持** | 命令行 + 文件管理器手动管理 Arsitect 项目 | 高（验证痛点真实性的对照组） |
| **Jira + 手动同步** | 在 Jira 中手动创建任务跟踪 AI Skill 执行 | 中（已有工作流惯性） |
| **Notion + 脚本** | 用 Notion 数据库手动记录阶段进度 | 低（无 DAG 依赖表达） |

---

## 2. JTBD 对比矩阵

> 核心 Job Statement：*When 我使用 AI 辅助开发软件时，I want to 管理从需求到上线的完整流程，so I can 确保每一步规范执行、产物可追溯、关键节点不遗漏。*

| 用户任务（JTBD） | 现状维持 | Jira/Linear | Dify/CrewAI | C4 InterFlow | Coco Workflow | OpenHands | SDLC Visualizer（本系统） |
|-----------------|---------|-------------|-------------|--------------|---------------|-----------|------------------------|
| J1: 看到完整阶段地图 | ❌ 无 | ⚠️ 手动建任务 | ⚠️ 需自建阶段语义 | ❌ 仅架构图 | ❌ 仅路由决策 | ❌ 无 | ✅ 内置 9 Stage + 复杂度路由 |
| J2: 实时看 AI 执行进度 | ❌ 黑盒 | ❌ 无 AI 语义 | ⚠️ Agent 日志 | ❌ 无 | ❌ 无 | ⚠️ Docker 日志 | ✅ 拓扑图 + 实时状态同步 |
| J3: Gate 节点快速审批 | ❌ 易遗漏 | ❌ 无 AI 摘要 | ❌ 无 Gate 概念 | ❌ 无 | ❌ 无 | ❌ 全自动无审批 | ✅ AI 自检摘要 + 30s 确认 |
| J4: 统一浏览 AI 产物 | ❌ 散落文件 | ❌ 附件管理 | ⚠️ 输出面板 | ✅ 架构图渲染 | ❌ 无 | ⚠️ 文件系统 | ✅ 多模态渲染 + C4 穿透 |
| J5: 历史项目复盘优化 | ❌ 无沉淀 | ⚠️ 报表导出 | ❌ 无 | ❌ 无 | ❌ 无 | ❌ 无 | ✅ 时间线 + 返工热力图 |
| J6: 复杂度自适应路由 | ❌ 无 | ❌ 无 | ❌ 无 | ❌ 无 | ✅ 四级路由 | ❌ 固定深度 | ✅ 规模评估 + 信号路由 + 人工覆盖 |

**未被充分满足的作业**：
- **J7: 架构设计与代码实现一致性校验** — 当前所有竞品均未提供设计架构 vs 实际代码的漂移检测（仅 Deep 路径支持）
- **J8: 多执行器安全调度** — OpenHands 沙箱 vs Claude Code 本地 vs Aider 批量，无竞品提供统一调度面板

---

## 3. Blue Ocean ERRC 分析

### 3.1 剔除（Eliminate）

| 行业通用做法 | 剔除理由 | 证据 |
|-------------|---------|------|
| 固定五阶段/九阶段流水线 | 简单需求走完整仪式是浪费 | Coco Workflow 洞察 (T3) [H] |
| 通用项目管理（工时/甘特图） | 与 Jira 竞争无差异化 | PRD-000 Non-goals (T5) [H] |
| 多 AI 平台适配（MVP） | 聚焦 Kimi CLI 验证核心体验 | PRD-000 NG-004 (T5) [H] |
| SaaS 化 / 云端存储 | MVP 面向超级个体本地优先 | PRD-000 NG-005 (T5) [H] |

### 3.2 减少（Reduce）

| 行业过度服务的维度 | 减少方式 |
|-------------------|---------|
| Gate 审批步骤数 | 四道 Gate 精简为 AI 辅助 30s 快速确认 |
| 架构文档手动维护 | C4 InterFlow 自动渲染，代码提交即更新 |
| 手动规模估算 | Triage 初估 + Calibrate 精修，两次评估自动化 |
| 产物版本手动管理 | 自动保留 10 版本 + 自动归档 + 一键回滚 |

### 3.3 提升（Raise）

| 维度 | 行业现状 | 本系统目标 |
|------|---------|-----------|
| AI 执行过程可见性 | 命令行黑盒（10-30 分钟无感知） | 拓扑图实时状态 + 产物增量监听 + 日志面板 |
| 架构-代码一致性 | 架构文档与代码脱节 | C4 穿透浏览 + 架构漂移检测（Deep 路径） |
| 流程自适应能力 | 固定模板一刀切 | 复杂度路由（Trivial/Light/Standard/Deep） |
| 安全执行隔离 | 本地文件系统无隔离 | OpenHands Docker 沙箱 + 本地执行器分级调度 |

### 3.4 创造（Create）

| 新维度 | 描述 | 竞品覆盖 |
|--------|------|---------|
| **Skill 语义化编排** | 基于 SKILL.md Frontmatter 动态生成 DAG，非硬编码工作流 | ❌ 无竞品支持 |
| **Draft/Active 双态 + Gate 自检** | 预立项轻量分析 vs 正式执行，关键节点 AI 辅助摘要 | ❌ 无竞品支持 |
| **复杂度-路径-产物** 三级联动 | 规模评估 → 路由决策 → Stage 合并 → Timebox 生成 → 产物预览 | ⚠️ Coco 仅有路由，无可视化联动 |
| **产物多模态渲染 + C4 穿透** | Markdown/Mermaid/Swagger + C4 Context→Container→Component→Code | ⚠️ C4 InterFlow 仅有渲染，无驾驶舱整合 |

---

## 4. 颠覆向量与威胁景观（H1/H2/H3）

| 视野 | 威胁来源 | 向量 | 时间窗口 | 应对策略 |
|------|---------|------|---------|---------|
| **H1（当前）** | Jira/Dify 推出 AI SDLC 可视化 | 功能追赶 | 6-12 个月 | 聚焦 Arsitect 生态深度兼容 + 本地私有化差异化 |
| **H1（当前）** | OpenHands 集成可视化层 | 全自动替代人机协作 | 12-18 个月 | 强调 AI 执行 + 人工把关的协作模式，OpenHands 仅作为安全沙箱执行器 |
| **H2（中期）** | GTPlanner/PocketFlow 垂直化为软件工程专用 | 通用框架下沉领域 | 18-24 个月 | 加速 Arsitect Skill 生态建设（41 个 Skill 规范壁垒） |
| **H2（中期）** | Coco Workflow 脱离 Claude Code 成为独立平台 | 路由理念产品化 | 12-18 个月 | 自研 ComplexityRouter，保持平台中立性 |
| **H3（长期）** | AI 编程助手（Cursor/Copilot）内置项目管理 | IDE 内嵌 SDLC 管理 | 24-36 个月 | 与 IDE 互补而非竞争：IDE 管代码，驾驶舱管流程与产物 |

---

## 5. 战略建议（O→I→R→C→W）

| 层级 | 内容 | 优先级 |
|------|------|--------|
| **O（目标）** | 成为 Arsitect 生态的官方驾驶舱，形成 Skill 规范 + 可视化工具的协同效应 | P0 |
| **I（洞察）** | 六开源项目均为底层基础设施，无一提供面向超级个体的 SDLC 全流程可视化；复杂度自适应是行业空白 | P0 |
| **R（推荐）** | 采取自研内核 + 外部服务化调用策略：自研 ComplexityRouter/StageGateController/WireframeEngine，依赖 C4 InterFlow/OpenHands/OpenUI 作为外部服务 | P0 |
| **C（约束）** | 外部依赖（C4 InterFlow 社区活跃度、OpenHands Docker 体积）可能失效，需预留降级链（Structurizr 备选、Claude Code 回退） | P1 |
| **W（预警）** | 若 OpenHands 或 GTPlanner 在 18 个月内推出集成可视化层，当前差异化窗口将关闭 | P1 |

---

## 6. 假设登记册

| 假设 | 支撑框架 | 置信度 | 推翻条件 | 来源 |
|------|---------|--------|----------|------|
| 六开源项目中无直接竞品 | Blue Ocean 竞争集合分析 | H | 任一项目宣布推出 SDLC 可视化驾驶舱 | GTPlanner 复用策略矩阵 (T1) |
| 复杂度自适应路由是差异化核心 | Blue Ocean 创造维度 | M | 竞品在 12 个月内推出类似四级路由 | Coco Workflow 文档 (T3) |
| OpenHands 不会短期内集成可视化 | 颠覆向量 H1/H2 | M | OpenHands 发布 Studio/Visualizer 组件 | OpenHands 官方 Roadmap (T5) |
| Arsitect 41 个 Skill 规范构成生态壁垒 | 7 Powers 资源独占 | H | 竞品推出兼容 SKILL.md 规范的替代框架 | AGENTS.md (T1) |
| 超级个体接受外部 Docker 作为可选依赖 | JTBD 隐性替代 | H | MVP 期间 >50% 用户反馈部署太重 | ASM-004 (T3) |

---

## 7. 对抗性自我批判

1. **无直接竞品可能是盲区**
   - 弱点：六开源项目均为海外项目，可能忽略了中国市场的低代码/AI 编排工具（如百度千帆、阿里 ModelScope）正在快速迭代。
   - 缓解：在 Gate 1 前补充中国市场竞品扫描。

2. **自研内核 + 外部调用策略的集成风险被低估**
   - 弱点：C4 InterFlow（.NET CLI）、OpenHands（Python Docker）、OpenUI（Node Docker）技术栈差异巨大，本地部署的兼容性测试成本可能超出预期。
   - 缓解：W1 即开始 C4 InterFlow CLI 跨平台安装测试（ASM-001），W4 开始 OpenHands Docker 基准测试（ASM-002）。

3. **Blue Ocean 的创造维度可能需求不足**
   - 弱点：Skill 语义化编排、Draft/Active 双态等创新点基于 Arsitect 规范假设，若目标用户并未实际使用 Arsitect 规范，则这些创新无价值。
   - 缓解：MVP 内测优先招募已有 Arsitect 使用经验的超级个体，验证规范采用率。

---

## 8. 来源

### T1（直接行为数据）
- GTPlanner.txt 复用策略矩阵（第十四章）：六项目协议、复用方式、技术实现
- AGENTS.md：Arsitect 41 个 Skill 规范体系

### T3（专家分析）
- Coco Workflow 复杂度路由理念：简单需求不走完整仪式
- C4 InterFlow Architecture as Code 白皮书（推断）

### T4（行业报告）
- SWE-bench 77%：OpenHands 官方性能数据

### T5（高管声明/项目文档）
- PRD-000 v1.4-draft：竞品格局、Non-goals、执行摘要
- OpenHands / OpenUI 官方 GitHub README

---

> **下游联动**：本报告作为 prd-generation Layer 4 竞品输入，已融入 PRD-000 v1.4-draft 的 3.2 竞品格局、3.3 替代方案、3.4 机会窗口章节。
