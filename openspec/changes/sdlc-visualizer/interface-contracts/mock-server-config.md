# Mock Server Configuration

## 方案一：Prism（推荐）

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

## 方案二：JSON Server（备选）

```bash
npx json-server --watch interface-contracts/mock-data.json --port 4010
```

## CORS 配置

Prism 默认允许所有来源。如需限制：
```bash
npx @stoplight/prism-cli mock interface-contracts/openapi.yaml -p 4010 --cors
```

## 延迟模拟

在 Prism 中可通过 `--delay` 参数模拟网络延迟：
```bash
npx @stoplight/prism-cli mock interface-contracts/openapi.yaml -p 4010 --delay 500
```

## 鉴权绕过

MVP 阶段 Mock 服务不校验 Bearer Token，所有接口公开访问。
P1 阶段需配置 `Authorization: Bearer <token>` Header。
