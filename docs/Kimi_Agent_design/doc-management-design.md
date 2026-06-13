# Arsitect 文档管理设计方案（DocForge 适配版）

> **文档版本**：v1.0.0  
> **编写日期**：2026-06-10  
> **目标读者**：架构师、AI Agent 开发者、技术负责人  
> **依赖输入**：`docs/ref-doc/DocForge-design.md`、`docs/ref-doc/C4-doc-rules.md`、`openspec/changes/sdlc-visualizer/`  
> **文档状态**：DRAFT

---

## 一、概要

### 1.1 设计目标

将 Arsitect 研发过程文档从**"文件级全量覆盖"**升级为**"基线 + Delta 增量编译"**模式，实现：

1. **像管理代码一样管理文档**：支持增量变更、版本追溯、合并编译、影响面分析
2. **C4 模型原生嵌入**：文档即架构接口，YAML Front Matter 绑定 C4 层级，正文通过 `@C4-` 标签与架构图谱精确关联
3. **AI 上下文按需组装**：Agent 不再全量读取所有文档，而是根据当前任务精准提取相关片段
4. **兼容现有 OpenSpec 目录结构**：不破坏 `openspec/changes/{变更}/` 的现有组织方式，平滑演进

### 1.2 核心设计哲学

```plain
代码管理                 文档管理（本方案）
─────────────────────────────────────────────────────────
Git commit              →  Delta 版本（增量补丁）
Git diff                →  Delta 编译器（章节级合并）
Git checkout            →  文档编译（基线 + Delta → 全量）
Code review             →  文档评审（迭代绑定 + 变更集）
Import / Dependency     →  @C4- 标签（跨文档架构引用）
```

---

## 二、适用场景

| 场景编号  | 场景描述                       | 当前痛点                              | 本方案解决方式                                                       |
| :---- | :------------------------- | :-------------------------------- | :------------------------------------------------------------ |
| S-001 | AI 架构师 Agent 编写概要设计时参考需求文档 | 需求散落在多次迭代的增量文件中，Agent 不知道该读哪个版本   | 文档编译器实时合成**当前最新全量视图**，Agent 只读一份完整文档                          |
| S-002 | 技术负责人评审某迭代的文档变更            | 需要人工对比前后两个版本的完整文件，无法快速定位"改了哪几节"   | Delta 指令天然记录变更范围，编译器输出**带批注的对比视图**                            |
| S-003 | 编码阶段 Agent 查询接口契约          | 接口定义在详细设计文档中，但设计文档已迭代 3 个版本，内容有覆盖 | 按 `fragment_id` + `target_version` 精准编译，Agent 获取**精确版本**的接口章节 |
| S-004 | 架构师维护 C4 模型与文档的一致性         | 架构图与文档脱节，文档改了但 C4 DSL 未同步，或反之     | `@C4-` 标签建立双向绑定，文档变更触发**跨层一致性校验**                             |
| S-005 | 项目归档时生成完整交付物               | 需要手动收集各阶段产物，拼凑成完整文档包              | 一键编译该变更下所有文档的**最新完整版本**，自动打包                                  |
| S-006 | 新成员接入项目，快速了解全貌             | 需要阅读数十份分散的 Markdown 文件，无法获取统一视图   | 按模块维度编译**聚合视图**（如：某模块的需求→设计→接口全链路）                            |

---

## 三、当前文档格式分析（基于 sdlc-visualizer 实践）

### 3.1 现有格式特征

通过分析 `openspec/changes/sdlc-visualizer/` 下的 100+ 份文档，总结当前格式规律：

#### 3.1.1 元信息区块（非结构化）

当前文档顶部使用**自由文本**描述元信息，而非标准 YAML Front Matter：

```markdown
# 设计总览

> 版本：HLD-000 v1.0
> 状态：**Draft**（等待 Gate 2 评审）
> 变更：sdlc-visualizer
> 日期：2026-06-01
> 编制依据：PRD-000 v2.0-patch2（Frozen）
```

**问题**：无法被机器解析，AI Agent 需要靠启发式规则提取版本、状态、依赖关系。

#### 3.1.2 修改记录表格

```markdown
| 版本 | 日期 | 修改人 | 修改内容 |
|------|------|--------|----------|
| v2.0 | 2026-06-01 | AI Agent | 基于 brainstorming v2.0 重构... |
| v2.0-patch1 | 2026-06-01 | AI Agent | 恢复审查功能... |
```

**问题**：修改记录与文档正文耦合，Delta 无法独立存在；版本语义不统一（有 `v2.0-patch1` 这种非 SemVer 格式）。

#### 3.1.3 章节标题无稳定锚点

```markdown
## 1. 引言

### 1.1 目的

## 2. 设计考量

### 2.1 假设
```

**问题**：章节编号随内容增删会变化（如插入新节导致 2.1 变 2.2），无法作为稳定的 Delta 定位标识。当前**无任何锚点ID**。

#### 3.1.4 跨文件引用使用相对路径

```markdown
| REF-001 | `high-level-requirements/00-requirements-overview.md` | v2.0-patch2 |
```

**问题**：路径引用是静态字符串，无版本号，无法判断引用的是哪个历史版本。

#### 3.1.5 无 C4 绑定标记

当前文档中**不存在** `@C4-L2-Container:api-service` 这类标签，C4 模型与文档正文的关联完全依赖人工记忆。

#### 3.1.6 文档组织按阶段分目录

```plain
openspec/changes/sdlc-visualizer/
├── high-level-requirements/
│   ├── 00-requirements-overview.md
│   └── 01-requirements-list.md
├── detailed-requirements/
│   └── feature-01-project-dashboard/
│       └── module-requirements.md
├── high-level-design/
│   ├── 00-design-overview.md
│   └── 01-architecture-core.md
├── detailed-design/
│   └── feature-01-project-dashboard/
│       └── module-design.md
└── interface-contracts/
    └── openapi.yaml
```

**特征**：阶段边界清晰，但模块信息散落在不同阶段目录中，缺乏"以模块为视角"的聚合能力。

### 3.2 与目标格式的差距

| 维度 | 当前状态 | DocForge + C4 目标 | 差距等级 |
|:-----|:---------|:-------------------|:---------|
| 元数据格式 | 自由文本 | YAML Front Matter（强类型） | 中 |
| 版本规范 | 文件级覆盖，SemVer 不统一 | 基线 + Delta，严格 SemVer | 高 |
| 章节定位 | 无锚点，靠标题文本 | 稳定锚点ID `{#sec-xxx}` | 高 |
| 增量能力 | 无，每次全量重写 | ADD/MODIFY/DELETE/PATCH 指令 | 高 |
| C4 绑定 | 无 | `c4_binding` YAML + `@C4-` 标签 | 高 |
| 编译合并 | 无 | 文档编译器合成全量视图 | 高 |
| 目录结构 | 按阶段组织 | 阶段 × 模块双维组织 | 中 |

---

## 四、格式规范

### 4.1 文档类型编码

兼容 DocForge 类型体系，与 Arsitect SDLC 阶段映射：

| 类型编码 | 类型名称 | SDLC 阶段 | C4 绑定强制 | 说明 |
|:---------|:---------|:----------|:-----------|:-----|
| `PRD` | 产品需求文档 | 概要需求 | 是（L1） | 用户故事、功能范围、验收标准 |
| `DOMAIN_MODEL` | 领域模型文档 | 详细需求 | 是（L2） | 实体定义、业务规则 |
| `ARCH` | 架构设计文档 | 概要设计 | 是（L2） | 容器划分、技术选型、数据流 |
| `DETAIL_DESIGN` | 详细设计文档 | 详细设计 | 是（L3） | 组件设计、状态机、算法 |
| `API_DESIGN` | 接口设计文档 | 接口契约 | 是（L3） | OpenAPI、请求/响应 Schema |
| `DB_DESIGN` | 数据库设计文档 | 详细设计 | 是（L2） | ER图、DDL、索引策略 |
| `TEST_PLAN` | 测试计划 | 单元测试/集成测试 | 否 | 测试范围、用例分类 |
| `TEST_CASE` | 测试用例 | 单元测试/集成测试 | 否 | 具体用例 |
| `DEPLOYMENT` | 部署文档 | 发布上线 | 否 | 发布步骤、回滚方案 |
| `CHANGELOG` | 变更日志 | 收尾归档 | 否 | 版本说明 |

### 4.2 YAML Front Matter 规范

所有过程文档**必须**在文件首行包含 YAML Front Matter（`---` 包裹）。

#### 4.2.1 公共字段

```yaml
---
doc_type: "PRD"                          # 文档类型编码，必填
fragment_id: "prd-sdlc-visualizer-001"   # 片段唯一标识，格式：{type}-{module}-{seq}
title: "SDLC Visualizer 概要需求"         # 人类可读标题，1-100字符
version: "1.0.0"                         # SemVer，必填
version_type: "BASELINE"                 # BASELINE 或 DELTA
base_version: ""                         # DELTA 时必填，指向基线版本
change_type: ""                          # DELTA 时必填：ADD/MODIFY/DELETE/PATCH
change_summary: ""                       # DELTA 时必填，50-200字符
author: "agent-pm"                       # 作者标识
tags: ["sdlc", "visualizer", "p0"]       # 业务标签
status: "FROZEN"                         # DRAFT / REVIEW / FROZEN / DEPRECATED
iteration: "sdlc-visualizer"             # 所属变更/迭代名称
dependencies:                            # 上游依赖文档列表
  - fragment_id: "brainstorm-sdlc-001"
    version: "1.0.0"
  - fragment_id: "comp-analysis-sdlc-001"
    version: "1.2.0"
c4_binding:                              # 架构绑定，架构类文档必填，见下节
  ...
---
```

#### 4.2.2 字段约束

| 字段 | 类型 | 必填 | 取值规则 |
|:-----|:-----|:-----|:---------|
| `doc_type` | ENUM | 是 | 见 4.1 类型编码表 |
| `fragment_id` | STRING | 是 | 小写，连字符分隔，`{type}-{module}-{seq}` |
| `title` | STRING | 是 | 1-100 字符 |
| `version` | SEMVER | 是 | `MAJOR.MINOR.PATCH`，基线默认 `1.0.0` |
| `version_type` | ENUM | 是 | `BASELINE` / `DELTA` |
| `base_version` | SEMVER | 条件 | `version_type=DELTA` 时必填 |
| `change_type` | ENUM | 条件 | `version_type=DELTA` 时必填 |
| `change_summary` | STRING | 条件 | `version_type=DELTA` 时必填，50-200字符 |
| `author` | STRING | 是 | AI Agent 填 `agent-{role}`，人工填用户名 |
| `status` | ENUM | 是 | `DRAFT` / `REVIEW` / `FROZEN` / `DEPRECATED` |
| `iteration` | STRING | 是 | 对应 `openspec/changes/{变更名}/` |
| `dependencies` | ARRAY | 否 | 每项含 `fragment_id` + `version` |
| `c4_binding` | OBJECT | 条件 | 架构类文档必填，见 C4-doc-rules.md |

### 4.3 章节锚点 ID 规范

#### 4.3.1 语法

所有标题级章节**必须**附加稳定锚点ID，格式：

```markdown
## 1. 功能范围 {#sec-scope}

### 1.1 用户登录 {#sec-user-login}

#### 异常处理 {#sec-login-error}
```

**BNF**：
```bnf
anchor_id ::= "sec-" segment ["-" segment]*
segment   ::= lowercase_letter | digit | "_"
```

**规则**：
- 前缀固定为 `sec-`
- 只允许小写字母、数字、下划线
- 禁止连续下划线 `__`
- 禁止以数字开头（前缀后）
- 最大长度：64 字符

#### 4.3.2 按文档类型的推荐锚点结构

| 文档类型 | 推荐顶层锚点 | 说明 |
|:---------|:-------------|:-----|
| `PRD` | `sec-business-context`, `sec-system-boundary`, `sec-scope`, `sec-nfr`, `sec-risk` | 业务上下文必须在最前 |
| `DOMAIN_MODEL` | `sec-domain-entities`, `sec-entity-{entity_id}`, `sec-relationships` | 实体章节锚点必须与 `entity_id` 对应 |
| `ARCH` | `sec-tech-arch`, `sec-deployment`, `sec-security`, `sec-data-flow` | 架构视图分区 |
| `DETAIL_DESIGN` | `sec-component-{component_id}`, `sec-class-diagram`, `sec-state-machine` | 组件章节锚点必须与 `component_id` 对应 |
| `API_DESIGN` | `sec-api-contracts`, `sec-api-{interface_id}`, `sec-dto-definitions` | 接口章节锚点必须与 `interface_id` 对应 |
| `DB_DESIGN` | `sec-er-diagram`, `sec-table-{table_id}`, `sec-migration-plan` | 表章节锚点必须与 `table_id` 对应 |

#### 4.3.3 自动生成兜底

若编写者未提供锚点，文档编译器自动按以下规则生成：

```python
# 标题文本 → slug → sec-{slug}
"1. 功能范围"       → "sec-gong-neng-fan-wei"
"用户登录流程"       → "sec-yong-hu-deng-lu-liu-cheng"
"API 契约定义"       → "sec-api-qi-yue-ding-yi"
```

**注意**：自动生成的锚点**不具备稳定性**（标题修改后锚点会变），仅作为兼容过渡，正式文档应**显式声明锚点**。

### 4.4 Delta 操作指令格式

Delta 版本正文分为两部分：

1. **YAML Front Matter**：版本元数据（见 4.2）
2. **操作指令区**：结构化变更描述

#### 4.4.1 操作指令语法

```markdown
---
fragment_id: "prd-sdlc-visualizer-001"
version: "1.1.0"
version_type: "DELTA"
base_version: "1.0.0"
change_type: "MODIFY"
change_summary: "增加复杂度路由需求章节"
---

## [MODIFY] 3. 功能范围 {#sec-scope}
> 替换整个章节

- 单项目端到端周期可视化覆盖率 100%
- **新增：复杂度路由自动适配（Trivial/Light/Standard/Deep）**
- Gate 自检确认耗时 < 30 秒

## [ADD] 3.1 复杂度路由 {#sec-complexity-router}
> 插入位置：after {#sec-scope}

### 3.1.1 路由信号

基于五维度规模评估：模块数、接口数、页面数、技术复杂度、风险等级。

## [PATCH] 4. 非功能需求 {#sec-nfr}
> 局部修改

- [ADD] 规模评估接口响应时间 < 500ms（P95）
- [MODIFY] 首屏加载时间 < 2s → 首屏加载时间 < 1.5s
```

#### 4.4.2 操作类型说明

| 操作 | 语法标记 | 作用域 | 说明 |
|:-----|:---------|:-------|:-----|
| `ADD` | `## [ADD] 标题 {#new-id}` | 章节级 | 在指定锚点前后插入新章节，必须提供 `> 插入位置` 指令 |
| `MODIFY` | `## [MODIFY] 标题 {#exist-id}` | 章节级 | 替换整个章节内容（含子章节），保留锚点ID |
| `DELETE` | `## [DELETE] 标题 {#exist-id}` | 章节级 | 删除该章节及其所有子章节 |
| `PATCH` | `## [PATCH] 标题 {#exist-id}` | 行/列表项级 | 在章节内部做局部修改，不破坏锚点结构 |

#### 4.4.3 插入位置指令

```markdown
> 插入位置：after {#sec-scope}
> 插入位置：before {#sec-nfr}
```

仅 `ADD` 操作必填。`after` 表示插入到锚点章节之后（成为同级下一个兄弟），`before` 表示插入到锚点章节之前。

### 4.5 @C4- 标签规范

架构相关文档（PRD/DOMAIN_MODEL/ARCH/DETAIL_DESIGN/API_DESIGN/DB_DESIGN）正文**必须**使用 `@C4-` 标签建立与 C4 模型的精确关联。

#### 4.5.1 标准标签清单

| 标签格式 | 适用文档类型 | 示例 |
|:---------|:-------------|:-----|
| `@C4-L1-System:{system_id}` | PRD | `@C4-L1-System:sdlc-visualizer` |
| `@C4-L1-Actor:{actor_id}` | PRD | `@C4-L1-Actor:developer` |
| `@C4-L2-Container:{container_id}` | ARCH, DETAIL_DESIGN | `@C4-L2-Container:web-frontend` |
| `@C4-L3-Component:{component_id}` | DETAIL_DESIGN, API_DESIGN | `@C4-L3-Component:ProjectService` |
| `@C4-Entity:{entity_id}` | DOMAIN_MODEL | `@C4-Entity:Project` |
| `@C4-Attribute:{entity_id}.{attr_name}` | DOMAIN_MODEL, API_DESIGN | `@C4-Attribute:Project.status` |
| `@C4-Interface:{METHOD} {path}` | API_DESIGN | `@C4-Interface:POST /api/v1/projects` |
| `@C4-Table-Name:{table_id}` | DB_DESIGN | `@C4-Table-Name:projects` |

#### 4.5.2 放置位置规则

| 标签 | 必须放置的位置 |
|:-----|:---------------|
| `@C4-L1-System` | 系统边界描述段落首行 |
| `@C4-L2-Container` | 容器职责描述段落首行 |
| `@C4-L3-Component` | 组件描述段落首行 |
| `@C4-Entity` | 实体定义章节标题下方第一行 |
| `@C4-Interface` | 接口契约章节标题下方第一行 |
| `@C4-Table-Name` | 表结构章节标题下方第一行 |

---

## 五、文档管理实现方案

### 5.1 目录结构（兼容现有 OpenSpec）

在保持现有 `openspec/changes/{变更}/` 目录框架基础上，引入**文档编译产物目录**和**Delta 目录**：

```plain
openspec/
├── changes/
│   └── sdlc-visualizer/
│       ├── _meta/                          # 变更级元数据（新增）
│       │   ├── manifest.yaml               # 变更涉及的所有 fragment 清单
│       │   └── progress.md                 # SSOT 进度（保留现有）
│       ├── baseline/                       # 基线文档（首次冻结后生成）
│       │   ├── prd-sdlc-visualizer-001.md
│       │   ├── arch-sdlc-visualizer-001.md
│       │   └── ...
│       ├── delta/                          # 增量补丁（新增）
│       │   ├── v1.1.0-prd-sdlc-visualizer-001.md
│       │   ├── v1.1.0-arch-sdlc-visualizer-001.md
│       │   └── ...
│       ├── compiled/                       # 编译产物（自动生成）
│       │   ├── prd-sdlc-visualizer-001@latest.md
│       │   ├── prd-sdlc-visualizer-001@1.2.0.md
│       │   └── ...
│       ├── high-level-requirements/        # 现有目录保留，存放人类可读原稿
│       ├── high-level-design/              # 现有目录保留
│       ├── detailed-requirements/          # 现有目录保留
│       ├── detailed-design/               # 现有目录保留
│       └── interface-contracts/            # 现有目录保留
│
└── archive/                                # 已归档变更
    └── sdlc-visualizer/
        ├── baseline/
        ├── delta/
        └── compiled/
```

**兼容性说明**：
- `high-level-requirements/` 等现有目录继续作为**人工编写/AI 生成原稿**的存放地
- `baseline/` 和 `delta/` 作为**机器管理的规范格式**存储地
- 提供迁移脚本，将现有自由格式文档转换为规范格式（首次基线化）

### 5.2 版本模型

#### 5.2.1 基线版本（BASELINE）

- 每个 `fragment_id` 的**第一个版本**必须是基线
- 基线存储文档的**完整初始内容**（符合 4.2 / 4.3 / 4.5 规范）
- 基线状态通常为 `FROZEN`（通过 Gate 后冻结）

#### 5.2.2 Delta 版本（DELTA）

- Delta 是**增量补丁**，只记录与上一个版本的差异
- Delta 正文采用**结构化操作指令**（ADD/MODIFY/DELETE/PATCH），而非全文 Diff
- 语义化版本递增规则：
  - 不兼容变更（章节重构、需求范围扩大）→ `MAJOR+1`
  - 功能新增（新接口、新实体）→ `MINOR+1`
  - 修复/优化（文案调整、数值修正）→ `PATCH+1`

#### 5.2.3 版本链示例

```plain
fragment_id: prd-sdlc-visualizer-001

1.0.0 (BASELINE)  ──→  1.1.0 (DELTA, MODIFY sec-scope)  ──→  1.2.0 (DELTA, ADD sec-complexity-router)
   │                        │                                      │
   │                        └─ base_version: 1.0.0                  └─ base_version: 1.1.0
   │
   └─ 完整 PRD 内容（Frozen at Gate 1）
```

### 5.3 文档编译器（Document Compiler）

#### 5.3.1 编译目标

将 `基线 + 版本链上的所有 Delta`，按顺序合并为一份**干净的完整文档**。

#### 5.3.2 编译策略

| 策略 | 说明 | 适用场景 |
|:-----|:-----|:---------|
| `overlay` | 增量覆盖，保留基线未变更章节 | **默认策略**，日常迭代 |
| `full` | 全量替换，Delta 包含完整新章节 | 章节大规模重构时使用 |
| `annotated` | 合并后保留版本批注（HTML/Markdown 注释） | 审计、评审场景 |

#### 5.3.3 编译流程

```plain
输入：fragment_id + target_version + strategy
  │
  ▼
查询版本链（从基线到 target_version 的所有版本）
  │
  ▼
读取基线内容 → 解析为章节树（DocumentTree）
  │
  ▼
遍历 Delta 链（按 version 升序）：
  ├─ 解析 Delta 操作指令 → List[DeltaOperation]
  ├─ 校验 target_id 在章节树中存在
  ├─ 执行合并（ADD/MODIFY/DELETE/PATCH）
  └─ 更新章节树
  │
  ▼
渲染为 Markdown（按 strategy 决定是否保留批注）
  │
  ▼
输出：compiled_content + version_chain 摘要
```

#### 5.3.4 编译缓存

```plain
cache_key = "compile:{fragment_id}:{target_version}:{strategy}:{content_hash}"
```

- **L1 缓存**：进程内 LRU（TTL 10 分钟）
- **L2 缓存**：本地文件系统 `openspec/changes/{变更}/compiled/`
- **失效条件**：版本链中任一 Delta 被修改或新增

### 5.4 模块级聚合编译

除单个 Fragment 编译外，支持**按模块维度聚合**多份文档：

```plain
输入：module = "project-dashboard", target_version = "latest"

聚合清单（由 manifest.yaml 定义）：
  - prd-project-dashboard-001 @latest
  - domain-project-dashboard-001 @latest
  - arch-project-dashboard-001 @latest
  - detail-project-dashboard-001 @latest
  - api-project-dashboard-001 @latest
  - db-project-dashboard-001 @latest

输出：project-dashboard-compiled.md
  （按 PRD → DOMAIN → ARCH → DETAIL → API → DB 顺序拼接，
   每份文档间插入分页符和来源标注）
```

### 5.5 C4 绑定与校验

#### 5.5.1 入库校验流程

```plain
文档提交（Baseline / Delta）
    │
    ▼
解析 YAML Front Matter
    │
    ▼
├─ 架构相关类型（PRD/DOMAIN_MODEL/ARCH/DETAIL_DESIGN/API_DESIGN/DB_DESIGN）
│   └─ 校验 c4_binding 完整性
│       ├─ 缺失 c4_binding → 阻断（错误码 40001）
│       ├─ level 与 doc_type 不匹配 → 阻断（错误码 40002）
│       └─ 通过 → 提取章节锚点 + @C4- 标签
│           └─ 进入跨层一致性校验
│
├─ 非架构类型（TEST/DEPLOY/BUG/CHANGELOG）
│   └─ 标记为 no-arch-binding，跳过 C4 提取
│
└─ 未知类型 → 进入 LLM 辅助发现（可选）
```

#### 5.5.2 跨文档一致性校验（CrossLayerValidator）

| 规则 ID | 校验内容 | 上游文档 | 下游文档 | 失败处理 |
|:--------|:---------|:---------|:---------|:---------|
| `VAL-001` | L1 外部系统引用一致性 | PRD (`external_systems`) | ARCH (`containers`) | 告警：孤立外部系统 |
| `VAL-002` | L2 实体定义一致性 | DOMAIN_MODEL (`entities`) | API_DESIGN (`request_schema`) | 告警：接口字段无领域来源 |
| `VAL-003` | L2 容器归属一致性 | ARCH (`containers`) | DETAIL_DESIGN/API_DESIGN/DB_DESIGN (`container_id`) | **阻断**：容器未定义 |
| `VAL-004` | L3 组件归属一致性 | DETAIL_DESIGN (`components`) | API_DESIGN (`component_id`) | **阻断**：组件未定义 |
| `VAL-005` | L3 接口归属一致性 | API_DESIGN (`interfaces`) | DETAIL_DESIGN (`components.interfaces`) | 提示：接口契约缺失 |
| `VAL-006` | 实体-表映射一致性 | DOMAIN_MODEL (`entities`) | DB_DESIGN (`tables.entity_map`) | 告警：表无领域来源 |

### 5.6 迭代绑定与变更集

#### 5.6.1 迭代模型

- 迭代（Iteration）对应 `openspec/changes/{变更名}/`
- 迭代与文档版本通过 `manifest.yaml` 绑定
- `manifest.yaml` 结构：

```yaml
iteration_id: "sdlc-visualizer"
status: "ACTIVE"
start_date: "2026-06-01"
gate_status:
  gate_1: "PASSED"
  gate_2_5: "PASSED"
  gate_2: "PASSED"
  gate_3: "PENDING"
fragments:
  - fragment_id: "prd-sdlc-visualizer-001"
    latest_version: "1.2.0"
    baseline_version: "1.0.0"
  - fragment_id: "arch-sdlc-visualizer-001"
    latest_version: "1.1.0"
    baseline_version: "1.0.0"
```

#### 5.6.2 变更集视图

支持查看某迭代涉及的全部文档变更：

```plain
迭代变更报告：sdlc-visualizer
─────────────────────────────────
PRD (prd-sdlc-visualizer-001)
  v1.0.0 → v1.1.0 [MODIFY] sec-scope
  v1.1.0 → v1.2.0 [ADD] sec-complexity-router

ARCH (arch-sdlc-visualizer-001)
  v1.0.0 → v1.1.0 [ADD] sec-container-complexity-router

影响面分析：
  - 下游需同步：DETAIL_DESIGN / API_DESIGN / DB_DESIGN
  - C4 模型变更：L2 新增容器 "complexity-router"
```

---

## 六、与现有 OpenSpec 的兼容与迁移策略

### 6.1 向后兼容原则

1. **不删除现有目录**：`high-level-requirements/`、`detailed-design/` 等现有目录继续保留，作为**源稿区**
2. **渐进式引入**：新变更（新项目）强制使用规范格式，历史变更可选迁移
3. **双轨运行**：过渡期允许"规范格式 Delta + 自由格式原稿"共存，编译器优先使用规范格式

### 6.2 现有文档迁移脚本

为现有 `openspec/changes/sdlc-visualizer/` 下的文档提供自动迁移：

```python
# 伪代码：migrate_legacy_doc.py
def migrate_legacy_to_baseline(file_path: str, doc_type: str) -> str:
    """将现有自由格式文档转换为规范 Baseline 格式。"""
    
    # 1. 读取原文件
    content = read(file_path)
    
    # 2. 提取元信息（启发式解析现有的 > 版本 / 状态 / 日期 区块）
    meta = heuristically_extract_meta(content)
    
    # 3. 生成 fragment_id（基于文件路径和 doc_type）
    fragment_id = generate_fragment_id(file_path, doc_type)
    
    # 4. 为所有标题自动生成锚点ID（若原文件无锚点）
    content_with_anchors = auto_inject_anchors(content)
    
    # 5. 组装 YAML Front Matter
    front_matter = build_front_matter(
        doc_type=doc_type,
        fragment_id=fragment_id,
        version="1.0.0",
        version_type="BASELINE",
        title=meta.title,
        author=meta.author or "agent-migration",
        status="FROZEN" if meta.status == "Frozen" else "DRAFT",
        iteration=extract_iteration_from_path(file_path),
    )
    
    # 6. 输出到 baseline/ 目录
    return f"{front_matter}\n\n{content_with_anchors}"
```

### 6.3 过渡期的 Delta 编写建议

在尚未全面迁移到规范格式前，允许使用**简化版 Delta**：

```markdown
---
fragment_id: "arch-sdlc-visualizer-001"
version: "1.1.0"
version_type: "DELTA"
base_version: "1.0.0"
change_type: "MODIFY"
change_summary: "更新技术栈版本：React 18 → React 19"
---

## [MODIFY] 2.1 前端技术栈 {#sec-tech-frontend}

原文：
- React 18 + TypeScript 4.9
- Vite 4

修改为：
- React 19 + TypeScript 5.6
- Vite 6
```

简化版 Delta 不需要完整的替换内容，仅需描述变更点，由人工在基线文件上直接修改后重新冻结。

---

## 七、非功能需求

| 指标 | 目标 | 说明 |
|:-----|:-----|:-----|
| 编译延迟 | < 500ms | 基线 + 5 个 Delta 的编译时间 |
| 版本链查询 | < 100ms | 查询某文档的完整版本链 |
| 存储成本 | 增量比 < 15% | Delta 文件大小相对于全量快照的占比 |
| 锚点唯一性 | 100% | 同一份文档内锚点ID无重复 |
| C4 标签覆盖率 | >= 80% | 架构类文档中可提取的 @C4- 标签占预期数量的比例 |
| 跨层校验通过率 | >= 95% | 迭代提交时跨文档一致性校验通过率 |

---

## 八、演进路线图

### Phase 1：规范固化（1 周）

- [ ] 定义 6 类架构文档的标准 YAML Front Matter 模板
- [ ] 定义标准 `@C4-` 标签清单（20 个）及正则提取规则
- [ ] 定义章节锚点 ID 白名单（按文档类型）
- [ ] 编写 `migrate_legacy_to_baseline.py` 迁移脚本
- [ ] 为新变更强制启用规范格式

### Phase 2：编译器实现（2 周）

- [ ] 实现 Markdown → 章节树解析器（支持锚点提取）
- [ ] 实现 Delta 解析器（ADD/MODIFY/DELETE/PATCH）
- [ ] 实现章节合并引擎（SectionMerger）
- [ ] 实现文档编译器 CLI（支持 `compile --fragment-id --target-version`）
- [ ] 实现编译缓存（本地文件系统 L2 缓存）

### Phase 3：C4 绑定与校验（1 周）

- [ ] 实现 YAML Front Matter 校验（含 `c4_binding` Schema 校验）
- [ ] 实现 `@C4-` 标签提取器
- [ ] 实现跨层一致性校验（VAL-001 ~ VAL-006）
- [ ] 与 C4 Navigator 前端对接：文档编译结果可渲染为 C4 DSL

### Phase 4：平台集成（1 周）

- [ ] 后端 API：文档版本管理、编译、对比
- [ ] 前端页面：文档浏览器（支持版本切换、Diff 视图）
- [ ] 前端页面：模块级聚合视图（需求→设计→接口全链路）
- [ ] AI Agent 上下文接口：按任务类型组装精准上下文

---

## 九、一句话总结

**本方案将 Arsitect 过程文档从"文件级全量覆盖"演进为"基线 + Delta 增量编译"模式：YAML Front Matter 是文档的机器可读接口，稳定锚点ID 是 Delta 补丁的定位系统，`@C4-` 标签是文档与架构图谱的双向绑定坐标——三者共同构成"像管理代码一样管理文档"的基础设施。**
