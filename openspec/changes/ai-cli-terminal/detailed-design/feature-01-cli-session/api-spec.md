---
doc_type: "DETAIL_DESIGN"
fragment_id: "dd-ai-cli-terminal-cli-session-api"
title: "AI CLI 终端 - CLI 会话管理 API 契约"
version: "1.0.0"
status: "DRAFT"
iteration: "ai-cli-terminal"
dependencies:
  - fragment_id: "dd-ai-cli-terminal-cli-session"
    version: "1.0.0"
c4_binding:
  level: "L3"
  container: "ai-cli-terminal"
  component: "cli-session"
  interface_type: "openapi"
---

# AI CLI 终端 - CLI 会话管理 API 契约 {#sec-cli-session-api}

## 1. 端点清单 {#sec-endpoints}

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/cli/sessions` | 创建会话 |
| GET | `/api/v1/cli/sessions/{session_id}/history` | 获取会话历史消息 |
| POST | `/api/v1/cli/sessions/{session_id}/close` | 关闭会话 |
| POST | `/api/v1/cli/sessions/{session_id}/mode` | 切换模式 |
| WS | `/api/v1/cli/ws/{session_id}` | WebSocket 长连接 |

## 2. OpenAPI 3.1 定义 {#sec-openapi}

```yaml
openapi: 3.1.0
info:
  title: AI CLI Terminal - Session API
  version: 1.0.0
paths:
  /api/v1/cli/sessions:
    post:
      tags: [cli]
      summary: 创建 AI CLI 会话
      operationId: createCliSession
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [project_id]
              properties:
                project_id:
                  type: string
                mode:
                  type: string
                  enum: [bug, arch]
                  default: bug
      responses:
        '201':
          description: 创建成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CliSession'
        '401':
          description: 未登录
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/cli/sessions/{session_id}/history:
    get:
      tags: [cli]
      summary: 获取会话历史消息
      operationId: getCliSessionHistory
      parameters:
        - name: session_id
          in: path
          required: true
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            default: 10
            maximum: 100
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
                      $ref: '#/components/schemas/CliMessage'
        '404':
          description: 会话不存在
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/cli/sessions/{session_id}/close:
    post:
      tags: [cli]
      summary: 关闭会话
      operationId: closeCliSession
      parameters:
        - name: session_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: 关闭成功
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                  session_id:
                    type: string
        '404':
          description: 会话不存在
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/cli/sessions/{session_id}/mode:
    post:
      tags: [cli]
      summary: 切换会话模式
      operationId: switchCliSessionMode
      parameters:
        - name: session_id
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
              required: [mode]
              properties:
                mode:
                  type: string
                  enum: [bug, arch]
      responses:
        '200':
          description: 切换成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CliSession'
        '400':
          description: 模式无效
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/cli/ws/{session_id}:
    get:
      tags: [cli]
      summary: WebSocket 长连接（非 OpenAPI 标准，仅供参考）
      description: |
        建立 WebSocket 连接后，客户端按 `CliRequest` 格式发送消息，
        服务端按 `CliResponse` 格式推送消息。

components:
  schemas:
    CliSession:
      $ref: '../shared/api-spec.md#/components/schemas/CliSession'
    CliMessage:
      $ref: '../shared/api-spec.md#/components/schemas/CliMessage'
    ErrorResponse:
      $ref: '../shared/api-spec.md#/components/schemas/ErrorResponse'
```

## 3. WebSocket 事件 {#sec-ws-events}

### 3.1 客户端事件 {#sec-client-events}

| type | payload | 说明 |
|------|---------|------|
| `command` | `{ text: string }` | 用户输入命令或文本 |
| `action` | `{ command: string, metadata?: object }` | 卡片按钮触发 |
| `abort` | `{}` | 中止当前 AI 任务 |
| `ping` | `{}` | 心跳 |

### 3.2 服务端事件 {#sec-server-events}

| type | payload | 说明 |
|------|---------|------|
| `text` | `{ text: string }` | 文本输出 |
| `card` | `{ card: CliCard }` | 交互卡片 |
| `progress` | `{ current, total, label }` | 进度更新 |
| `error` | `{ code, message }` | 错误 |
| `done` | `{}` | 任务完成 |
| `pong` | `{}` | 心跳响应 |
