---
name: detailed-design
description: 当用户提到'详细设计'、'detailed-design'、'按模块输出技术细节'、'生成DDL'、'接口定义'、'状态机细化'、'页面设计'、'UI设计'或基于已冻结概要设计和详细需求需要进入模块级详细设计阶段时触发。逐模块输出 module-design.md（聚合 6 个原子章节），衔接概要架构与编码实现。
---

# Detailed Design（详细设计）

按模块输出详细设计文档，将概要设计的架构约束落地为可编码的技术细节。

## 适用场景

- `high-level-design` 评审通过（Gate 2 已签字）且 `detailed-requirements` 评审通过（Gate 2.5 已签字）
- 需要基于概要设计的架构约束，为每个功能模块生成可编码的技术细节
- 需要自动生成 DDL、OpenAPI/Swagger 接口定义、模块内部状态机 Mermaid 图
- 需要定义前端页面规格、用户旅程与页面-接口映射，支撑 Sketch 旅程画布与 OpenUI 高保真原型

## 核心职责

1. **逐模块独立输出**：基于 `detailed-design/feature-XX-{模块名}/` 目录，为每个模块生成 1 个标准文件 `module-design.md`
2. **架构约束继承**：概要设计中的技术选型、安全策略、部署约束必须向下传导
3. **功能点映射**：详细需求中的每个功能点必须有对应的实现方案
4. **自动化生成**：自动生成 DDL 语句、索引建议、OpenAPI 格式接口、状态机 Mermaid 图
5. **模块间矛盾检测**：检测两个模块对同一数据表字段定义冲突、接口不兼容、页面拓扑冲突等问题
6. **前端页面规格定义**：输出页面拓扑、用户旅程、页面-接口映射、页面状态机，为 Sketch 旅程画布和 OpenUI 高保真原型提供结构化输入

## 前置依赖

| 上游 Skill | 产出物 | 用途 | 是否必需 |
|---|---|---|---|
| `high-level-design` | `high-level-design/01-05.md` | 架构约束、技术选型、全局状态机 | **必须** |
| `detailed-requirements` | `feature-*/module-requirements.md` | 功能规格、io-table、logic、prototype | **必须** |
| `human` | `human-decisions.md` | Gate 2 与 Gate 2.5 签字状态 | **必须** |
| `competitive-analysis` | `competitive-analysis.md` | 技术选型参考 | 建议 |

> **硬性阻断**：Gate 2 或 Gate 2.5 未签字时，禁止启动详细设计。

## 输入数据

| 输入来源 | 具体内容 |
|----------|----------|
| 概要设计 | `high-level-design/01-05.md`：系统架构、技术选型、数据架构、部署架构等 6 个主题文件 |
| 详细需求 | `detailed-requirements/feature-*/module-requirements.md`：功能规格与验收标准、输入输出字段、业务逻辑、交互规格 |
| 前端设计规范 | `openspec/config.yaml`：`frontend.framework`、`design_system`、`responsive_breakpoints`、`design_tokens` | 页面渲染约束与组件选型 |
| 配置 | `openspec/config.yaml`：`high-level-design.required_sections` | 输出模板约束 |

## 处理逻辑

### Step 1：约束加载与模块识别

1. 读取 `openspec/config.yaml` 中 `high-level-design.required_sections` 作为输出模板约束
2. 自动解析 `high-level-requirements/02-functional-requirements.md` 或扫描 `detailed-requirements/feature-*/` 目录获取模块清单
3. 读取 `high-level-design/01-05.md` 提取架构约束：技术栈、安全策略、性能指标、全局状态机
4. **读取设计系统上下文**：加载 `openspec/config.yaml` 中 `frontend` 区块（框架、组件库、设计系统、断点、token 路径）；若存在 `.better-web-ui.md` 或 `design-system/tokens.json` 一并加载。若无，使用框架默认值并标注 `[ASSUMPTION]`

> **Constitution 约束传导**：将概要设计中的技术栈、安全约束、CWE 映射视为不可偏离的"架构 DNA"。详细设计阶段任何偏离均视为 BLOCKER。

### Step 2：逐模块生成（串行）

对每个 `feature-XX-{模块名}` 独立生成 1 个文件 `module-design.md`。

每个 `module-design.md` 文件头部必须包含以下 YAML Front Matter：

```yaml
---
doc_type: "DETAIL_DESIGN"
fragment_id: "detail-{iteration}-{module-seq}"
title: "{模块名} 详细设计"
version: "1.0.0"
version_type: "BASELINE"
base_version: ""
change_type: ""
change_summary: ""
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
```

**生成规则**：
- `container_id` 自动映射：从上游 `ARCH` 文档的 `c4_binding.containers` 中，根据模块职责匹配归属容器；若匹配失败，标记为 `[ASSUMPTION]` 并告警
- 组件定义自动收集：在生成"模块架构与组件设计"章节时，同步收集组件信息到 `c4_binding.components`；每个组件必须包含：`component_id`（PascalCase）、`name`、`type`（Controller/Service/Repository/DomainService/Factory/Gateway/Config/Entity/ValueObject/Mapper/Middleware/EventHandler）、`technology`、`responsibilities`、`code_path`
- **C4 标签后置提取**：正文保持自然流畅，禁止在组件描述段落首行插入 `@C4-L3-Component` 标签。在文档末尾统一附加《C4 标签映射表》，由 AI 自动从正文中提取并填充。用户只需在关键组件名词首次出现时加粗即可。

文件内部包含 6 个原子章节：

#### ## 1. 模块架构与组件设计 {#sec-module-architecture}

- 后端分层（Controller / Service / Repository / Domain）及职责边界
- 类/函数设计（签名、职责、依赖关系），核心算法伪代码
- 模块依赖图（Mermaid `flowchart`）
- **前端组件架构**：Page → Widget/Section → Base 分层，与后端 Controller/Service/Repository 对齐
- **路由设计**：前端路由表，与页面层级对应，明确路由参数与接口路径映射
- 公共组件/基类引用路径（禁止在模块内重复定义）
- 代码风格必须与项目规范一致（Python `python-google-style` / Java `java-alibaba-style`）

#### ## 2. 接口定义 {#sec-api-definition}

- RESTful / gRPC / MCP / 消息队列端点清单（方法、路径、Content-Type）
- 请求/响应字段表（字段名、类型、必填、约束、示例）
- 错误码定义（HTTP 状态码 + 业务错误码 + 错误消息模板）
- 权限与鉴权（RBAC 角色、OAuth2 scope）、幂等策略与限流配置
- **页面消费接口**：每个接口标注消费页面、调用时机（mount/click/poll/websocket）
- 输出标准 OpenAPI 3.1 YAML 片段，确保 `interface-first-dev` 零摩擦衔接
- 公共接口引用路径（模块级只定义本模块对外暴露的接口）

#### ## 3. 数据表结构 {#sec-database-schema}

- **本模块独占表**：DDL（CREATE TABLE / INDEX / CONSTRAINT）、字段类型映射、索引策略、缓存 Key 设计
- **公共表引用**：列出依赖的 `shared/db-schema.md` 中的表（表名、引用路径、使用方式、扩展字段）
- **前端数据模型**：标注前端 Store / State 中对应的数据结构（Redux Slice shape、Pinia Store state）
- 禁止重复定义公共表、禁止硬编码连接串/密码

#### ## 4. 模块状态机 {#sec-module-state-machine}

- 业务状态机：将概要设计全局状态机拆解到模块内部，Mermaid `stateDiagram-v2`
- 每个状态转换标注：触发条件、校验规则、异常分支
- **页面状态机**：描述页面级交互状态（如 `loading → empty → loaded → editing → submitting → success/error`），与业务状态机区分
- 与全局状态机的映射关系

#### ## 5. 测试策略 {#sec-test-strategy}

- 单元测试用例（Given/When/Then 格式），与详细需求 AC 的追溯关系
- 集成测试场景（模块间交互、外部服务 Mock 策略）
- 边界条件覆盖（空值、越界、并发、超时）
- **前端测试策略**：组件级单测（渲染、交互、状态变更）、E2E 用户旅程场景
- 测试数据构造与清理策略

#### 运行时行为验证策略（V3.2 新增）

静态测试策略（单元测试、集成测试）之外，必须为含 I/O 边界或状态变更的模块规划运行时行为验证：

**5.0 探测点扫描规则（V3.2 新增）**

为每个模块扫描代码，标记以下运行时探测点，输出到设计文档附录：

| 探测点类型 | 标记规则 | 示例 | 风险等级 |
|------------|----------|------|----------|
| **外部依赖** | 函数体内调用非纯函数 | `db.query()`, `http.post()`, `fs.readFile()`, `redis.get()` | 高 |
| **内部状态** | 修改全局/静态/单例变量 | `global.config`, `singleton.state`, `class static field` | 中 |
| **副作用** | 产生不可逆外部影响 | `sendEmail()`, `log.audit()`, `metrics.increment()`, `event.emit()` | 高 |
| **资源操作** | 申请/释放系统资源 | `db.beginTransaction()`, `lock.acquire()`, `file.open()` | 高 |

探测点清单格式：
```json
{
  "module": "payment_service",
  "probe_points": [
    {"line": 42, "type": "外部依赖", "target": "db.query()", "risk": "高"},
    {"line": 55, "type": "副作用", "target": "sendEmail()", "risk": "高"},
    {"line": 60, "type": "资源操作", "target": "db.beginTransaction()", "risk": "高"}
  ]
}
```

**5.1 行为探测矩阵规划**
为每个含副作用的模块定义 4 类探测的测试场景：

| 探测类型 | 测试场景设计要点 | 断言重点 |
|----------|-----------------|----------|
| Baseline | 正常输入下的端到端流程 | 返回值正确、DB/缓存/文件状态符合预期 |
| Edge | 空值、极大值、特殊字符、零值、并发输入 | 不崩溃、无副作用泄漏、返回有意义错误 |
| Fault | 网络超时、DB 断开、下游 503、磁盘满 | 事务回滚、资源释放、降级状态、无脏数据 |
| Drift | 同一输入重复执行 | 输出/副作用完全一致（幂等性） |

**5.2 属性测试规划（Property-Based Testing）**
识别适合属性测试的模块，定义属性公式：
- Roundtrip：`decode(encode(x)) == x`
- Idempotence：`f(f(x)) == f(x)`
- Invariant：状态变换前后不变量保持
- Oracle：`new_impl(x) == reference_impl(x)`

规划属性测试的随机数据生成策略（如 `hypothesis`、`fast-check`、`jqwik`）。

**5.3 覆盖率盲区反向驱动规划**
- 预估静态测试可能无法触发的分支（异常处理、并发路径、异步回调）
- 规划针对性输入数据和故障注入场景，用于运行时填补盲区
- 明确覆盖率门控后的盲区填补责任人（开发 / 测试）

**5.4 故障注入清单**
| 故障类型 | 注入方式 | 验证目标 | 适用模块 |
|----------|----------|----------|----------|
| 网络超时 | toxiproxy / 模拟延迟 | 降级行为、重试策略 | 支付、通知 |
| DB 断开 | 模拟连接异常 | 事务回滚、无脏数据 | 订单、库存 |
| 下游 503 | Mock 返回 503 | 熔断、缓存命中 | 推荐、搜索 |
| 磁盘满 | 模拟磁盘空间不足 | 优雅拒绝、日志不丢 | 文件上传 |

**5.5 运行时测试目录结构规范（V3.2 新增）**

模块级运行时测试统一存放于 `tests/runtime/`，与静态单元测试分离：

```
tests/
├── unit/                          # 静态单元测试（由 TDD / unit-test 生成）
│   └── {module}/
│       ├── test_*.py
│       └── conftest.py
└── runtime/                       # 运行时行为验证（由运行时测试策略驱动）
    ├── probes/
    │   ├── test_{module}_baseline.py    # Baseline + Edge 探测
    │   ├── test_{module}_fault.py       # Fault 注入探测
    │   └── test_{module}_drift.py       # Drift / 幂等性探测
    ├── properties/
    │   └── test_{module}_properties.py  # Property-Based Testing
    └── differential/
        └── test_{module}_diff.py        # 差分验证（重构/优化对比）
```

设计阶段需明确：
- 哪些探测点需要 Baseline 探测？
- 哪些探测点需要 Fault 注入？
- 哪些模块适合 Property-Based Testing？
- 是否存在新旧实现对比需求（差分验证）？

#### ## 6. 页面设计与用户旅程 {#sec-page-design}

#### ### 6.1 页面拓扑图 {#sec-page-topology}

节点 `Pg_` 前缀，边标签 `"触发元素 / nav_type"`，nav_type ∈ {push, modal, drawer, replace, tab}；每个节点标注 `page_level`（entry/sub/modal/drawer）

#### ### 6.2 用户旅程场景 {#sec-user-journeys}

按业务闭环组织，标注起点(entry)、终点(success/fail)、关键决策点、预期耗时

#### ### 6.3 页面规格表 {#sec-page-specs}

每个页面按 `references/page-spec-template.md` 标准表格输出，含 page_id、layout_type、layout_pattern、route_path、fields、actions、empty_state、loading_state、error_state、responsive、a11y、motion、design_tokens

#### ### 6.4 页面-接口映射表 {#sec-page-api-mapping}

每个页面消费接口清单，request/response 字段与页面展示字段一一对应

#### ### 6.5 页面状态机 {#sec-page-state-machine}

页面级交互状态流转，每个转换标注触发条件与 UI 反馈

#### ### 6.6 前端组件架构 {#sec-frontend-components}

组件复用矩阵（跨页面复用组件列出引用路径）、状态管理划分（Global / URL / Local / Server State）

> **参考文件加载**：生成第 1-5 章时按需加载 `references/backend-design-guide.md`；生成第 6 章时必须加载 `references/frontend-design-guide.md` 和 `references/page-spec-template.md`。

### Step 3：架构视图生成

为每个模块自动生成：
- 模块内类图/组件图（Mermaid `classDiagram`）
- 核心流程时序图（Mermaid `sequenceDiagram`）
- ER 子图（仅本模块涉及的实体关系）
- 页面拓扑图（Mermaid `flowchart`，含 `page_level` 与跳转类型标注）

> 所有图表必须遵循 `references/mermaid-style-guide.md` 的工程化规范。图表必须与文本描述严格一致，禁止矛盾。

### Step 4：模块间矛盾检测

所有模块生成完毕后执行 Cross-Module Design Audit：

- 同名字段在不同模块的类型/约束是否一致
- 接口 request/response 中同一数据结构字段是否兼容
- 状态枚举值是否冲突；对同一数据表的写权限是否冲突
- **页面拓扑矛盾**：不同模块对同一页面的 `page_level` 定义是否冲突
- **旅程断层**：跨模块的页面跳转是否在接口和路由层面有支撑
- 模块与 `shared/` 公共内容的一致性（重复定义 = Error）

Error 数量 > 0 时阻塞进入下游阶段，返回修复。

### Step 5：输出后质量门控

对生成的 module-design.md 执行"能否不猜就编码"审查：

**通用检查**：
- 对每个规格项判定 **SPECIFIED / VAGUE / MISSING**
- 检测模糊语言："标准方案"、"按需"、"TBD"、"as needed"
- 检测 magic number、未标注单位的数值
- 接口必须包含完整的 request/response/error 格式
- 数据库设计必须包含完整的 DDL + 索引 + 约束

**前端设计质量检查**：
- 每个页面是否有明确的 `layout_type` 和 `layout_pattern`（MISSING = BLOCKER）
- 页面拓扑图边标签是否包含 `触发元素 / nav_type`（MISSING = BLOCKER）
- 页面规格表是否包含 `empty_state`、`loading_state`、`error_state`（MISSING = WARNING）
- 是否使用设计系统 token（而非 magic number）定义色彩、间距、字体（VAGUE = WARNING）
- 是否存在 a11y 字段（至少 keyboard 导航和 ARIA 角色）（MISSING = WARNING）
- 是否存在响应式断点行为描述（MISSING = WARNING）

**判定规则**：
- MISSING → 🔴 BLOCKER
- VAGUE 数量 ≥ 3 → 🟡 WARNING
- 所有核心接口 SPECIFIED + 页面拓扑图边标签完整 → ✅ 通过

### Step 6：设计质量自评

触发 `/design-assessment` 等效自检：
- 评分维度：完备性、清晰度、准确性、可测试性、可扩展性、**前端可落地性**
- 阻塞维度（完备性、清晰度、准确性）< 3 分时暂停并报告缺口
- 无 CRITICAL 或 HIGH 发现项方可进入下游

### Step 7：保存与触发下游

按模块保存到 `openspec/changes/{变更名}/detailed-design/feature-XX-{模块名}/`

每个模块只生成 1 个文件：
- **`module-design.md`**：合并 6 个原子章节（design + api-spec + db-schema + state-machine + test-plan + page-design）

全局文件保存到 `openspec/changes/{变更名}/detailed-design/` 根目录：
- **`_design-index.md`**：全局模块索引、状态、版本、追溯关系、变更历史
- **`shared/` 目录**：跨模块公共技术能力
  - `_index.md`、 `design.md`、`api-spec.md`、`db-schema.md`、**`page-design.md`**（公共页面：全局搜索、个人中心、错误页、布局框架）

> **合并边界**：`module-design.md` 内的 6 个原子章节红线独立生效，禁止在章节间混入不相关内容。

全部模块保存后：
1. 调用 `self-check` skill 执行阶段 4 详细设计自查
2. 调用 `progress-tracker` 更新阶段 4 为"已完成"
3. 提示用户：
   - 先执行 `writing-plans` 生成实现计划（plan.md），再由 `writing-plans` 引导进入 `task-breakdown`
   - 同时可并行启动 `interface-first-dev`、`sketch` 或 `open-ui`
   - **顺序纪律**：`detailed-design` → `writing-plans` → `task-breakdown`

## 执行模式

根据用户意图和已有上下文，选择以下模式之一：

| 模式 | 触发条件 | 生成范围 | 说明 |
|---|---|---|---|
| **default** | 用户仅说"详细设计"或"进入阶段4" | 完整的 module-design.md（6个章节） | 默认模式，一次产出完整设计 |
| **backend-only** | 用户明确提及"后端设计"、"API设计"、"数据库设计" | 仅第1/2/3/4/5章 | 第6章标注 `[DEFERRED: 待前端详细设计补充]` |
| **frontend-only** | 用户明确提及"页面设计"、"UI设计"、"原型设计"，且 module-design.md 已存在 | 仅第6章 + 已有章节对齐校验 | 假设第1/2/3章已由上游提供，只做页面-接口对齐校验 |

> frontend-only 模式禁止在没有已有后端设计的情况下独立执行，避免产生无接口映射的孤立页面设计。

## 参考文件加载规则（渐进式披露）

| 生成阶段 | 加载的参考文件 | 用途 |
|---|---|---|
| 第1/2/3/5章 | `references/backend-design-guide.md` | 后端分层、DDL、OpenAPI、测试模板 |
| 第6章 | `references/frontend-design-guide.md` | 布局模式库、反模式、a11y、动效、响应式 |
| 第6章 | `references/page-spec-template.md` | PageSpec 标准表格模板 |
| Step 3 生成图表 | `references/mermaid-style-guide.md` | Mermaid 语法规范与检查清单 |

- 禁止将参考文件内容直接复制到 SKILL.md 正文
- 参考文件仅在实际生成对应章节时加载，避免上下文膨胀

## 下游消费契约

| 下游 Skill | 消费章节 | 解析方式 | 关键字段 |
|---|---|---|---|
| `sketch` | 6.1 页面拓扑图 + 6.3 页面规格表 | Mermaid flowchart 节点/边 + PageSpec 表格 | `page_id`, `page_level`, `layout_type`, `route_path` |
| `open-ui` | 6.3 页面规格表 + 6.4 页面-接口映射 + 2. 接口定义 | PageSpec 表格 + 接口字段表 | `fields`, `actions`, `design_tokens`, `responsive`, `motion` |
| `interface-first-dev` | 2. 接口定义 | OpenAPI YAML 代码块 | 完整 OpenAPI 3.1 片段 |
| `writing-plans` | 1. 模块架构 + 2. 接口定义 + 6. 页面设计 | 组件分层 + 接口清单 + 页面拓扑 | Page/Widget/Base 清单、路由表 |
| `task-breakdown` | 1. 模块架构 + 2. 接口定义 + 4. 状态机 + 6. 页面设计 | 组件、接口、状态、页面 | 开发任务拆解依据 |
| `executing-plans` | 完整 module-design.md | 按章节消费 | 编码与 TDD 依据 |
| `unit-test` | 5. 测试策略 | 测试用例表格 | 补全单测与覆盖率验证 |

## 增量更新支持

当需求发生变更时，支持局部重生成：
1. 对比变更前后的 `detailed-requirements/feature-*/module-requirements.md`，识别受影响模块
2. 仅重新生成受影响模块的 module-design.md
3. 未受影响模块保持原设计冻结状态
4. 重生成后重新执行 Cross-Module Audit 和质量门控
5. **页面拓扑变更时**：若页面层级（`page_level`）或跳转关系变更，触发 `sketch` 和 `open-ui` 的增量重生成

## Gotchas

- **Gate 阻断**：Gate 2 或 Gate 2.5 未签字时绝对禁止启动，不可跳过
- **串行生成**：逐个模块输出，防止上下文丢失和编号混乱
- **架构约束不可偏离**：技术栈、安全策略必须与概要设计一致，擅自变更 = BLOCKER
- **字段级细节拦截**：概要设计只定义影响 ≥2 模块的决策，详细设计只定义模块内部细节，二者不可越位
- **状态机映射**：模块状态机必须与概要设计全局状态机兼容，发现冲突时标记 BLOCKER
- **DDL 必须与选型一致**：若概要设计选定 MySQL，禁止生成 PostgreSQL 专属语法
- **接口 URI 动词红线**：禁止 `/getOrder`、`/createUser` 等动词 URI，必须使用资源导向路径
- **缓存 Key 禁止硬编码环境信息**：如域名、端口号不得写入缓存 Key 模板
- **测试计划必须追溯 AC**：每个测试用例必须能追溯到详细需求中的至少一个验收标准
- **模糊语言零容忍**：发现"TBD"、"standard approach"、"as needed"等模糊表达，标记 VAGUE 并要求具体化
- **模块间矛盾不可静默忽略**：Cross-Module Audit 发现 Error 时必须返回修复，不可跳过
- **OpenAPI 片段必须可解析**：YAML 片段语法必须正确，确保 `interface-first-dev` 可直接消费
- **禁止在详细设计阶段做架构变更**：若发现概要设计有缺陷，应暂停并反馈用户走架构变更流程
- **设计锁定原则**：详细设计评审通过后冻结，后续变更需重新执行 `detailed-design` 并走变更流程
- **图表一致性**：Mermaid 图表必须与文本描述严格一致，禁止矛盾
- **页面层级必须明确**：每个页面必须标注 `page_level`（entry/sub/modal/drawer），禁止模糊
- **跳转类型必须标注**：push/modal/drawer/replace/tab 必须明确，禁止用"跳转"泛指
- **页面-接口必须对齐**：接口字段必须与页面展示字段一一对应，禁止脱节
- **旅程场景必须闭环**：每个用户旅程必须有明确的起点（entry）和终点（成功/失败）
- **公共页面必须收敛到 shared/page-design.md**：全局搜索、个人中心、错误页等 ≥2 模块共用的页面，禁止在模块级重复定义
- **前端设计反模式**：禁止无意义紫色渐变、卡片嵌套卡片、纯黑文本/背景、无 empty/error 状态定义（详见 `references/frontend-design-guide.md` 第2章）

## 输出前格式自检

全部模块文件写入前，执行以下检查：
1. YAML Front Matter 可被解析，`doc_type` = "DETAIL_DESIGN"，`c4_binding.level` = "L3"
2. 所有 `##` / `###` 标题含 `{#sec-xxx}` 锚点
3. `c4_binding.container_id` 在上游 ARCH 文档中存在
4. 文档末尾包含《C4 标签映射表》，且映射表中每个组件在 `c4_binding.components` 中有对应定义
5. `dependencies` 包含上游 ARCH 和 PRD 的 fragment_id + version

任一检查失败，标记 🔴 阻塞。详细清单见 `references/output-checklist.md`。
