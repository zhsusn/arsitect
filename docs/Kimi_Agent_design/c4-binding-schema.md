# c4_binding 完整 Schema 规范

> **文档版本**：v1.0.0  
> **编写日期**：2026-06-10  
> **目标读者**：架构师、AI Agent 开发者、DocForge 平台开发者  
> **规范来源**：
> - C4 Model（Simon Brown，https://c4model.com/）
> - Structurizr JSON Schema（OpenAPI 3.0，https://github.com/structurizr/structurizr/tree/main/structurizr-json）
> - Arsitect C4-doc-rules.md（内部规则集）  
> **文档状态**：DRAFT

---

## 一、设计目标

`c4_binding` 是文档与 C4 架构模型之间的**强类型接口**。它承担三个核心职责：

1. **双向绑定**：文档通过 `c4_binding` 声明其承载的架构元素，架构图谱通过 `@C4-` 标签反向定位到文档章节
2. **模型互操作**：`c4_binding` 的数据结构可直接映射为 Structurizr Workspace JSON 的 `model` 子集，支持一键导出为 `.dsl` / `.json`
3. **跨文档一致性**：下游文档引用上游文档的架构元素时，`c4_binding` 提供强类型校验基准

---

## 二、与 Structurizr 的映射关系

| Arsitect `c4_binding` 字段 | Structurizr JSON 对应路径 | 说明 |
|:---------------------------|:--------------------------|:-----|
| `system_id` / `system_name` | `model.softwareSystems[].id` / `name` | PRD 定义的系统在 Structurizr 中映射为 softwareSystem |
| `external_systems[].id` | `model.softwareSystems[].id`（location=External） | 外部系统映射为 location=External 的 softwareSystem |
| `actors[].id` | `model.people[].id` | 用户角色映射为 Person |
| `containers[].container_id` | `model.softwareSystems[].containers[].id` | 容器映射为 Container |
| `container_relations[]` | `model.softwareSystems[].containers[].relationships[]` + `model.relationships[]` | 容器间关系 |
| `components[].component_id` | `model.softwareSystems[].containers[].components[].id` | 组件映射为 Component |
| `entities[].entity_id` | 扩展字段 `properties["c4:entityId"]` | Structurizr 原生无 Entity 类型，通过 Container/Component 的 `properties` 扩展 |
| `interfaces[].interface_id` | 扩展字段 `properties["c4:interfaceId"]` | 同理通过 properties 扩展 |
| `tables[].table_id` | `model.softwareSystems[].containers[].id`（tag="Database"） | 数据表映射为 Database 类型的 Container |

> **命名空间约定**：Structurizr 的 `properties` 是任意 key-value 对象。Arsitect 扩展字段统一使用 `arsitect:` 前缀，如 `arsitect:entityId`、`arsitect:interfaceId`。

---

## 三、顶层公共 Schema

所有架构相关文档的 `c4_binding` 必须包含以下公共字段：

```yaml
c4_binding:
  level: "L1" | "L2" | "L3" | "L4"    # 必填，C4 层级
```

`level` 与 `doc_type` 的强制对应关系：

| `doc_type` | 强制 `level` | 说明 |
|:-----------|:-------------|:-----|
| `PRD` | `L1` | 系统上下文 |
| `DOMAIN_MODEL` | `L2` | 领域模型归属容器 |
| `ARCH` | `L2` | 容器划分与技术栈 |
| `DETAIL_DESIGN` | `L3` | 组件设计 |
| `API_DESIGN` | `L3` | 接口契约归属组件 |
| `DB_DESIGN` | `L2` | 数据存储容器 |

---

## 四、按文档类型的专用 Schema

### 4.1 PRD 专用 Schema（`doc_type = PRD`，`level = L1`）

```yaml
c4_binding:
  level: "L1"
  system_id: string           # 系统标识，全局唯一，kebab-case
  system_name: string         # 系统名称，人类可读
  external_systems:           # 外部系统列表，可选（无外部依赖可为空数组）
    - id: string              # 外部系统标识，kebab-case，全局唯一
      name: string            # 外部系统名称
      description: string     # 与本系统的关系描述
      relation: string        # 关系描述（如"提供应收账款数据"）
      interface_type: string  # 可选：交互协议类型，如 REST / gRPC / MessageQueue / HTTPS
      location: "External"    # 固定值，标记为外部系统
  actors:                     # 用户角色列表，可选
    - id: string              # 角色标识，kebab-case
      name: string            # 角色名称
      role_type: "PRIMARY" | "SECONDARY" | "SYSTEM"  # 角色类型
      description: string     # 角色描述
      location: "Internal" | "External" | "Unspecified"  # 角色位置，默认 Internal
```

#### 4.1.1 字段约束

| 字段 | 类型 | 必填 | 取值规则 |
|:-----|:-----|:-----|:---------|
| `system_id` | STRING | 是 | kebab-case，全局唯一，作为 C4 L1 的根节点 ID |
| `system_name` | STRING | 是 | 1-100 字符，人类可读 |
| `external_systems.id` | STRING | 是 | kebab-case，禁止与 `system_id` 重复 |
| `external_systems.name` | STRING | 是 | 1-100 字符 |
| `external_systems.interface_type` | STRING | 否 | 建议从白名单选取：REST / gRPC / MessageQueue / HTTPS / SOAP / GraphQL / TCP / UDP |
| `actors.id` | STRING | 是 | kebab-case，全局唯一 |
| `actors.role_type` | ENUM | 是 | PRIMARY（核心业务操作者）/ SECONDARY（辅助角色）/ SYSTEM（其他系统/定时任务） |
| `actors.location` | ENUM | 否 | Internal（内部用户）/ External（外部用户）/ Unspecified（未指定），默认 Internal |

#### 4.1.2 Structurizr 映射示例

```json
{
  "model": {
    "people": [
      {
        "id": "developer",
        "name": "开发者",
        "description": "使用 AI 辅助开发的超级个体",
        "location": "Internal",
        "tags": "PRIMARY",
        "properties": { "arsitect:actorId": "developer" }
      }
    ],
    "softwareSystems": [
      {
        "id": "sdlc-visualizer",
        "name": "SDLC Visualizer",
        "description": "Arsitect 可视化驾驶舱",
        "location": "Internal",
        "properties": { "arsitect:systemId": "sdlc-visualizer" }
      },
      {
        "id": "kimi-cli",
        "name": "Kimi CLI",
        "description": "AI 执行引擎",
        "location": "External",
        "tags": "External System",
        "properties": { "arsitect:externalSystemId": "kimi-cli" }
      }
    ],
    "relationships": [
      { "sourceId": "developer", "destinationId": "sdlc-visualizer", "description": "Uses" }
    ]
  }
}
```

---

### 4.2 DOMAIN_MODEL 专用 Schema（`doc_type = DOMAIN_MODEL`，`level = L2`）

```yaml
c4_binding:
  level: "L2"
  container_id: string        # 归属容器，必须在 C4 L2 基线中存在
  container_name: string      # 人类可读名称（冗余但便于阅读）
  entities:                   # 领域实体列表，至少 1 个
    - entity_id: string       # 实体标识，PascalCase，全局唯一
      name: string            # 实体名称（人类可读）
      type: "AggregateRoot" | "Entity" | "ValueObject"  # DDD 类型
      description: string     # 描述
      attributes:             # 属性列表
        - name: string        # 属性名，camelCase
          type: string        # 业务类型：String / Integer / Decimal / Boolean / Enum / DateTime / JSON / UUID
          business_rule: string   # 业务规则摘要
          nullable: boolean   # 是否可空
          enum_values: [string]   # 当 type=Enum 时必填
      relationships:          # 关系列表，可选
        - target_entity: string   # 目标实体 ID
          relation_type: "contains" | "references" | "belongs_to" | "extends"  # 关系类型
          cardinality: "1:1" | "1:N" | "N:M"  # 基数
```

#### 4.2.1 字段约束

| 字段 | 类型 | 必填 | 取值规则 |
|:-----|:-----|:-----|:---------|
| `container_id` | STRING | 是 | 必须在 ARCH 文档的 `c4_binding.containers` 中存在 |
| `entity_id` | STRING | 是 | PascalCase，全局唯一 |
| `type` | ENUM | 是 | AggregateRoot / Entity / ValueObject |
| `attributes.type` | ENUM | 是 | String / Integer / Decimal / Boolean / Enum / DateTime / JSON / UUID |
| `attributes.nullable` | BOOLEAN | 否 | 默认 false |
| `relationships.relation_type` | ENUM | 是 | contains / references / belongs_to / extends |
| `relationships.cardinality` | ENUM | 是 | 1:1 / 1:N / N:M |

#### 4.2.2 校验规则

- `AggregateRoot` 必须有至少一个 `attributes`
- `ValueObject` 禁止有 `relationships`
- 每个 `entity_id` 必须在正文中通过 `@C4-Entity:{entity_id}` 至少引用一次
- `attributes.name` 使用 camelCase

---

### 4.3 ARCH 专用 Schema（`doc_type = ARCH`，`level = L2`）

```yaml
c4_binding:
  level: "L2"
  containers:                 # 容器列表，至少 1 个
    - container_id: string    # 容器标识，kebab-case，全局唯一
      name: string            # 容器名称
      type: "Frontend" | "Backend" | "Database" | "Cache" | "MessageQueue" | "ExternalService" | "Mobile" | "WebBrowser" | "SPA"
      technology: string      # 技术栈，自由文本
      responsibilities: string    # 职责描述
      deployment_target: string   # 部署目标，可选（如 Browser / Docker / Kubernetes / Lambda）
      ports: [string]         # 端口列表，可选
      tags: [string]          # 标签列表，可选（如 "Database" / "Web" / "API" / "Critical Path"）
      group: string           # 分组名，可选（用于在图中按业务域分组）
      url: string             # 更多信息 URL，可选
      properties:             # 扩展属性，可选
        key: value
  container_relations:        # 容器间关系，可选
    - source: string          # 源容器 ID
      target: string          # 目标容器 ID
      protocol: string        # 通信协议（如 HTTPS/REST / gRPC / JDBC / Redis Protocol）
      description: string     # 关系描述
      interaction_style: "Synchronous" | "Asynchronous"  # 交互风格，可选
      technology: string      # 关系技术（如 HTTPS, JDBC, gRPC）
```

#### 4.3.1 字段约束

| 字段 | 类型 | 必填 | 取值规则 |
|:-----|:-----|:-----|:---------|
| `container_id` | STRING | 是 | kebab-case，全局唯一，禁止与 `system_id` 重复 |
| `type` | ENUM | 是 | Frontend / Backend / Database / Cache / MessageQueue / ExternalService / Mobile / WebBrowser / SPA |
| `technology` | STRING | 是 | 自由文本，但建议从组织技术栈白名单中选取 |
| `container_relations.source` | STRING | 是 | 必须在 `containers` 列表中存在 |
| `container_relations.target` | STRING | 是 | 必须在 `containers` 列表中存在 |
| `interaction_style` | ENUM | 否 | Synchronous / Asynchronous |

#### 4.3.2 Structurizr 映射示例

```json
{
  "model": {
    "softwareSystems": [
      {
        "id": "sdlc-visualizer",
        "name": "SDLC Visualizer",
        "containers": [
          {
            "id": "web-frontend",
            "name": "Web Frontend",
            "technology": "React 19 + TypeScript",
            "description": "用户交互层",
            "tags": "Frontend,Web",
            "properties": { "arsitect:containerId": "web-frontend" }
          },
          {
            "id": "api-service",
            "name": "API Service",
            "technology": "FastAPI + Python 3.11",
            "description": "业务逻辑与领域服务",
            "tags": "Backend,API",
            "properties": { "arsitect:containerId": "api-service" }
          },
          {
            "id": "sqlite",
            "name": "SQLite",
            "technology": "SQLite 3.39+",
            "description": "本地关系型数据持久化",
            "tags": "Database",
            "properties": { "arsitect:containerId": "sqlite" }
          }
        ]
      }
    ],
    "relationships": [
      {
        "sourceId": "web-frontend",
        "destinationId": "api-service",
        "description": "调用后端 API",
        "technology": "HTTPS/REST"
      },
      {
        "sourceId": "api-service",
        "destinationId": "sqlite",
        "description": "读写数据",
        "technology": "SQLAlchemy/SQLite"
      }
    ]
  }
}
```

---

### 4.4 DETAIL_DESIGN 专用 Schema（`doc_type = DETAIL_DESIGN`，`level = L3`）

```yaml
c4_binding:
  level: "L3"
  container_id: string        # 归属容器，必须存在于 L2 基线
  components:                 # 组件列表，至少 1 个
    - component_id: string    # 组件标识，PascalCase，在容器内唯一
      name: string            # 组件名称
      type: "Controller" | "Service" | "Repository" | "DomainService" | "Factory" | "Gateway" | "Config" | "Entity" | "ValueObject" | "Mapper" | "Middleware" | "EventHandler"
      technology: string      # 技术栈
      responsibilities: string    # 职责描述
      code_path: string       # 代码路径（相对路径），支持反向定位
      group: string           # 分组名，可选
      interfaces:             # 组件暴露的接口，可选
        - interface_id: string    # 接口标识，kebab-case
          method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE" | "HEAD" | "OPTIONS" | "MESSAGE" | "EVENT"
          path: string        # HTTP 路径或消息主题名
          description: string # 接口描述
          operation_id: string    # OpenAPI operationId，camelCase
          tags: [string]      # OpenAPI 标签
```

#### 4.4.1 字段约束

| 字段 | 类型 | 必填 | 取值规则 |
|:-----|:-----|:-----|:---------|
| `container_id` | STRING | 是 | 必须在 L2 基线的 `containers` 中存在 |
| `component_id` | STRING | 是 | PascalCase，在容器内唯一。跨容器可重复，全局唯一标识为 `{container_id}.{component_id}` |
| `type` | ENUM | 是 | Controller / Service / Repository / DomainService / Factory / Gateway / Config / Entity / ValueObject / Mapper / Middleware / EventHandler |
| `code_path` | STRING | 否 | 相对路径，用于 US-012 反向代码定位 |
| `interfaces.method` | ENUM | 是 | GET / POST / PUT / PATCH / DELETE / HEAD / OPTIONS / MESSAGE / EVENT |
| `interfaces.path` | STRING | 是 | HTTP 路径必须以 `/` 开头；消息接口为主题名 |

#### 4.4.2 校验规则

- `Controller` 类型必须有至少一个 `interfaces`
- `Repository` 建议关联 `DB_DESIGN` 中的表
- `code_path` 对应的文件若不存在，标记为 `stale`
- 每个 `component_id` 必须在正文中通过 `@C4-Component:{component_id}` 至少引用一次

---

### 4.5 API_DESIGN 专用 Schema（`doc_type = API_DESIGN`，`level = L3`）

```yaml
c4_binding:
  level: "L3"
  component_id: string        # 归属组件，必须存在于 L3 基线
  container_id: string        # 归属容器，必须存在于 L2 基线
  interfaces:                 # 接口契约列表，至少 1 个
    - interface_id: string    # 接口标识，kebab-case，在组件内唯一
      method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE" | "HEAD" | "OPTIONS"
      path: string            # 路径，必须以 / 开头，禁止尾部 /
      summary: string         # 接口摘要
      operation_id: string    # OpenAPI operationId，camelCase
      tags: [string]          # OpenAPI 标签
      request_schema:         # 请求 Schema
        ref: string           # 引用 DTO 名称
        content_type: string  # 如 application/json
        required: [string]    # 必填字段列表
      response_schema:        # 响应 Schema
        ref: string           # 引用 DTO 名称
        content_type: string  # 如 application/json
        status_codes: [integer]   # 状态码列表
      auth_required: boolean  # 是否需要认证
      rate_limit: string      # 限流策略，可选（如 "100/min"）
      idempotency_key: boolean    # 是否需要幂等键，可选
      deprecated: boolean     # 是否已废弃，可选
```

#### 4.5.1 字段约束

| 字段 | 类型 | 必填 | 取值规则 |
|:-----|:-----|:-----|:---------|
| `component_id` + `container_id` | STRING | 是 | 联合校验，必须在 L3 基线中存在对应组件 |
| `interface_id` | STRING | 是 | kebab-case，在组件内唯一。全局唯一标识为 `{container_id}.{component_id}.{interface_id}` |
| `method` | ENUM | 是 | GET / POST / PUT / PATCH / DELETE / HEAD / OPTIONS |
| `path` | STRING | 是 | 必须以 `/` 开头，禁止尾部 `/`。路径参数用 `{param}` 格式 |
| `operation_id` | STRING | 是 | camelCase，全局唯一 |
| `request_schema.ref` | STRING | 否 | 引用的 DTO 必须在 `DETAIL_DESIGN` 或正文中定义 |
| `response_schema.status_codes` | INTEGER[] | 是 | 至少包含一个成功状态码（2xx） |

#### 4.5.2 校验规则

- 每个 `interface_id` 必须在正文中通过 `@C4-Interface:{METHOD} {path}` 至少引用一次
- `request_schema.ref` / `response_schema.ref` 引用的 DTO 必须在 `DOMAIN_MODEL` 的实体属性或 `DETAIL_DESIGN` 的组件中定义

---

### 4.6 DB_DESIGN 专用 Schema（`doc_type = DB_DESIGN`，`level = L2`）

```yaml
c4_binding:
  level: "L2"
  container_id: string        # 归属数据容器，必须指向 L2 基线中 type="Database" 的容器
  storage_type: "Relational" | "Document" | "KeyValue" | "Graph" | "TimeSeries" | "ColumnFamily" | "SearchEngine"
  tables:                     # 表列表，至少 1 个
    - table_id: string        # 表标识，snake_case
      table_name: string      # 表名（通常与 table_id 相同）
      entity_map: string      # 映射的领域实体 ID，必须在 DOMAIN_MODEL 中存在
      engine: string          # 存储引擎，可选（如 InnoDB）
      charset: string         # 字符集，可选（如 utf8mb4）
      description: string     # 表描述
      columns:                # 字段列表
        - column_name: string # 字段名，snake_case
          data_type: string   # 数据库类型（如 VARCHAR(64), DECIMAL(15,2), JSONB）
          nullable: boolean   # 是否可空
          default_value: string   # 默认值，可选
          index_type: "BTREE" | "HASH" | "FULLTEXT" | "GIN" | "GIST" | "NONE"  # 索引类型
          comment: string     # 字段注释
          attribute_map: string   # 映射的领域属性，格式：{EntityID}.{attribute_name}
      indexes:                # 索引列表，可选
        - name: string        # 索引名
          type: string        # 索引类型
          columns: [string]   # 索引字段列表
          unique: boolean     # 是否唯一索引
      foreign_keys:           # 外键列表，可选
        - name: string        # 外键名
          column: string      # 本表字段
          ref_table: string   # 引用表
          ref_column: string  # 引用字段
          on_delete: "CASCADE" | "SET NULL" | "RESTRICT" | "NO ACTION"
          on_update: "CASCADE" | "SET NULL" | "RESTRICT" | "NO ACTION"
      partitions:             # 分区策略，可选
        type: string          # 分区类型（如 RANGE / HASH / LIST）
        key: string           # 分区键
```

#### 4.6.1 字段约束

| 字段 | 类型 | 必填 | 取值规则 |
|:-----|:-----|:-----|:---------|
| `container_id` | STRING | 是 | 必须指向 L2 基线中 `type = "Database"` 的容器 |
| `storage_type` | ENUM | 是 | Relational / Document / KeyValue / Graph / TimeSeries / ColumnFamily / SearchEngine |
| `table_id` | STRING | 是 | snake_case，全局唯一 |
| `entity_map` | STRING | 否 | 必须在 `DOMAIN_MODEL` 的 `entities` 中存在 |
| `columns.data_type` | STRING | 是 | 数据库原生类型 |
| `columns.index_type` | ENUM | 否 | BTREE / HASH / FULLTEXT / GIN / GIST / NONE |
| `columns.attribute_map` | STRING | 否 | 格式为 `{EntityID}.{attribute_name}`，必须在对应实体的 `attributes` 中存在 |

#### 4.6.2 校验规则

- 非关系型数据库（MongoDB / Redis 等）时，`indexes` 和 `foreign_keys` 可为空
- `entity_map` 必须在 `DOMAIN_MODEL` 中存在
- `attribute_map` 必须在对应实体的 `attributes` 中存在
- 每个 `table_id` 必须在正文中通过 `@C4-Table-Name:{table_id}` 至少引用一次

---

## 五、共享子结构定义

### 5.1 Relationship（关系）

```yaml
Relationship:
  type: object
  properties:
    source_id: string         # 源元素 ID
    target_id: string         # 目标元素 ID
    description: string       # 关系描述
    technology: string        # 关系技术（如 HTTPS, JDBC, gRPC）
    interaction_style: "Synchronous" | "Asynchronous"
    tags: [string]            # 标签列表
    url: string               # 更多信息 URL
```

### 5.2 Perspective（架构视角）

```yaml
Perspective:
  type: object
  properties:
    name: string              # 视角名称（如 "Security" / "Performance" / "Data Privacy"）
    description: string       # 描述
    value: string             # 视角值
    url: string               # 视角文档 URL
```

### 5.3 DeploymentNode（部署节点）

```yaml
DeploymentNode:
  type: object
  properties:
    node_id: string           # 节点标识，kebab-case
    name: string              # 节点名称
    description: string       # 描述
    technology: string        # 技术（如 "Docker", "Kubernetes", "AWS EC2"）
    environment: string       # 环境（如 "Development", "Staging", "Production"）
    instances: string         # 实例数（如 "1", "3", "0..N", "0..*"）
    children: [DeploymentNode]    # 子节点
    container_instances:      # 运行的容器实例
      - container_id: string
        instance_id: integer
        health_checks:
          - name: string
            url: string
            interval: integer     # 秒
            timeout: integer      # 毫秒
```

---

## 六、完整 JSON Schema 定义

以下是 `c4_binding` 的正式 JSON Schema（ Draft 7 ），可用于 DocForge 平台的自动校验：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://arsitect.dev/schemas/c4-binding.json",
  "title": "C4 Binding Schema",
  "description": "Arsitect 文档与 C4 架构模型的绑定规范",
  "type": "object",
  "required": ["level"],
  "properties": {
    "level": {
      "type": "string",
      "enum": ["L1", "L2", "L3", "L4"],
      "description": "C4 模型层级"
    }
  },
  "allOf": [
    {
      "if": {
        "properties": { "level": { "const": "L1" } }
      },
      "then": {
        "$ref": "#/definitions/PRDBinding"
      }
    },
    {
      "if": {
        "properties": { "level": { "const": "L2" } }
      },
      "then": {
        "anyOf": [
          { "$ref": "#/definitions/DomainModelBinding" },
          { "$ref": "#/definitions/ArchBinding" },
          { "$ref": "#/definitions/DBDesignBinding" }
        ]
      }
    },
    {
      "if": {
        "properties": { "level": { "const": "L3" } }
      },
      "then": {
        "anyOf": [
          { "$ref": "#/definitions/DetailDesignBinding" },
          { "$ref": "#/definitions/APIDesignBinding" }
        ]
      }
    }
  ],
  "definitions": {
    "PRDBinding": {
      "type": "object",
      "required": ["level", "system_id", "system_name"],
      "properties": {
        "level": { "const": "L1" },
        "system_id": { "type": "string", "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$" },
        "system_name": { "type": "string", "minLength": 1, "maxLength": 100 },
        "external_systems": {
          "type": "array",
          "items": { "$ref": "#/definitions/ExternalSystem" }
        },
        "actors": {
          "type": "array",
          "items": { "$ref": "#/definitions/Actor" }
        }
      }
    },
    "ExternalSystem": {
      "type": "object",
      "required": ["id", "name"],
      "properties": {
        "id": { "type": "string", "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$" },
        "name": { "type": "string", "minLength": 1, "maxLength": 100 },
        "description": { "type": "string" },
        "relation": { "type": "string" },
        "interface_type": { "type": "string" },
        "location": { "type": "string", "enum": ["External"], "default": "External" }
      }
    },
    "Actor": {
      "type": "object",
      "required": ["id", "name", "role_type"],
      "properties": {
        "id": { "type": "string", "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$" },
        "name": { "type": "string", "minLength": 1, "maxLength": 100 },
        "role_type": { "type": "string", "enum": ["PRIMARY", "SECONDARY", "SYSTEM"] },
        "description": { "type": "string" },
        "location": { "type": "string", "enum": ["Internal", "External", "Unspecified"], "default": "Internal" }
      }
    },
    "DomainModelBinding": {
      "type": "object",
      "required": ["level", "container_id", "entities"],
      "properties": {
        "level": { "const": "L2" },
        "container_id": { "type": "string" },
        "container_name": { "type": "string" },
        "entities": {
          "type": "array",
          "minItems": 1,
          "items": { "$ref": "#/definitions/Entity" }
        }
      }
    },
    "Entity": {
      "type": "object",
      "required": ["entity_id", "name", "type"],
      "properties": {
        "entity_id": { "type": "string", "pattern": "^[A-Z][a-zA-Z0-9]*$" },
        "name": { "type": "string" },
        "type": { "type": "string", "enum": ["AggregateRoot", "Entity", "ValueObject"] },
        "description": { "type": "string" },
        "attributes": {
          "type": "array",
          "items": { "$ref": "#/definitions/EntityAttribute" }
        },
        "relationships": {
          "type": "array",
          "items": { "$ref": "#/definitions/EntityRelationship" }
        }
      }
    },
    "EntityAttribute": {
      "type": "object",
      "required": ["name", "type"],
      "properties": {
        "name": { "type": "string", "pattern": "^[a-z][a-zA-Z0-9]*$" },
        "type": { "type": "string", "enum": ["String", "Integer", "Decimal", "Boolean", "Enum", "DateTime", "JSON", "UUID"] },
        "business_rule": { "type": "string" },
        "nullable": { "type": "boolean", "default": false },
        "enum_values": { "type": "array", "items": { "type": "string" } }
      }
    },
    "EntityRelationship": {
      "type": "object",
      "required": ["target_entity", "relation_type", "cardinality"],
      "properties": {
        "target_entity": { "type": "string" },
        "relation_type": { "type": "string", "enum": ["contains", "references", "belongs_to", "extends"] },
        "cardinality": { "type": "string", "enum": ["1:1", "1:N", "N:M"] }
      }
    },
    "ArchBinding": {
      "type": "object",
      "required": ["level", "containers"],
      "properties": {
        "level": { "const": "L2" },
        "containers": {
          "type": "array",
          "minItems": 1,
          "items": { "$ref": "#/definitions/Container" }
        },
        "container_relations": {
          "type": "array",
          "items": { "$ref": "#/definitions/ContainerRelation" }
        }
      }
    },
    "Container": {
      "type": "object",
      "required": ["container_id", "name", "type", "technology", "responsibilities"],
      "properties": {
        "container_id": { "type": "string", "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$" },
        "name": { "type": "string", "minLength": 1, "maxLength": 100 },
        "type": { "type": "string", "enum": ["Frontend", "Backend", "Database", "Cache", "MessageQueue", "ExternalService", "Mobile", "WebBrowser", "SPA"] },
        "technology": { "type": "string" },
        "responsibilities": { "type": "string" },
        "deployment_target": { "type": "string" },
        "ports": { "type": "array", "items": { "type": "string" } },
        "tags": { "type": "array", "items": { "type": "string" } },
        "group": { "type": "string" },
        "url": { "type": "string", "format": "uri" }
      }
    },
    "ContainerRelation": {
      "type": "object",
      "required": ["source", "target"],
      "properties": {
        "source": { "type": "string" },
        "target": { "type": "string" },
        "protocol": { "type": "string" },
        "description": { "type": "string" },
        "interaction_style": { "type": "string", "enum": ["Synchronous", "Asynchronous"] },
        "technology": { "type": "string" }
      }
    },
    "DetailDesignBinding": {
      "type": "object",
      "required": ["level", "container_id", "components"],
      "properties": {
        "level": { "const": "L3" },
        "container_id": { "type": "string" },
        "components": {
          "type": "array",
          "minItems": 1,
          "items": { "$ref": "#/definitions/Component" }
        }
      }
    },
    "Component": {
      "type": "object",
      "required": ["component_id", "name", "type", "technology", "responsibilities"],
      "properties": {
        "component_id": { "type": "string", "pattern": "^[A-Z][a-zA-Z0-9]*$" },
        "name": { "type": "string" },
        "type": { "type": "string", "enum": ["Controller", "Service", "Repository", "DomainService", "Factory", "Gateway", "Config", "Entity", "ValueObject", "Mapper", "Middleware", "EventHandler"] },
        "technology": { "type": "string" },
        "responsibilities": { "type": "string" },
        "code_path": { "type": "string" },
        "group": { "type": "string" },
        "interfaces": {
          "type": "array",
          "items": { "$ref": "#/definitions/ComponentInterface" }
        }
      }
    },
    "ComponentInterface": {
      "type": "object",
      "required": ["interface_id", "method", "path"],
      "properties": {
        "interface_id": { "type": "string", "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$" },
        "method": { "type": "string", "enum": ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "MESSAGE", "EVENT"] },
        "path": { "type": "string" },
        "description": { "type": "string" },
        "operation_id": { "type": "string", "pattern": "^[a-z][a-zA-Z0-9]*$" },
        "tags": { "type": "array", "items": { "type": "string" } }
      }
    },
    "APIDesignBinding": {
      "type": "object",
      "required": ["level", "component_id", "container_id", "interfaces"],
      "properties": {
        "level": { "const": "L3" },
        "component_id": { "type": "string" },
        "container_id": { "type": "string" },
        "interfaces": {
          "type": "array",
          "minItems": 1,
          "items": { "$ref": "#/definitions/APIInterface" }
        }
      }
    },
    "APIInterface": {
      "type": "object",
      "required": ["interface_id", "method", "path", "summary", "operation_id"],
      "properties": {
        "interface_id": { "type": "string", "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$" },
        "method": { "type": "string", "enum": ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"] },
        "path": { "type": "string", "pattern": "^/.*[^/]$" },
        "summary": { "type": "string" },
        "operation_id": { "type": "string", "pattern": "^[a-z][a-zA-Z0-9]*$" },
        "tags": { "type": "array", "items": { "type": "string" } },
        "request_schema": { "$ref": "#/definitions/SchemaRef" },
        "response_schema": { "$ref": "#/definitions/SchemaRef" },
        "auth_required": { "type": "boolean", "default": true },
        "rate_limit": { "type": "string" },
        "idempotency_key": { "type": "boolean", "default": false },
        "deprecated": { "type": "boolean", "default": false }
      }
    },
    "SchemaRef": {
      "type": "object",
      "required": ["ref"],
      "properties": {
        "ref": { "type": "string" },
        "content_type": { "type": "string", "default": "application/json" },
        "required": { "type": "array", "items": { "type": "string" } }
      }
    },
    "DBDesignBinding": {
      "type": "object",
      "required": ["level", "container_id", "storage_type", "tables"],
      "properties": {
        "level": { "const": "L2" },
        "container_id": { "type": "string" },
        "storage_type": { "type": "string", "enum": ["Relational", "Document", "KeyValue", "Graph", "TimeSeries", "ColumnFamily", "SearchEngine"] },
        "tables": {
          "type": "array",
          "minItems": 1,
          "items": { "$ref": "#/definitions/Table" }
        }
      }
    },
    "Table": {
      "type": "object",
      "required": ["table_id", "table_name"],
      "properties": {
        "table_id": { "type": "string", "pattern": "^[a-z][a-z0-9_]*$" },
        "table_name": { "type": "string" },
        "entity_map": { "type": "string" },
        "engine": { "type": "string" },
        "charset": { "type": "string" },
        "description": { "type": "string" },
        "columns": {
          "type": "array",
          "items": { "$ref": "#/definitions/Column" }
        },
        "indexes": {
          "type": "array",
          "items": { "$ref": "#/definitions/Index" }
        },
        "foreign_keys": {
          "type": "array",
          "items": { "$ref": "#/definitions/ForeignKey" }
        }
      }
    },
    "Column": {
      "type": "object",
      "required": ["column_name", "data_type"],
      "properties": {
        "column_name": { "type": "string", "pattern": "^[a-z][a-z0-9_]*$" },
        "data_type": { "type": "string" },
        "nullable": { "type": "boolean", "default": true },
        "default_value": { "type": "string" },
        "index_type": { "type": "string", "enum": ["BTREE", "HASH", "FULLTEXT", "GIN", "GIST", "NONE"] },
        "comment": { "type": "string" },
        "attribute_map": { "type": "string", "pattern": "^[A-Z][a-zA-Z0-9]*\\.[a-z][a-zA-Z0-9]*$" }
      }
    },
    "Index": {
      "type": "object",
      "required": ["name", "columns"],
      "properties": {
        "name": { "type": "string" },
        "type": { "type": "string" },
        "columns": { "type": "array", "items": { "type": "string" } },
        "unique": { "type": "boolean", "default": false }
      }
    },
    "ForeignKey": {
      "type": "object",
      "required": ["name", "column", "ref_table", "ref_column"],
      "properties": {
        "name": { "type": "string" },
        "column": { "type": "string" },
        "ref_table": { "type": "string" },
        "ref_column": { "type": "string" },
        "on_delete": { "type": "string", "enum": ["CASCADE", "SET NULL", "RESTRICT", "NO ACTION"] },
        "on_update": { "type": "string", "enum": ["CASCADE", "SET NULL", "RESTRICT", "NO ACTION"] }
      }
    }
  }
}
```

---

## 七、校验规则汇总

### 7.1 阻断级校验（BLOCKER）

| 规则 ID | 规则描述 | 失败处理 |
|:--------|:---------|:---------|
| `C4-VAL-001` | `c4_binding` 缺失（架构类文档） | 拒绝入库，返回错误码 40001 |
| `C4-VAL-002` | `level` 与 `doc_type` 不匹配 | 拒绝入库，返回错误码 40002 |
| `C4-VAL-003` | `system_id` / `container_id` / `component_id` 重复 | 拒绝入库 |
| `C4-VAL-004` | `container_id` 在 L2 基线中不存在 | 拒绝入库，标记为 draft |
| `C4-VAL-005` | `component_id` 在 L3 基线中不存在 | 拒绝入库，标记为 draft |
| `C4-VAL-006` | `@C4-` 标签引用的 ID 在 `c4_binding` 中不存在 | 拒绝入库 |
| `C4-VAL-007` | `interface_id` 在组件内重复 | 拒绝入库 |
| `C4-VAL-008` | `table_id` 全局重复 | 拒绝入库 |

### 7.2 告警级校验（WARNING）

| 规则 ID | 规则描述 | 失败处理 |
|:--------|:---------|:---------|
| `C4-WARN-001` | `external_systems` 非空但正文中无 `@C4-L1-System` 标签 | 告警"孤立外部系统" |
| `C4-WARN-002` | `entity_map` 在 `DOMAIN_MODEL` 中不存在 | 告警"表无领域来源" |
| `C4-WARN-003` | `attribute_map` 在对应实体中不存在 | 告警"字段无属性来源" |
| `C4-WARN-004` | `code_path` 对应的文件不存在 | 标记为 `stale` |
| `C4-WARN-005` | `technology` 不在组织技术栈白名单中 | 提示"非标准技术栈" |

### 7.3 提示级校验（INFO）

| 规则 ID | 规则描述 | 失败处理 |
|:--------|:---------|:---------|
| `C4-INFO-001` | `ports` 未定义（Backend 类型容器） | 提示"建议声明服务端口" |
| `C4-INFO-002` | `group` 未定义（容器数 > 5 时） | 提示"建议按业务域分组" |
| `C4-INFO-003` | `url` 未定义 | 提示"可补充架构决策记录链接" |

---

## 八、完整示例

### 8.1 PRD 示例

```yaml
---
doc_type: "PRD"
fragment_id: "prd-sdlc-visualizer-000"
title: "SDLC Visualizer 概要需求"
version: "1.0.0"
version_type: "BASELINE"
author: "agent-pm"
tags: ["sdlc", "visualizer", "p0"]
status: "FROZEN"
iteration: "sdlc-visualizer"
dependencies:
  - fragment_id: "brainstorm-sdlc-visualizer-001"
    version: "1.0.0"
c4_binding:
  level: "L1"
  system_id: "sdlc-visualizer"
  system_name: "SDLC Visualizer"
  external_systems:
    - id: "kimi-cli"
      name: "Kimi CLI"
      description: "AI 执行引擎，本地调用"
      relation: "触发 Skill 执行，获取产物"
      interface_type: "CLI"
      location: "External"
    - id: "openui-docker"
      name: "OpenUI Docker"
      description: "高保真原型渲染服务"
      relation: "上传草图，获取高保真原型"
      interface_type: "HTTP"
      location: "External"
  actors:
    - id: "developer"
      name: "开发者"
      role_type: "PRIMARY"
      description: "使用 AI 辅助开发的超级个体"
      location: "Internal"
    - id: "tech-lead"
      name: "Tech Lead"
      role_type: "SECONDARY"
      description: "审批 Gate，技术决策"
      location: "Internal"
    - id: "cron-job"
      name: "定时任务"
      role_type: "SYSTEM"
      description: "定时扫描风险预警、Timebox 到期检查"
      location: "Internal"
---
```

### 8.2 ARCH 示例

```yaml
---
doc_type: "ARCH"
fragment_id: "arch-sdlc-visualizer-001"
title: "SDLC Visualizer 架构核心"
version: "1.0.0"
version_type: "BASELINE"
author: "agent-architect"
tags: ["architecture", "p0"]
status: "FROZEN"
iteration: "sdlc-visualizer"
dependencies:
  - fragment_id: "prd-sdlc-visualizer-000"
    version: "1.0.0"
c4_binding:
  level: "L2"
  containers:
    - container_id: "web-frontend"
      name: "Web Frontend"
      type: "Frontend"
      technology: "React 19 + TypeScript 5.6 + Vite 6"
      responsibilities: "用户交互层，SDLC 画布渲染，产物浏览器"
      deployment_target: "Browser"
      ports: ["5173"]
      tags: ["Frontend", "Web", "Critical Path"]
      group: "用户接入层"
    - container_id: "api-service"
      name: "API Service"
      type: "Backend"
      technology: "FastAPI 0.115 + Python 3.11 + SQLAlchemy 2.0"
      responsibilities: "业务逻辑与领域服务，REST API + SSE"
      deployment_target: "Docker"
      ports: ["8000"]
      tags: ["Backend", "API", "Critical Path"]
      group: "服务层"
    - container_id: "sqlite"
      name: "SQLite"
      type: "Database"
      technology: "SQLite 3.39+"
      responsibilities: "本地关系型数据持久化"
      deployment_target: "本地文件"
      tags: ["Database"]
      group: "数据层"
    - container_id: "redis"
      name: "Redis"
      type: "Cache"
      technology: "Redis 7+"
      responsibilities: "编译缓存、版本链缓存"
      deployment_target: "Docker"
      ports: ["6379"]
      tags: ["Cache"]
      group: "数据层"
  container_relations:
    - source: "web-frontend"
      target: "api-service"
      protocol: "HTTPS/REST + SSE"
      description: "前端调用后端 API，SSE 接收实时状态推送"
      interaction_style: "Synchronous"
      technology: "HTTPS/REST"
    - source: "api-service"
      target: "sqlite"
      protocol: "SQLAlchemy/SQLite"
      description: "读写业务数据"
      interaction_style: "Synchronous"
      technology: "SQLite"
    - source: "api-service"
      target: "redis"
      protocol: "Redis Protocol"
      description: "读写编译缓存"
      interaction_style: "Synchronous"
      technology: "Redis"
---
```

### 8.3 API_DESIGN 示例

```yaml
---
doc_type: "API_DESIGN"
fragment_id: "api-sdlc-visualizer-001"
title: "项目工作台 API 契约"
version: "1.0.0"
version_type: "BASELINE"
author: "agent-developer"
tags: ["api", "project-dashboard", "p0"]
status: "FROZEN"
iteration: "sdlc-visualizer"
dependencies:
  - fragment_id: "arch-sdlc-visualizer-001"
    version: "1.0.0"
  - fragment_id: "detail-sdlc-visualizer-001"
    version: "1.0.0"
c4_binding:
  level: "L3"
  component_id: "ProjectController"
  container_id: "api-service"
  interfaces:
    - interface_id: "create-project"
      method: "POST"
      path: "/api/v1/projects"
      summary: "创建项目"
      operation_id: "createProject"
      tags: ["Project"]
      request_schema:
        ref: "ProjectCreateDTO"
        content_type: "application/json"
        required: ["project_name", "application_id", "template_level"]
      response_schema:
        ref: "ProjectResponseDTO"
        content_type: "application/json"
        status_codes: [201, 400, 409, 422]
      auth_required: false
      rate_limit: "100/min"
      idempotency_key: true
      deprecated: false
    - interface_id: "list-projects"
      method: "GET"
      path: "/api/v1/projects"
      summary: "查询项目列表"
      operation_id: "listProjects"
      tags: ["Project"]
      request_schema:
        ref: "ProjectFilterDTO"
        content_type: "application/json"
      response_schema:
        ref: "PaginatedProjectListDTO"
        content_type: "application/json"
        status_codes: [200]
      auth_required: false
      rate_limit: "200/min"
---
```

---

## 九、版本演进

| 版本 | 日期 | 变更内容 |
|:-----|:-----|:---------|
| v1.0.0 | 2026-06-10 | 初始版本，覆盖 PRD / DOMAIN_MODEL / ARCH / DETAIL_DESIGN / API_DESIGN / DB_DESIGN 六类文档的 C4 绑定 Schema |
| v1.1.0（计划） | - | 增加 DeploymentView 绑定（部署节点、容器实例、健康检查） |
| v1.2.0（计划） | - | 增加 DynamicView 绑定（动态视图、时序交互） |
| v1.3.0（计划） | - | 增加 FilteredView 绑定（基于标签的过滤视图） |

---

## 十、参考资源

1. **C4 Model 官方规范**：https://c4model.com/
2. **Structurizr DSL 文档**：https://docs.structurizr.com/dsl
3. **Structurizr JSON Schema（OpenAPI 3.0）**：https://github.com/structurizr/structurizr/tree/main/structurizr-json
4. **Arsitect C4 文档规则集**：`docs/ref-doc/C4-doc-rules.md`
5. **Arsitect 文档管理设计**：`docs/doc-management-design.md`
