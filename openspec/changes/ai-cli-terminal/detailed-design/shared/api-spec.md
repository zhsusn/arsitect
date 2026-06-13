---
doc_type: "DETAIL_DESIGN"
fragment_id: "dd-ai-cli-terminal-shared-api"
title: "AI CLI 终端 - 共享 API 契约"
version: "1.0.0"
status: "DRAFT"
iteration: "ai-cli-terminal"
dependencies:
  - fragment_id: "dd-ai-cli-terminal-shared"
    version: "1.0.0"
c4_binding:
  level: "L3"
  container: "ai-cli-terminal"
  interface_type: "openapi"
---

# AI CLI 终端 - 共享 API 契约 {#sec-shared-api}

## 1. 概述 {#sec-overview}

本文档定义 `ai-cli-terminal` 各模块共享的数据模型与错误响应格式。所有 HTTP API 前缀为 `/api/v1`。

## 2. 共享 Schema {#sec-schemas}

### 2.1 CliSession {#sec-schema-cli-session}

```yaml
CliSession:
  type: object
  required:
    - id
    - project_id
    - user_id
    - mode
    - status
    - created_at
  properties:
    id:
      type: string
      description: 会话唯一标识
      example: "CLI-01928374-5566-7788-99aa-bbccddeeff00"
    project_id:
      type: string
      description: 关联项目 ID
    user_id:
      type: string
      description: 创建用户 ID
    mode:
      type: string
      enum: [bug, arch]
      description: 当前工作模式
    status:
      type: string
      enum: [active, paused, closed]
      description: 会话状态
    created_at:
      type: string
      format: date-time
    closed_at:
      type: string
      format: date-time
      nullable: true
```

### 2.2 CliMessage {#sec-schema-cli-message}

```yaml
CliMessage:
  type: object
  required:
    - id
    - session_id
    - message_type
    - sequence_no
    - created_at
  properties:
    id:
      type: string
    session_id:
      type: string
    message_type:
      type: string
      enum: [user, ai, system, error, success, card, progress]
    content:
      type: string
      nullable: true
    card_data:
      type: object
      nullable: true
    metadata:
      type: object
      nullable: true
    sequence_no:
      type: integer
    created_at:
      type: string
      format: date-time
```

### 2.3 CliCard {#sec-schema-cli-card}

```yaml
CliCard:
  type: object
  required:
    - type
    - data
    - actions
  properties:
    type:
      type: string
      enum: [bug-report, fix-proposal, arch-decision, progress, confirm]
    data:
      type: object
    actions:
      type: array
      items:
        type: object
        required: [label, command]
        properties:
          label:
            type: string
          command:
            type: string
          style:
            type: string
            enum: [primary, danger, default]
```

### 2.4 Error Response {#sec-schema-error}

```yaml
ErrorResponse:
  type: object
  required:
    - code
    - message
  properties:
    code:
      type: string
      example: "SESSION_NOT_FOUND"
    message:
      type: string
      example: "会话已失效，请重新创建"
    detail:
      type: object
      nullable: true
```

## 3. 共享错误码 {#sec-error-codes}

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| SESSION_NOT_FOUND | 404 | 会话不存在或已关闭 |
| SESSION_CLOSED | 409 | 会话已关闭，禁止操作 |
| INVALID_MODE | 400 | 模式只能是 bug 或 arch |
| UNAUTHORIZED | 401 | 用户未登录 |
| FORBIDDEN | 403 | 用户无权限 |
| AI_TIMEOUT | 504 | AI 调用超时 |
| EXEC_FAILED | 500 | 执行引擎失败 |
| RATE_LIMITED | 429 | 请求过于频繁 |

## 4. WebSocket 协议 {#sec-websocket}

### 4.1 连接地址 {#sec-ws-url}

```
ws://host/api/v1/cli/ws/{sessionId}
```

### 4.2 客户端消息 {#sec-ws-client}

```yaml
CliRequest:
  type: object
  required: [type, sessionId]
  properties:
    type:
      type: string
      enum: [command, input, action, abort, ping]
    sessionId:
      type: string
    payload:
      type: object
      properties:
        text:
          type: string
        command:
          type: string
        actionType:
          type: string
        metadata:
          type: object
```

### 4.3 服务端消息 {#sec-ws-server}

```yaml
CliResponse:
  type: object
  required: [type, sessionId, timestamp]
  properties:
    type:
      type: string
      enum: [text, card, progress, error, done, prompt, pong]
    sessionId:
      type: string
    payload:
      type: object
      properties:
        text:
          type: string
        card:
          $ref: '#/components/schemas/CliCard'
        progress:
          type: object
          properties:
            current:
              type: integer
            total:
              type: integer
            label:
              type: string
        error:
          $ref: '#/components/schemas/ErrorResponse'
    timestamp:
      type: integer
      description: Unix 毫秒时间戳
```
