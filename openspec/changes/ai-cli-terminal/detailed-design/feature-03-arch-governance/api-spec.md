---
doc_type: "DETAIL_DESIGN"
fragment_id: "dd-ai-cli-terminal-arch-governance-api"
title: "AI CLI 终端 - 架构治理模块 API 契约"
version: "1.0.0"
status: "DRAFT"
iteration: "ai-cli-terminal"
dependencies:
  - fragment_id: "dd-ai-cli-terminal-arch-governance"
    version: "1.0.0"
c4_binding:
  level: "L3"
  container: "ai-cli-terminal"
  component: "arch-governance"
  interface_type: "openapi"
---

# AI CLI 终端 - 架构治理模块 API 契约 {#sec-arch-governance-api}

## 1. 端点清单 {#sec-endpoints}

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/arch/scan` | 触发架构扫描 |
| GET | `/api/v1/arch/issues` | 查询治理项列表 |
| GET | `/api/v1/arch/issues/{issue_id}` | 获取治理项详情 |
| POST | `/api/v1/arch/issues/{issue_id}/plan` | 生成治理方案 |
| POST | `/api/v1/arch/issues/{issue_id}/execute` | 执行重构 |
| POST | `/api/v1/arch/issues/{issue_id}/skip` | 跳过治理项 |
| GET | `/api/v1/arch/rules` | 获取扫描规则配置 |
| PUT | `/api/v1/arch/rules` | 更新扫描规则配置 |

## 2. OpenAPI 3.1 定义 {#sec-openapi}

```yaml
openapi: 3.1.0
info:
  title: AI CLI Terminal - Arch Governance API
  version: 1.0.0
paths:
  /api/v1/arch/scan:
    post:
      tags: [arch]
      summary: 触发架构扫描
      operationId: scanArchIssues
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [project_id, session_id]
              properties:
                project_id:
                  type: string
                session_id:
                  type: string
                rules:
                  type: array
                  items:
                    type: string
                  description: 指定启用的规则 ID 列表，为空则使用默认规则
      responses:
        '202':
          description: 扫描已接受，结果通过 WebSocket 推送
          content:
            application/json:
              schema:
                type: object
                properties:
                  scan_id:
                    type: string
                  status:
                    type: string

  /api/v1/arch/issues:
    get:
      tags: [arch]
      summary: 查询治理项列表
      operationId: listArchIssues
      parameters:
        - name: project_id
          in: query
          required: true
          schema:
            type: string
        - name: status
          in: query
          schema:
            type: string
            enum: [detected, planned, executed, verified, closed, skipped]
        - name: severity
          in: query
          schema:
            type: string
            enum: [critical, warning, info]
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
                      $ref: '#/components/schemas/ArchIssue'

  /api/v1/arch/issues/{issue_id}:
    get:
      tags: [arch]
      summary: 获取治理项详情
      operationId: getArchIssue
      parameters:
        - name: issue_id
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
                $ref: '#/components/schemas/ArchIssue'
        '404':
          description: 治理项不存在

  /api/v1/arch/issues/{issue_id}/plan:
    post:
      tags: [arch]
      summary: 生成治理方案
      operationId: generateArchPlan
      parameters:
        - name: issue_id
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
                $ref: '#/components/schemas/ArchIssue'

  /api/v1/arch/issues/{issue_id}/execute:
    post:
      tags: [arch]
      summary: 执行重构
      operationId: executeArchGovernance
      parameters:
        - name: issue_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: 执行结果
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ExecResult'

  /api/v1/arch/issues/{issue_id}/skip:
    post:
      tags: [arch]
      summary: 跳过治理项
      operationId: skipArchIssue
      parameters:
        - name: issue_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: 已跳过
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ArchIssue'

  /api/v1/arch/rules:
    get:
      tags: [arch]
      summary: 获取扫描规则配置
      operationId: listArchRules
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/ScanRule'
    put:
      tags: [arch]
      summary: 更新扫描规则配置
      operationId: updateArchRules
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/ScanRule'
      responses:
        '200':
          description: 更新成功

components:
  schemas:
    ArchIssue:
      type: object
      required:
        - id
        - project_id
        - session_id
        - issue_type
        - severity
        - title
        - status
      properties:
        id:
          type: string
        project_id:
          type: string
        session_id:
          type: string
        issue_type:
          type: string
        severity:
          type: string
          enum: [critical, warning, info]
        rule_id:
          type: string
        title:
          type: string
        description:
          type: string
          nullable: true
        location:
          type: string
          nullable: true
        impact_analysis:
          type: string
          nullable: true
        governance_plan:
          type: string
          nullable: true
        refactor_diff:
          type: string
          nullable: true
        review_points:
          type: array
          items:
            type: string
        status:
          type: string
          enum: [detected, planned, executed, verified, closed, skipped]
        executed_at:
          type: string
          format: date-time
          nullable: true
        adr_id:
          type: string
          nullable: true
        created_at:
          type: string
          format: date-time
    ScanRule:
      type: object
      required: [rule_id, name, enabled, severity]
      properties:
        rule_id:
          type: string
        name:
          type: string
        description:
          type: string
        enabled:
          type: boolean
        severity:
          type: string
          enum: [critical, warning, info]
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
| `command` | `scan arch` | 触发扫描 |
| `action` | `fix {index}` | 选择治理项 |
| `action` | `Y` / `N` | 确认或跳过方案 |

### 3.2 服务端消息 {#sec-server}

| type | 说明 |
|------|------|
| `progress` | 扫描进度 |
| `card` | 治理项列表 / 治理方案卡片 |
| `text` | 执行日志 |
| `done` | 完成 |
