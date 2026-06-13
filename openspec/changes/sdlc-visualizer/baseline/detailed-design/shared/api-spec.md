---
doc_type: API_DESIGN
fragment_id: api-design-sdlc-visualizer-shared-824
title: shared/api-spec.md — 公共 REST 接口规范
version: 1.0.0
version_type: BASELINE
author: agent-migration
tags:
- sdlc-visualizer
- architecture
status: DRAFT
iteration: sdlc-visualizer
dependencies:
- fragment_id: arch-sdlc-visualizer-001
  version: '1.0'
- fragment_id: arch-sdlc-visualizer-002
  version: 1.0.0
- fragment_id: db-design-sdlc-visualizer-shared-607
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat13-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat14-628
  version: 1.0.0
c4_binding:
  level: L3
---

# shared/api-spec.md — 公共 REST 接口规范


> **C4 绑定引用**：
> - `@C4-Interface:GET /api/v1/health`
> - `@C4-Interface:GET /api/v1/history/{app_id}/timeline`
> - `@C4-Interface:GET /api/v1/monitoring/{project_id}/operation-logs`
> - `@C4-Interface:GET /api/v1/search`
> - `@C4-Interface:POST /api/v1/files/upload`
> - `@C4-L2-Container:frontend-spa`
> - `@C4-L2-Container:sqlite-db`

> **说明**：本文件定义被 ≥2 个模块消费的全局公共 REST 接口。模块级接口定义中对这些接口的引用通过本文件实现。

---

## 1. 分页查询规范 {#sec-1-fenyechaxunguifan}
### 1.1 分页请求参数 {#sec-11-fenyeu8bf7qiuu53c2shu}
所有列表查询接口统一使用以下分页参数：

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|:----:|:------:|------|
| `page` | integer | 否 | 1 | 页码，从 1 开始 |
| `page_size` | integer | 否 | 50 | 每页条数，最大 200 |
| `sort_by` | string | 否 | `created_at` | 排序字段 |
| `sort_order` | string | 否 | `desc` | 排序方向：`asc` / `desc` |

### 1.2 分页响应 DTO {#sec-12-fenyeu54cdying-dto}
```typescript
interface PageResponse<T> {
  data: T[];                    -- 当前页数据列表
  total_count: number;          -- 总记录数（不分页）
  page: number;                 -- 当前页码
  page_size: number;            -- 每页条数
  total_pages: number;          -- 总页数（向上取整）
  has_next: boolean;            -- 是否有下一页
  has_previous: boolean;       -- 是否有上一页
}
```

### 1.3 使用本规范的模块接口 {#sec-13-u4f7fyongbenguifandemokuaijie}
| 接口 | 所属模块 | 分页参数 |
|------|----------|----------|
| `GET /api/v1/history/{app_id}/timeline` | DR-013 | `page`, `page_size`, `sort_by` |
| `GET /api/v1/monitoring/{project_id}/operation-logs` | DR-014 | `page`, `page_size` |

---

## 2. 全局搜索接口 {#sec-2-quanu5c40sousuojiekou}
### 2.1 `GET /api/v1/search` {#sec-21-get-apiv1search}
全局跨模块搜索，支持项目、产物、Skill、Gate 等多实体联合搜索。

**Query Params**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|:----:|:----:|
| `q` | string | 是 | 搜索关键词，长度 1-128 |
| `entity_types` | string[] | 否 | 限定搜索实体类型：`project` / `artifact` / `skill` / `gate` |
| `project_id` | string | 否 | 限定搜索范围到指定项目 |

**Response**：`PageResponse<SearchResultDTO>`

```typescript
interface SearchResultDTO {
  result_id: string;
  entity_type: "project" | "artifact" | "skill" | "gate";
  title: string;
  summary: string;              -- 匹配内容摘要（含高亮标记）
  url_path: string;             -- 前端路由路径
  matched_fields: string[];     -- 匹配的字段名列表
  score: number;                -- 匹配得分（用于排序）
}
```

**性能要求**：响应时间 < 500ms（P95，关键词长度 ≤ 10 字符）

> **MVP 说明**：MVP 阶段全局搜索仅支持 SQLite `LIKE` 前缀匹配，P1 阶段升级为全文检索（FTS5）。

---

## 3. 文件上传接口 {#sec-3-wenjianshangchuanjiekou}
### 3.1 `POST /api/v1/files/upload` {#sec-31-post-apiv1filesupload}
通用文件上传接口，支持产物文件、基线快照、报告导出等场景。

**Request**：`multipart/form-data`

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|:----:|:----:|
| `file` | File | 是 | 上传文件，最大 10MB |
| `purpose` | string | 是 | 用途标识：`artifact` / `baseline` / `report` / `avatar` |
| `project_id` | string | 否 | 关联项目标识 |

**Response**：`FileUploadResultDTO`

```typescript
interface FileUploadResultDTO {
  file_id: string;              -- 服务器端文件标识
  file_name: string;
  file_url: string;             -- 访问 URL
  file_size_bytes: number;
  mime_type: string;
  uploaded_at: string;
  expires_at: string | null;    -- 临时文件过期时间
}
```

**错误码**：
- `413`：文件大小超过限制
- `415`：不支持的文件类型
- `400`：`purpose` 参数非法

---

## 4. 统一错误响应格式 {#sec-4-tongyiu9519u8befu54cdyingu683c}
所有接口错误响应统一使用以下格式：

```typescript
interface ApiErrorResponse {
  error_code: string;           -- 机器可读错误码，如 `PROJECT_NOT_FOUND`
  message: string;              -- 人类可读错误描述
  details: Record<string, unknown> | null;  -- 额外上下文信息
  request_id: string;           -- 请求追踪标识
  timestamp: string;            -- ISO 8601 时间戳
}
```

**HTTP 状态码映射**：

| 状态码 | 使用场景 | 示例 error_code |
|--------|----------|----------------|
| `400` | 请求参数校验失败 | `INVALID_PARAMETER`, `VALIDATION_ERROR` |
| `401` | 未认证 | `UNAUTHORIZED` |
| `403` | 权限不足 | `FORBIDDEN`, `INSUFFICIENT_PERMISSION` |
| `404` | 资源不存在 | `PROJECT_NOT_FOUND`, `STAGE_NOT_FOUND` |
| `409` | 资源冲突 | `DUPLICATE_NAME`, `BASELINE_MISSING` |
| `413` | 请求体过大 | `PAYLOAD_TOO_LARGE` |
| `415` | 不支持的媒体类型 | `UNSUPPORTED_MEDIA_TYPE` |
| `422` | 业务逻辑错误 | `GATE_ALREADY_DECIDED`, `STAGE_BLOCKED` |
| `429` | 请求频率限制 | `RATE_LIMITED` |
| `500` | 服务器内部错误 | `INTERNAL_ERROR` |
| `503` | 服务暂时不可用 | `SERVICE_UNAVAILABLE` |

---

## 5. 健康检查接口 {#sec-5-u5065u5eb7jianchajiekou}
### 5.1 `GET /api/v1/health` {#sec-51-get-apiv1health}
系统健康检查，供前端启动时验证后端可用性。

**Response**：

```typescript
interface HealthCheckDTO {
  status: "healthy" | "degraded" | "unhealthy";
  version: string;              -- 后端版本号
  database: "connected" | "disconnected";
  uptime_seconds: number;
  timestamp: string;
}
```

---

## 6. 公共 Header 规范 {#sec-6-u516cgong-header-guifan}
| Header 名 | 类型 | 必填 | 说明 |
|-----------|------|:----:|:----:|
| `X-Request-ID` | string | 否 | 请求追踪标识，前端生成 UUID，用于日志串联 |
| `X-User-Role` | string | 否 | 当前用户角色：`tech_lead` / `developer`（MVP 本地会话） |
| `X-Project-ID` | string | 条件 | 项目级接口必填，用于权限校验和数据范围限定 |

---

## 7. 接口版本策略 {#sec-7-jiekoubanbenceu7565}
- URL 路径版本化：`/api/v1/...`
- 重大变更升级主版本号（`/api/v2/...`）
- 小版本变更通过 `Accept-Version` Header 协商
- 废弃接口保留至少 2 个版本周期，返回 `Deprecation` Header 警告
