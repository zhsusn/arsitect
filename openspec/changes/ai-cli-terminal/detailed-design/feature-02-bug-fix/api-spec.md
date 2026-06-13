---
doc_type: "DETAIL_DESIGN"
fragment_id: "dd-ai-cli-terminal-bug-fix-api"
title: "AI CLI 终端 - Bug 修复模块 API 契约"
version: "1.0.0"
status: "DRAFT"
iteration: "ai-cli-terminal"
dependencies:
  - fragment_id: "dd-ai-cli-terminal-bug-fix"
    version: "1.0.0"
c4_binding:
  level: "L3"
  container: "ai-cli-terminal"
  component: "bug-fix"
  interface_type: "openapi"
---

# AI CLI 终端 - Bug 修复模块 API 契约 {#sec-bug-fix-api}

## 1. 端点清单 {#sec-endpoints}

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/bugs` | 创建 Bug 记录 |
| GET | `/api/v1/bugs` | 查询历史 Bug（支持 signature） |
| GET | `/api/v1/bugs/{bug_id}` | 获取 Bug 详情 |
| POST | `/api/v1/bugs/{bug_id}/execute` | 执行修复方案 |
| POST | `/api/v1/bugs/{bug_id}/ignore` | 忽略修复方案 |

## 2. OpenAPI 3.1 定义 {#sec-openapi}

```yaml
openapi: 3.1.0
info:
  title: AI CLI Terminal - Bug Fix API
  version: 1.0.0
paths:
  /api/v1/bugs:
    post:
      tags: [bugs]
      summary: 创建 Bug 记录
      operationId: createBugRecord
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [project_id, session_id, error_input]
              properties:
                project_id:
                  type: string
                session_id:
                  type: string
                error_input:
                  type: string
                  description: 用户粘贴的原始异常信息
      responses:
        '201':
          description: 创建成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BugRecord'
    get:
      tags: [bugs]
      summary: 查询历史 Bug
      operationId: listBugRecords
      parameters:
        - name: project_id
          in: query
          required: true
          schema:
            type: string
        - name: signature
          in: query
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/BugRecord'

  /api/v1/bugs/{bug_id}:
    get:
      tags: [bugs]
      summary: 获取 Bug 详情
      operationId: getBugRecord
      parameters:
        - name: bug_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BugRecord'
        '404':
          description: Bug 不存在
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/bugs/{bug_id}/execute:
    post:
      tags: [bugs]
      summary: 执行修复方案
      operationId: executeBugFix
      parameters:
        - name: bug_id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                edited_diff:
                  type: string
                  nullable: true
                  description: 用户编辑后的 Diff，为空则使用原始 Diff
      responses:
        '200':
          description: 执行结果
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ExecResult'
        '403':
          description: 权限不足
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '409':
          description: 高风险，建议生成 PR
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/bugs/{bug_id}/ignore:
    post:
      tags: [bugs]
      summary: 忽略修复方案
      operationId: ignoreBugFix
      parameters:
        - name: bug_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: 已忽略
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BugRecord'

components:
  schemas:
    BugRecord:
      type: object
      required:
        - id
        - project_id
        - session_id
        - error_signature
        - error_type
        - error_input
        - status
      properties:
        id:
          type: string
        project_id:
          type: string
        session_id:
          type: string
        error_signature:
          type: string
        error_type:
          type: string
        error_input:
          type: string
        error_stack:
          type: string
          nullable: true
        root_cause:
          type: string
          nullable: true
        affected_files:
          type: array
          items:
            type: string
        fix_diff:
          type: string
          nullable: true
        fix_risk:
          type: string
          enum: [low, medium, high]
        status:
          type: string
          enum: [pending, executed, verified, failed, ignored]
        executed_by:
          type: string
        verified_result:
          type: string
          nullable: true
        similar_bug_id:
          type: string
          nullable: true
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time
    ExecResult:
      type: object
      required: [success]
      properties:
        success:
          type: boolean
        output:
          type: string
          nullable: true
        error:
          type: string
          nullable: true
        branch:
          type: string
          nullable: true
    ErrorResponse:
      $ref: '../shared/api-spec.md#/components/schemas/ErrorResponse'
```

## 3. WebSocket 业务消息 {#sec-ws-messages}

### 3.1 客户端消息 {#sec-client}

| type | command | 说明 |
|------|---------|------|
| `command` | 用户输入文本 | 提交异常信息 |
| `action` | `Y` / `N` / `edit` | 修复方案决策 |

### 3.2 服务端消息 {#sec-server}

| type | 说明 |
|------|------|
| `text` | AI 分析流式文本 |
| `card` | 修复方案卡片 |
| `progress` | 执行进度 |
| `error` | 执行失败 |
| `done` | 修复完成 |
