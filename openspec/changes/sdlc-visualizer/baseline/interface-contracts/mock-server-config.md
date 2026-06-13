---
doc_type: API_DESIGN
fragment_id: api-design-sdlc-visualizer-404
title: Mock Server Configuration
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
c4_binding:
  level: L3
---

# Mock Server Configuration


> **C4 绑定引用**：
> - `@C4-L2-Container:frontend-spa`

## 方案一：Prism（推荐） {#sec-u65b9u6848yiprismtuiu8350}
```bash
# 安装
npm install -g @stoplight/prism-cli

# 启动 Mock 服务
npx @stoplight/prism-cli mock interface-contracts/openapi.yaml -p 4010
```

前端接入示例：
```typescript
const API_BASE = 'http://localhost:4010/api/v1';
fetch(`${API_BASE}/health`).then(r => r.json());
```

## 方案二：JSON Server（备选） {#sec-u65b9u6848erjson-serverbeixuan}
```bash
npx json-server --watch interface-contracts/mock-data.json --port 4010
```

## CORS 配置 {#sec-cors-peizhi}
Prism 默认允许所有来源。如需限制：
```bash
npx @stoplight/prism-cli mock interface-contracts/openapi.yaml -p 4010 --cors
```

## 延迟模拟 {#sec-yanchimou62df}
在 Prism 中可通过 `--delay` 参数模拟网络延迟：
```bash
npx @stoplight/prism-cli mock interface-contracts/openapi.yaml -p 4010 --delay 500
```

## 鉴权绕过 {#sec-u9274quanu7ed5guo}
MVP 阶段 Mock 服务不校验 Bearer Token，所有接口公开访问。
P1 阶段需配置 `Authorization: Bearer <token>` Header。
