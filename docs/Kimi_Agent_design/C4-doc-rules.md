# C4 绑定文档模板规则集（Template Rulebook）

> **版本**：v1.0  
> **状态**：DRAFT  
> **适用**：DocForge 平台 + SDLC Visualizer C4 绑定系统  
> **原则**：模板即接口，缺失即阻断，取值即语义

---

## 1. 文档类型准入与绑定策略

### 1.1 文档类型矩阵

表格

|DocForge 类型编码|中文名称|必须含 `c4_binding`|强制绑定层级|可选绑定层级|说明|
|:--|:--|:--|:--|:--|:--|
|`PRD`|产品需求文档|**是**|L1|—|仅当包含系统边界/外部系统/用户角色时才强制|
|`DOMAIN_MODEL`|领域模型文档|**是**|L2|—|必须含领域实体定义|
|`ARCH`|架构设计文档|**是**|L2|—|必须含容器划分与技术栈|
|`DETAIL_DESIGN`|详细设计文档|**是**|L3|L2|必须含组件划分；可补充容器级技术细节|
|`API_DESIGN`|接口设计文档|**是**|L3|—|必须含接口契约与组件归属|
|`DB_DESIGN`|数据库设计文档|**是**|L2|—|必须含数据存储容器映射|
|`TEST_PLAN`|测试计划|**否**|—|—|不进入 C4 绑定流程|
|`TEST_CASE`|测试用例|**否**|—|—|不进入 C4 绑定流程|
|`DEPLOYMENT`|部署文档|**否**|—|—|不进入 C4 绑定流程|
|`BUG_REPORT`|缺陷报告|**否**|—|—|不进入 C4 绑定流程|
|`CHANGELOG`|变更日志|**否**|—|—|不进入 C4 绑定流程|

### 1.2 准入规则（Gate 规则）

yaml

```yaml
rule_id: TPL-001
name: "c4_binding 强制存在性校验"
applies_to: [PRD, DOMAIN_MODEL, ARCH, DETAIL_DESIGN, API_DESIGN, DB_DESIGN]
severity: BLOCKER
logic: |
  IF doc_type IN [PRD, DOMAIN_MODEL, ARCH, DETAIL_DESIGN, API_DESIGN, DB_DESIGN]
    AND YAML Front Matter 中缺失 `c4_binding` 字段
  THEN 拒绝入库，返回错误码 40001
  ELSE 继续后续校验
```

yaml

```yaml
rule_id: TPL-002
name: "c4_binding.level 与 doc_type 一致性校验"
severity: BLOCKER
logic: |
  PRD       → c4_binding.level MUST BE "L1"
  DOMAIN_MODEL → c4_binding.level MUST BE "L2"
  ARCH      → c4_binding.level MUST BE "L2"
  DETAIL_DESIGN → c4_binding.level MUST BE "L3" (可含 L2 补充)
  API_DESIGN → c4_binding.level MUST BE "L3"
  DB_DESIGN → c4_binding.level MUST BE "L2"
  不匹配则拒绝入库，返回错误码 40002
```

---

## 2. 文档级：YAML Front Matter Schema

### 2.1 公共字段（所有文档通用）

表格

|字段|类型|必填|取值规则|示例|
|:--|:--|:--|:--|:--|
|`doc_type`|ENUM|是|必须为 `PRD`/`DOMAIN_MODEL`/`ARCH`/`DETAIL_DESIGN`/`API_DESIGN`/`DB_DESIGN`/`TEST_PLAN`/`TEST_CASE`/`DEPLOYMENT`/`BUG_REPORT`/`CHANGELOG`|`PRD`|
|`fragment_id`|STRING|是|格式：`{type}-{module}-{seq}`，全平台唯一，小写，连字符分隔|`prd-financing-001`|
|`title`|STRING|是|1-100 字符，人类可读|`供应链融资平台需求总览`|
|`version`|SEMVER|是|语义化版本 `MAJOR.MINOR.PATCH`，基线默认 `1.0.0`|`1.0.0`|
|`version_type`|ENUM|是|`BASELINE` 或 `DELTA`|`BASELINE`|
|`base_version`|SEMVER|条件|当 `version_type = DELTA` 时必填，指向基线或上游 Delta|`1.0.0`|
|`change_type`|ENUM|条件|当 `version_type = DELTA` 时必填：`ADD`/`MODIFY`/`DELETE`/`PATCH`|`MODIFY`|
|`change_summary`|STRING|条件|当 `version_type = DELTA` 时必填，50-200 字符|`增加微信扫码登录接口`|
|`author`|STRING|是|作者标识，AI Agent 填 `agent-{role}`，人工填用户名|`agent-architect`|
|`tags`|STRING[]|否|业务标签，用于检索|`[auth, login, wechat]`|
|`c4_binding`|OBJECT|条件|架构相关文档必填，见下节各类型 Schema|见下|

### 2.2 PRD 专用 `c4_binding` Schema

yaml

```yaml
c4_binding:
  level: "L1"                          # 固定值，强制
  system_id: "financing-platform"     # 系统标识，全局唯一，kebab-case
  system_name: "供应链融资平台"         # 系统名称，人类可读
  external_systems:                    # 外部系统列表，可选（无外部依赖可为空数组）
    - id: "core-erp"                  # 外部系统标识，kebab-case，全局唯一
      name: "核心企业ERP"              # 外部系统名称
      relation: "提供应收账款数据"      # 与本系统的关系描述
      interface_type: "REST"          # 可选：交互协议类型
    - id: "bank-gateway"
      name: "银行网关"
      relation: "放款与回款通道"
      interface_type: "HTTPS"
  actors:                              # 用户角色列表，可选
    - id: "supplier"                  # 角色标识，kebab-case
      name: "供应商"                   # 角色名称
      role_type: "PRIMARY"             # 枚举：PRIMARY / SECONDARY / SYSTEM
      description: "融资申请方"         # 角色描述
    - id: "admin"
      name: "平台管理员"
      role_type: "SECONDARY"
      description: "审批与配置管理"
```

**取值逻辑与约束**：

- `system_id`：从项目名称自动派生（`{project}-system`），或人工指定。必须全局唯一，作为 C4 L1 的根节点 ID。
    
- `external_systems.id`：禁止与 `system_id` 重复。若存在，则必须在正文中通过 `@C4-L1-System:{id}` 至少引用一次。
    
- `actors.role_type`：`PRIMARY` 表示核心用户，`SECONDARY` 表示辅助用户，`SYSTEM` 表示其他系统/定时任务等。
    
- 校验规则：若 `external_systems` 非空，则正文中必须存在至少一个 `@C4-L1-System` 标签；否则告警"孤立外部系统"。
    

### 2.3 DOMAIN_MODEL 专用 `c4_binding` Schema

yaml

```yaml
c4_binding:
  level: "L2"                          # 固定值
  container_id: "api-service"           # 归属容器，必须在 C4 L2 基线中存在
  container_name: "业务服务层"          # 人类可读名称
  entities:                             # 领域实体列表，至少 1 个
    - entity_id: "FinancingApplication" # 实体标识，PascalCase，全局唯一
      type: "AggregateRoot"            # 枚举：AggregateRoot / Entity / ValueObject
      description: "融资申请聚合根"       # 描述
      attributes:                        # 属性列表
        - name: "amount"                # 属性名，camelCase
          type: "Decimal"               # 业务类型：String / Integer / Decimal / Boolean / Enum / DateTime / JSON
          business_rule: "单笔不超过500万" # 业务规则摘要
          nullable: false               # 是否可空
        - name: "status"
          type: "Enum"
          enum_values: ["DRAFT", "SUBMITTED", "APPROVED", "REJECTED"]
          nullable: false
      relationships:                   # 关系列表，可选
        - target_entity: "Receivable"   # 目标实体 ID
          relation_type: "contains"    # 枚举：contains / references / belongs_to / extends
          cardinality: "1:N"           # 枚举：1:1 / 1:N / N:M
```

**取值逻辑与约束**：

- `container_id`：必须在 C4 基线的 `containers` 列表中存在。若不存在，标记为 `draft`，并触发"容器缺失"告警。
    
- `entity_id`：PascalCase，全局唯一。同一实体在不同 Fragment 中定义时，`entity_id` 必须一致，否则触发冲突告警。
    
- `type`：`AggregateRoot` 必须有至少一个 `attributes`；`ValueObject` 禁止有 `relationships`。
    
- `attributes.type`：业务类型，非数据库类型。数据库类型在 `DB_DESIGN` 中映射。
    
- 校验规则：每个 `entity_id` 必须在正文中通过 `@C4-Entity:{entity_id}` 至少引用一次。
    

### 2.4 ARCH 专用 `c4_binding` Schema

yaml

```yaml
c4_binding:
  level: "L2"
  containers:                           # 容器列表，至少 1 个
    - container_id: "web-app"           # 容器标识，kebab-case
      name: "WebApp"                    # 容器名称
      type: "Frontend"                  # 枚举：Frontend / Backend / Database / Cache / MessageQueue / ExternalService / Mobile
      technology: "Vue3 + TypeScript"   # 技术栈，自由文本
      responsibilities: "用户交互层"   # 职责描述
      deployment_target: "Browser"       # 部署目标，可选
      ports: ["80", "443"]             # 端口列表，可选
    - container_id: "api-service"
      name: "APIService"
      type: "Backend"
      technology: "Spring Boot + Java 17"
      responsibilities: "业务逻辑与领域服务"
      deployment_target: "Docker"
      ports: ["8080"]
    - container_id: "mysql"
      name: "MySQL"
      type: "Database"
      technology: "MySQL 8.0"
      responsibilities: "关系型数据持久化"
      deployment_target: "Docker"
      ports: ["3306"]
  container_relations:                   # 容器间关系，可选
    - source: "web-app"
      target: "api-service"
      protocol: "HTTPS/REST"
      description: "前端调用后端 API"
    - source: "api-service"
      target: "mysql"
      protocol: "JDBC"
      description: "数据持久化"
```

**取值逻辑与约束**：

- `container_id`：kebab-case，全局唯一。禁止与 `system_id` 重复。
    
- `type`：必须从枚举中选取。`Database` 类型必须出现在 `DB_DESIGN` 的绑定中。
    
- `technology`：自由文本，但建议从组织技术栈白名单中选取（便于后续统计）。
    
- `container_relations`：若定义，则 `source` 和 `target` 必须在 `containers` 列表中存在。
    
- 校验规则：每个 `container_id` 必须在正文中通过 `@C4-L2-Container:{container_id}` 至少引用一次。
    

### 2.5 DETAIL_DESIGN 专用 `c4_binding` Schema

yaml

```yaml
c4_binding:
  level: "L3"
  container_id: "api-service"           # 归属容器，必须存在于 L2 基线
  components:                           # 组件列表，至少 1 个
    - component_id: "FinancingController" # 组件标识，PascalCase
      name: "融资申请控制器"              # 组件名称
      type: "Controller"                 # 枚举：Controller / Service / Repository / DomainService / Factory / Gateway / Config
      technology: "Spring MVC"           # 技术栈
      responsibilities: "处理融资申请 HTTP 请求"
      code_path: "src/main/java/com/example/financing/FinancingController.java"  # 代码路径，支持反向定位
      interfaces:                        # 组件暴露的接口，可选
        - interface_id: "create-application"
          method: "POST"
          path: "/api/financing-applications"
          description: "创建融资申请"
```

**取值逻辑与约束**：

- `container_id`：必须在 L2 基线的 `containers` 中存在。不存在则标记 `draft`。
    
- `component_id`：PascalCase，在容器内唯一。跨容器可重复（如两个容器都有 `UserController`），但全局唯一标识为 `{container_id}.{component_id}`。
    
- `type`：`Controller` 必须有至少一个 `interfaces`；`Repository` 建议关联 `DB_DESIGN` 中的表。
    
- `code_path`：相对路径，用于 US-012 的反向代码定位。文件必须存在（若不存在，标记 `stale`）。
    
- 校验规则：每个 `component_id` 必须在正文中通过 `@C4-Component:{component_id}` 至少引用一次。
    

### 2.6 API_DESIGN 专用 `c4_binding` Schema

yaml

```yaml
c4_binding:
  level: "L3"
  component_id: "FinancingController"   # 归属组件，必须存在于 L3 基线
  container_id: "api-service"           # 归属容器，必须存在于 L2 基线
  interfaces:                           # 接口契约列表，至少 1 个
    - interface_id: "create-financing-application"  # 接口标识，kebab-case
      method: "POST"                    # HTTP 方法
      path: "/api/financing-applications" # 路径，必须以 / 开头
      summary: "创建融资申请"             # 摘要
      operation_id: "createFinancingApplication"  # OpenAPI operationId，camelCase
      tags: ["Financing"]               # OpenAPI 标签
      request_schema:                   # 请求 Schema
        ref: "FinancingApplicationDTO"  # 引用 DTO 名称
        content_type: "application/json"
      response_schema:                  # 响应 Schema
        ref: "FinancingApplicationResponse"
        content_type: "application/json"
        status_codes: [201, 400, 422, 500]
      auth_required: true               # 是否需要认证
      rate_limit: "100/min"             # 限流策略，可选
```

**取值逻辑与约束**：

- `component_id` + `container_id`：联合校验，必须在 L3 基线中存在对应组件。
    
- `method`：枚举 `GET/POST/PUT/PATCH/DELETE/HEAD/OPTIONS`。
    
- `path`：必须以 `/` 开头，禁止尾部 `/`。路径参数用 `{param}` 格式。
    
- `interface_id`：kebab-case，在组件内唯一。全局唯一标识为 `{container_id}.{component_id}.{interface_id}`。
    
- `request_schema.ref` / `response_schema.ref`：引用的 DTO 必须在 `DETAIL_DESIGN` 或正文中定义。
    
- 校验规则：每个 `interface_id` 必须在正文中通过 `@C4-Interface:{method} {path}` 至少引用一次。
    

### 2.7 DB_DESIGN 专用 `c4_binding` Schema

yaml

```yaml
c4_binding:
  level: "L2"
  container_id: "mysql"                 # 归属数据容器，必须存在于 L2 基线
  storage_type: "Relational"            # 枚举：Relational / Document / KeyValue / Graph / TimeSeries
  tables:                               # 表列表，至少 1 个
    - table_id: "financing_application" # 表标识，snake_case
      table_name: "financing_application" # 表名
      entity_map: "FinancingApplication"  # 映射的领域实体 ID，必须在 DOMAIN_MODEL 中存在
      engine: "InnoDB"                   # 存储引擎
      charset: "utf8mb4"                 # 字符集
      description: "融资申请主表"
      columns:                           # 字段列表
        - column_name: "amount"          # 字段名
          data_type: "DECIMAL(15,2)"    # 数据库类型
          nullable: false
          default_value: null
          index_type: "BTREE"            # 索引类型：BTREE / HASH / FULLTEXT / NONE
          comment: "申请金额"
          attribute_map: "FinancingApplication.amount"  # 映射的领域属性
      indexes:                           # 索引列表
        - name: "idx_status"
          type: "BTREE"
          columns: ["status"]
      foreign_keys:                      # 外键列表
        - name: "fk_receivable"
          column: "receivable_id"
          ref_table: "receivable"
          ref_column: "id"
          on_delete: "CASCADE"
```

**取值逻辑与约束**：

- `container_id`：必须指向 L2 基线中 `type = "Database"` 的容器。
    
- `entity_map`：必须在 `DOMAIN_MODEL` 的 `c4_binding.entities` 中存在。不存在则告警"表无领域来源"。
    
- `attribute_map`：格式为 `{EntityID}.{attribute_name}`，必须在对应实体的 `attributes` 中存在。
    
- `storage_type`：非关系型数据库（如 MongoDB）时，`indexes` 和 `foreign_keys` 可为空。
    
- 校验规则：每个 `table_id` 必须在正文中通过 `@C4-Table-Name:{table_id}` 至少引用一次。
    

---

## 3. 章节级：锚点 ID 命名规范

### 3.1 锚点 ID 语法

bnf

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
    

### 3.2 按文档类型的推荐锚点结构

表格

|文档类型|推荐顶层锚点|说明|
|:--|:--|:--|
|`PRD`|`sec-business-context`, `sec-system-boundary`, `sec-scope`, `sec-nfr`, `sec-risk`|业务上下文必须在最前|
|`DOMAIN_MODEL`|`sec-domain-entities`, `sec-entity-{entity_id}`, `sec-relationships`, `sec-business-rules`|实体章节锚点必须与 `entity_id` 对应|
|`ARCH`|`sec-tech-arch`, `sec-deployment`, `sec-security`, `sec-data-flow`|架构视图分区|
|`DETAIL_DESIGN`|`sec-component-{component_id}`, `sec-class-diagram`, `sec-state-machine`, `sec-algorithm`|组件章节锚点必须与 `component_id` 对应|
|`API_DESIGN`|`sec-api-contracts`, `sec-api-{interface_id}`, `sec-dto-definitions`, `sec-error-codes`|接口章节锚点必须与 `interface_id` 对应|
|`DB_DESIGN`|`sec-er-diagram`, `sec-table-{table_id}`, `sec-migration-plan`, `sec-index-strategy`|表章节锚点必须与 `table_id` 对应|

### 3.3 Delta 操作定位规则

Delta 补丁通过锚点 ID 定位目标：

yaml

```yaml
delta_operation:
  op_type: "ADD" | "MODIFY" | "DELETE" | "PATCH"
  target_id: "sec-api-wechat-oauth"      # 目标锚点 ID
  anchor_id: "sec-api-contracts"        # ADD 时的插入锚点（after/before）
  position: "after" | "before"          # ADD 时必填
```

**约束**：

- `target_id` 必须在基线或上游 Delta 中存在。
    
- `ADD` 操作必须提供 `anchor_id` + `position`。
    
- `MODIFY` 操作会替换整个 `target_id` 章节的内容，但**保留锚点 ID**（即新内容的第一行标题必须包含相同的 `{#target_id}`）。
    
- `DELETE` 操作会删除 `target_id` 章节及其所有子章节。
    
- `PATCH` 操作在章节内部做局部修改，不破坏锚点结构。
    

---

## 4. 行内级：`@C4-` 标签语法规范

### 4.1 语法定义（BNF）

bnf

```bnf
c4_tag ::= "@C4-" level "-" target ":" identifier ["-" sub_target]
level    ::= "L1" | "L2" | "L3" | "L4"
target   ::= "System" | "Actor" | "Boundary" | "Container" | "Component" | "Entity" | "Attribute" | "Interface" | "Table" | "Page"
identifier ::= kebab_case | PascalCase | camelCase | path_literal
sub_target ::= "Type" | "State" | "Method" | "Name" | "Map" | "Target" | "Container"
```

### 4.2 标准标签清单与取值规则

表格

|标签格式|适用文档类型|取值规则|示例|
|:--|:--|:--|:--|
|`@C4-L1-System:{system_id}`|PRD|引用 L1 外部系统，`system_id` 必须在 `c4_binding.external_systems` 中存在|`@C4-L1-System:core-erp`|
|`@C4-L1-Actor:{actor_id}`|PRD|引用 L1 用户角色，`actor_id` 必须在 `c4_binding.actors` 中存在|`@C4-L1-Actor:supplier`|
|`@C4-L1-Boundary:{description}`|PRD|描述系统边界，自由文本，但建议与 `system_name` 关联|`@C4-L1-Boundary:融资平台与核心企业ERP的交互边界`|
|`@C4-L2-Container:{container_id}`|ARCH, DETAIL_DESIGN|引用 L2 容器，`container_id` 必须在 L2 基线中存在|`@C4-L2-Container:api-service`|
|`@C4-L3-Component:{component_id}`|DETAIL_DESIGN, API_DESIGN|引用 L3 组件，`component_id` 必须在 L3 基线中存在|`@C4-L3-Component:FinancingController`|
|`@C4-Entity:{entity_id}`|DOMAIN_MODEL, DETAIL_DESIGN|引用领域实体，`entity_id` 必须在 DOMAIN_MODEL 中存在|`@C4-Entity:FinancingApplication`|
|`@C4-Entity-Type:{type}`|DOMAIN_MODEL|实体类型，枚举：AggregateRoot/Entity/ValueObject|`@C4-Entity-Type:AggregateRoot`|
|`@C4-Attribute:{entity_id}.{attr_name}`|DOMAIN_MODEL, API_DESIGN, DB_DESIGN|引用实体属性，必须在对应实体的 `attributes` 中存在|`@C4-Attribute:FinancingApplication.amount`|
|`@C4-Interface:{METHOD} {path}`|API_DESIGN|引用接口，`METHOD` 和 `path` 必须在 `c4_binding.interfaces` 中存在|`@C4-Interface:POST /api/financing-applications`|
|`@C4-Interface-Type:{type}`|API_DESIGN|接口类型：read/write/batch/event|`@C4-Interface-Type:write`|
|`@C4-Entity-Target:{entity_id}`|API_DESIGN|接口操作的目标实体|`@C4-Entity-Target:FinancingApplication`|
|`@C4-Table-Name:{table_id}`|DB_DESIGN|引用表，`table_id` 必须在 `c4_binding.tables` 中存在|`@C4-Table-Name:financing_application`|
|`@C4-Entity-Map:{entity_id}`|DB_DESIGN|表映射的实体|`@C4-Entity-Map:FinancingApplication`|
|`@C4-Page-Type:{type}`|DOMAIN_MODEL, PRD|推断页面类型：list/detail/dashboard/form/wizard/modal/search|`@C4-Page-Type:form`|
|`@C4-Page-Container:{container_id}`|DOMAIN_MODEL|页面归属的容器|`@C4-Page-Container:api-service`|
|`@C4-Entity-State:{entity_id}.{attr}=="{value}"`|DOMAIN_MODEL|实体状态条件，用于向导页推断|`@C4-Entity-State:FinancingApplication.status=="DRAFT"`|

### 4.3 标签放置位置规则

表格

|标签|必须放置的位置|禁止放置的位置|
|:--|:--|:--|
|`@C4-L1-System`|系统边界描述段落首行|功能需求细节段落|
|`@C4-L2-Container`|容器职责描述段落首行|接口参数表格内|
|`@C4-L3-Component`|组件描述段落首行|部署拓扑章节|
|`@C4-Entity`|实体定义章节标题下方第一行|接口 URL 行|
|`@C4-Interface`|接口契约章节标题下方第一行|业务规则描述|
|`@C4-Table-Name`|表结构章节标题下方第一行|ER 图说明文字|
|`@C4-Page-Type`|用户故事/页面流程描述段落|技术架构章节|

---

## 5. 提取器路由与匹配规则

### 5.1 提取器分层路由

plain

```plain
Fragment 入库 / Delta 提交
    ↓
DocumentTemplateEngine 识别 doc_type
    ↓
├─ 架构相关类型（PRD/DM/ARCH/DD/API/DB）
│   └─ 校验 YAML Front Matter 完整性
│       ├─ 缺失 c4_binding → 阻断（错误码 40001）
│       ├─ level 与 doc_type 不匹配 → 阻断（错误码 40002）
│       └─ 通过 → 进入 StructuredExtractor
│           ├─ 提取 YAML Front Matter（正则/Parser，confidence=1.0）
│           ├─ 提取章节锚点 ID（正则，confidence=1.0）
│           ├─ 提取行内 @C4- 标签（正则，confidence=1.0）
│           └─ 进入 HybridValidator
│               ├─ 校验标签引用的 ID 是否在 c4_binding 中存在
│               ├─ 校验实体/接口/组件的跨文档一致性
│               └─ 输出 BindingRecord（status=validated）
│
├─ 非架构类型（TEST/DEPLOY/BUG/CHANGELOG）
│   └─ 标记为 no-arch-binding
│       └─ 跳过 C4 提取，仅存入 DocForge 元数据
│
└─ 未知类型 / 无模板
    └─ 进入 LLMExtractor（语义发现）
        ├─ 识别内容是否含架构关键词（模块/实体/接口/组件）
        ├─ 输出 draft 级绑定建议
        └─ 等待人工确认（人工确认后转为 validated）
```

### 5.2 正则提取规则（StructuredExtractor）

表格

|提取目标|正则模式|示例匹配|
|:--|:--|:--|
|YAML Front Matter|`^---\n(.*?)\n---`|文档头部元数据|
|章节锚点|`^(#{1,6})\s+(.+?)\s*\{#([a-zA-Z0-9_]+)\}\s*$`|`## 1. 接口契约 {#sec-api-contracts}`|
|`@C4-` 标签|`@C4-([A-Za-z0-9-]+):(.+?)(?=\s|$)`|`@C4-Entity:FinancingApplication`|
|实体属性引用|`@C4-Attribute:([A-Z][a-zA-Z0-9]*)\.([a-z][a-zA-Z0-9]*)`|`@C4-Attribute:FinancingApplication.amount`|
|接口定义|`@C4-Interface:(GET\|POST\|PUT\|PATCH\|DELETE)\s+(\S+)`|`@C4-Interface:POST /api/orders`|

### 5.3 LLM 辅助提取（LLMExtractor）触发条件

仅在以下情况触发 LLM 辅助：

1. 文档类型为架构相关，但 **YAML Front Matter 中 `c4_binding` 存在但字段不完整**（如 `entities` 为空数组）
    
2. 正文中发现架构关键词（"模块"、"实体"、"接口"、"组件"），但 **无对应的 `@C4-` 标签**
    
3. 用户手动标记 `?c4_discover=true` 请求 AI 发现遗漏
    

**LLM 提取输出格式**：

JSON

```json
{
  "discovered_items": [
    {
      "type": "Entity",
      "name": "Invoice",
      "confidence": 0.85,
      "location": "sec-business-context, line 12",
      "suggested_tag": "@C4-Entity:Invoice",
      "reason": "段落描述了一个具有金额和状态的业务对象"
    }
  ],
  "requires_human_confirmation": true
}
```

**约束**：LLM 发现的标签必须人工确认后才能写入 BindingRegistry，初始状态为 `draft`。

---

## 6. 一致性校验规则（CrossLayerValidator）

### 6.1 跨文档校验矩阵

表格

|校验规则 ID|校验内容|上游文档|下游文档|校验逻辑|失败处理|
|:--|:--|:--|:--|:--|:--|
|`VAL-001`|L1 外部系统引用一致性|PRD (`external_systems`)|ARCH (`containers` 中 `ExternalService` 类型)|PRD 定义的每个外部系统，必须在 ARCH 中有对应容器或集成点|告警：孤立外部系统|
|`VAL-002`|L2 实体定义一致性|DOMAIN_MODEL (`entities`)|API_DESIGN (`request_schema`/`response_schema`)|API 的 DTO 字段必须能在 DOMAIN_MODEL 的实体属性中找到映射|告警：接口字段无领域来源|
|`VAL-003`|L2 容器归属一致性|ARCH (`containers`)|DETAIL_DESIGN/API_DESIGN/DB_DESIGN (`container_id`)|下游文档引用的 `container_id` 必须在 ARCH 中存在|阻断：容器未定义|
|`VAL-004`|L3 组件归属一致性|DETAIL_DESIGN (`components`)|API_DESIGN (`component_id`)|API 归属的组件必须在 DETAIL_DESIGN 中定义|阻断：组件未定义|
|`VAL-005`|L3 接口归属一致性|API_DESIGN (`interfaces`)|DETAIL_DESIGN (`components.interfaces`)|DETAIL_DESIGN 中组件声明的接口，必须在 API_DESIGN 中有详细契约|提示：接口契约缺失|
|`VAL-006`|实体-表映射一致性|DOMAIN_MODEL (`entities`)|DB_DESIGN (`tables.entity_map`)|每张表映射的实体必须在 DOMAIN_MODEL 中存在|告警：表无领域来源|
|`VAL-007`|属性-字段映射一致性|DOMAIN_MODEL (`entities.attributes`)|DB_DESIGN (`tables.columns.attribute_map`)|字段映射的属性必须在对应实体中存在|告警：字段无属性来源|
|`VAL-008`|页面类型推断一致性|DOMAIN_MODEL (`@C4-Page-Type`)|WireframeEngine (DR-019)|若 `@C4-Page-Type` 与 DomainMapper 推断结果冲突，以人工标注为准|提示：推断冲突|

### 6.2 校验触发时机

表格

|时机|触发校验|范围|
|:--|:--|:--|
|Fragment 首次入库|VAL-003, VAL-004|单文档|
|Delta 版本提交|VAL-001~VAL-008（增量）|变更涉及的相关文档|
|编译完整文档时|VAL-001~VAL-008（全量）|项目内所有架构文档|
|用户手动触发"架构校验"|VAL-001~VAL-008（全量）|项目内所有架构文档|

---

## 7. 实施检查清单

### Phase 1：模板固化（2 天）

- [ ] 定义 6 份标准模板 Markdown 文件（含完整 YAML Front Matter 示例）
    
- [ ] 每份模板配套 JSON Schema，用于 DocumentTemplateEngine 自动校验
    
- [ ] 定义 20 个标准 `@C4-` 标签的完整语法规范（含正则）
    
- [ ] 定义章节锚点 ID 白名单（按文档类型）
    
- [ ] 编写模板使用指南（给 AI Agent 和人工作者）
    

### Phase 2：引擎改造（3 天）

- [ ] DocForge `DocumentTemplateEngine` 集成 JSON Schema 校验
    
- [ ] `StructuredExtractor` 实现 6 套正则提取规则
    
- [ ] `HybridValidator` 实现 8 条跨层校验规则
    
- [ ] `BindingRegistry` 建表（含 `source_location` 字段，支持反向定位到文档行号）
    
- [ ] 与 DR-011（C4 DSL 生成器）对接：编译器输出 `arsitect.aac.yml`
    

### Phase 3：闭环验证（2 天）

- [ ] 用真实项目（供应链融资平台）跑通 6 类文档的入库 → 提取 → 校验 → 编译全流程
    
- [ ] 统计规则提取 vs LLM 提取的准确率（目标：规则 100%，LLM 辅助发现率 > 60%）
    
- [ ] 验证 Delta 增量提取性能（目标：单 Delta < 100ms）
    

---

## 8. 一句话总结

**模板规则不是"写作建议"，而是"架构接口契约"。YAML Front Matter 是文档与 C4 基线的强类型接口，`@C4-` 标签是正文与架构图谱的精确坐标，章节锚点是 Delta 补丁的定位系统。三者共同构成 DocForge 的"架构感知编译器"输入规范。**