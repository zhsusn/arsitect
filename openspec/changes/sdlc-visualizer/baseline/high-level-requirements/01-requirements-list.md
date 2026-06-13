---
doc_type: PRD
fragment_id: prd-sdlc-visualizer-001
title: 01 - 需求清单
version: 2.0-patch2
version_type: BASELINE
author: agent-migration
tags:
- sdlc-visualizer
- architecture
status: FROZEN
iteration: sdlc-visualizer
dependencies:
- fragment_id: arch-sdlc-visualizer-001
  version: '1.0'
- fragment_id: prd-sdlc-visualizer-000
  version: 2.0-patch2
c4_binding:
  level: L1
---

# 01 - 需求清单


> **C4 绑定引用**：
> - `@C4-L1-Actor:developer`
> - `@C4-L1-System:git`
> - `@C4-L1-System:kimi-cli`
> - `@C4-L1-System:local-filesystem`

v2.0-patch2：扩展 Wireframe 页面类型至 7 种（列表/详情/仪表盘/表单/弹窗/搜索/向导）；新增 US-017（需求草图生成）+ REQ-P0-040；更新 RTM。

## 1. 范围与边界 {#sec-1-fanweiyuu8fb9u754c}
### 1.1 In-Scope {#sec-11-inscope}
- **项目治理**：Workspace / Application / Project / Module 的 CRUD，Draft/Active 双态管理，项目健康度计算。
- **SDLC 可视化**：拓扑图视图（动态节点+依赖连线）、泳道视图（按阶段分组）、列表视图（批量筛选）。
- **Skill Flow 编排**：YAML 驱动 DAG 调度、并行执行、条件分支、失败重试（rollback/retry/skip/notify）、产物传递。
- **Skill 执行与调度**：Kimi CLI 本地调用，统一遵循 PocketFlow 三阶段生命周期（prep-exec-post）；输入注入、输出捕获、日志收集、状态持久化；多平台 Adapter 接口预留。
- **Gate 自检确认**：四道 Gate（Gate-1/2.5/2/3）的 Waiting 状态管理、AI 辅助摘要生成、快速确认/驳回/重试、历史追溯。
- **产物管理**：产物存储/检索、版本管理、Markdown/Mermaid/Swagger/YAML/JSON 多模态渲染、**平台内编辑写回**、**Git 快照与 diff 对比**。
- **实时同步**：Skill 状态变更 WebSocket 推送、Gate 等待通知、产物增量监听、**文件系统事件监听与冲突检测**。
- **历史分析**：已完成项目时间线、阶段耗时对比、返工热力图。
- **Skill 注册**：用户手动注册/导入 Skill 路径、Frontmatter 解析、画布动态生成、**SKILL.md 上下游引用自动解析 + 手动调整 DAG**。
- **模板引擎**：管理员预制模板（Trivial/Light/Standard/Deep）、模板与项目弱关联、阶段-Skill 绑定推荐及跳过阶段定义、模板偏离记录。
- **复杂度路由**：基于五维度规模评估（模块数/接口数/页面数/技术复杂度/风险等级）的复杂度信号采集与等级判定，自动路由 Trivial/Light/Standard/Deep 四级执行路径，可视化路径差异，支持人工覆盖。
- **C4 架构浏览**：平台根据概要设计**自动生成** C4 L1 Context / L2 Container DSL，支持层级穿透下钻；用户可手动覆盖 DSL 内容。
- **OpenUI 原型验证**：平台根据 C4 Container 图和接口契约生成 OpenUI 提示词，调用 OpenUI 服务获取可交互 HTML 原型，支持实时预览。
- **WireframeEngine 线框图**：领域感知线框生成，基于 C4 模型映射领域实体到页面结构，生成 SVG 线框图，支持接口覆盖度检查。
- **产物审查与重新生成**：产物行内批注、Stage 审查面板、参考资料注入、AI 基于反馈重新生成、diff 对比、版本历史与回滚。

### 1.2 Out-of-Scope {#sec-12-outofscope}
- 多租户与企业级 RBAC（P1 后考虑）。
- 多 AI 平台适配实现（Claude/Cursor/MCP），MVP 仅支持 Kimi CLI + 预留接口。
- 通用项目管理（任务分配、工时统计、甘特图、资源调度）。
- 外部 CI/CD 工具链替代（如替代 GitHub Actions、GitLab CI）。
- 底层 LLM 基座选型与训练。
- 产物云端存储/SaaS 化（MVP 仅本地文件系统）。
- 实时协同编辑（多用户同时操作同一项目）。
- 移动端适配（P2 评估）。
- 架构漂移检测的自动修复建议（P1 后评估）。
- CI/CD 架构文档即代码流水线（P2 评估）。
- C4 InterFlow 架构查询引擎（JSONPath-like 影响分析）（P1 后评估）。

### 1.3 Non-goals（非目标） {#sec-13-nongoalsfeimubiao}
Non-goals 见 `00-requirements-overview.md` 第 4.3 节，此处不再重复。

---

## 2. 业务术语表 {#sec-2-yewuu672fu8bedbiao}
> 术语表前置到第 2 节，确保后文首次出现术语时读者已具备定义。

| 术语 | 定义 | 使用场景 |
|------|------|----------|
| **Arsitect** | AI 驱动软件工程全生命周期管理平台，包含 41 个 Skill 的规范体系 | 全文 |
| **Workspace** | 团队/部门的研发资源边界，含多个应用；MVP 阶段简化为本地单机默认 Workspace | 项目治理 |
| **Application** | 长期存在的产品或系统，有独立用户群体和技术栈；Project 必须绑定一个 Application | 项目治理 |
| **Module** | 应用内的功能子域，可独立设计、独立交付，有独立里程碑状态 | 项目治理 |
| **Skill** | AI 能力单元，由 SKILL.md（YAML Frontmatter）+ meta.json 定义，执行特定 SDLC 任务并产出工件；执行遵循 PocketFlow prep-exec-post 三阶段生命周期 | 全文 |
| **Stage（SDLC 阶段）** | 软件交付标准阶段，如需求探索 / 概要需求 / 详细需求 / 概要设计 / 详细设计 / 编码 / 测试 / 发布 / 归档。每个 Stage 可绑定 1-n 个 Skill（1 个主 Skill + 0-n 个辅助 Skill） | 流程描述 |
| **Skill Flow** | 声明式 YAML 工作流，定义 Stage 间的依赖关系、Stage 内 Skill 编排、数据流转、审批节点与错误处理策略 | 编排引擎 |
| **Gate** | 人工审批节点，阻塞下游 Stage 解锁，共四道（Gate-1 概要需求 / Gate-2.5 详细需求 / Gate-2 概要设计 / Gate-3 UAT） | 流程描述 |
| **Draft/Active 双态** | 预立项 Draft 态（轻量分析，仅允许分析型 Skill）与正式执行 Active 态（完整流程，允许执行型 Skill） | 项目治理 |
| **HITL** | Human-in-the-Loop，人工参与关键决策节点，实现"AI 执行、人工把关"；支持旁路审批（先执行后补审） | 审批流程 |
| **Waiting** | Skill 执行到 Gate 节点时的暂停状态，释放执行锁，等待用户确认后继续 | 状态机 |
| **产物（Artifact）** | Skill 执行生成的文件（Markdown、YAML、JSON、代码等），存储于本地文件系统 | 产物管理 |
| **Git 快照** | 平台为每个产物文件自动维护的本地 Git 仓库版本历史，支持 diff 对比和一键回滚 | 产物管理 |
| **拓扑图** | SDLC 流程画布的一种视图，以 Skill 为节点、依赖关系为连线，展示项目执行拓扑 | 可视化 |
| **PocketFlow** | Skill 执行的三阶段生命周期：prep（准备输入/上下文）→ exec（调用 AI/CLI 执行）→ post（产物处理/质量检查/Git 快照） | 执行引擎 |
| **复杂度路由（Complexity Router）** | 基于五维度规模评估的流程路径推荐系统。综合模块数/接口数/页面数/技术复杂度/风险等级自动判定复杂度等级，推荐 Trivial/Light/Standard/Deep 四级路径，支持人工覆盖 | 流程描述 |
| **C4 Interactive Navigator** | C4 架构模型层级穿透浏览器，支持从 Context 图逐层下钻到 Code 级（Context → Container → Component → Code），并支持手动编辑任意层级 DSL | 可视化 |
| **超级个体** | 独立开发者或全栈自由职业者，一人承担产品、设计、开发、测试、运维多角色 | 用户画像 |
| **模板（Template）** | 管理员预制的复杂度路径模板（Trivial/Light/Standard/Deep），定义阶段与 Skill 的推荐绑定关系及跳过阶段。与项目为弱关联，允许执行过程中偏离 | 项目治理 |
| **审查（Review）** | 人工对 AI 生成产物的检查与批注过程，含行内批注、全局修改建议、参考资料注入。审查通过后才可进入 Gate 审批 | 质量保障 |
| **迭代修改（Revision）** | 基于人工审查反馈和参考资料，AI 重新生成产物的过程。每次重新生成产生新版本，支持版本对比 | 质量保障 |
| **参考资料（Reference）** | 用户向 AI 提供的辅助材料（竞品链接、设计规范、代码规范、示例文档、截图），作为重新生成的上下文输入 | 质量保障 |
| **REVIEW_PENDING** | 主 Skill 产物生成后的等待审查状态，节点显示"待审查"徽章。必须人工审查通过后才可流转到 GATE_PENDING 或 PASSED | 状态机 |

---

## 3. 用户故事与验收标准 {#sec-3-yonghuguu4e8byuyanshoubiaozhun}
### US-001：创建项目并选择模板 {#sec-us001chuangjianu9879mubingxuanu6}
**应用场景（Given/When）**：
Given 用户已打开平台首页，When 点击"新建项目"

**完整操作路径**：
1. 用户点击首页"新建项目"按钮
2. 系统弹出项目创建表单
3. 用户选择或创建 Application（确定技术栈、历史继承）
4. 用户填写项目名称、描述（可选）
5. 系统自动执行 Skill-SizeEstimate（Triage 初估）：输入业务目标，输出规模区间 [乐观, 预期, 保守] + 推荐复杂度路径
6. 系统展示模板选择面板（Trivial / Light / Standard / Deep），显示各模板的阶段-Skill 绑定预览和跳过阶段说明
7. 用户选择模板（可随时切换，默认按 Triage 结果推荐）
8. 系统实时校验输入合法性
9. 用户确认创建，系统初始化项目目录、数据库记录、以及产物 Git 仓库
10. 系统自动进入 Draft 态，根据模板预设生成初始 SDLC 画布节点（仅渲染用户已导入的 Skill）

**用户目标（So That）**：
在 1 分钟内创建结构化的 SDLC 项目，基于模板获得标准化起点，同时保留后续灵活调整的空间。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given 用户已打开平台，When 填写有效项目名称（1-100 字符）并选择模板后提交，Then 系统在 500ms 内创建项目，自动跳转项目工作台，项目状态为 Draft，画布根据模板和已导入 Skill 渲染节点。
- **AC2（Negative Path）**：Given 用户未填写项目名称，When 点击提交，Then 系统在 200ms 内提示"项目名称为必填项"，禁止提交。
- **AC3（Edge Case）**：Given 用户输入项目名称已存在，When 点击提交，Then 系统提示"项目名称已存在，请修改"，保留其他表单数据不丢失。
- **AC4（Non-behavioral）**：Given 项目创建完成，When 检查产物目录，Then 发现该目录下已初始化 Git 仓库（`.git/` 存在）。

**关联 JTBD**：J1
**优先级**：P0

---

### US-002：浏览 SDLC 拓扑图并执行 Skill {#sec-us002u6d4flan-sdlc-u62d3u6251tub}
**应用场景（Given/When）**：
Given 用户已进入项目工作台且项目处于 Active 态，When 点击画布中某个未开始节点

**完整操作路径**：
1. 用户在项目工作台点击"进入画布"
2. 系统加载该项目的 SDLC 拓扑图（动态生成节点和连线）
3. 用户查看节点状态（NOT_STARTED / IN_PROGRESS / REVIEW_PENDING / REVISION_REQUESTED / PASSED / BLOCKED / GATE_PENDING / BYPASSED）
4. 用户点击一个前置依赖已满足的未开始节点
5. 右侧滑出阶段详情面板，展示 Skill 指令快照和输入产物
6. 用户点击"执行 Skill"
7. 系统调用 Kimi CLI，节点状态变为 IN_PROGRESS
8. 用户可查看实时日志或等待产物生成
9. 执行完成后，节点状态自动更新，输出产物出现在详情面板

**用户目标（So That）**：
直观地看到项目全生命周期状态，一键触发 AI 执行并获取产物。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given 项目处于 Active 态且前置节点已 PASSED，When 用户点击 NOT_STARTED 节点并执行 Skill，Then 系统在 3s 内触发 Kimi CLI，节点状态变为 IN_PROGRESS，右侧面板展示实时日志流。
- **AC2（Negative Path）**：Given 前置节点未 PASSED，When 用户点击下游节点，Then 系统提示"前置依赖未完成，不可执行"，禁用执行按钮。
- **AC3（Edge Case）**：Given Kimi CLI 未安装或版本不兼容，When 用户执行 Skill，Then 系统捕获错误并在面板中展示安装引导链接，节点状态变为 BLOCKED。

**关联 JTBD**：J2
**优先级**：P0

---

### US-003：在 Gate 节点进行自检确认 {#sec-us003zai-gate-u8282u70b9jinxingz}
**应用场景（Given/When）**：
Given Skill 执行完成且该节点关联 Gate，When 系统弹出 Gate 确认卡片

**完整操作路径**：
1. Skill 执行成功，节点状态变为 GATE_PENDING
2. 系统自动生成 Gate 自检摘要（关键风险点 + 待补充项清单）
3. 用户收到通知（页面内提示 + 可选声音）
4. 用户点击节点或通知，进入审批中心
5. 用户查看待审产物列表和快速预览
6. 用户阅读 AI 生成的自检摘要
7. 用户选择"确认通过"（可附加评语）或"返回补充"
8. 系统记录决策时间戳和评语，更新节点状态
9. 若通过，下游节点解锁；若驳回，节点状态变为 BLOCKED，用户可重试

**用户目标（So That）**：
在 30 秒内完成关键节点的风险确认，避免遗漏重要检查项。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given Gate 节点处于 GATE_PENDING 且 AI 摘要已生成，When 用户阅读摘要后点击"确认通过"，Then 系统在 500ms 内记录决策，节点状态变为 PASSED，下游节点在 1s 内解锁为可执行状态。
- **AC2（Negative Path）**：Given 用户发现产物存在严重问题，When 点击"返回补充"并填写理由，Then 节点状态变为 BLOCKED，系统提示"请修复后重新提交"，保留历史决策记录。
- **AC3（Edge Case）**：Given AI 摘要生成失败或置信度为"低"，When 用户查看 Gate 卡片，Then 系统强制展示"摘要置信度低，请查看原始产物"警告，禁用一键通过，要求用户至少浏览一份产物后才可确认。

**关联 JTBD**：J3
**优先级**：P0

---

### US-004：浏览、编辑和管理产物 {#sec-us004u6d4flanbianjiheguanlichanu}
**应用场景（Given/When）**：
Given 用户已完成一个或多个 Skill 的执行，When 点击"产物浏览器"

**完整操作路径**：
1. 用户在阶段详情面板或顶部导航点击"产物浏览器"
2. 系统展示产物目录树（按项目/阶段/Skill 组织）
3. 用户点击某 Markdown 产物
4. 系统渲染 Markdown 内容，包括代码高亮、Mermaid 图表实时转换
5. 用户点击"编辑"按钮，进入文本编辑器模式
6. 用户修改产物内容（如修正设计文档中的错别字或补充说明）
7. 用户点击"保存"，系统检测外部文件系统是否被修改
8. 若外部未修改，直接写回文件系统并自动创建 Git 快照；若外部已修改，提示用户冲突并询问是否覆盖
9. 用户可点击"版本历史"查看该产物的 Git 快照列表、diff 对比和一键回滚

**用户目标（So That）**：
无需离开平台即可查看、编辑和版本管理所有 AI 生成的产物，获得比纯文本更好的阅读和协作体验。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given 产物文件存在且格式为 Markdown，When 用户在产物浏览器中点击该文件，Then 系统在 500ms 内渲染完整内容，Mermaid 代码块在 2s 内完成图表渲染。
- **AC2（Negative Path）**：Given 产物文件被外部删除，When 用户点击该文件，Then 系统提示"产物文件不存在，可能已被外部删除"，提供"刷新目录"按钮。
- **AC3（Edge Case）**：Given 产物文件体积 > 10MB，When 用户点击该文件，Then 系统提示"文件较大，建议下载后查看"，提供分页预览（前 5000 字）和完整下载选项。
- **AC4（Happy Path - 编辑）**：Given 用户在平台内编辑产物并点击保存，When 外部文件系统未发生变更，Then 系统在 1s 内写回文件系统并自动创建 Git 提交，提交信息包含时间戳和编辑摘要。
- **AC5（Negative Path - 冲突）**：Given 用户在平台内编辑产物期间外部文件被修改，When 用户点击保存，Then 系统检测哈希变化并弹窗提示"外部已变更，确认覆盖？"，用户确认后方可保存。
- **AC6（Edge Case - 回滚）**：Given 产物已有 3 个以上 Git 快照，When 用户选择回滚到第 2 个版本，Then 系统恢复该版本内容至文件系统，创建新的回滚提交，并在版本历史中标记为"回滚恢复"。

**关联 JTBD**：J2
**优先级**：P0

---

### US-005：导入 Skill 并生成画布节点 {#sec-us005daoru-skill-bingshengu6210h}
**应用场景（Given/When）**：
Given 用户本地有新的 Skill 目录，When 进入 Skill 管理页面

**完整操作路径**：
1. 用户点击"Skill 管理"
2. 系统展示已注册的 Skill 列表
3. 用户点击"导入 Skill"
4. 用户选择本地目录或拖拽文件夹
5. 系统解析 SKILL.md Frontmatter 和 meta.json
6. 系统校验 Skill 格式合法性
7. 系统自动解析 SKILL.md 中的上下游 Skill 引用，构建 DAG 边建议
8. 系统展示预览（节点名称、描述、阶段归属、上下游连接建议）
9. 用户可手动调整 DAG 连线
10. 用户确认导入
11. 系统更新画布节点库，现有项目可选择是否启用新 Skill

**用户目标（So That）**：
将自定义 Skill 纳入平台管理，自动解析依赖关系，减少手动配置成本。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given 用户导入符合规范的 Skill 目录，When 解析完成后，Then 系统在 2s 内展示节点预览，上下游引用解析准确率 >= 80%。
- **AC2（Negative Path）**：Given 用户导入格式错误的 Skill（如缺失 meta.json），When 解析失败，Then 系统提示具体错误原因（如"meta.json 缺失"），提供修复建议。
- **AC3（Edge Case）**：Given 导入的 Skill 与已有 Skill 名称冲突，When 用户确认导入，Then 系统提示"名称冲突，是否覆盖？"，覆盖后更新所有关联项目的画布节点。

**关联 JTBD**：J1
**优先级**：P0

---

### US-006：查看历史项目统计 {#sec-us006chakanu5386u53f2u9879mutong}
**应用场景（Given/When）**：
Given 用户已完成至少一个项目，When 进入"历史回溯"页面

**完整操作路径**：
1. 用户点击导航"历史回溯"
2. 系统展示已完成项目列表
3. 用户选择某个项目，查看时间线视图
4. 用户查看各阶段耗时对比
5. 用户查看返工热力图（哪些阶段频繁重试/驳回）
6. 用户可导出统计报告

**用户目标（So That）**：
从历史项目中提取经验，优化后续项目的执行策略。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given 用户有 3 个已完成项目，When 进入历史回溯，Then 系统展示项目列表，点击后渲染时间线和阶段耗时对比图表。
- **AC2（Edge Case）**：Given 用户仅有 1 个已完成项目，When 进入历史回溯，Then 系统提示"数据不足，建议完成至少 2 个项目后查看对比"，仍展示单项目时间线。

**关联 JTBD**：J4
**优先级**：P1

---

### US-007：评估项目规模并调整执行路径 {#sec-us007pingguu9879muguimobingtiaou}
**应用场景（Given/When）**：
Given 项目处于 Draft 态且已生成需求产物，When 用户点击"规模评估"

**完整操作路径**：
1. 用户在 Draft 项目点击"规模评估"
2. 系统自动扫描需求产物，统计文件数、实体数、跨服务标记
3. 系统基于规则引擎计算复杂度等级（XS / S / M / L / XL）
4. 系统推荐匹配的复杂度路径（Trivial / Light / Standard / Deep）
5. 用户查看推荐结果，可选择接受或手动覆盖
6. 若用户偏离推荐模板，系统记录偏离原因
7. 评估结果影响后续画布节点推荐和执行路径

**用户目标（So That）**：
根据项目实际规模获得合理的执行路径建议，避免过度设计或遗漏关键步骤。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given 项目需求产物包含 5 个实体和 3 个模块，When 执行规模评估，Then 系统在 3s 内返回复杂度等级为 M，推荐 Standard 模板。
- **AC2（Negative Path）**：Given 需求产物为空或格式异常，When 执行规模评估，Then 系统提示"需求产物不足，无法评估"，允许用户手动选择模板。
- **AC3（Edge Case）**：Given 用户手动选择 Simple 模板但项目规模实际为 L，When 执行过程中系统检测到规模不匹配，Then 在项目工作台展示警告"当前规模可能超出模板建议范围"，允许用户随时调整。

**关联 JTBD**：J5
**优先级**：P0

---

### US-008：配置里程碑 Timebox {#sec-us008peizhiliu7a0bu7891-timebox}
**应用场景（Given/When）**：
Given 项目处于 Active 态，When 用户进入项目设置

**完整操作路径**：
1. 用户点击项目设置
2. 用户查看系统基于规模评估生成的 Timebox 初稿
3. 用户调整各阶段的时间预期
4. 系统保存 Timebox 配置
5. 执行过程中，系统监控各阶段耗时，到期前发送预警
6. 若阶段超时，用户可选择裁剪非核心需求或延长时间

**用户目标（So That）**：
为项目设定合理的时间边界，防止单一阶段无限蔓延。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given 用户设置 Timebox 为 14 天，When 项目执行到第 12 天，Then 系统发送预警通知"距离 Timebox 到期还剩 2 天"。
- **AC2（Edge Case）**：Given 阶段已超时，When 用户选择"裁剪需求"，Then 系统展示可裁剪的非核心需求列表，用户确认后更新执行计划。

**关联 JTBD**：J1
**优先级**：P0

---

### US-009：审查 AI 产物并提交迭代修改建议 {#sec-us009shencha-ai-chanu7269bingtij}
**应用场景（Given/When）**：
Given 用户已完成一个 Stage 的主 Skill 执行且产物已生成，When 进入阶段详情面板的"审查"Tab

**完整操作路径**：
1. 主 Skill 执行完成，产物生成后，系统自动进入 REVIEW_PENDING 状态，节点显示"待审查"徽章
2. 用户点击 Stage 节点，进入阶段详情面板
3. 用户切换到"审查"Tab，查看主 Skill 产物
4. 用户在 Artifact Viewer 中高亮文本并添加评论气泡（批注关联到文件、行号和版本）
5. 用户在全局修改建议输入框中填写结构化建议（P0阻塞/P1建议/P2优化）
6. 用户拖拽/粘贴参考资料（URL/文件/文本）到参考资料区
7. 系统展示已添加的批注列表和参考资料引用摘要
8. 用户确认修改建议后，点击"提交审查"（或一键"无批注通过"）
9. 系统校验浏览时长 >=30 秒（BR-024），记录审查结果，状态从 REVIEW_PENDING 流转到 GATE_PENDING（若有关联 Gate）或 PASSED（若无关联 Gate）
10. 若用户选择"提交修改建议"，状态变为 REVISION_REQUESTED，用户可点击"重新生成"，系统携带前序版本全部批注和参考资料作为上下文触发 Skill 重新执行
11. 系统生成新版本，用户可查看版本列表、diff 对比（增删改高亮），或回滚到任意历史版本

**用户目标（So That）**：
在平台内完成对 AI 生成产物的质量把关，通过结构化批注和参考资料注入提升重新生成的准确性。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given 产物已生成且用户进入审查面板，When 用户高亮文本添加批注并提交 P1 建议后点击"重新生成"，Then 系统在 5s 内触发 Skill 重新执行，新版本产物在 3 分钟内生成，且批注内容出现在执行日志的上下文注入记录中。
- **AC2（Negative Path）**：Given 用户未浏览任何产物且停留时间 < 30 秒，When 点击"提交审查"，Then 系统提示"请至少浏览 1 份产物并停留 30 秒以上"，禁止提交。
- **AC3（Edge Case）**：Given 产物版本历史已有 10 个版本，When 重新生成第 11 个版本，Then 系统自动将最早版本归档到压缩存储，版本列表仅保留最近 10 个版本。
- **AC4（Edge Case）**：Given 用户选择回滚到第 3 个历史版本，When 点击"回滚到此版本"，Then 系统标记当前版本为 abandoned，恢复第 3 个版本为 active，并记录回滚决策日志。

**关联 JTBD**：J3
**优先级**：P0

---

### US-010：管理产物版本与回滚 {#sec-us010guanlichanu7269banbenyuhuig}
**应用场景（Given/When）**：
Given 用户发现某产物的新版本不如旧版本，When 进入版本历史

**完整操作路径**：
1. 用户在产物浏览器点击"版本历史"
2. 系统展示该产物的所有 Git 快照（按时间倒序）
3. 用户选择两个版本进行 diff 对比
4. 用户选择某个旧版本
5. 用户点击"回滚到此版本"
6. 系统恢复旧版本内容至文件系统，创建新的回滚提交
7. 系统更新产物浏览器显示

**用户目标（So That）**：
在产物迭代过程中安全地回溯到历史版本，避免不可逆的错误修改。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given 产物有 5 个 Git 快照，When 用户选择第 3 个快照回滚，Then 系统在 1s 内恢复内容，创建标记为"回滚至 v3"的新提交，产物浏览器展示回滚后内容。
- **AC2（Edge Case）**：Given 用户回滚后再次编辑并保存，When 查看版本历史，Then 回滚操作本身作为独立版本记录，后续编辑在回滚基础上继续。

**关联 JTBD**：J2
**优先级**：P0

---

### US-011：在复杂度路由面板查看并调整执行路径 {#sec-us011zaifuu6742duluyouu9762banch}
**应用场景（Given/When）**：
Given 项目已完成规模评估，When 用户进入"复杂度路由"面板

**完整操作路径**：
1. 用户点击"复杂度路由"面板
2. 系统展示当前复杂度等级和推荐路径
3. 系统可视化展示四条路径（Trivial/Light/Standard/Deep）的差异（阶段合并策略、跳过的阶段、包含的 Skill）
4. 用户可切换模板，查看切换后的画布预览
5. 用户确认或覆盖推荐路径
6. 系统记录偏离决策日志

**用户目标（So That）**：
清晰理解不同执行路径的差异，做出符合项目实际的路径选择。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given 系统推荐 Standard 模板，When 用户切换至 Simple 模板，Then 画布实时更新，隐藏非必要阶段节点，系统记录"用户手动降级至 Simple"日志。
- **AC2（Edge Case）**：Given 用户已执行部分阶段后切换模板，When 确认切换，Then 已执行阶段保持不变，未执行阶段按新模板重新渲染，系统提示"已执行阶段不受影响"。

**关联 JTBD**：J5
**优先级**：P0

---

### US-012：浏览 C4 架构图并穿透下钻 {#sec-us012u6d4flan-c4-jiagoutubingu7a}
**应用场景（Given/When）**：
Given 项目已完成概要设计阶段，When 用户进入"架构浏览器"

**完整操作路径**：
1. 用户点击"架构浏览器"
2. 系统自动解析 `high-level-design.md` 生成 C4 L1 Context 图
3. 用户查看 Context 图，点击某个系统边界
4. 系统下钻至 L2 Container 图，展示系统内的服务/应用边界
5. 用户点击某个 Container，系统下钻至 L3 Component 图，展示该容器内的组件和接口契约
6. 用户点击某个 Component，系统下钻至 L4 Code 图，展示代码级元素和类/函数关系
7. 用户可手动编辑任意层级 C4 DSL 内容，保存后实时重新渲染
8. 用户可导出架构图为 PNG/SVG

**用户目标（So That）**：
直观理解系统架构，快速发现和修正架构设计中的遗漏。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given 概要设计文档包含 3 个模块，When 进入架构浏览器，Then 系统在 5s 内生成 L1 Context 图，模块边界正确，命名与设计文档一致。
- **AC2（Negative Path）**：Given 概要设计文档格式异常或缺失模块描述，When 生成 C4 图，Then 系统提示"设计文档解析失败，请检查格式"，提供手动编辑 DSL 入口。
- **AC3（Edge Case）**：Given 用户手动修改 DSL 后保存，When 重新渲染，Then 系统优先使用用户修改后的 DSL，不再自动覆盖，并在版本历史中标记"手动覆盖"。

**关联 JTBD**：J2
**优先级**：P0

---

### US-013：查看架构漂移检测报告 {#sec-us013chakanjiagouu6f02yijianceba}
**应用场景（Given/When）**：
Given 项目已进入编码阶段且已存在历史架构基线，When 用户进入"架构验证中心"

**完整操作路径**：
1. 用户点击"架构验证中心"
2. 系统对比历史架构基线（上次 Gate-2 通过的 C4 快照）与当前代码扫描结果
3. 系统生成漂移检测报告，列出差异项（新增未授权依赖、缺少接口、技术栈不一致）
4. 用户查看 diff 可视化对比
5. 用户可标记差异为"预期变更"或"需要修复"

**用户目标（So That）**：
及时发现编码实现与架构设计的偏离，防止技术债务累积。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given 代码扫描结果与基线存在 2 处差异，When 进入架构验证中心，Then 系统正确展示差异列表和 diff 可视化。
- **AC2（Edge Case）**：Given 项目无历史架构基线，When 进入架构验证中心，Then 系统提示"请先完成概要设计并通过 Gate-2 以建立基线"。

**关联 JTBD**：J4
**优先级**：P1

---

### US-014：多人协作批注 {#sec-us014u591arenu534fu4f5cpizhu}
**应用场景（Given/When）**：
Given 项目已进入多用户模式（P1），When 多个团队成员需要同时审查同一份产物

**完整操作路径**：
1. 成员 A 打开产物并添加批注
2. 系统实时同步批注到成员 B 的视图
3. 成员 B 回复成员 A 的批注（支持评论线程）
4. 成员 C 标记某批注为"已解决"
5. 项目负责人查看所有未解决批注的汇总列表
6. 基于共识批注触发重新生成

**用户目标（So That）**：
在团队协作场景下实现异步审查，避免单人审查的视角盲区。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given 3 名成员同时打开同一份产物，When 成员 A 添加批注后，Then 成员 B 和 C 在 2s 内看到该批注出现在对应行号位置。
- **AC2（Negative Path）**：Given 成员 A 和 B 同时编辑同一条批注，When 后提交者点击保存，Then 系统提示"该批注已被他人修改，请刷新后重试"，不覆盖他人内容。
- **AC3（Edge Case）**：Given 网络中断期间成员 A 添加批注，When 网络恢复后，Then 系统自动同步离线期间的批注，冲突时提示人工合并。

**关联 JTBD**：J3
**优先级**：P1

---

### US-015：预览 OpenUI 可交互原型 {#sec-us015yulan-openui-u53efjiaou4e92}
**应用场景（Given/When）**：
Given 项目已完成 C4 Container 设计并生成了接口契约，When 用户需要验证设计是否符合预期

**完整操作路径**：
1. 用户点击"原型验证中心"
2. 系统根据 C4 Container 图和接口契约生成 OpenUI 提示词
3. 系统调用 OpenUI 服务获取可交互 HTML 原型
4. 用户在平台内嵌套预览原型，支持页面跳转和基础交互
5. 用户可标记页面与 C4 接口的对应关系

**用户目标（So That）**：
通过可交互原型在编码前验证页面流程和交互设计，减少返工。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given C4 Container 图和接口契约存在，When 进入原型验证中心，Then 系统在 10s 内生成可交互 HTML 原型，页面渲染正确。
- **AC2（Edge Case）**：Given OpenUI 服务未启动，When 生成原型，Then 系统提示"OpenUI 服务不可用，请检查 Docker 状态"，并提供 Wireframe 静态预览降级方案。

**关联 JTBD**：J2
**优先级**：P0

---

### US-016：查看 Wireframe 领域感知线框图 {#sec-us016chakan-wireframe-lingyuu611}
**应用场景（Given/When）**：
Given 项目已生成 C4 架构图和领域模型，When 用户需要快速验证页面结构是否与架构设计一致

**完整操作路径**：
1. 用户点击"线框图"Tab
2. DomainMapper 读取 C4 DSL 映射领域实体到页面结构（列表/详情/仪表盘/表单/弹窗/搜索/向导）
3. LayoutPlanner 基于页面类型生成 SVG 线框图坐标
4. NavigationLinker 根据 C4 接口依赖建立页面跳转关系
5. 用户查看线框图，标注页面与 C4 接口的对应关系
6. 用户可一键回写缺失接口到 C4 DSL

**用户目标（So That）**：
通过线框图快速验证页面结构、导航流程与 C4 架构的一致性，提前发现接口遗漏。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given C4 DSL 和领域模型存在，When 进入线框图视图，Then 系统在 5s 内生成 SVG 线框图，页面类型识别准确率 >= 80%。
- **AC2（Edge Case）**：Given 线框图发现某页面缺少对应 C4 接口，When 用户点击"回写架构"，Then 系统自动更新 C4 DSL 并标记架构变更待 Gate 评审。

**关联 JTBD**：J2
**优先级**：P0

---

### US-017：查看需求草图确认页面逻辑 {#sec-us017chakanxuqiuu8349tuquerenyeu}
**应用场景（Given/When）**：
Given 项目处于 Align（需求对齐）阶段且已编写用户故事和验收标准，When 用户需要确认页面逻辑是否符合预期

**完整操作路径**：
1. 用户完成用户故事和验收标准的编写
2. 系统自动扫描需求产物，提取含页面描述的用户故事
3. 系统基于 PageSpec 规则生成低保真需求草图（文本框+箭头，标注字段、按钮、跳转关系）
4. 用户在审查面板查看需求草图
5. 用户标记与预期不符的字段或流程
6. 系统记录偏差并提示修正需求文档

**用户目标（So That）**：
在详细需求阶段通过可视化草图确认页面逻辑，提前发现遗漏字段或流程错误，减少设计阶段返工。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given 3 个含页面描述的用户故事，When 生成需求草图，Then 系统在 3s 内产出草图，字段覆盖率 >=90%。
- **AC2（Negative Path）**：Given 某用户故事缺少页面字段描述，When 生成草图，Then 系统提示"该故事缺少页面字段描述，草图可能不完整"，允许用户补充后重新生成。
- **AC3（Edge Case）**：Given 草图与预期不符，When 用户标记偏差并填写原因，Then 系统记录偏差到对应用户故事的批注，状态变为 REVIEW_PENDING。

**关联 JTBD**：J3
**优先级**：P0

---

## 4. 全生命周期产物清单 {#sec-4-quanshengu547dzhouqichanu7269u}
> 按阶段定义标准产物与裁剪产物，以及对应的责任人与平台机制。

### 4.1 Draft 阶段（预立项） {#sec-41-draft-u9636u6bb5yuu7acbu9879}
| 输出物 | 内容要求 | 责任人 | 平台机制 | 裁剪条件（Trivial/Light） |
|--------|----------|--------|----------|--------------------------|
| 脑暴纪要 | 核心用户场景、痛点假设、价值主张 | 临时 PO | Skill-brainstorming 自动生成 | Trivial 可省略，Light 简化为一页纸 |
| 竞品分析 | 3 款竞品对标、差异化机会 | 临时 PO | Skill-competitive-analysis | Trivial 可省略 |
| 规模初估报告 | 三档得分、推断依据、置信度、立项建议 | AIE 辅助 | Skill-SizeEstimate（Triage 模式） | 不可裁剪 |
| 立项建议书 | Go/No-Go 理由、关键风险、退出条件 | 临时 PO | 模板化问卷，AI 辅助生成 | 不可裁剪 |

### 4.2 Active 阶段（正式执行） {#sec-42-active-u9636u6bb5u6b63u5f0fzh}
| 阶段 | 标准产物（Standard/Deep） | 裁剪产物（Trivial/Light） | 人工 Gate |
|------|--------------------------|--------------------------|----------|
| **Clarify（需求澄清）** | 范围确认书、用户故事、验收标准 | 需求设计一页纸 + 草图 | 范围确认（PO 为 A） |
| **Align（需求对齐）** | PRD、Feature Spec、接口契约初稿、**需求草图/页面流程图** | 需求设计一页纸 + 草图 | 范围确认（PO 为 A） |
| **Contract（设计契约）** | HLD、DD、OpenAPI、DB 设计、安全设计 | 技术方案 + 关键接口 | 架构评审（TL 为 A） |
| **Build（编码实现）** | 代码、单元测试、集成脚本、部署配置、日志规范 | 代码 + 单元测试 | 代码审查（TL 为 A） |
| **Verify（测试验证）** | 测试报告、性能基准、安全扫描报告、兼容性报告 | 测试报告 + 核心链路通过 | 测试通过（QA 为 A） |
| **Release（发布上线）** | 上线 Checklist、监控配置、回滚方案、值班表 | Checklist + 回滚命令 | 上线审批（SRE 为 A，会签） |

### 4.3 产物标准规则 {#sec-43-chanu7269biaozhunguize}
- **基线前**：产物处于草稿态，任意修改，不触发变更流程。
- **基线后**：产物变更触发 Stale 传播，自动计算受影响范围，强制人工确认重跑范围。
- **时间盒硬截止**：里程碑到期强制推进或裁剪，不可无限延期。
- **范围锚定**：启动时锁定模块清单，新增模块需人工确认并重估规模。

---

## 5. 需求清单 {#sec-5-xuqiuu6e05dan}
### 5.1 P0 需求（必须交付） {#sec-51-p0-xuqiuu5fc5u987bjiaofu}
| 编号 | 需求描述 | 关联用户故事 | 优先级 |
|------|----------|-------------|--------|
| REQ-P0-001 | 项目 CRUD：创建、读取、更新、删除项目，支持 Draft/Active/Archived/Cancelled 状态流转 | US-001 | P0 |
| REQ-P0-002 | 模板选择：项目创建时展示 Trivial/Light/Standard/Deep 四级路径预览，支持一键选择和后续切换 | US-001, US-011 | P0 |
| REQ-P0-003 | SDLC 拓扑图：动态渲染 Skill 节点和依赖连线，支持缩放/拖拽/筛选 | US-002 | P0 |
| REQ-P0-004 | 泳道视图：按 Stage 分组展示节点状态 | US-002 | P0 |
| REQ-P0-005 | 列表视图：表格形式展示所有节点，支持批量筛选 | US-002 | P1 |
| REQ-P0-006 | Skill 执行触发：一键调用 Kimi CLI，注入输入产物，捕获输出和日志 | US-002 | P0 |
| REQ-P0-007 | 实时状态同步：节点状态变更（NOT_STARTED/IN_PROGRESS/REVIEW_PENDING/REVISION_REQUESTED/PASSED/BLOCKED/GATE_PENDING/BYPASSED）端到端延迟 < 5s | US-002 | P0 |
| REQ-P0-008 | Gate 自检摘要：AI 自动生成风险点和待补充项清单 | US-003 | P0 |
| REQ-P0-009 | Gate 快速确认：一键通过/驳回/重试，记录决策时间戳和评语 | US-003 | P0 |
| REQ-P0-010 | 产物渲染：支持 Markdown、Mermaid、YAML、JSON、OpenAPI/Swagger 格式 | US-004 | P0 |
| REQ-P0-011 | 产物编辑：平台内编辑产物内容，保存时检测外部变更冲突 | US-004 | P0 |
| REQ-P0-012 | 产物 Git 快照：自动初始化 Git 仓库，每次保存自动提交，支持 diff 和回滚 | US-004, US-010 | P0 |
| REQ-P0-013 | Skill 导入：解析 SKILL.md Frontmatter 和 meta.json，校验格式合法性 | US-005 | P0 |
| REQ-P0-014 | DAG 自动解析：从 SKILL.md 提取上下游 Skill 引用，准确率 >= 80% | US-005 | P0 |
| REQ-P0-015 | DAG 手动调整：可视化界面支持用户手动增删改节点连线 | US-005 | P0 |
| REQ-P0-016 | 规模评估：基于文件数/实体数/跨服务标记的自动复杂度判定 | US-007 | P0 |
| REQ-P0-017 | Timebox 配置：各阶段时间预期设置与到期预警 | US-008 | P0 |
| REQ-P0-018 | 复杂度路由面板：可视化展示 Trivial/Light/Standard/Deep 四级路径差异，支持人工覆盖 | US-011 | P0 |
| REQ-P0-019 | C4 L1/L2/L3/L4 自动生成：解析概要设计文档生成 Context/Container/Component/Code 四级架构图 | US-012 | P0 |
| REQ-P0-020 | C4 层级穿透导航：支持从 Context 逐层下钻到 Container/Component/Code 级，面包屑导航同步更新 | US-012 | P0 |
| REQ-P0-021 | C4 DSL 手动编辑：用户可手动修改生成的 DSL，保存后优先使用手动版本 | US-012 | P0 |
| REQ-P0-022 | 项目健康度卡片：展示进度/风险/待审批 Gate | US-001 | P0 |
| REQ-P0-023 | 风险预警：自动检测覆盖率不足、Gate Rejected、超时等异常并展示 | US-001 | P0 |
| REQ-P0-024 | 产物目录树：按项目/Stage/Skill 组织产物文件 | US-004 | P0 |
| REQ-P0-025 | 执行日志展示：按 Skill 分组展示 stdout/stderr 摘要 | US-002 | P0 |
| REQ-P0-026 | Gate 历史追溯：展示所有 Gate 决策记录、评语、时间戳 | US-003 | P0 |
| REQ-P0-027 | 模板偏离记录：记录用户偏离推荐模板的决策日志 | US-011 | P0 |
| REQ-P0-028 | OpenUI 原型生成：将 C4 Container 和接口契约转换为 OpenUI 提示词，调用服务生成可交互 HTML 原型 | — | P0 |
| REQ-P0-029 | OpenUI 原型预览：在平台内嵌套 OpenUI 原型，支持页面跳转和基础交互 | — | P0 |
| REQ-P0-030 | WireframeEngine 领域映射：读取 C4 DSL 和领域模型，映射领域实体到页面结构（列表/详情/仪表盘） | — | P0 |
| REQ-P0-031 | WireframeEngine 线框渲染：基于页面类型生成 SVG 线框图，标注页面与 C4 接口的对应关系 | — | P0 |
| REQ-P0-032 | 原型-架构双向绑定：原型中发现接口缺失时，支持一键回写 C4 DSL 并标记架构变更待评审 | — | P0 |
| REQ-P0-033 | C4 反向代码定位：Component/Code 级节点支持反向定位到本地代码文件（通过 arsitect.codegen_target） | US-012 | P0 |
| REQ-P0-034 | 产物行内批注：用户在 Artifact Viewer 中高亮文本并添加评论气泡，批注关联到具体文件、行号和版本 | US-009 | P0 |
| REQ-P0-035 | Stage 审查面板：Stage Detail 面板提供"审查"Tab，含全局修改建议输入框（结构化：P0阻塞/P1建议/P2优化）、参考资料拖拽/粘贴区 | US-009 | P0 |
| REQ-P0-036 | 参考资料注入：用户提供的参考资料在 AI 重新生成时自动注入为上下文输入，系统展示参考资料引用摘要 | US-009 | P0 |
| REQ-P0-037 | 产物版本历史与对比：每次重新生成产生新版本，支持版本列表查看、diff 对比（增删改高亮）、版本回滚到任意历史版本 | US-009, US-010 | P0 |
| REQ-P0-038 | 基于反馈重新生成：用户提交批注和建议后，点击"重新生成"，系统携带前序版本全部批注和参考资料作为输入触发 Skill 重新执行 | US-009 | P0 |
| REQ-P0-039 | 阶段详情面板：点击 Stage 节点打开右侧阶段详情面板，展示 Stage 内 Skill 指令快照、输入/输出产物、执行日志、质量门禁结果 | US-002 | P0 |
| REQ-P0-040 | 需求草图生成：基于用户故事和验收标准，系统自动提取含页面描述的故事并生成低保真需求草图（文本框+箭头，标注字段、按钮、跳转关系），字段覆盖率 >=90%，每 3 个故事 1 张草图 | US-017 | P0 |

### 5.2 P1 需求（重要，影响核心体验） {#sec-52-p1-xuqiuchongyaou5f71u54cdhex}
| 编号 | 需求描述 | 关联用户故事 | 优先级 |
|------|----------|-------------|--------|
| REQ-P1-001 | 历史项目时间线：展示已完成项目的阶段执行时间线 | US-006 | P1 |
| REQ-P1-002 | 阶段耗时对比：同类型项目横向对比阶段耗时 | US-006 | P1 |
| REQ-P1-003 | 返工热力图：可视化展示各阶段重试/驳回频率 | US-006 | P1 |
| REQ-P1-004 | 多人协作批注：多用户实时同步批注、评论线程、标记已解决、离线同步 | US-014 | P1 |
| REQ-P1-005 | 架构漂移检测：对比历史基线与当前代码扫描结果，展示差异列表 | US-013 | P1 |
| REQ-P1-006 | 漂移 diff 可视化：图形化展示设计架构与实际架构的差异 | US-013 | P1 |
| REQ-P1-007 | 监控看板：进度追踪、阶段耗时统计、Token 消耗统计、瓶颈识别 | — | P1 |
| REQ-P1-008 | 多用户支持（Tech Lead/开发者角色）：项目级权限控制 | — | P1 |

### 5.3 P2 需求（优化项，可延后） {#sec-53-p2-xuqiuyouhuau9879u53efyanu5}
| 编号 | 需求描述 | 关联用户故事 | 优先级 |
|------|----------|-------------|--------|
| REQ-P2-001 | 多 AI 平台适配：Claude/Cursor/MCP Adapter 实现 | — | P2 |
| REQ-P2-002 | （已合并至 REQ-P0-019）C4 L3/L4 自动生成 | — | P2 |
| REQ-P2-003 | 移动端只读适配：查看项目进度和产物（不可编辑） | — | P2 |
| REQ-P2-004 | Skill 市场/模板订阅：在线下载社区 Skill 和模板 | — | P2 |
| REQ-P2-005 | 远程 Git 同步：产物自动同步到远程 Git 仓库 | — | P2 |

---

## 5. 业务规则 {#sec-5-yewuguize}
### 5.1 规则清单 {#sec-51-guizeu6e05dan}
| 编号 | 规则描述 | 优先级 | 适用模块 | 触发条件 |
|------|----------|--------|----------|----------|
| BR-001 | 只有处于 Draft 或 Active 状态的项目才可执行 Skill | 硬规则 | 项目治理 | 用户点击"执行" |
| BR-002 | Gate 审批通过前，下游节点不可执行 | 硬规则 | SDLC 画布 | 节点依赖关系校验 |
| BR-003 | Draft 态项目仅允许执行预立项分析型 Skill | 硬规则 | 项目治理 | 用户选择 Skill 类型 |
| BR-004 | 模板与项目为弱关联，执行过程中允许随时偏离推荐路径 | 软规则 | 模板引擎 | 用户调整路径 |
| BR-005 | 节点执行失败后，用户可手动重试，最多重试 3 次 | 门控规则 | Skill 调度 | 用户点击"重试" |
| BR-006 | 产物平台内保存前，必须检测外部文件系统哈希变化；若外部已变更，弹窗提示用户确认覆盖 | 硬规则 | 产物服务 | 用户点击"保存" |
| BR-007 | 产物文件自动纳入 Git 快照管理；单文件 > 10MB 时不纳入 Git 快照，仅保留当前版本 | 门控规则 | 产物服务 | 文件保存 |
| BR-008 | C4 架构图自动生成覆盖 L1 Context / L2 Container / L3 Component / L4 Code 四级；用户可手动覆盖任意层级 DSL | 硬规则 | C4 浏览器 | 生成请求 |
| BR-009 | Gate 摘要置信度为"低"时，禁止一键通过，要求用户至少浏览一份产物 | 门控规则 | 审批中心 | AI 摘要生成完成 |
| BR-010 | AI 禁止自动执行发布相关 Skill（release-management / finish） | 硬规则 | 安全规则 | 系统调度器 |
| BR-011 | 复杂度路由基于五维度规则引擎判定，不调用 LLM 深度分析 | 硬规则 | 复杂度路由 | 规模评估请求 |
| BR-012 | SKILL.md 解析失败时，标记为"需手动配置"，不阻塞其他 Skill 导入 | 软规则 | Skill 注册 | Frontmatter 解析 |
| BR-013 | 项目取消（Cancelled）后，保留产物和决策记录，仅冻结状态变更 | 硬规则 | 项目治理 | 取消操作 |
| BR-014 | 紧急情况下支持旁路审批：需 TL 或 SO 提前授权，执行过程全量记录，事后 24h 内必须补审批 | 门控规则 | HITL 服务 | 紧急执行请求 |
| BR-015 | Draft 态 Token 消耗与执行耗时计入 Application 级研发管理费，Active 态开始计入项目预算 | 硬规则 | 项目治理 | Draft/Active 状态转换 |
| BR-016 | 所有 Skill 执行必须遵循 PocketFlow 三阶段：prep（准备输入/上下文）→ exec（调用 CLI/AI）→ post（产物处理/质量检查/Git 快照） | 硬规则 | Skill 调度 | 任何 Skill 执行触发 |
| BR-017 | 立项 Gate 在 Draft 态完成，不计入 Active 态 Gate 总数；每个 Active Gate 必须有且只有一个最终负责人（Accountable） | 硬规则 | Gate 审批 | Gate 创建/分配 |
| BR-018 | 模块级里程碑独立推进：同一 Module 内有依赖的 Skills 串行，无依赖可并行；跨 Module 完全并行 | 硬规则 | Skill Flow 编排 | 模块调度时 |
| BR-019 | 工件基线化后变更触发 Stale 传播：自动计算受影响范围，强制人工确认重跑范围 | 硬规则 | 产物服务 | 基线产物变更 |
| BR-020 | 每个 Stage 必须有且仅有 1 个主 Skill（primary），辅助 Skill（auxiliary）数量不限；主 Skill 失败则 Stage 失败 | 硬规则 | Stage 编排 | Stage 执行调度 |
| BR-021 | 合并后的 Stage 共享同一个 Gate，Gate 通过即视为合并内所有原 Stage 通过 | 门控规则 | Stage 编排 | Gate 审批提交 |
| BR-022 | 合并 Stage 中的 Skills 按原 Stage 分组并行执行，同一原 Stage 内按 execution_order 串行执行 | 硬规则 | Stage 编排 | Stage 执行计划生成 |
| BR-023 | 主 Skill 产物生成后必须进入 REVIEW_PENDING 状态，禁止自动流转到 GATE_PENDING 或 PASSED；辅助 Skill 产物默认不触发 REVIEW_PENDING，但可在审查面板查看 | 硬规则 | 审查规则 | 产物生成完成 |
| BR-024 | 人工必须至少浏览 1 份产物并停留 >=30 秒，才可提交修改建议或 Gate 审批 | 门控规则 | 审查规则 | 提交修改建议 / Gate 审批 |
| BR-025 | 重新生成时必须携带前序版本的全部人工批注和参考资料作为上下文输入 | 硬规则 | 审查规则 | 触发重新生成 |
| BR-026 | 产物版本历史保留最近 10 个版本，超过后自动归档到压缩存储 | 门控规则 | 版本管理 | 版本生成 |
| BR-027 | Gate 审批驳回后，系统必须保留驳回理由并自动关联到产物批注 | 硬规则 | Gate 规则 | Gate 驳回 |
| BR-028 | 复杂度路由推荐作为默认建议，用户可在路由面板手动覆盖；降级到更低路径（如 Deep→Standard）需二次确认并记录原因 | 软规则 | 项目治理 | 用户在路由面板切换路径 |

### 5.2 冲突仲裁逻辑 {#sec-52-u51b2u7a81u4ef2u88c1luoji}
| 冲突场景 | 涉及规则 | 仲裁结果 |
|----------|----------|----------|
| 用户强制通过置信度为"低"的 Gate | BR-009 vs 用户意图 | **BR-009 优先**：系统禁止一键通过，但允许用户在浏览至少一份产物后手动勾选"我已知晓风险"再提交。仲裁记录写入 `human-decisions.md`。 |
| 外部修改产物后平台内也修改，用户点击保存 | BR-006 vs 用户效率 | **BR-006 优先**：必须弹窗提示冲突，用户确认覆盖后方可保存。不允许静默覆盖。 |
| 用户已执行部分阶段后切换模板，新模板缺失已执行阶段 | BR-004 vs 数据一致性 | **BR-004 优先**：已执行阶段保持不变，新模板仅影响未执行阶段。系统展示警告提示，记录偏离日志。 |
| 复杂度路由推荐 Standard，但用户手动选择 Trivial 后规模不匹配 | BR-011 vs 用户选择 | **用户选择优先**：系统允许选择，但持续展示规模不匹配警告。若后续 Stage 失败率升高，建议在 Gate 摘要中提示"规模评估可能不准确"。 |
| 旁路审批后 24h 内未补审批 | BR-014 vs 流程合规 | **BR-014 优先**：超过 24h 未补审批自动触发告警，项目状态标记为"旁路待补审"，阻塞下游 Gate 解锁。 |
| PocketFlow post 阶段产物校验失败但 exec 退出码为 0 | BR-016 vs 执行成功 | **BR-016 优先**：post 阶段失败整体标记为 BLOCKED，不视为 Success。用户可查看 post 阶段失败详情并重试。 |

---

## 6. 需求追溯矩阵（RTM） {#sec-6-xuqiuzhuiu6eafu77e9u9635rtm}
| 用户故事 | 功能需求 | 需求描述 | 优先级 | 验收标准 | 状态 |
|----------|----------|----------|--------|----------|------|
| US-001 | REQ-P0-001 | 项目 CRUD | P0 | AC1: 500ms 内创建；AC2: 必填校验；AC3: 重名检测；AC4: Git 初始化 | Draft |
| US-001 | REQ-P0-002 | 模板选择 | P0 | AC1: 模板预览渲染；AC2: 实时切换 | Draft |
| US-001 | REQ-P0-022 | 健康度卡片 | P0 | 卡片数据与项目状态一致 | Draft |
| US-002 | REQ-P0-003 | SDLC 拓扑图 | P0 | AC1: 3s 内触发执行；AC2: 前置依赖校验；AC3: CLI 异常处理 | Draft |
| US-002 | REQ-P0-006 | Skill 执行触发 | P0 | CLI 调用成功，日志捕获完整 | Draft |
| US-002 | REQ-P0-007 | 实时状态同步 | P0 | 状态变更延迟 < 5s | Draft |
| US-002 | REQ-P0-025 | 执行日志展示 | P0 | 日志按 Skill 分组，支持搜索 | Draft |
| US-003 | REQ-P0-008 | Gate 自检摘要 | P0 | AC1: 500ms 内记录决策；AC2: 驳回处理；AC3: 低置信度拦截 | Draft |
| US-003 | REQ-P0-009 | Gate 快速确认 | P0 | 一键通过/驳回/重试 | Draft |
| US-003 | REQ-P0-026 | Gate 历史追溯 | P0 | 决策记录完整，时间戳准确 | Draft |
| US-004 | REQ-P0-010 | 产物渲染 | P0 | AC1: 500ms 渲染；AC2: 外部删除检测；AC3: 大文件分页 | Draft |
| US-004 | REQ-P0-011 | 产物编辑 | P0 | AC4: 1s 内写回+Git 提交；AC5: 冲突检测弹窗 | Draft |
| US-004 | REQ-P0-012 | 产物 Git 快照 | P0 | AC6: 回滚 1s 内完成 | Draft |
| US-004 | REQ-P0-024 | 产物目录树 | P0 | 目录树按 Stage/Skill 组织 | Draft |
| US-005 | REQ-P0-013 | Skill 导入 | P0 | AC1: 2s 内解析预览；AC2: 格式错误提示；AC3: 名称冲突处理 | Draft |
| US-005 | REQ-P0-014 | DAG 自动解析 | P0 | 解析准确率 >= 80% | Draft |
| US-005 | REQ-P0-015 | DAG 手动调整 | P0 | 可视化连线编辑 | Draft |
| US-007 | REQ-P0-016 | 规模评估 | P0 | AC1: 3s 内返回等级；AC2: 空文档提示；AC3: 规模不匹配警告 | Draft |
| US-008 | REQ-P0-017 | Timebox 配置 | P0 | 到期前预警，超时处理 | Draft |
| US-011 | REQ-P0-018 | 复杂度路由面板 | P0 | 路径差异可视化，切换实时预览 | Draft |
| US-011 | REQ-P0-027 | 模板偏离记录 | P0 | 偏离决策日志完整 | Draft |
| US-002 | REQ-P0-039 | 阶段详情面板 | P0 | 面板滑出 < 300ms；Skill 快照/产物/日志/门禁完整展示 | Draft |
| US-012 | REQ-P0-019 | C4 L1/L2/L3/L4 自动生成 | P0 | AC1: 5s 内生成 Context；AC2: 格式异常提示；AC3: 手动覆盖优先 | Draft |
| US-012 | REQ-P0-020 | C4 层级穿透导航 | P0 | 下钻 < 1s；面包屑同步更新 | Draft |
| US-012 | REQ-P0-021 | C4 DSL 手动编辑 | P0 | 手动版本优先于自动生成 | Draft |
| US-012 | REQ-P0-033 | C4 反向代码定位 | P0 | Component/Code 级节点可定位到本地文件 | Draft |
| US-006 | REQ-P1-001~003 | 历史回溯 | P1 | 时间线/对比/热力图 | Draft |
| US-009 | REQ-P0-034 | 产物行内批注 | P0 | 批注触发重新生成；未浏览拦截；版本归档；回滚恢复 | Draft |
| US-009 | REQ-P0-035 | Stage 审查面板 | P0 | 结构化建议提交；参考资料区 | Draft |
| US-009 | REQ-P0-036 | 参考资料注入 | P0 | 参考资料上下文注入 | Draft |
| US-009 | REQ-P0-037 | 产物版本历史与对比 | P0 | diff 对比与回滚 | Draft |
| US-009 | REQ-P0-038 | 基于反馈重新生成 | P0 | 携带批注重新生成 | Draft |
| US-010 | REQ-P0-012 | 产物 Git 快照 | P0 | 回滚操作作为独立版本记录 | Draft |
| US-010 | REQ-P0-037 | 产物版本历史与对比 | P0 | diff 对比与回滚 | Draft |
| US-013 | REQ-P1-005~006 | 架构漂移检测 | P1 | 差异列表+diff 可视化 | Draft |
| US-014 | REQ-P1-004 | 多人协作批注 | P1 | 实时同步；并发编辑冲突；离线同步 | Draft |
| US-015 | REQ-P0-028 | OpenUI 原型生成 | P0 | 10s 内生成可交互原型 | Draft |
| US-015 | REQ-P0-029 | OpenUI 原型预览 | P0 | 页面渲染正确；服务不可用降级 | Draft |
| US-016 | REQ-P0-030 | WireframeEngine 领域映射 | P0 | 5s 内线框图；页面类型识别 >=80% | Draft |
| US-016 | REQ-P0-031 | WireframeEngine 线框渲染 | P0 | SVG 渲染正确 | Draft |
| US-016 | REQ-P0-032 | 原型-架构双向绑定 | P0 | 接口缺失检测；一键回写 C4 DSL | Draft |
| US-017 | REQ-P0-040 | 需求草图生成 | P0 | 字段覆盖率 >=90%；3s 内生成；缺失字段提示 | Draft |

---

## 7. 变更影响说明 {#sec-7-biangengu5f71u54cdu8bf4u660e}
本次 v2.0 相对于 v1.4 的主要变更及下游影响：

| 变更项 | v1.4 | v2.0 | 下游影响 |
|--------|------|------|----------|
| 模板关系 | 复杂度路由强制绑定路径 | 弱关联，允许偏离 | `02-functional-requirements.md` 状态机需增加"模板切换"转移路径 |
| 产物版本 | 未定义版本管理 | Git 快照 | `detailed-design/` 需增加产物服务的数据库表设计（ArtifactVersion） |
| C4 来源 | 从 `arsitect.aac.yml` 读取 | 平台自动生成 + 手动覆盖 | `high-level-design/` 需增加 C4 生成器模块设计 |
| OpenHands | 外部 Docker 依赖 | 已移除 | `high-level-design/` 移除 OpenHands 相关架构 |
| US 编号 | US-001/004 独立 | 合并模板选择和产物编辑 | `detailed-requirements/` 按新 US 拆分需求 |
| 审查功能 | US-009 缺失，无 REVIEW_PENDING 状态 | 恢复 US-009（P0）+ REVIEW_PENDING/REVISION_REQUESTED 状态机 + 批注/重新生成/版本管理 | `02-functional-requirements.md` 状态机需增加 REVIEW_PENDING/REVISION_REQUESTED；`detailed-design/` 需增加审查服务与批注存储设计 |
| C4 范围 | 仅 L1/L2 自动生成 | 恢复 L1/L2/L3/L4 四级自动生成 + 反向代码定位（P0） | `high-level-design/` 需增加 L3/L4 生成器模块设计；`detailed-design/` 需增加代码反向定位服务设计 |

---

## 附录：历史补充内容（来自 docs/ 目录） {#sec-u9644luu5386u53f2u8865u5145u5185}
- **项目治理**：Workspace / Application / Project / Module 的 CRUD，Draft/Active 双态管理，项目健康度计算。
- **SDLC 可视化**：拓扑图视图（动态节点+依赖连线）、泳道视图（按阶段分组）、列表视图（批量筛选）。
- **Skill Flow 编排**：YAML 驱动 DAG 调度、并行执行、条件分支、失败重试（rollback/retry/skip/notify）、产物传递。复杂度路由路径决定 Stage 合并策略和验证深度，取代固定的"标准/快速/自定义"模板选择。
- **Skill 执行与调度**：Kimi CLI 本地调用、输入注入、输出捕获、日志收集、状态持久化。
- **Gate 自检确认**：四道 Gate（Gate-1/2.5/2/3）的 Waiting 状态管理、AI 辅助摘要生成、快速确认/驳回/重试、历史追溯。
- **产物管理**：产物存储/检索、版本管理、Markdown/Mermaid/Swagger/YAML/JSON 多模态渲染。
- **实时同步**：Skill 状态变更 WebSocket 推送、Gate 等待通知、产物增量监听。
- **历史分析**：已完成项目时间线、阶段耗时对比、返工热力图。
- **Skill 注册**：用户手动注册/导入 Skill 路径、Frontmatter 解析、画布动态生成。
- **复杂度路由面板**：流程路径选择的唯一决策点。综合规模等级和技术信号自动判定 Trivial/Light/Standard/Deep 四级复杂度，可视化四条执行路径的差异（Stage 合并策略、跳过阶段、额外阶段），支持人工覆盖。
- **复杂度路由面板**：基于信号自动判定复杂度等级（Trivial/Light/Standard/Deep），可视化四条执行路径的差异（Stage 合并策略、跳过阶段、额外阶段），支持人工覆盖。
- **C4 架构浏览**：从 arsitect.aac.yml 渲染 C4 Context/Container/Component/Code 四级架构图，支持层级穿透下钻与反向代码定位。

- 多租户与企业级 RBAC（P1 后考虑）。
- 多 AI 平台适配（Claude/Cursor/MCP），MVP 仅支持 Kimi CLI。
- 通用项目管理（任务分配、工时统计、甘特图、资源调度）。
- 外部 CI/CD 工具链替代（如替代 GitHub Actions、GitLab CI）。
- 底层 LLM 基座选型与训练。
- 产物云端存储/SaaS 化（MVP 仅本地文件系统）。
- 实时协同编辑（多用户同时操作同一项目）。
- 移动端适配（P2 评估）。

| 术语 | 定义 | 使用场景 |
|------|------|----------|
| **Arsitect** | AI 驱动软件工程全生命周期管理平台（即 skill-arsenal 项目），包含 41 个 Skill 的规范体系 | 全文 |
| **Skill** | AI 能力单元，由 SKILL.md（YAML Frontmatter）+ meta.json 定义，执行特定 SDLC 任务并产出工件 | 全文 |
| **Stage（SDLC 阶段）** | 软件交付标准阶段，基础骨架含 9 个阶段：需求探索 / 概要需求 / 详细需求 / 概要设计 / 详细设计 / 编码 / 测试 / 发布 / 归档。复杂度路由路径（Trivial/Light/Standard/Deep）决定 Stage 的合并策略和验证深度。每个 Stage 可绑定 1-n 个 Skill（1 个主 Skill + 0-n 个辅助 Skill） | 流程描述 |
| **审查（Review）** | 人工对 AI 生成产物的检查与批注过程，含行内批注、全局修改建议、参考资料注入。审查通过后才可进入 Gate 审批 | 质量保障 |
| **迭代修改（Revision）** | 基于人工审查反馈和参考资料，AI 重新生成产物的过程。每次重新生成产生新版本，支持版本对比 | 质量保障 |
| **参考资料（Reference）** | 用户向 AI 提供的辅助材料（竞品链接、设计规范、代码规范、示例文档、截图），作为重新生成的上下文输入 | 质量保障 |
| **Skill Flow** | 声明式 YAML 工作流，定义 Stage 间的依赖关系、Stage 内 Skill 编排、数据流转、审批节点与错误处理策略 | 编排引擎 |
| **Gate** | 人工审批节点，阻塞下游 Stage 解锁，共四道（Gate-1 概要需求 / Gate-2.5 详细需求 / Gate-2 概要设计 / Gate-3 UAT）。合并后的 Stage 共享同一个 Gate | 流程描述 |
| **Draft/Active 双态** | 预立项 Draft 态（轻量分析，仅允许分析型 Skill）与正式执行 Active 态（完整流程，允许执行型 Skill） | 项目治理 |
| **HITL** | Human-in-the-Loop，人工参与关键决策节点，实现"AI 执行、人工把关" | 审批流程 |
| **Waiting** | Skill 执行到 Gate 节点时的暂停状态，释放执行锁，等待用户确认后继续 | 状态机 |
| **产物（Artifact）** | Skill 执行生成的文件（Markdown、YAML、JSON、代码等），存储于本地文件系统 | 产物管理 |
| **拓扑图** | SDLC 流程画布的一种视图，以 Skill 为节点、依赖关系为连线，展示项目执行拓扑 | 可视化 |
| **复杂度路由（Complexity Router）** | 流程路径选择的唯一决策点。综合 US-007 规模等级（XS~XL）和技术信号（文件数、实体数、跨服务标记、状态机、新技术引入）自动判定复杂度等级（Trivial/Light/Standard/Deep），推荐对应执行路径。Trivial 跳过 Domain/C4/原型，Stage 合并为 3 个超级 Stage；Light 仅 C4 Container 一层，Stage 合并为 5 个；Standard 完整 9 Stage 流水线；Deep 完整流水线 + 架构漂移检测 + OpenHands 沙箱验证 | 流程描述 |
| **C4 Interactive Navigator** | C4 架构模型层级穿透浏览器，支持从 Context 图逐层下钻到 Container、Component、Code 四级，并支持从 Component 反向定位到本地代码文件 | 可视化 |
| **架构漂移（Architecture Drift）** | 设计架构（arsitect.aac.yml）与实际代码扫描生成的架构之间的偏离，类型包括缺少接口、新增未授权依赖、技术栈不一致 | 质量保障 |
| **OpenHands Executor** | L5 全自动沙箱执行器，基于 Docker 隔离运行，适用于无人值守、高风险操作和架构验证场景。与 Claude Code 本地执行器、Aider 批量重构执行器并列 | 执行层 |
| **超级个体** | 独立开发者或全栈自由职业者，一人承担产品、设计、开发、测试、运维多角色 | 用户画像 |

### US-001：创建项目并初始化复杂度路由预设 {#sec-us001chuangjianu9879mubingchushi}
**完整操作路径**：
1. 用户点击首页"新建项目"按钮
2. 系统弹出项目创建表单
3. 用户填写项目名称、描述、选择 Application（可选）
4. 用户填写项目类型标记（如 Web 应用 / API 服务 / 工具脚本），系统后续基于复杂度路由自动推荐执行路径
5. 系统实时校验输入合法性
6. 用户确认创建，系统初始化项目目录和数据库记录
7. 系统自动进入 Draft 态，引导用户开始脑暴

**用户目标（So That）**：
在 1 分钟内创建结构化的 SDLC 项目，复杂度路由自动处理路径选择，无需手动配置固定模板。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given 用户已打开平台，When 填写有效项目名称（1-100 字符）并选择项目类型标记后提交，Then 系统在 500ms 内创建项目，自动跳转项目工作台，项目状态为 Draft，系统已根据项目类型预设默认复杂度路径。
- **AC2（Negative Path）**：Given 用户未填写项目名称，When 点击提交，Then 系统在 200ms 内提示"项目名称为必填项"，禁止提交。
- **AC3（Edge Case）**：Given 用户输入项目名称已存在，When 点击提交，Then 系统提示"项目名称已存在，请修改"，保留其他表单数据不丢失。

**完整操作路径**：
1. 用户在项目工作台点击"进入画布"
2. 系统加载该项目的 SDLC 拓扑图（动态生成节点和连线）
3. 用户查看节点状态（未开始/进行中/已通关/已阻塞/Gate 等待）
4. 用户点击一个前置依赖已满足的未开始节点
5. 右侧滑出阶段详情面板，展示 Skill 指令快照和输入产物
6. 用户点击"执行 Skill"
7. 系统调用 Kimi CLI，节点状态变为"进行中"
8. 用户可查看实时日志或等待产物生成
9. 执行完成后，节点状态自动更新，输出产物出现在详情面板

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given 项目处于 Active 态且前置节点已通关，When 用户点击未开始节点并执行 Skill，Then 系统在 3s 内触发 Kimi CLI，节点状态变为 IN_PROGRESS，右侧面板展示实时日志流。
- **AC2（Negative Path）**：Given 前置节点未通关，When 用户点击下游节点，Then 系统提示"前置依赖未完成，不可执行"，禁用执行按钮。
- **AC3（Edge Case）**：Given Kimi CLI 未安装或版本不兼容，When 用户执行 Skill，Then 系统捕获错误并在面板中展示安装引导链接，节点状态变为 BLOCKED。

### US-004：浏览和管理产物 {#sec-us004u6d4flanheguanlichanu7269}
**完整操作路径**：
1. 用户在阶段详情面板或顶部导航点击"产物浏览器"
2. 系统展示产物目录树（按项目/阶段/Skill 组织）
3. 用户点击某 Markdown 产物
4. 系统渲染 Markdown 内容，包括代码高亮、Mermaid 图表实时转换
5. 用户点击 Mermaid 图表旁的"渲染"按钮，查看可视化图表
6. 用户点击 OpenAPI YAML，系统渲染为交互式 API 文档
7. 用户可下载产物或在新标签页打开源码

**用户目标（So That）**：
无需离开平台即可查看所有 AI 生成的产物，且获得比纯文本更好的阅读体验。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given 产物文件存在且格式为 Markdown，When 用户在产物浏览器中点击该文件，Then 系统在 500ms 内渲染完整内容，Mermaid 代码块在 2s 内完成图表渲染。
- **AC2（Negative Path）**：Given 产物文件被外部删除，When 用户点击该文件，Then 系统提示"产物文件不存在，可能已被外部删除"，提供"刷新目录"按钮。
- **AC3（Edge Case）**：Given 产物文件体积 > 10MB，When 用户点击该文件，Then 系统提示"文件较大，建议下载后查看"，提供分页预览（前 5000 字）和完整下载选项。

**完整操作路径**：
1. 用户点击"Skill 管理"
2. 系统展示已注册的 Skill 列表
3. 用户点击"导入 Skill"
4. 用户选择本地目录或拖拽文件夹
5. 系统解析 SKILL.md Frontmatter 和 meta.json
6. 系统校验 Skill 格式合法性
7. 系统展示预览（节点名称、描述、阶段归属）
8. 用户确认导入
9. 系统更新画布节点库，现有项目可选择是否启用新 Skill

**用户目标（So That）**：
灵活扩展平台的 Skill 覆盖范围，不被预置节点数量限制。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given 用户导入符合规范的 Skill 目录，When 点击确认导入，Then 系统在 2s 内完成解析，新增节点出现在画布节点库中，meta.json 中的 `platforms` 字段包含 "kimi"。
- **AC2（Negative Path）**：Given 用户导入缺少 SKILL.md 的目录，When 点击确认导入，Then 系统提示"未找到 SKILL.md，导入失败"，不添加节点。
- **AC3（Edge Case）**：Given 导入的 Skill 名称与已有 Skill 重复，When 点击确认导入，Then 系统提示"Skill 名称冲突，是否覆盖？"，用户可选择覆盖或重命名。

### US-006：查看历史项目分析 {#sec-us006chakanu5386u53f2u9879mufenx}
**应用场景（Given/When）**：
Given 用户有至少 1 个已完成项目，When 进入"历史回溯"页面

**完整操作路径**：
1. 用户点击顶部导航"历史回溯"
2. 系统展示已完成项目列表
3. 用户选择一个项目查看详情
4. 系统展示项目时间线（各阶段开始/结束时间）
5. 用户可查看阶段耗时统计
6. 用户可选择两个项目进行对比
7. 系统展示阶段耗时对比表格和偏差高亮
8. 用户查看返工热力图（高亮频繁重试的阶段）

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given 存在 2 个已完成项目，When 用户选择对比，Then 系统在 1s 内展示阶段耗时对比表，偏差超过 30% 的阶段用红色高亮。
- **AC2（Negative Path）**：Given 用户无已完成项目，When 进入历史回溯页面，Then 系统展示空状态提示"暂无已完成项目，完成一个项目后即可查看分析"。
- **AC3（Edge Case）**：Given 用户选择对比的项目阶段不完全一致（如一个使用了自定义模板），When 对比时，Then 系统仅展示共有阶段，缺失阶段标注"N/A"并提示"阶段结构不同，对比仅供参考"。

### US-007：评估项目规模并生成 Timebox 初稿 {#sec-us007pingguu9879muguimobingsheng}
**应用场景（Given/When）**：
Given 用户已创建 Draft 项目并输入需求描述，When 进入项目工作台

**完整操作路径**：
1. 用户创建 Draft 项目，填写需求描述
2. 系统自动触发 Triage 初估（关键词模式匹配五维度：模块数、接口数、页面数、复杂度、风险）
3. 系统展示初估结果：三档得分（乐观/预期/保守）、规模等级（XS/S/M/L/XL）、置信度
4. 用户查看初估报告，可选择"继续 Draft"或"调整参数"
5. 用户在 Draft 阶段完成脑暴/概要需求分析
6. 系统触发 Calibrate 精修，用实际模块数/接口数/页面数替代推断值
7. 系统展示精修结果与初估偏差对比
8. 用户确认最终规模等级（可手动 +/-1 级覆盖），系统生成里程碑 Timebox 初稿（各 Phase 工时区间）
9. 规模评估结果作为复杂度路由（US-011）的输入信号之一，用户进入复杂度路由面板选择执行路径

**用户目标（So That）**：
在项目启动前量化规模，生成里程碑 Timebox 初稿，为复杂度路由（US-011）提供输入信号。规模评估本身不决定执行路径，路径决策由复杂度路由统一处理。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given 用户输入需求描述"开发一个订单管理系统，包含用户、订单、支付三个模块，约 15 个接口，8 个页面"，When Triage 自动执行，Then 系统在 3s 内输出三档得分和规模等级（如 M 级），置信度 >= Medium，并生成 Timebox 初稿（各 Phase 默认工时区间）。
- **AC2（Calibrate 精修）**：Given Draft 阶段产出头脑风暴结果（实际模块数 4，接口数 12），When 用户点击"精修评估"，Then 系统在 2s 内用实际值重新计算，展示与初估的偏差（如模块数偏差 -20%，等级维持 M 级）。
- **AC3（手动覆盖）**：Given 精修结果为 M 级，用户基于业务判断认为应为 L 级，When 用户选择 +1 级覆盖并填写原因，Then 系统记录覆盖决策日志，更新 Timebox 初稿，并同步调整复杂度路由的默认推荐（M 级默认 Standard，L 级默认 Deep），但用户仍可在 US-011 面板覆盖路径选择。
- **AC4（Edge Case）**：Given 保守得分 > 70（XL 级），When Triage 完成，Then 系统提示"建议拆分为多个子项目，单个项目规模过大可能导致里程碑失控"，提供"仍继续"和"拆分建议"两个选项。

### US-008：管理里程碑时间盒与范围变更 {#sec-us008guanliliu7a0bu7891shijianu7}
**应用场景（Given/When）**：
Given 项目已进入 Active 态，When 用户需要设定里程碑计划或遇到范围变更

**完整操作路径**：
1. 用户进入项目工作台，查看里程碑时间线
2. 系统展示默认 Timebox（基于规模等级和模板推荐自动生成）
3. 用户可调整各 Phase 的截止日期（调整时系统实时计算总工期变化）
4. 用户在执行过程中需要新增模块
5. 系统弹出"范围锚定警告"，提示新增模块将触发规模重估和 Timebox 调整
6. 用户确认新增后，系统重新计算规模等级，推荐 Timebox 调整方案
7. 用户选择接受调整或维持原计划（接受则将新增模块标记为 P1 或后续迭代）
8. 基线后的产物发生变更（如 PRD 修改）
9. 系统自动标记变更产物为 Stale，计算受影响下游节点
10. 用户查看影响分析结果，决定重跑/复用/终止哪些节点

**用户目标（So That）**：
通过时间盒约束防止项目无限蔓延，通过范围锚定和影响分析控制变更风险。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given 项目为 M 级标准模板（6 个 Phase），When 系统自动生成 Timebox，Then 每个 Phase 默认分配合理的工时区间（如 Clarify 2h / Align 4h / Contract 4h / Build 12h / Verify 4h / Release 2h），总时长不超过 28h，且截止前 24h 和 4h 分别发送预警通知。
- **AC2（范围锚定）**：Given 项目已锁定模块清单（3 个模块），When 用户尝试新增第 4 个模块，Then 系统弹出确认对话框，展示"新增模块将使规模等级从 M 升至 L，建议 Timebox +8h，是否继续？"，用户确认后才可新增。
- **AC3（Stale 传播）**：Given Gate-1 后的 PRD 基线产物被用户外部修改，When 系统检测到哈希变化，Then 自动标记 PRD 为 Stale，影响分析引擎在 2s 内计算出下游 Align/Contract 阶段 4 个节点受影响，展示"建议重跑"列表。
- **AC4（Edge Case）**：Given Timebox 到期用户未处理，When 截止时间到达，Then 系统将未开始节点标记为"裁剪候选"，发送通知"Clarify 阶段 Timebox 已到期，建议裁剪非核心需求或延长时间盒"，项目状态不变更，由用户决策。

**关联 JTBD**：J1, J3
**优先级**：P0

**完整操作路径**：
1. 用户点击 Stage 节点，进入阶段详情面板
2. 用户切换到"审查"Tab，查看主 Skill 产物
3. 用户在 Artifact Viewer 中高亮文本并添加评论气泡（批注关联到文件、行号和版本）
4. 用户在全局修改建议输入框中填写结构化建议（P0阻塞/P1建议/P2优化）
5. 用户拖拽/粘贴参考资料（URL/文件/文本）到参考资料区
6. 系统展示已添加的批注列表和参考资料引用摘要
7. 用户确认修改建议后，点击"提交审查"
8. 系统记录审查结果，Stage 状态变为 REVIEW_PENDING
9. 用户可选择"重新生成"，系统携带前序版本全部批注和参考资料作为上下文触发 Skill 重新执行
10. 系统生成新版本，用户可查看版本列表、diff 对比（增删改高亮），或回滚到任意历史版本

### US-010：多人协作批注（P1） {#sec-us010u591arenu534fu4f5cpizhup1}
### US-011：查看复杂度路由推荐并确认执行路径 {#sec-us011chakanfuu6742duluyoutuiu835}
**应用场景（Given/When）**：
Given 用户在 Draft 阶段已完成规模评估（US-007），When 系统展示复杂度路由推荐

**完整操作路径**：
1. 系统采集复杂度信号：US-007 规模等级（XS/S/M/L/XL）作为基础输入，叠加技术信号（文件数、实体数、跨服务标记、状态机、新技术引入）
2. 综合信号自动判定复杂度等级（Trivial / Light / Standard / Deep）
3. 系统展示复杂度路由面板，可视化四条执行路径
4. 每条路径展示：包含的 Stage 列表、合并策略、跳过的阶段（灰色）、额外增加的阶段（高亮）
5. 推荐路径高亮，系统说明推荐依据（信号置信度 + 规模等级关联）
6. 用户可点击任意路径查看详细 Stage 拓扑预览
7. 用户确认推荐路径，或选择其他路径并填写覆盖原因
8. 系统记录路由决策，生成对应的 Skill Flow YAML，结合 US-007 的 Timebox 初稿初始化里程碑

> **决策分层原则**：US-011 是流程路径选择的唯一决策点。US-007 回答"项目有多大"（规模估算），US-011 回答"走哪条路径"（路径决策）。规模等级作为复杂度路由的输入信号之一，但非唯一决定因素。技术信号（跨服务/新技术）可独立将路径提升为 Deep，即使规模等级为 S。

**用户目标（So That）**：
在项目启动前直观理解不同执行路径的差异，选择最适合当前需求的流程深度，避免简单需求走完整仪式或复杂需求遗漏关键验证。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given 系统判定为 Standard 级，When 用户查看路由面板，Then 系统在 1s 内展示四条路径对比，Standard 路径高亮，展示完整 9 阶段流水线。
- **AC2（路径差异可视化）**：Given 用户对比 Trivial 与 Standard 路径，When 点击"差异对比"，Then 系统高亮 Trivial 跳过的阶段（需求探索深度分析、C4 建模、原型验证），并标注"预计节省 60% 时间"。
- **AC3（人工覆盖）**：Given 系统推荐 Light 级，用户基于业务判断选择 Standard 级，When 用户切换路径并填写原因，Then 系统记录覆盖决策日志，允许进入 Active，但标记"人工覆盖"标签。
- **AC4（降级安全）**：Given 系统推荐 Deep 级（触发条件：跨服务依赖或新技术引入），When 用户尝试降级到 Standard，Then 系统弹出警告"降级将跳过架构漂移检测和 OpenHands 沙箱验证，风险自担"，要求二次确认。

### US-012：C4 架构模型层级穿透浏览 {#sec-us012c4-jiagoumoxingu5c42jiu7a7f}
**应用场景（Given/When）**：
Given 项目已生成或导入 arsitect.aac.yml 架构模型文件，When 用户进入"架构"视图

**完整操作路径**：
1. 用户在产物浏览器或专用"C4 架构"Tab 中查看项目架构
2. 系统从 arsitect.aac.yml 渲染 C4 Context 图（最高层级，展示系统边界和外部依赖）
3. 用户点击某个 Container（如"风控服务"）
4. 系统下钻到 C4 Container 图，展示该容器内的 Component 和技术栈
5. 用户点击某个 Component
6. 系统下钻到 C4 Component 图，展示代码级元素和接口契约
7. 用户点击"查看代码"可反向定位到本地代码文件
8. 系统支持面包屑导航返回上级层级，支持缩略图总览

**用户目标（So That）**：
在平台内完成对架构设计的多层级可视浏览，从宏观系统边界快速穿透到微观代码实现，确保架构设计与代码实现的一致性可视。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given arsitect.aac.yml 存在且格式合法，When 用户打开 C4 架构浏览器，Then 系统在 2s 内渲染 Context 图，节点可点击且布局稳定。
- **AC2（层级穿透）**：Given Context 图已渲染，When 用户点击"风控服务"Container，Then 系统在 1s 内下钻到 Container 图，面包屑更新为"Context > 风控服务"。
- **AC3（反向定位）**：Given Container 图内某 Component 绑定了代码路径（arsitect.codegen_target），When 用户点击"查看代码"，Then 系统调用本地默认 IDE 或代码编辑器打开对应文件（若存在）。
- **AC4（异常处理）**：Given arsitect.aac.yml 缺失或格式错误，When 用户打开 C4 架构浏览器，Then 系统提示"架构模型文件不存在或格式错误，请检查项目配置"，不崩溃且提供"新建空模板"按钮。

### US-013：查看架构漂移检测报告并处理偏离（P1） {#sec-us013chakanjiagouu6f02yijianceba_1}
**应用场景（Given/When）**：
Given 项目已完成代码生成且系统触发了 C4 InterFlow 反向扫描，When 检测到设计架构与实际架构存在偏离

**完整操作路径**：
1. 系统在代码生成后自动触发 C4 InterFlow 反向扫描（Deep 路径）
2. 对比引擎对比设计架构（arsitect.aac.yml）与实际架构（arsitect.actual.yml）
3. 若发现偏离，生成架构漂移报告
4. 用户在产物浏览器或"架构验证中心"查看报告
5. 报告展示：偏离类型（缺少接口 / 新增未授权依赖 / 技术栈不一致）、影响组件、严重级别、修复建议
6. 用户可选择"忽略此项"（记录原因）或"回退修复"（触发重新生成或手动修改）
7. 若选择回退，系统将相关 Stage 状态回退到 BLOCKED，并自动关联产物批注

**用户目标（So That）**：
在代码实现偏离架构设计时及时发现并可视化管理偏离项，防止架构腐烂。

**验收标准（Given-When-Then）**：
- **AC1（Happy Path）**：Given 架构漂移检测完成且发现 2 项偏离，When 用户查看报告，Then 系统展示偏离列表，每项含类型、影响组件、严重级别、修复建议。
- **AC2（Diff 对比）**：Given 用户点击某偏离项，When 选择"查看设计 vs 实际对比"，Then 系统展示左右分栏 diff 视图，左侧为设计架构片段，右侧为实际扫描结果，差异行高亮。
- **AC3（一键回退）**：Given 用户确认需要修复，When 点击"回退到修复节点"，Then 系统将相关 Stage 状态回退到 BLOCKED，并自动关联产物批注"架构漂移：缺少接口 X"。

## 4. 功能需求清单 {#sec-4-gongnengxuqiuu6e05dan}
> 编号规范：REQ-P0-001 顺序编号，禁止 a/b/c 后缀。每个功能需求必须追溯到一个用户故事。

| 编号 | 需求描述 | 优先级 | 关联用户故事 | 关联验收标准 | 状态 |
|------|----------|--------|-------------|-------------|------|
| REQ-P0-001 | 创建项目时初始化复杂度路由：系统根据 US-007 规模评估结果预设默认执行路径（Trivial/Light/Standard/Deep），用户在路由面板（US-011）确认或覆盖。不再提供独立的"标准 SDLC / 快速通道 / 自定义"模板选择 | P0 | US-001, US-011 | AC1, AC2, AC3 | INCLUDED |
| REQ-P0-002 | 项目列表支持搜索、排序和状态筛选 | P0 | US-001 | AC1 | INCLUDED |
| REQ-P0-003 | SDLC 拓扑图动态渲染（基于导入的 Skill 生成节点和连线） | P0 | US-002 | AC1, AC2 | INCLUDED |
| REQ-P0-004 | 节点状态实时同步（未开始/进行中/已通关/已阻塞/Gate 等待） | P0 | US-002 | AC1, AC2 | INCLUDED |
| REQ-P0-005 | 点击节点打开阶段详情面板（Skill 快照、输入/输出产物、日志、门禁） | P0 | US-002 | AC1 | INCLUDED |
| REQ-P0-006 | 触发 Kimi CLI 执行 Skill 并捕获输出 | P0 | US-002 | AC1, AC3 | INCLUDED |
| REQ-P0-007 | Gate 节点 AI 辅助自检摘要生成 | P0 | US-003 | AC1, AC3 | INCLUDED |
| REQ-P0-008 | Gate 快速确认/驳回/重试操作 | P0 | US-003 | AC1, AC2 | INCLUDED |
| REQ-P0-009 | Gate 历史决策追溯 | P0 | US-003 | AC1 | INCLUDED |
| REQ-P0-010 | 产物浏览器多模态渲染（Markdown/Mermaid/Swagger/YAML/JSON） | P0 | US-004 | AC1, AC2, AC3 | INCLUDED |
| REQ-P0-011 | 产物目录树浏览和下载 | P0 | US-004 | AC1, AC2 | INCLUDED |
| REQ-P0-012 | 用户手动注册/导入 Skill 路径 | P0 | US-005 | AC1, AC2, AC3 | INCLUDED |
| REQ-P0-013 | Skill Frontmatter 和 meta.json 解析与校验 | P0 | US-005 | AC1, AC2 | INCLUDED |
| REQ-P0-014 | 项目 Draft/Active 双态管理 | P0 | US-001 | AC1 | INCLUDED |
| REQ-P0-015 | 实时通知（Skill 状态变更、Gate 等待） | P0 | US-002, US-003 | AC1 | INCLUDED |
| REQ-P1-001 | 已完成项目时间线与阶段耗时统计 | P1 | US-006 | AC1 | PLANNED |
| REQ-P1-002 | 项目间阶段耗时对比与偏差高亮 | P1 | US-006 | AC1, AC3 | PLANNED |
| REQ-P1-003 | 返工热力图（按阶段统计重试次数） | P1 | US-006 | AC1 | PLANNED |
| REQ-P0-016 | 项目规模评估向导（五维度输入、Triage/Calibrate 两次评估、三档得分、规模等级推荐、Timebox 初稿生成）。规模评估不直接决定执行路径，路径决策由 US-011 复杂度路由统一处理 | P0 | US-007 | AC1, AC2, AC3, AC4 | INCLUDED |
| REQ-P0-017 | 里程碑 Timebox 与范围锚定（截止日期管理、新增模块确认、基线化 Stale 传播、影响分析引擎） | P0 | US-008 | AC1, AC2, AC3, AC4 | INCLUDED |
| REQ-P0-018 | Stage 与 Skill 绑定配置：每个 Stage 可绑定 1-n 个 Skill，含主 Skill（核心产出）和辅助 Skill（进度更新、质量检查、产物校验），YAML 中定义绑定关系 | P0 | US-001 | AC1 | INCLUDED |
| REQ-P0-019 | Stage 合并与拆分：复杂度路由路径（Trivial/Light/Standard/Deep）预设 Stage 合并策略（如 Trivial 自动合并为 3 个超级 Stage，Light 合并为 5 个 Stage）。用户可在路由面板查看合并效果，支持手动微调合并分组。支持从合并 Stage 中拆分回独立 Stage（P1） | P0 | US-011 | AC1 | INCLUDED |
| REQ-P0-020 | 产物行内批注：用户在 Artifact Viewer 中高亮文本并添加评论气泡，批注关联到具体文件、行号和版本 | P0 | US-009 | AC1 | INCLUDED |
| REQ-P0-021 | Stage 审查面板：Stage Detail 面板提供"审查"Tab，含全局修改建议输入框（结构化：P0阻塞/P1建议/P2优化）、参考资料拖拽/粘贴区（URL/文件/文本） | P0 | US-009 | AC1 | INCLUDED |
| REQ-P0-022 | 参考资料注入：用户提供的参考资料在 AI 重新生成时自动注入为上下文输入，系统展示参考资料引用摘要 | P0 | US-009 | AC2 | INCLUDED |
| REQ-P0-023 | 产物版本历史与对比：每次重新生成产生新版本，支持版本列表查看、diff 对比（增删改高亮）、版本回滚到任意历史版本 | P0 | US-009 | AC3 | INCLUDED |
| REQ-P0-024 | 基于反馈重新生成：用户提交批注和建议后，点击"重新生成"，系统携带前序版本全部批注和参考资料作为输入触发 Skill 重新执行 | P0 | US-009 | AC4 | INCLUDED |
| REQ-P1-004 | 多人协作批注：多用户实时同步批注、评论线程、标记已解决、离线同步 | P1 | US-010 | — | PLANNED |
| REQ-P0-025 | 复杂度信号自动采集与等级判定：基于文件数、实体数、跨服务标记、状态机、新技术引入五维信号，自动判定 Trivial/Light/Standard/Deep 四级复杂度 | P0 | US-011 | AC1 | INCLUDED |
| REQ-P0-026 | 四级执行路径可视化对比：每条路径展示 Stage 列表、合并策略、跳过阶段（灰色置灰）、额外阶段（高亮），支持路径间差异高亮对比 | P0 | US-011 | AC2 | INCLUDED |
| REQ-P0-027 | 路由推荐人工覆盖与决策日志：用户可切换推荐路径并填写覆盖原因，系统记录覆盖决策日志，标记"人工覆盖"标签，降级到更低路径需二次确认 | P0 | US-011 | AC3, AC4 | INCLUDED |
| REQ-P0-028 | C4 架构模型四级渲染：从 arsitect.aac.yml 解析并渲染 Context/Container/Component/Code 四级架构图，支持 Mermaid/PlantUML/SVG 多格式输出 | P0 | US-012 | AC1, AC4 | INCLUDED |
| REQ-P0-029 | C4 层级穿透导航与反向代码定位：支持点击下钻到下一层级，面包屑导航同步更新；Component 级节点支持反向定位到本地代码文件（通过 arsitect.codegen_target） | P0 | US-012 | AC2, AC3 | INCLUDED |
| REQ-P1-005 | 架构漂移检测报告展示：展示偏离类型（缺少接口/新增未授权依赖/技术栈不一致）、影响组件、严重级别、修复建议，支持"忽略"与"回退修复"操作 | P1 | US-013 | AC1, AC3 | PLANNED |
| REQ-P1-006 | 设计架构与实际架构 diff 可视化：左右分栏对比视图，差异行高亮，支持单偏离项逐条查看 | P1 | US-013 | AC2 | PLANNED |
| REQ-P2-001 | 多 AI 平台适配（Claude/Cursor/MCP） | P2 | — | — | PLANNED |

| 规则编号 | 规则描述 | 适用模块 | 触发条件 |
|----------|----------|----------|----------|
| BR-001 | 只有处于 Draft 或 Active 状态的项目才可执行 Skill | 项目治理 | 用户点击"执行" |
| BR-002 | Gate 审批通过前，下游节点不可执行 | SDLC 画布 | 节点依赖关系校验 |
| BR-003 | Draft 态项目仅允许执行预立项分析型 Skill | 项目治理 | 用户选择 Skill 类型 |
| BR-004 | Draft 项目 7 天无活动自动归档为 Cancelled | 项目治理 | 定时任务触发 |
| BR-005 | 节点执行失败后，用户可手动重试，最多重试 3 次 | Skill 调度 | 用户点击"重试" |
| BR-006 | 产物文件哈希校验失败时，标记节点为 BLOCKED | 产物管理 | 用户打开产物或系统轮询 |
| BR-007 | Skill 执行状态变更必须写入数据库审计日志 | 执行追踪 | 每次状态转移 |
| BR-008 | 用户导入 Skill 时，若名称冲突必须显式确认覆盖或重命名 | Skill 注册 | 用户导入 Skill |
| BR-009 | Gate 摘要置信度为"低"时，禁止一键通过 | Gate 审批 | AI 摘要生成完成 |
| BR-010 | AI 禁止自动执行发布相关 Skill（release-management / finish） | 安全规则 | 系统调度器 |
| BR-011 | 规模等级变更需用户显式确认，自动降级可接受，升级需二次确认 | 项目治理 | Calibrate 结果与初估等级不同 |
| BR-012 | Timebox 到期前 24h 和 4h 分别发送预警通知 | 项目治理 | 定时任务触发 |
| BR-013 | 范围锚定后新增模块必须触发规模重估和 Timebox 调整建议 | 项目治理 | 用户新增模块 |
| BR-014 | 基线后的产物变更自动标记 Stale，下游依赖节点状态更新为待确认 | 产物管理 | 产物哈希校验变化 |
| BR-015 | 每个 Stage 必须有且仅有 1 个主 Skill（primary），辅助 Skill（auxiliary）数量不限。主 Skill 失败则 Stage 失败 | Stage 编排 | Stage 执行调度 |
| BR-016 | 合并后的 Stage 共享同一个 Gate，Gate 通过即视为合并内所有原 Stage 通过 | Stage 编排 | Gate 审批提交 |
| BR-017 | 合并 Stage 中的 Skills 按原 Stage 分组并行执行，同一原 Stage 内的 Skills 按 execution_order 串行执行 | Stage 编排 | Stage 执行计划生成 |
| BR-018 | Stage 产物生成后必须进入 REVIEW_PENDING 状态，禁止自动流转到 GATE_PENDING 或 COMPLETED | 审查规则 | 产物生成完成 |
| BR-019 | 人工必须至少浏览 1 份产物并停留 >=30 秒，才可提交修改建议或 Gate 审批 | 审查规则 | 提交修改建议 / Gate 审批 |
| BR-020 | 重新生成时必须携带前序版本的全部人工批注和参考资料作为上下文输入 | 审查规则 | 触发重新生成 |
| BR-021 | 产物版本历史保留最近 10 个版本，超过后自动归档到压缩存储 | 版本管理 | 版本生成 |
| BR-022 | Gate 审批驳回后，系统必须保留驳回理由并自动关联到产物批注 | Gate 规则 | Gate 驳回 |
| BR-023 | 辅助 Skill 的产物（自检报告、质量门禁报告）默认不触发 REVIEW_PENDING，但可在审查面板查看 | 审查规则 | 辅助 Skill 执行完成 |
| BR-024 | 复杂度路由推荐作为默认建议，用户可在路由面板手动覆盖；降级到更低路径（如 Deep→Standard）需二次确认并记录原因 | 项目治理 | 用户在路由面板切换路径 |
| BR-025 | C4 架构模型必须从 arsitect.aac.yml 实时渲染，禁止缓存过期数据；文件变更后自动刷新或提示用户手动刷新 | 产物管理 | arsitect.aac.yml 文件哈希变化 |
| BR-026 | 流程路径选择的唯一决策点为复杂度路由（US-011）。US-007 规模评估仅输出规模等级和 Timebox 初稿，不直接决定执行路径。技术信号（跨服务依赖/新技术引入）可独立提升路径等级，不受规模等级上限约束 | 项目治理 | 规模评估完成或技术信号变更 |

### 5.1 规则优先级与冲突仲裁 {#sec-51-guizeyouu5148jiyuu51b2u7a81u4}
| 优先级 | 规则类型 | 说明 | 冲突示例 |
|--------|----------|------|----------|
| P1 | 硬规则（Hard Rule） | 不可覆盖，违反则系统拒绝 | BR-010（AI 禁止自动发布）、BR-003（Draft 态限制）、BR-013（范围锚定强制重估）、BR-015（主 Skill 唯一性） |
| P2 | 门控规则（Gate Rule） | 可通过人工审批有条件覆盖 | BR-002（Gate 阻塞）、BR-009（低置信度强制检查）、BR-011（等级升级确认）、BR-016（合并 Stage Gate 共享） |
| P3 | 软规则（Soft Rule） | 系统警告但不阻止，需人工确认 | BR-004（7 天自动归档前发送提醒）、BR-006（哈希校验失败警告）、BR-012（Timebox 预警）、BR-014（Stale 标记提示）、BR-017（合并 Stage 执行顺序）、BR-019（阅读时长不足预警）、BR-023（辅助产物审查提示）、BR-025（C4 缓存过期提示） |

**冲突仲裁逻辑**：
- 硬规则 > 门控规则 > 软规则
- 当并行启动规则与 Gate 阻塞规则冲突时：以 Gate 节点为硬边界，Gate 未通过前，被阻塞阶段节点不可执行，但不受影响的阶段节点可正常推进。

> 打通用户故事 -> 功能需求 -> 验收标准。每个功能需求必须追溯到一个用户故事，否则视为伪需求。

| 用户故事 | 功能需求 | 需求描述 | 优先级 | 验收标准 | 状态 |
|----------|----------|----------|--------|----------|------|
| US-001 | REQ-P0-001 | 创建项目时初始化复杂度路由预设 | P0 | AC1: 项目创建 < 500ms；AC2: 空名称校验；AC3: 重名提示 | INCLUDED |
| US-011 | REQ-P0-001 | 复杂度路由面板确认路径选择 | P0 | AC1: 路径渲染 < 1s；AC2: 差异对比高亮；AC3: 覆盖记录 | INCLUDED |
| US-001 | REQ-P0-002 | 项目列表搜索排序筛选 | P0 | AC1: 列表加载 < 1s | INCLUDED |
| US-001 | REQ-P0-014 | Draft/Active 双态管理 | P0 | AC1: 状态切换正确 | INCLUDED |
| US-002 | REQ-P0-003 | SDLC 拓扑图动态渲染 | P0 | AC1: 节点渲染 < 2s；AC2: 前置依赖校验 | INCLUDED |
| US-002 | REQ-P0-004 | 节点状态实时同步 | P0 | AC1: 状态同步 < 5s；AC2: 前置依赖校验 | INCLUDED |
| US-002 | REQ-P0-005 | 阶段详情面板 | P0 | AC1: 面板滑出 < 300ms | INCLUDED |
| US-002 | REQ-P0-006 | 触发 Kimi CLI 执行 | P0 | AC1: 触发 < 3s；AC3: CLI 未安装错误处理 | INCLUDED |
| US-002 | REQ-P0-015 | 实时通知 | P0 | AC1: 通知推送 < 1s | INCLUDED |
| US-003 | REQ-P0-007 | Gate AI 自检摘要 | P0 | AC1: 摘要生成 < 5s；AC3: 低置信度警告 | INCLUDED |
| US-003 | REQ-P0-008 | Gate 确认/驳回/重试 | P0 | AC1: 确认 < 500ms；AC2: 驳回保留记录 | INCLUDED |
| US-003 | REQ-P0-009 | Gate 历史追溯 | P0 | AC1: 历史记录可查 | INCLUDED |
| US-004 | REQ-P0-010 | 产物多模态渲染 | P0 | AC1: Markdown 渲染 < 500ms；AC2: 文件缺失提示；AC3: 大文件分页 | INCLUDED |
| US-004 | REQ-P0-011 | 产物目录树和下载 | P0 | AC1: 目录树加载 < 1s | INCLUDED |
| US-005 | REQ-P0-012 | 手动导入 Skill | P0 | AC1: 导入 < 2s；AC2: 格式错误提示；AC3: 冲突处理 | INCLUDED |
| US-005 | REQ-P0-013 | Skill 解析校验 | P0 | AC1: 解析成功；AC2: 缺失文件检测 | INCLUDED |
| US-006 | REQ-P1-001 | 历史项目时间线 | P1 | AC1: 时间线渲染 < 1s | PLANNED |
| US-006 | REQ-P1-002 | 项目对比 | P1 | AC1: 对比表生成 < 1s；AC3: 阶段差异提示 | PLANNED |
| US-006 | REQ-P1-003 | 返工热力图 | P1 | AC1: 热力图渲染 < 2s | PLANNED |
| US-007 | REQ-P0-016 | 项目规模评估向导 | P0 | AC1: Triage < 3s; AC2: Calibrate < 2s; AC3: 覆盖记录; AC4: XL 级拆分提示 | INCLUDED |
| US-008 | REQ-P0-017 | 里程碑 Timebox 与范围锚定 | P0 | AC1: Timebox 自动生成 + 预警; AC2: 新增模块确认; AC3: Stale 影响分析 < 2s; AC4: 到期裁剪候选 | INCLUDED |
| US-009 | REQ-P0-020 | 产物行内批注 | P0 | AC1: 批注触发重新生成; AC2: 未浏览拦截; AC3: 版本归档; AC4: 回滚恢复 | INCLUDED |
| US-009 | REQ-P0-021 | Stage 审查面板 | P0 | AC1: 结构化建议提交 | INCLUDED |
| US-009 | REQ-P0-022 | 参考资料注入 | P0 | AC2: 参考资料上下文注入 | INCLUDED |
| US-009 | REQ-P0-023 | 产物版本历史与对比 | P0 | AC3: diff 对比与回滚 | INCLUDED |
| US-009 | REQ-P0-024 | 基于反馈重新生成 | P0 | AC4: 携带批注重新生成 | INCLUDED |
| US-010 | REQ-P1-004 | 多人协作批注 | P1 | AC1: 实时同步; AC2: 并发编辑冲突; AC3: 离线同步 | PLANNED |
| US-011 | REQ-P0-019 | Stage 合并与拆分（复杂度路由预设策略） | P0 | AC1: 合并/拆分正确 | INCLUDED |
| US-011 | REQ-P0-025 | 复杂度信号自动采集与等级判定 | P0 | AC1: 自动判定并展示 | INCLUDED |
| US-011 | REQ-P0-026 | 四级执行路径可视化对比 | P0 | AC2: 路径差异高亮 | INCLUDED |
| US-011 | REQ-P0-027 | 路由推荐人工覆盖与决策日志 | P0 | AC3, AC4: 覆盖记录与降级二次确认 | INCLUDED |
| US-012 | REQ-P0-028 | C4 架构模型四级渲染 | P0 | AC1: 2s 内渲染 Context; AC4: 异常处理 | INCLUDED |
| US-012 | REQ-P0-029 | C4 层级穿透导航与反向代码定位 | P0 | AC2: 下钻 < 1s; AC3: 反向定位 | INCLUDED |
| US-013 | REQ-P1-005 | 架构漂移检测报告展示 | P1 | AC1: 偏离列表; AC3: 回退修复 | PLANNED |
| US-013 | REQ-P1-006 | 设计架构与实际架构 diff 可视化 | P1 | AC2: 左右分栏 diff | PLANNED |

## 7. 变更日志 {#sec-7-biangengrizhi}
| 版本         | 日期         | 变更内容                                                                                                              | 变更人      |
| ---------- | ---------- | ----------------------------------------------------------------------------------------------------------------- | -------- |
| v1.4-draft | 2026-06-01 | 架构决策澄清（方案 A）：复杂度路由（US-011）取代流程模板选择，US-007 规模评估弱化为纯规模估算+Timebox，不直接决定执行路径。更新 REQ-P0-001/P0-016/P0-019、术语表、In-Scope、用户旅程、新增 BR-026 明确决策分层 | AI Agent |
| v1.3-draft | 2026-06-01 | 扩展 MVP 范围：补充假设登记册；新增 US-011（复杂度路由面板）、US-012（C4 架构穿透浏览）、US-013（架构漂移检测）；对应新增 REQ-P0-025~029、REQ-P1-005~006、BR-024~025；更新 RTM 与模块映射 | AI Agent |
| v1.2-draft | 2026-06-01 | 修复 doc-quality-gate 发现问题：统一版本号为 v1.2-draft；修正需求阶段状态标记为 INCLUDED/PLANNED；补充 US-009/US-010 消除悬空引用；Stage 绑定规则修正为 1-n | AI Agent |
| v1.1-draft | 2026-05-31 | 补充 US-007/US-008 及 REQ-P0-016/REQ-P0-017、BR-011~BR-014、RTM 更新                                                     | AI PM    |
| v1.0-draft | 2026-05-31 | 初始版本，包含 6 个用户故事、15 个 P0 需求、3 个 P1 需求                                                                              | AI PM    |

---

## 附录：adaptive-architecture-engine 补充内容 {#sec-u9644luadaptivearchitectureengin}
# PRD-000 需求清单 - arsitect 自适应架构引擎升级

| 属性 | 值 |
|------|-----|
| 变更名 | adaptive-architecture-engine |
| 版本 | PRD-000 v1.0-draft |
| 状态 | 待用户确认基线后冻结 |
| 上游输入 | 00-requirements-overview.md |

- 复杂度自适应路由引擎（Trivial / Light / Standard / Deep 四级）
- C4 InterFlow DSL 架构模型管理（正向渲染、反向扫描、架构查询）
- 架构漂移检测与报告生成
- OpenHands 沙箱执行器集成（Docker 服务调用）
- 原型-架构双向绑定（OpenUI 验证后自动回写 DSL）
- CI/CD 架构文档即代码流水线（GitHub Actions 自动渲染 + 漂移检测）
- Stage Gate 控制器与进度追踪的增强（支持 drift 状态）
- 现有 41 个 Skill 在新架构下的零修改兼容运行

- 替换现有 41 个 Skill 的 Markdown 定义内容
- 修改外部 AI 平台（Kimi/Claude/Cursor）的接口协议
- 重写 arsitect 的 Markdown 核心载体格式
- OpenUI 前端代码生成引擎本身的开发（仅集成调用）
- C4 InterFlow CLI 工具本身的开发（仅集成调用）
- OpenHands 核心代理能力的开发（仅集成调用）
- 多语言反向工程支持（MVP 仅支持 Java，其他语言后续扩展）

### 1.3 Non-goals {#sec-13-nongoals}
| 非目标 | 排除原因 |
|--------|---------|
| 本期不做 AI 模型层面的微调或训练 | 依赖外部 LLM 平台能力，arsitect 只做编排层 |
| 本期不做多 Workspace 的并发性能优化 | 当前单 Workspace 已能满足核心场景，多 Workspace 为 Phase 3 目标 |
| 本期不做移动端 App 或小程序适配 | arsitect 面向 AI CLI/IDE 插件场景，无移动端需求 |
| 本期不做支付、订阅、计费等商业化功能 | 当前为内部工程平台，商业化非本期重点 |
| 本期不做实时协作编辑（多人同时编辑同一文档） | 架构 DSL 以文件为中心，协作编辑为 P2 优化项 |

| 术语 | 定义 |
|------|------|
| AaC | Architecture as Code，架构即代码，指用代码/配置文件描述系统架构 |
| Complexity Router | 复杂度路由引擎，根据需求信号自动判定应走的 SDLC 路径 |
| Context Package | 发送给代码执行器的上下文包，包含需求描述、架构约束、接口契约等 |
| Drift Detection | 架构漂移检测，对比设计架构与实际代码架构的一致性 |
| Execution Path | 执行路径，指 Trivial / Light / Standard / Deep 四种 SDLC 流程 |
| Gate | 阶段门控，人工评审节点（Gate 1/2.5/2/3），未签字禁止进入下一阶段 |
| OpenHands | 开源 AI 代码代理，支持在 Docker 沙箱中自主执行代码任务 |
| SDLC | Software Development Life Cycle，软件开发生命周期 |
| Skill | arsitect 的核心能力单元，自包含的 Markdown 工作流定义 |
| Stage | 阶段，指需求分析、概要设计、详细设计、编码、测试、发布等 SDLC 阶段 |
| Trivial / Light / Standard / Deep | 四级复杂度定义，决定流程仪式的轻重程度 |

## 3. 需求清单 {#sec-3-xuqiuu6e05dan}
### 3.1 P0 需求（必须交付） {#sec-31-p0-xuqiuu5fc5u987bjiaofu}
| 编号 | 需求名称 | 需求描述 | 优先级 |
|------|---------|---------|--------|
| REQ-P0-001 | 复杂度路由引擎 | 系统根据需求信号自动判定复杂度等级（Trivial/Light/Standard/Deep），并推荐对应的执行路径 | P0 |
| REQ-P0-002 | C4 InterFlow DSL 底座 | 系统支持以 C4 InterFlow DSL 描述架构，支持正向渲染生成架构图 | P0 |
| REQ-P0-003 | 架构漂移检测 MVP | 系统支持从代码反向生成架构模型，并与设计架构对比，输出漂移报告 | P0 |
| REQ-P0-004 | Stage Gate 增强 | 系统支持 drift 状态，允许架构漂移报告作为 Gate 评审的输入，不跳过任何人工门控 | P0 |
| REQ-P0-005 | 现有 Skill 兼容 | 系统升级后，现有 41 个 Skill 的触发条件和行为规范保持不变 | P0 |
| REQ-P0-006 | 降级策略 | 外部服务不可用时，系统自动降级到本地模式，核心流程不中断 | P0 |

### 3.2 P1 需求（重要，影响核心体验） {#sec-32-p1-xuqiuchongyaou5f71u54cdhex}
| 编号 | 需求名称 | 需求描述 | 优先级 |
|------|---------|---------|--------|
| REQ-P1-001 | OpenHands 沙箱执行器 | 系统支持将 Context Package 发送至 OpenHands Docker 沙箱执行，并收集结果 | P1 |
| REQ-P1-002 | 原型-架构双向绑定 | OpenUI 原型验证发现缺失接口时，系统自动回写 C4 InterFlow DSL 并标记变更 | P1 |
| REQ-P1-003 | CI/CD 架构渲染流水线 | 代码提交时自动触发架构图渲染和漂移检测，结果作为 CI 门禁 | P1 |
| REQ-P1-004 | 复杂度路由人工覆盖 | PM/Tech Lead 可在路由面板手动覆盖自动推荐的路径 | P1 |
| REQ-P1-005 | 架构查询引擎 | 支持基于 JSONPath 的架构影响分析查询（如查找所有 Spring Boot 服务） | P1 |

### 3.3 P2 需求（优化项，可延后） {#sec-33-p2-xuqiuyouhuau9879u53efyanu5}
| 编号 | 需求名称 | 需求描述 | 优先级 |
|------|---------|---------|--------|
| REQ-P2-001 | 多语言反向工程 | 支持 Python/Go/TypeScript 等语言的反向工程扫描 | P2 |
| REQ-P2-002 | 路由阈值自动校准 | 基于历史路由日志，自动优化信号权重和阈值 | P2 |
| REQ-P2-003 | 夜间批处理模式 | 支持定时任务触发 Deep 路径的无人值守执行 | P2 |
| REQ-P2-004 | 架构版本对比 | 支持查看架构模型的历史版本差异 | P2 |

## 4. 用户故事与验收标准 {#sec-4-yonghuguu4e8byuyanshoubiaozhun}
### US-001：快速修复开发者（Trivial 路径） {#sec-us001u5febsuxiufukaifau8005trivi}
**背景**：Alex 是一名后端开发，需要修复一个单字段校验规则的问题。

**用户故事**：
> 作为后端开发者，当我提交一个单文件修改的 bug fix 需求时，我希望系统直接生成代码而不走完整文档流程，以便在 15 分钟内完成修复。

**验收标准**：

AC1 (Happy Path):
Given Alex 已登录并提交一个 estimated_files=1 且无新实体的需求，
When 系统完成复杂度分析，
Then 复杂度路由推荐 Trivial 路径，并跳过 DomainParser、C4 建模、原型验证阶段。

AC2 (Happy Path):
Given 需求被判定为 Trivial 路径，
When Alex 确认执行，
Then 系统直接生成 Context Package 并调用 AI Code 平台生成代码，总耗时不超过 15 分钟。

AC3 (Negative Path):
Given Alex 提交的需求被误判为 Trivial（实际涉及跨服务修改），
When PM 在评审时发现误判，
Then PM 可在路由面板手动将路径覆盖为 Standard，系统重新按完整流程执行。

AC4 (Edge Case):
Given 外部 C4 InterFlow CLI 服务不可用，
When 需求进入 Trivial 路径执行，
Then 系统自动降级到本地模式，代码生成流程不受影响。

### US-002：架构负责人（Standard/Deep 路径） {#sec-us002jiagoufuu8d23renstandarddee}
**背景**：Ben 是 Tech Lead，需要确保新微服务的代码实现符合架构设计。

**用户故事**：
> 作为 Tech Lead，当我启动一个跨服务的新模块开发时，我希望系统自动执行完整架构建模和沙箱验证，以便在代码合并前确认实现与设计一致。

**验收标准**：

AC1 (Happy Path):
Given Ben 提交一个涉及跨服务依赖的新模块需求，
When 系统完成复杂度分析，
Then 复杂度路由推荐 Deep 路径，并自动展开 C4 建模、架构查询、OpenHands 沙箱验证。

AC2 (Happy Path):
Given Deep 路径执行到代码生成阶段，
When OpenHands 在沙箱中完成代码生成，
Then 系统自动调用 C4 InterFlow 反向扫描生成实际架构，并与设计架构对比。

AC3 (Negative Path):
Given 架构漂移检测发现代码实现缺少设计中的某个接口，
When 系统生成漂移报告，
Then 报告标记为 drift 状态，Ben 在 Gate 2 评审时可选择接受偏差或要求修复。

AC4 (Edge Case):
Given OpenHands 沙箱连续 2 次执行失败，
When 系统检测到执行异常，
Then 自动回退到 Claude Code 本地执行模式，并记录降级事件到审计日志。

### US-003：项目管理者（路径管理与进度追踪） {#sec-us003u9879muguanliu8005lujinggua}
**背景**：Cindy 是 PM，需要根据需求复杂度合理估算工期并跟踪进度。

**用户故事**：
**验收标准**：

AC1 (Happy Path):
Given Cindy 进入项目看板，
When 查看当前激活的需求列表，
Then 每个需求显示其复杂度路径（Trivial/Light/Standard/Deep）、当前阶段、待通过的 Gate。

AC2 (Happy Path):
Given 某需求处于 Gate 2 待评审状态，
When Cindy 点击查看详情，
Then 系统显示该 Gate 的签字人、签字状态、关联的漂移报告（如有）。

AC3 (Negative Path):
Given 系统检测到某需求被跳过 Gate 直接进入下一阶段，
When progress-tracker 执行扫描，
Then 系统立即阻断该需求并发送告警给 Cindy 和 Tech Lead。

AC4 (Edge Case):
Given 项目中有 10 个同时激活的需求，
When Cindy 刷新看板，
Then 页面加载时间不超过 2 秒（P95）。

### 5.1 硬规则（不可违反） {#sec-51-u786cguizebuu53efu8fddfan}
| 编号 | 规则 | 说明 |
|------|------|------|
| BR-001 | Gate 不可跳过 | 任何需求必须经过对应路径要求的全部 Gate 人工签字，系统不得自动通过 Gate |
| BR-002 | 无规格编码禁止 | executing-plans（编码实现）必须等待 interface-first-dev（接口契约）和 task-breakdown（任务拆解）完成后方可启动 |
| BR-003 | 外部服务降级 | 外部 Docker 服务不可用时，系统必须自动降级到本地模式，不得阻断核心流程 |
| BR-004 | 沙箱结果审查 | OpenHands 沙箱生成的代码必须通过 PR + 代码审查后方可合并到主仓库 |
| BR-005 | 数据隔离 | 不同项目的架构 DSL、漂移报告、沙箱日志必须按项目 ID 隔离 |

### 5.2 门控规则（Stage Gate 控制） {#sec-52-menkongguizestage-gate-kongzh}
| 编号 | 规则 | 说明 |
|------|------|------|
| BR-006 | Gate 1 在概要需求完成后冻结需求基线 | 未通过 Gate 1 禁止进入详细需求与概要设计 |
| BR-007 | Gate 2.5 在详细需求完成后评审模块级需求 | 未通过禁止进入详细设计 |
| BR-008 | Gate 2 在概要设计完成后确认架构决策 | 未通过禁止进入详细设计 |
| BR-009 | Gate 3 在 UAT 完成后验收业务流程 | 未通过禁止进入发布阶段 |
| BR-010 | 复杂度路由不改变 Gate 要求 | Trivial 路径可跳过部分阶段，但所需 Gate 的签字要求不变 |

### 5.3 软规则（可配置/可覆盖） {#sec-53-u8f6fguizeu53efpeizhiu53effug}
| 编号 | 规则 | 说明 |
|------|------|------|
| BR-011 | 复杂度路由默认推荐 | 系统根据信号自动推荐路径，PM/Tech Lead 可手动覆盖 |
| BR-012 | 保守阈值策略 | MVP 期间，模糊需求默认判定为 Standard 路径 |
| BR-013 | 漂移检测灵敏度 | 架构漂移检测的误报容忍度默认 < 15%，可由 Architect 调整 |
| BR-014 | 上下文压缩触发 | 单轮 LLM 上下文超过 80K tokens 时自动触发摘要压缩 |

### 5.4 冲突仲裁逻辑 {#sec-54-u51b2u7a81u4ef2u88c1luoji}
| 冲突场景 | 仲裁逻辑 |
|---------|---------|
| 自动路由推荐 Trivial，但 PM 手动覆盖为 Standard | 以人工覆盖为准，记录覆盖原因到审计日志 |
| 漂移检测报告建议 block，但 Tech Lead 选择接受 | Tech Lead 签字确认后放行，记录偏差说明 |
| 外部服务可用性波动导致频繁降级 | 连续 3 次降级后触发 DevOps 告警，人工介入检查 |
| 同一需求在多个执行器（Claude Code vs OpenHands）生成不同代码 | 以 Git PR 审查结果为准，冲突由 Tech Lead 裁决 |

| 用户故事 | 功能需求 | 需求描述 | 优先级 | 验收标准 | 状态 |
|----------|----------|----------|--------|----------|------|
| US-001 | REQ-P0-001 | 复杂度路由引擎 | P0 | AC1: Trivial 路径推荐正确；AC2: 15 分钟内完成；AC3: 人工覆盖有效；AC4: 降级成功 | NOT_STARTED |
| US-001 | REQ-P0-006 | 降级策略 | P0 | AC4: 外部服务不可用时降级到本地 | NOT_STARTED |
| US-001 | REQ-P1-004 | 复杂度路由人工覆盖 | P1 | AC3: PM 可手动覆盖路径 | NOT_STARTED |
| US-002 | REQ-P0-001 | 复杂度路由引擎 | P0 | AC1: Deep 路径推荐正确 | NOT_STARTED |
| US-002 | REQ-P0-002 | C4 InterFlow DSL 底座 | P0 | AC2: 反向扫描生成实际架构 | NOT_STARTED |
| US-002 | REQ-P0-003 | 架构漂移检测 MVP | P0 | AC2/AC3: 漂移检测与报告 | NOT_STARTED |
| US-002 | REQ-P0-004 | Stage Gate 增强 | P0 | AC3: drift 状态作为 Gate 输入 | NOT_STARTED |
| US-002 | REQ-P1-001 | OpenHands 沙箱执行器 | P1 | AC2: 沙箱执行与反向扫描 | NOT_STARTED |
| US-002 | REQ-P1-002 | 原型-架构双向绑定 | P1 | Deep 路径包含原型验证 | NOT_STARTED |
| US-002 | REQ-P1-003 | CI/CD 架构渲染流水线 | P1 | 代码提交触发渲染与检测 | NOT_STARTED |
| US-003 | REQ-P0-004 | Stage Gate 增强 | P0 | AC1/AC2: 进度追踪与 Gate 状态展示 | NOT_STARTED |
| US-003 | REQ-P0-005 | 现有 Skill 兼容 | P0 | 看板与现有 progress-tracker 兼容 | NOT_STARTED |
| US-003 | REQ-P0-006 | 降级策略 | P0 | AC4: 看板加载性能保障 | NOT_STARTED |

| 版本 | 日期 | 变更内容 | 变更人 |
|------|------|---------|--------|
| v1.0-draft | 2026-06-01 | 初始版本，基于 brainstorming 产出物和 GTPlanner.txt 生成 | AI Agent |
