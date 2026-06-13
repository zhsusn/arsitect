---
doc_type: CHANGELOG
fragment_id: changelog-sdlc-visualizer-287
title: Research Report - sdlc-visualizer
version: '1.0'
version_type: BASELINE
author: agent-migration
tags:
- sdlc-visualizer
status: DRAFT
iteration: sdlc-visualizer
dependencies:
- fragment_id: prd-sdlc-visualizer-000
  version: 2.0-patch2
---

# Research Report - sdlc-visualizer

---

## 本地文档 {#sec-bendiwendang}
### docs/brainstorming/requirement-draft.md（历史 v1.0） {#sec-docsbrainstormingrequirementdraf}
- **摘要**：定义了 sdlc-visualizer 的初始需求草案，澄清度 0.88。核心为"超级个体的 AI 辅助开发过程可视化"，包含客户叙事、7 个提问维度覆盖、数据口径声明（Skill 数量动态、10 项目上限、4 Gate、1 平台、本地单机）。
- **引用段落**：客户叙事（第 9 行）、数据口径声明（第 47 行）、假设登记册（第 60 行）。
- **与本次差异**：本次在历史基础上增加了 GTPlanner V2 内置、模板驱动、多平台 Adapter 预留、双向同步等决策，覆盖了历史文档中的"待确认项"。

### docs/high-level-requirements/00-requirements-overview.md（PRD v1.4-draft） {#sec-docshighlevelrequirements00requi}
- **摘要**：扩展了 MVP 范围，引入 GTPlanner V2 架构升级交互层（复杂度路由面板 US-011、C4 架构穿透浏览 US-012、架构漂移检测 US-013）。新增假设登记册 ASM-001~ASM-005，引入 OpenHands Docker 和 C4 InterFlow CLI 外部依赖。
- **引用段落**：执行摘要（第 35 行）、GTPlanner V2 相关需求（第 13 行修改记录）、假设登记册（第 86 行）。
- **与本次差异**：历史 PRD 假设 GTPlanner V2 为外部系统（Docker + CLI），本次用户决策改为"内置重新实现"，推翻了 ASM-002 和 ASM-004。

### docs/skill-studio-ui-spec.md（UI 规格书 V2.0） {#sec-docsskillstudiouispecmdui-guiu68}
- **摘要**：定义了基于 `skills/sdlc` 下 25 个 Skill 节点的可视化平台界面原型。包含项目工作台、SDLC 流程画布（拓扑图/泳道/列表）、阶段详情面板、产物浏览器、审批中心、历史回溯六大模块。
- **引用段落**：信息架构（第 24 行）、拓扑图视图（第 107 行）、节点状态说明（第 143 行）。
- **与本次差异**：UI 规格书预设 25 个固定 Skill 节点，本次用户决策为"完全动态化，零预置节点"，UI 需适配动态节点渲染和手动 DAG 调整。

### docs/skill-flow-yaml-schema.md（Schema V1.0） {#sec-docsskillflowyamlschemamdschema-}
- **摘要**：定义了 skill-arsenal 多 Agent 编排引擎的声明式工作流 Schema，包含 Stage 定义（Skill 调用、并行、Gate、条件分支、错误处理）、产物传递、状态持久化。
- **引用段落**：Schema 顶层结构（第 28 行）、Stage 定义（第 62 行）、完整示例（第 106 行）。
- **与本次差异**：Schema 未涉及模板驱动或动态 Skill 导入的交互，本次需扩展"模板选择 -> DAG 生成"的衔接逻辑。

### docs/competitive-analysis/competitive-analysis.md {#sec-docscompetitiveanalysiscompetiti}
- **摘要**：对比了 Dify、CrewAI + CrewAI Studio、LangGraph + LangGraph Studio、Jira/Linear、ChatDev 五款竞品。结论：本系统聚焦"AI 辅助软件开发全生命周期管理"，差异化在于 SDLC 语义覆盖、软件工程纪律（Draft/Active、四道 Gate）、人机协作模式。
- **引用段落**：竞品格局（第 3.2 节）、替代方案与决策（第 3.3 节）。
- **与本次关系**：竞品分析结论仍然有效，无需更新。

---

## 交叉验证 {#sec-jiaou53c9yanu8bc1}
### 冲突点 1：Skill 数量 {#sec-u51b2u7a81u70b9-1skill-shuliang}
- **本地文档 A**（UI 规格书 V2.0）：预设 25 个 Skill 节点
- **本地文档 B**（AGENTS.md）：实际 41 个 Skill
- **本地文档 C**（历史 requirement-draft）：Skill 数量动态，以用户导入为准
- **本次决策**：完全动态化（零预置），由用户导入决定
- **验证结论**：本次决策统一了历史冲突，以用户最新回答为准。UI 规格书需从"25 固定节点"升级为"动态节点 + 模板推荐"。

### 冲突点 2：GTPlanner V2 依赖形态 {#sec-u51b2u7a81u70b9-2gtplanner-v2-yi}
- **本地文档 A**（PRD v1.4）：假设 C4 InterFlow CLI 和 OpenHands Docker 为外部依赖（ASM-001~ASM-004）
- **本地文档 B**（历史 requirement-draft）：未涉及 GTPlanner V2
- **本次决策**：GTPlanner V2 内置重新实现，不依赖外部 Docker
- **验证结论**：用户明确推翻历史假设，需在假设登记册中登记 A-008（内置工作量风险），并准备降级方案。

### 冲突点 3：DAG 构建方式 {#sec-u51b2u7a81u70b9-3dag-goujianu65b}
- **本地文档 A**（skill-flow-yaml-schema）：由用户编写 YAML 显式定义 DAG
- **本地文档 B**（AGENTS.md）：Skill 间上下游关系通过 SKILL.md 正文描述
- **本次决策**：自动解析 SKILL.md 提取上下游引用 + 用户手动调整
- **验证结论**：混合模式兼顾智能化与灵活性，但需验证 SKILL.md 中上下游引用的文本模式是否足够规范（如"下游衔接：prd-generation"）。

### 冲突点 4：产物同步方向 {#sec-u51b2u7a81u70b9-4chanu7269tongbu}
- **本地文档 A**（历史 requirement-draft）：待确认项 Q4，倾向双向同步但策略未定
- **本地文档 B**（PRD v1.4）：未明确产物编辑能力
- **本次决策**：双向同步，文件系统优先冲突解决
- **验证结论**：决策已锁定，数据层需实现文件系统事件监听 + 哈希校验 + 弹窗提示。

---

## 研究局限性 {#sec-u7814u7a76u5c40xianxing}
1. **无网络搜索**：本次资料收集以本地历史文档为主，未执行实时网络搜索。竞品信息（Dify、CrewAI 等）均来源于历史文档，若竞品在 2026-05-31 至 2026-06-01 期间有重大更新，可能存在信息滞后。
2. **Kimi CLI 协议未验证**：CLI 实时状态捕获的技术可行性（如是否支持 JSON Lines 进度输出）尚未通过 POC 验证，依赖于假设 A-004。
3. **SKILL.md 解析模式未抽样**：自动解析 DAG 的准确性依赖于 SKILL.md 中上下游引用的文本规范性，尚未对 41 个 Skill 进行全量抽样验证。

---

## 下游传递路径 {#sec-xiau6e38chuanu9012lujing}
| 文档 | 路径 | 用途 |
|------|------|------|
| requirement-draft.md | `openspec/changes/sdlc-visualizer/brainstorming/requirement-draft.md` | 衔接 prd-generation 的核心输入 |
| ai-architecture-decision.md | `openspec/changes/sdlc-visualizer/brainstorming/ai-architecture-decision.md` | 影响 PRD 的 05-non-functional.md AI 架构需求章节 |
| review-prep.md | `openspec/changes/sdlc-visualizer/brainstorming/review-prep.md` | Gate 1 评审准备材料 |
| research-report.md | `openspec/changes/sdlc-visualizer/brainstorming/research-report.md` | PRD Layer 1 和 Layer 4 的竞品/技术输入 |
| brainstorming-log.md | `openspec/changes/sdlc-visualizer/brainstorming/brainstorming-log.md` | 决策追溯 |

---

## 附录：历史补充内容（来自 docs/ 目录） {#sec-u9644luu5386u53f2u8865u5145u5185}
> 生成时间：2026-05-31 14:54
> 来源类型：local（hybrid 中本地文档优先，未触发网络搜索）

| 文件名 | 路径 | 摘要 | 关联度 |
|--------|------|------|--------|
| AI_Code_v3.2.md | @docs/AI_Code_v3.2.md | AI Code 研发平台 PRD v3.3，含双态模型、HITL、六层架构、状态机、RACI、演进路线、技术栈选型（React 19 + FastAPI + SQLite/PostgreSQL） | 直接相关 |
| skill-studio-ui-spec.md | @docs/skill-studio-ui-spec.md | SDLC 可视化平台 UI 规格书 V2.0，定义流程画布、阶段详情、产物浏览器、审批中心、历史回溯等页面原型与前端技术栈 | 直接相关 |
| skill-flow-yaml-schema.md | @docs/skill-flow-yaml-schema.md | Skill Flow YAML Schema V1.0，定义声明式编排语法、DAG 调度、Gate 审批、数据流、状态机、Skill Adapter、CLI/API 接口 | 直接相关 |
| AGENTS.md | @AGENTS.md | Arsitect 项目全局说明，41 个 Skill 清单、目录规范、OpenSpec 变更管理体系、12 阶段 SDLC 与人工闸门规则 | 直接相关 |

## 交叉验证结果 {#sec-jiaou53c9yanu8bc1jieu679c}
- [一致] 三份参考文档均支持 Draft/Active 双态、四道 Gate（Gate-1/2.5/2/3）、HITL Waiting 状态。
- [一致] 技术栈方向一致：React 19 + FastAPI + 关系型数据库。
- [冲突] UI 规格书预设 25 个 Skill 节点，AGENTS.md 记录 41 个；用户决策：以实际导入为准，不限定数量。
- [冲突] UI 规格书建议 Git API 读取产物；用户决策：独立数据库 + Kimi CLI 实时联动。
- [冲突] PRD v3.3 规划 MVP 4 周 + P1 2 周 + P2 4 周 + P3 4 周；用户决策：原型先行，节奏可调整。

## 可信度总览 {#sec-u53efxinduzonglan}
- 高可信度：4 条（全部为项目内部文件，由用户直接提供）
- 中可信度：0 条
- 低可信度：0 条

## 关键发现 {#sec-guanu952efaxian}
1. **平台本质差异**：参考文档中 UI 规格书偏向"可视化驾驶舱"（只读展示），而 YAML Schema 文档设计了完整的编排执行引擎（Scheduler/Executor/State Manager）。用户明确要求"内置 Skill Flow 编排引擎"，因此本平台是"可视化+执行"一体化，而非纯看板。
2. **超级个体重塑 Gate 体验**：传统四道 Gate 是为多人团队设计的会签/审批机制。在单人场景下，Gate 的核心价值从"他人把关"转变为"AI 辅助自检+用户快速确认"。产品需在 UI 上将"审批"重新包装为"阶段确认清单+风险提示"。
3. **Skill 动态发现机制**：用户选择手动注册/导入 Skill 路径，意味着平台不能写死 25 或 41 个节点。画布必须是动态生成的：用户导入路径 -> 平台解析 SKILL.md Frontmatter -> 按 skill-flow.yaml 的 stages 定义或自动拓扑排序渲染节点。
4. **产物存储双轨制**：用户要求"自己维护独立数据库"，但 Skill 执行产物（Markdown/YAML）天然适合文件系统存储。设计阶段需决策：数据库保存执行状态/元数据/审批记录，产物文件保存于本地文件系统（如 `~/.sdlc-visualizer/projects/{id}/`），两者通过路径关联。
5. **Kimi CLI 集成约束**：Skill 执行通过调用本地 Kimi CLI 完成。CLI 的执行模型是进程级的（启动 -> 执行 -> 退出），与平台需要的"实时状态推送"存在架构张力。需在概要设计阶段明确：是通过轮询产物文件/日志，还是通过 CLI 的 stdout/stderr 捕获中间状态。

---

## 附录：adaptive-architecture-engine 补充内容 {#sec-u9644luadaptivearchitectureengin}
# Research Report - adaptive-architecture-engine

## 变更背景 {#sec-biangengbeijing}
arsitect 当前采用固定五阶段流水线（Domain -> Sketch -> Tech -> Validate -> Design），对所有需求执行相同仪式。本次调研旨在寻找开源方案，实现：
1. 架构模型标准化（Architecture as Code）
2. 流程自适应（根据复杂度选择路径）
3. 自动执行与验证（沙箱 + 反向工程）

## 网络资料 {#sec-u7f51u7edcu8d44u6599}
- [高相关] C4 InterFlow GitHub - https://github.com/plantuml/C4-PlantUML / https://github.com/plantuml/plantuml-c4：提供 C4 DSL 和 CLI 渲染能力，支持反向工程。
- [高相关] OpenHands (OpenDevin) GitHub - https://github.com/All-Hands-AI/OpenHands：CodeAct 架构，SWE-bench 77%，支持 Docker 沙箱自主执行。
- [高相关] Coco Workflow 设计理念：Claude Code 插件，核心洞察为"不同复杂度需求应走不同流程"。
- [中相关] GTPlanner / PocketFlow 架构：通用异步工作流引擎，采用 prep -> exec -> post 三阶段节点生命周期。
- [中相关] OpenUI (WandB) - https://github.com/wandb/openui：自然语言生成多框架前端代码并实时预览。
- [中相关] AI Wireframe Generator：基于 LangGraph StateGraph 的多 Agent 线框图生成流水线。

- `docs/GTPlanner.txt`：六项目深度调研与复用策略矩阵，涵盖架构调整总览、数据模型、复杂度路由、执行器对比、CI/CD 集成方案。

- [一致] C4 InterFlow MIT 协议允许 CLI 调用 + DSL 扩展，与 arsitect 自研策略无冲突。
- [一致] OpenHands Docker 隔离方案与 arsitect 安全要求（禁止 AI 自动执行高危操作）兼容，沙箱结果需人工合并。
- [一致] Coco Workflow 的信号-路径映射思想可零代码借鉴，不引入平台绑定。
- [冲突已解决] GTPlanner 的 PocketFlow 节点语义与 arsitect 架构语义不匹配，决定只借鉴生命周期协议，自研 ArchitectNode。
- [冲突已解决] OpenUI 协议未明确，按保守策略假设 MIT/Apache，以 Docker 服务方式调用。

## 关键数据口径 {#sec-guanu952eshujukoujing}
| 指标 | 数值 | 来源 | 状态 |
|------|------|------|------|
| OpenHands SWE-bench 性能 | 77% | OpenHands 官方报告 | 锁定 |
| C4 InterFlow 反向工程支持语言 | Java/Go/C#（优先） | C4 InterFlow README | 锁定 |
| 复杂度分级数 | 4 级（Trivial/Light/Standard/Deep） | Coco Workflow 借鉴 | 锁定 |
| 实施周期 | 6 周 | 项目估算 | 预计 |
| 新增外部服务依赖 | 3 个（C4 InterFlow CLI、OpenHands、OpenUI） | 调研结论 | 锁定 |
