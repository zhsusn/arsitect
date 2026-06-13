# Skill 生成文档的规范化落地指南

> **文档版本**：v1.0.0  
> **编写日期**：2026-06-10  
> **目标读者**：AI Agent 开发者、Skill 维护者、架构师  
> **依赖文档**：`docs/doc-management-design.md`、`docs/ref-doc/C4-doc-rules.md`  
> **文档状态**：DRAFT

---

## 一、核心结论

**能，而且 Skill 是文档规范落地的最佳载体。**

原因：Arsitect 的 41 个 Skill 中，`prd-generation`、`high-level-design`、`detailed-design`、`detailed-requirements`、`interface-first-dev` 等核心 Skill 直接负责产出过程文档。只要在 Skill 的模板（`references/system-outline-template.md`）和输出指令（`SKILL.md` 的 Step 5）中嵌入文档规范要求，AI Agent 生成的文档天然就是规范格式。

> **关键洞察**：约束 AI 产出格式，比约束人类写作者更容易落地——因为 Skill 的模板就是 Prompt 的一部分，AI 会严格遵守模板中的格式指令。

---

## 二、当前 Skill 生成文档 vs 文档规范的差距分析

### 2.1 元信息格式差距

| 维度 | 当前 Skill 输出（以 prd-generation 为例） | 文档规范要求 | 差距 |
|:-----|:------------------------------------------|:-------------|:-----|
| **元数据格式** | 自由文本引用块 `> 版本：PRD-000 v1.0-draft` | 标准 YAML Front Matter `---` 包裹 | 机器不可解析 |
| **文档类型** | 隐式（由目录决定） | 显式 `doc_type: PRD` | 无法做类型校验 |
| **片段标识** | 无 | `fragment_id: prd-{module}-{seq}` | 无法做片段级版本管理 |
| **版本语义** | 自由文本（`v2.0-patch2`） | 严格 SemVer（`1.0.0`）+ `version_type: BASELINE/DELTA` | 无法做版本链查询 |
| **依赖声明** | 正文中硬编码路径引用 | `dependencies` 数组（含 `fragment_id` + `version`） | 无法做影响面分析 |
| **C4 绑定** | 完全缺失 | `c4_binding` YAML 块 + `@C4-` 标签 | 架构与文档脱节 |

### 2.2 内容结构差距

| 维度 | 当前 Skill 输出 | 文档规范要求 | 差距 |
|:-----|:----------------|:-------------|:-----|
| **章节锚点** | `## 1. 功能范围`（无锚点ID） | `## 1. 功能范围 {#sec-scope}` | 章节级 Delta 无法定位 |
| **跨文件引用** | `` `high-level-requirements/00.md` `` | `dependencies[].fragment_id` + 正文 `@C4-` 标签 | 引用无版本，无法追溯 |
| **修改记录** | 正文中的表格 | Delta 版本独立文件 | 修改记录与正文耦合 |
| **增量能力** | 无，每次全量重写文件 | 基线 + Delta 编译 | 无法精准查看"改了什么" |

### 2.3 具体案例对比

**当前 `prd-generation` 输出的文件头部：**

```markdown
# 00 - 需求总览

> 版本：PRD-000 v2.0-patch2
> 状态：**Frozen** (Gate 1 已通过)
> 作者：AI Product Manager
> 评审人：用户
> 日期：2026-06-01

### 修改记录

| 版本 | 日期 | 修改人 | 修改内容 |
|------|------|--------|----------|
| v2.0 | 2026-06-01 | AI Agent | 基于 brainstorming v2.0 重构... |
```

**按文档规范应输出的文件头部：**

```markdown
---
doc_type: "PRD"
fragment_id: "prd-sdlc-visualizer-000"
title: "SDLC Visualizer 概要需求"
version: "1.0.0"
version_type: "BASELINE"
base_version: ""
change_type: ""
change_summary: ""
author: "agent-pm"
tags: ["sdlc", "visualizer", "p0"]
status: "FROZEN"
iteration: "sdlc-visualizer"
dependencies:
  - fragment_id: "brainstorm-sdlc-visualizer-001"
    version: "1.0.0"
  - fragment_id: "comp-analysis-sdlc-visualizer-001"
    version: "1.2.0"
c4_binding:
  level: "L1"
  system_id: "sdlc-visualizer"
  system_name: "SDLC Visualizer"
  external_systems: []
  actors:
    - id: "developer"
      name: "开发者"
      role_type: "PRIMARY"
      description: "使用 AI 辅助开发的超级个体"
---

# 00 - 需求总览 {#doc-title}

> 状态：**FROZEN** (Gate 1 已通过)  
> 冻结时间：2026-06-01T11:37:00+08:00

## 1. 执行摘要 {#sec-executive-summary}
...
```

---

## 三、Skill 改造方案

### 3.1 改造原则

1. **模板驱动**：修改各 Skill 的 `references/system-outline-template.md`（或同类模板），将 YAML Front Matter 和锚点ID 作为模板的**强制头部**
2. **指令强化**：在 `SKILL.md` 的"输出步骤"中增加格式校验检查点（类似现有的"章节对齐校验"）
3. **渐进落地**：PRD → 概要设计 → 详细设计 → 接口契约 按阶段顺序改造，不要求一次全改
4. **向后兼容**：现有历史文档通过 `migrate_legacy_to_baseline.py` 迁移，Skill 只负责新文档的规范输出

### 3.2 需要改造的 Skill 清单

| Skill                               | 产出文档类型                                       | 改造优先级  | 改造内容                                                                   |
| :---------------------------------- | :------------------------------------------- | :----- | :--------------------------------------------------------------------- |
| `prd-generation`                    | `PRD`                                        | **P0** | 三主题文件模板增加 YAML Front Matter + 锚点ID；增加 `c4_binding` 生成步骤                |
| `high-level-design`                 | `ARCH`                                       | **P0** | 六主题文件模板增加 YAML Front Matter + 锚点ID；容器定义自动写入 `c4_binding`               |
| `detailed-requirements`             | `PRD`（模块级）                                   | **P0** | `module-requirements.md` 模板增加 YAML Front Matter；实体定义写入 `c4_binding`    |
| `detailed-design`                   | `DETAIL_DESIGN` / `API_DESIGN` / `DB_DESIGN` | **P0** | 模块设计模板增加 YAML Front Matter + 锚点ID；组件/接口/表定义写入 `c4_binding`             |
| `interface-first-dev`               | `API_DESIGN`                                 | **P0** | `openapi.yaml` 配套 Markdown 文档增加 YAML Front Matter + `@C4-Interface` 标签 |
| `functional-architecture-generator` | `ARCH` 辅助                                    | **P1** | 生成的功能架构文档增加 `@C4-L2-Container` 标签                                      |
| `documentation`                     | `CHANGELOG` / 运维文档                           | **P1** | 非架构类文档使用简化版 YAML Front Matter（无 `c4_binding`）                          |

> **注意**：`test-driven-development`、`executing-plans`、`code-review-pipeline` 等编码/测试类 Skill 不直接产出过程文档，本次无需改造。

---

## 四、具体改造细节（按 Skill）

### 4.1 prd-generation 改造

#### 4.1.1 修改 `references/system-outline-template.md`

将三个主题文件的模板头部替换为**带 YAML Front Matter 的标准格式**。

**`00-requirements-overview.md` 模板头部改造：**

```markdown
---
doc_type: "PRD"
fragment_id: "prd-{iteration}-000"
title: "{项目名} 概要需求"
version: "1.0.0"
version_type: "BASELINE"
author: "agent-pm"
tags: ["p0"]
status: "DRAFT"
iteration: "{iteration}"
dependencies:
  - fragment_id: "brainstorm-{iteration}-001"
    version: "1.0.0"
c4_binding:
  level: "L1"
  system_id: "{kebab-case-project-name}"
  system_name: "{项目名}"
  external_systems: []
  actors: []
---

# 00 - 需求总览 {#doc-title}

> 状态：Draft（等待 Gate 1 评审）

## 1. 执行摘要 {#sec-executive-summary}
...
```

#### 4.1.2 修改 `SKILL.md` Step 5

在"输出与冻结"步骤中增加：

1. **Step 5.1：YAML Front Matter 生成**
   - 基于 Layer 1~4 的产出，自动填充 `c4_binding.system_id`（从项目名称派生 kebab-case）
   - 基于竞品分析结果填充 `c4_binding.external_systems`
   - 基于 Persona 卡片填充 `c4_binding.actors`
   - 基于上游文档填充 `dependencies`

2. **Step 5.2：锚点ID注入**
   - 为每个 `##` / `###` 标题自动附加锚点ID（如 `## 2. 背景与问题 {#sec-background}`）
   - 锚点ID遵循 `sec-{章节关键词}` 的命名规则

3. **Step 5.3：格式自检（新增）**
   - 检查 YAML Front Matter 是否可被标准 YAML 解析器解析
   - 检查 `doc_type` 是否为 `PRD`
   - 检查 `c4_binding.level` 是否为 `L1`
   - 检查所有 `##` / `###` 标题是否包含锚点ID
   - 若检查失败，标记为 🔴 阻塞，禁止保存

4. **Step 5.4：基线冻结（改造）**
   - 冻结时不再修改自由文本的 `> 版本：PRD-000 v1.0`，而是修改 YAML Front Matter 中的 `version: "1.0.0"` 和 `status: "FROZEN"`
   - 同步生成 `baseline/prd-{iteration}-000.md`

#### 4.1.3 增加 `c4_binding` 生成指南（新增 reference 文件）

在 `references/` 下新增 `c4-binding-guide-for-prd.md`，指导 AI 如何从 PRD 内容中提取 C4 L1 信息：

```markdown
# PRD 的 c4_binding 生成指南

## system_id 派生规则
从项目名称自动转换为 kebab-case：
- "SDLC Visualizer" → "sdlc-visualizer"
- "供应链融资平台" → "supply-chain-financing"

## external_systems 提取规则
在 PRD 的"竞品格局"和"外部依赖"章节中，识别以下信号：
- "需对接 xxx 系统" → 外部系统
- "通过 xxx API 获取数据" → 外部系统
- "与 xxx 平台集成" → 外部系统

## actors 提取规则
在 PRD 的"用户画像"和"角色职责描述"章节中，识别以下信号：
- 每个 Persona 对应一个 Actor
- `role_type` 判定：核心业务操作者 → PRIMARY / 辅助角色 → SECONDARY / 系统/定时任务 → SYSTEM
```

### 4.2 high-level-design 改造

#### 4.2.1 六主题文件模板头部改造

以 `01-architecture-core.md` 为例：

```markdown
---
doc_type: "ARCH"
fragment_id: "arch-{iteration}-001"
title: "{项目名} 架构核心"
version: "1.0.0"
version_type: "BASELINE"
author: "agent-architect"
tags: ["architecture", "p0"]
status: "DRAFT"
iteration: "{iteration}"
dependencies:
  - fragment_id: "prd-{iteration}-000"
    version: "1.0.0"
c4_binding:
  level: "L2"
  containers: []
  container_relations: []
---

# 01 - 架构核心 {#doc-title}

## 1. 系统分层 {#sec-system-layers}
...
```

#### 4.2.2 修改 `SKILL.md` Step 3

在"逐项生成"步骤中增加：

1. **容器定义自动收集**
   - 在生成 `01-architecture-core.md` 的"系统分层"章节时，同步收集容器信息到 `c4_binding.containers`
   - 每个容器必须包含：`container_id`（kebab-case）、`name`、`type`（Frontend/Backend/Database/Cache/MessageQueue/ExternalService）、`technology`、`responsibilities`

2. **容器关系自动收集**
   - 在生成数据流/部署拓扑 Mermaid 图时，同步提取容器间关系到 `c4_binding.container_relations`

3. **`@C4-L2-Container` 标签自动注入**
   - 在描述每个容器职责的段落首行，自动插入 `@C4-L2-Container:{container_id}`

### 4.3 detailed-requirements 改造

#### 4.3.1 模块需求文件模板头部

```markdown
---
doc_type: "PRD"
fragment_id: "prd-{iteration}-{module-seq}"
title: "{模块名} 详细需求"
version: "1.0.0"
version_type: "BASELINE"
author: "agent-pm"
tags: ["detailed-requirements", "{module-name}"]
status: "DRAFT"
iteration: "{iteration}"
dependencies:
  - fragment_id: "prd-{iteration}-000"
    version: "1.0.0"
c4_binding:
  level: "L1"
  system_id: "{project-system-id}"
---

# DR-{NNN}：{模块名} 详细需求 {#doc-title}

## 1. 需求追溯与验收标准 {#sec-requirements-traceability}
...
```

#### 4.3.2 修改 `SKILL.md` Phase 2

在"逐模块生成"步骤中增加：

1. **模块级 `fragment_id` 生成规则**
   - 格式：`prd-{iteration}-{module-seq}`，如 `prd-sdlc-visualizer-001`
   - `module-seq` 与 `feature-{NN}-{name}` 的 `NN` 对齐

2. **`@C4-Entity` 标签注入（可选）**
   - 在 `io-table.md` 章节中涉及的业务实体描述处，注入 `@C4-Entity:{entity_id}`
   - 在 `logic.md` 的状态机定义处，注入 `@C4-Entity-State:{entity_id}.{attr}=="{value}"`

### 4.4 detailed-design 改造

#### 4.4.1 模块设计文件模板头部

```markdown
---
doc_type: "DETAIL_DESIGN"
fragment_id: "detail-{iteration}-{module-seq}"
title: "{模块名} 详细设计"
version: "1.0.0"
version_type: "BASELINE"
author: "agent-developer"
tags: ["detailed-design", "{module-name}"]
status: "DRAFT"
iteration: "{iteration}"
dependencies:
  - fragment_id: "arch-{iteration}-001"
    version: "1.0.0"
  - fragment_id: "prd-{iteration}-{module-seq}"
    version: "1.0.0"
c4_binding:
  level: "L3"
  container_id: "{归属容器id}"
  components: []
---

# DR-{NNN} {模块名} — 模块详细设计 {#doc-title}

## 1. 模块架构与组件设计 {#sec-module-architecture}
...
```

#### 4.4.2 修改 `SKILL.md` Step 2

在"逐模块生成"步骤中增加：

1. **`container_id` 自动映射**
   - 从上游 `ARCH` 文档的 `c4_binding.containers` 中，根据模块职责匹配归属容器
   - 若匹配失败，标记为 `[ASSUMPTION]` 并告警

2. **组件定义自动收集**
   - 在生成"模块架构与组件设计"章节时，同步收集组件信息到 `c4_binding.components`
   - 每个组件必须包含：`component_id`（PascalCase）、`name`、`type`（Controller/Service/Repository/DomainService/Factory/Gateway/Config）、`technology`、`responsibilities`、`code_path`

3. **`@C4-L3-Component` 标签注入**
   - 在描述每个组件的段落首行，自动插入 `@C4-L3-Component:{component_id}`

### 4.5 interface-first-dev 改造

#### 4.5.1 接口契约 Markdown 文档（新增）

除 `openapi.yaml` 外，新增一份配套 Markdown 文档用于承载 `@C4-` 标签和详细说明：

```markdown
---
doc_type: "API_DESIGN"
fragment_id: "api-{iteration}-{module-seq}"
title: "{模块名} 接口设计"
version: "1.0.0"
version_type: "BASELINE"
author: "agent-developer"
tags: ["api", "openapi", "{module-name}"]
status: "DRAFT"
iteration: "{iteration}"
dependencies:
  - fragment_id: "detail-{iteration}-{module-seq}"
    version: "1.0.0"
c4_binding:
  level: "L3"
  component_id: "{组件名}"
  container_id: "{容器id}"
  interfaces: []
---

# API-{NNN} {模块名} 接口契约 {#doc-title}

## 1. 接口清单 {#sec-api-list}

### 1.1 创建资源 {#sec-api-create}

@C4-Interface:POST /api/v1/{resources}

{接口详细说明...}
```

#### 4.5.2 修改 `SKILL.md` Step 4

1. **`c4_binding.interfaces` 自动收集**
   - 在组装 OpenAPI 3.1 时，同步提取接口信息到 `c4_binding.interfaces`
   - 每个接口必须包含：`interface_id`（kebab-case）、`method`、`path`、`summary`、`operation_id`、`tags`、`request_schema`、`response_schema`

2. **`@C4-Interface` 标签注入**
   - 在 Markdown 文档的每个接口章节首行，插入 `@C4-Interface:{METHOD} {path}`

---

## 五、Skill 模板标准化工具包

### 5.1 YAML Front Matter 生成函数（Prompt 片段）

以下 Prompt 片段可直接嵌入各 Skill 的 `SKILL.md` 中，指导 AI 生成规范的 YAML Front Matter：

```text
【文档头部生成规则】

每个 Markdown 文件的首行必须是 YAML Front Matter，格式如下：

```
---
doc_type: "{文档类型编码}"
fragment_id: "{类型前缀}-{迭代名}-{序号}"
title: "{人类可读标题}"
version: "1.0.0"
version_type: "BASELINE"
author: "agent-{角色}"
tags: [{标签列表}]
status: "DRAFT"
iteration: "{迭代名}"
dependencies:
  - fragment_id: "{上游 fragment_id}"
    version: "{上游版本}"
c4_binding:
  {按文档类型的 c4_binding Schema 填充}
---
```

生成规则：
1. `doc_type` 必须从以下枚举中选取：PRD / DOMAIN_MODEL / ARCH / DETAIL_DESIGN / API_DESIGN / DB_DESIGN / TEST_PLAN / TEST_CASE / DEPLOYMENT / CHANGELOG
2. `fragment_id` 格式：{doc_type 小写前缀}-{iteration}-{3位序号}，如 `prd-sdlc-visualizer-000`
3. `version` 基线默认 `1.0.0`，后续 Delta 按 SemVer 递增
4. `status` 初稿为 `DRAFT`，冻结后改为 `FROZEN`
5. `dependencies` 必须列出所有直接上游文档的 fragment_id + version
6. `c4_binding` 按 C4-doc-rules.md 的 Schema 填充，缺失字段标记为 `[]` 或 `""`，不得省略整个 `c4_binding` 块
```

### 5.2 锚点ID 注入函数（Prompt 片段）

```text
【章节锚点注入规则】

每个 `##` 和 `###` 级别的标题必须附加稳定锚点ID，格式为 `## 标题 {#sec-xxx}`。

锚点ID命名规则：
1. 前缀固定为 `sec-`
2. 只允许小写字母、数字、下划线
3. 使用章节核心关键词的英文或拼音缩写
4. 同一份文档内锚点ID必须全局唯一

示例映射：
- `## 1. 执行摘要` → `## 1. 执行摘要 {#sec-executive-summary}`
- `## 2. 背景与问题` → `## 2. 背景与问题 {#sec-background}`
- `### 2.1 竞品格局` → `### 2.1 竞品格局 {#sec-competitive-landscape}`
- `## 3. 功能范围` → `## 3. 功能范围 {#sec-scope}`
- `## 4. 非功能需求` → `## 4. 非功能需求 {#sec-nfr}`
- `## 5. 用户画像` → `## 5. 用户画像 {#sec-personas}`

禁止行为：
- 不要为 `#` 一级标题（文档标题）加锚点（已由 YAML Front Matter 中的 title 覆盖）
- 不要使用章节编号作为锚点（如 `sec-1`），因为编号会随内容增删变化
- 不要使用中文作为锚点ID（如 `sec-执行摘要`）
```

### 5.3 `@C4-` 标签注入指南（Prompt 片段）

```text
【@C4- 标签注入规则】

在架构相关文档（PRD/DOMAIN_MODEL/ARCH/DETAIL_DESIGN/API_DESIGN/DB_DESIGN）中，必须在指定位置插入 @C4- 标签，建立正文与架构图谱的双向绑定。

标签清单与放置位置：

| 标签格式 | 放置位置 | 示例 |
|:---------|:---------|:-----|
| `@C4-L1-System:{system_id}` | 系统边界描述段落首行 | `@C4-L1-System:sdlc-visualizer` |
| `@C4-L1-Actor:{actor_id}` | 角色职责描述段落首行 | `@C4-L1-Actor:developer` |
| `@C4-L2-Container:{container_id}` | 容器职责描述段落首行 | `@C4-L2-Container:web-frontend` |
| `@C4-L3-Component:{component_id}` | 组件描述段落首行 | `@C4-L3-Component:ProjectService` |
| `@C4-Entity:{entity_id}` | 实体定义章节标题下方第一行 | `@C4-Entity:Project` |
| `@C4-Interface:{METHOD} {path}` | 接口契约章节标题下方第一行 | `@C4-Interface:POST /api/v1/projects` |
| `@C4-Table-Name:{table_id}` | 表结构章节标题下方第一行 | `@C4-Table-Name:projects` |

约束：
- 标签中的 ID 必须与 `c4_binding` 中定义的 ID 严格一致
- 每个被 `c4_binding` 引用的元素，必须在正文中至少出现一次对应的 @C4- 标签
```

---

## 六、Delta 版本生成机制（面向 Skill）

### 6.1 何时生成 Delta？

当前 Skill 在**迭代内修改文档**时，采用"全量覆盖"模式（直接重写文件）。按文档规范，应改为：

1. **首次生成**：输出 BASELINE（`version: "1.0.0"`，`version_type: "BASELINE"`）
2. **同一迭代内修改**：输出 DELTA（`version: "1.0.1"` 或 `"1.1.0"`，`version_type: "DELTA"`）
3. **跨迭代修改**（如 Gate 冻结后发现错误）：基于上一个 FROZEN 基线输出新的 BASELINE（`version: "2.0.0"`）

### 6.2 Skill 中实现 Delta 生成的 Prompt 指令

```text
【文档版本控制规则】

在输出文档前，按以下逻辑判断输出类型：

1. 检查 `openspec/changes/{iteration}/baseline/` 目录是否已存在同 fragment_id 的文件
   - 不存在 → 输出 BASELINE（完整文档）到 `baseline/` 和原目录
   - 存在 → 进入步骤 2

2. 检查当前变更是否"章节级增删改"
   - 是 → 输出 DELTA（增量补丁）到 `delta/`，同时在原目录输出编译后的完整视图
   - 否（仅文案微调）→ 在原目录直接更新文件，版本号 PATCH+1

Delta 文件格式要求：
- YAML Front Matter 中 `version_type: "DELTA"`，`base_version` 指向上一版本
- 正文中使用 `[ADD]` / `[MODIFY]` / `[DELETE]` / `[PATCH]` 操作指令
- 示例见 docs/doc-management-design.md 第 4.4 节
```

### 6.3 简化版 Delta（过渡期）

在编译器未完全实现前，允许 Skill 使用**简化版 Delta**——即在正文中用"修改记录"描述变更，但元数据使用 YAML Front Matter：

```markdown
---
fragment_id: "prd-sdlc-visualizer-000"
version: "1.1.0"
version_type: "DELTA"
base_version: "1.0.0"
change_type: "MODIFY"
change_summary: "增加复杂度路由需求"
---

# 00 - 需求总览 {#doc-title}

> 版本：1.1.0（基于 1.0.0 基线增量修改）

## 修改记录 {#sec-changelog}

| 版本 | 日期 | 修改人 | 修改内容 | 影响面 |
|------|------|--------|----------|--------|
| 1.1.0 | 2026-06-02 | agent-pm | 增加 §3.5 复杂度路由需求 | 下游：high-level-design |

---

## 1. 执行摘要 {#sec-executive-summary}
...

## 3. 功能范围 {#sec-scope}
...

### 3.5 复杂度路由 {#sec-complexity-router}
> 【新增】基于五维度规模评估的 Trivial/Light/Standard/Deep 路径推荐
...
```

这种格式的优势：
- 机器可读（YAML Front Matter）
- 人类可读（修改记录表格）
- 不依赖编译器即可理解变更内容
- 未来可自动转换为标准 Delta 格式

---

## 七、验证与门禁

### 7.1 Skill 自检检查点

在各 Skill 的 `SKILL.md` 末尾增加"输出前格式自检"步骤：

```text
【输出前格式自检清单】

在将文档写入文件系统前，必须完成以下检查：

□ YAML Front Matter 检查
  - 文件首行是否为 `---`？
  - `doc_type` 是否在合法枚举中？
  - `fragment_id` 是否符合格式规范？
  - `version` 是否为有效 SemVer？
  - `status` 是否为 DRAFT/REVIEW/FROZEN/DEPRECATED 之一？
  - 架构类文档是否包含 `c4_binding`？

□ 锚点ID 检查
  - 所有 `##` / `###` 标题是否包含 `{#sec-xxx}` 锚点？
  - 同文档内锚点ID是否有重复？
  - 锚点ID是否只含小写字母、数字、下划线？

□ C4 标签检查（仅架构类文档）
  - `c4_binding` 中定义的每个元素，正文中是否有对应的 @C4- 标签？
  - @C4- 标签格式是否符合规范？

□ 依赖声明检查
  - `dependencies` 中的上游文档是否真实存在？
  - `dependencies` 中的版本号是否与上游文档一致？

□ 交叉引用检查
  - 正文中引用的其他文档是否存在于 `dependencies` 中？

检查通过后方可写入文件。任一检查项失败，标记为 🔴 阻塞，列出修复清单。
```

### 7.2 config.yaml 扩展

在 `openspec/config.yaml` 的各阶段 `artifact_specs` 中增加格式校验规则：

```yaml
phases:
  high-level-requirements:
    gate_to_next:
      artifact:
        check:
          action: required_files
          path: openspec/changes/{change}/high-level-requirements/
          files:
            - 00-requirements-overview.md
            - 01-requirements-list.md
            - 02-functional-requirements.md
          # 新增：格式校验
          format_check:
            - yaml_front_matter_required: true
            - doc_type_must_be: "PRD"
            - c4_binding_level_must_be: "L1"
            - anchor_id_required: true
          action: confirm_integrity
```

---

## 八、演进路线图

### Phase 1：模板改造（1 周）

- [ ] 修改 `prd-generation/references/system-outline-template.md`：增加 YAML Front Matter + 锚点ID 模板
- [ ] 修改 `high-level-design/SKILL.md`：增加 `c4_binding` 生成步骤
- [ ] 修改 `detailed-requirements/SKILL.md`：增加模块级 YAML Front Matter 生成
- [ ] 修改 `detailed-design/SKILL.md`：增加组件级 `c4_binding` 生成
- [ ] 修改 `interface-first-dev/SKILL.md`：增加接口契约 Markdown 文档生成
- [ ] 各 Skill 新增"输出前格式自检"步骤

### Phase 2： Pilot 验证（1 周）

- [ ] 选一个真实变更（如 `sdlc-visualizer` 的下一个迭代），用改造后的 Skill 生成全套文档
- [ ] 验证 YAML Front Matter 可被标准解析器解析
- [ ] 验证锚点ID 全局唯一性
- [ ] 验证 `c4_binding` 与 `@C4-` 标签的一致性
- [ ] 收集 AI Agent 执行过程中的格式错误，迭代模板

### Phase 3：存量迁移（1 周）

- [ ] 运行 `migrate_legacy_to_baseline.py`，将历史文档转换为规范 Baseline 格式
- [ ] 为历史文档自动生成 `fragment_id` 和锚点ID
- [ ] 历史文档的 `c4_binding` 采用 LLM 辅助发现 + 人工确认模式

### Phase 4：Delta 机制上线（2 周）

- [ ] 实现文档编译器 CLI（`docforge compile`）
- [ ] 在 Skill 中接入 Delta 生成逻辑（基线判断 → Delta 输出 → 编译合并）
- [ ] 前端文档浏览器支持版本切换和 Diff 视图

---

## 九、常见问题

### Q1：YAML Front Matter 对 AI 来说是否增加了认知负担？

**A**：不会。YAML Front Matter 是结构化数据，AI 生成结构化数据的能力远强于生成自由文本。实际上，将元信息从自由文本改为 YAML，反而减少了 AI 的"格式决策"负担——因为字段和格式是固定的。

### Q2：现有 41 个 Skill 全部要改吗？

**A**：不需要。只需要改造**直接产出过程文档**的 5~6 个核心 Skill（prd-generation、high-level-design、detailed-requirements、detailed-design、interface-first-dev、documentation）。编码/测试/审查类 Skill 不直接产出文档，但可能需要在生成的代码注释中支持 `@C4-` 标签（P2 扩展）。

### Q3：C4 绑定对非架构类文档（如测试计划）是否强制？

**A**：不强制。`TEST_PLAN` / `TEST_CASE` / `DEPLOYMENT` / `CHANGELOG` / `BUG_REPORT` 等类型无需 `c4_binding`，只需基础 YAML Front Matter（`doc_type`、`fragment_id`、`version` 等）。

### Q4：如果 AI 生成的锚点ID 不够规范怎么办？

**A**：在"输出前格式自检"步骤中增加锚点ID 校验规则，不通过则阻塞输出。同时，在模板中提供"推荐锚点映射表"（如 `sec-executive-summary`、`sec-background` 等常见锚点的标准命名），降低 AI 的命名自由度。

### Q5：文档规范是否会导致 Skill 输出文件体积变大？

**A**：YAML Front Matter 通常 < 50 行，锚点ID 每个标题仅增加约 20 字符，对文件体积的影响可忽略不计。但带来的收益（机器可读、版本追溯、影响面分析）是巨大的。

---

## 十、总结

**文档规范通过 Skill 模板落地，是成本最低、效果最可控的路径。**

具体做法：

1. **改模板**：将各 Skill 的 `references/system-outline-template.md` 中的自由文本头部，替换为标准 YAML Front Matter
2. **加锚点**：在模板中为每个章节标题附加 `{#sec-xxx}` 锚点ID
3. **绑 C4**：在模板中预留 `c4_binding` 块，在 Skill 执行步骤中指导 AI 从内容中提取架构信息填充
4. **注入标签**：在 Skill 的章节生成指令中，要求 AI 在指定位置插入 `@C4-` 标签
5. **设门禁**：在 Skill 的"输出前自检"步骤中增加格式校验，不通过禁止保存

通过这套改造，AI Agent 生成的每份文档都将成为"架构感知的、可版本化的、可编译的"规范文档，为后续的文档编译器、影响面分析、AI 上下文精准组装奠定数据基础。
