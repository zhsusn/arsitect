# DR-022：LLM 配置中心（LLM Config Center）模块详细设计

> **模块编号**：DR-022  
> **模块名称**：LLM 配置中心（LLM Config Center）  
> **版本**：v1.0  
> **设计状态**：FROZEN  
> **上游追溯**：DR-022 概要需求（REQ-P0-042：统一配置节点管理、LLM Provider 可配置、LLM 权限可配置）  
> **下游消费**：AI CLI 页面（DR-007）、架构治理自动修复（DR-016）、后续所有需要统一配置管理的模块  
> **变更**：sdlc-visualizer

---

## 1. 背景与目标

当前 Arsitect 的 LLM 配置完全依赖环境变量（`GOVERNANCE_LLM_PROVIDER`、`OPENAI_API_KEY` 等），没有持久化的配置模型，也没有 UI 配置入口。AI CLI 页面虽能切换 provider，但：

- 无法配置 LLM 对文件、终端、外部资源的访问权限；
- 无法按项目/用户/全局分层管理配置；
- 新增配置项需要改表或改 env，扩展性差。

本模块旨在：

1. 设计一个可扩展的**统一配置节点（Config Node）**模型，支持后续所有配置项（LLM、安全、审计、通知等）的集中管理。
2. 在可视化驾驶舱中新增 **“LLM 配置中心”** 页面，管理 LLM Provider 节点与权限策略。
3. 参考 Cursor / Claude Code / Copilot / Cline / Windsurf / Continue.dev 的权限模型，为 AI CLI 和架构治理修复等场景提供文件/终端/外部资源访问控制。

---

## 2. 竞品调研结论

| 产品 | 文件读取 | 文件编辑 | 终端 | 网络/外部资源 | 配置方式 | 默认立场 |
|---|---|---|---|---|---|---|
| **Cursor** | 项目内自动；项目外可配 | 项目内自动；敏感文件询问 | 询问 / 自动运行模式 + allowlist | 搜索允许；浏览器操作询问 | `permissions.json` + IDE 设置 | 读写项目自动；终端/MCP 询问 |
| **Claude Code** | 只读工具自由使用 | 编辑询问；`acceptEdits` 模式可自动 | `allow/ask/deny` 规则 + 命令模式 | `WebFetch/WebSearch` 域名规则 | `settings.json` + `/permissions` | 只读自由；写入/终端/网络询问 |
| **GitHub Copilot Agent** | 通过 agent 工具读取 | 按 glob 的 `chat.tools.edits.autoApprove` | 命令映射 `chat.tools.terminal.autoApprove` | URL allowlist | `.vscode/settings.json` | 终端默认拦截危险命令 |
| **Cline / Roo Code** | 按范围开关 | 按范围开关 | 安全命令 / 所有命令 / YOLO | 浏览器开关 | 扩展面板开关 + `.clinerules` | 读项目自动；其余询问 |
| **Windsurf / Cascade** | 索引/自动 | 编辑允许；创建文件开关 | Manual / Semi-auto / Turbo / Custom | 浏览器预览 + 网络搜索 | `.windsurfrules` + 设置面板 | 终端默认询问 |
| **Continue.dev** | `allow` | `ask` | `ask` | `Fetch` `ask` | `permissions.yaml` + TUI | 只读自动；写入/执行询问 |

### 对 Arsitect 的启示

1. **三级权限模型**：`allow / ask / deny`，按 `deny → ask → allow` 优先级求值。
2. **作用域分层**：managed（IT 策略）> local > project > user，低层不可覆盖高层 deny。
3. **分类控制**：文件读、文件写、终端执行、WebFetch/WebSearch、外部 API。
4. **模式切换**：`readonly`（需求/设计阶段）、`accept_edits`（编码阶段）、`auto`（受信重复任务）。
5. **审计与钩子**：每个 tool 调用记录决策来源；支持 `PreToolUse` 钩子拦截高危动作。
6. **与人工闸门结合**：发布、schema 迁移、合并等必须走 Gate 1–3，不能用简单开关替代。

---

## 3. 设计原则

1. **统一配置节点**：所有配置项抽象为 `ConfigNode`，通过 `node_type` 区分，避免为每个配置新建表。
2. **分层作用域**：`global` → `project` → `user`，并预留 `managed` 策略层。
3. **最小可用**：先实现 LLM Provider 与 LLM Permission 两类节点，后续通过 `node_type` 扩展。
4. **安全默认**：文件读取项目内允许；写入、终端、外部网络默认 `ask`；敏感路径默认 `deny`。
5. **MCP 无关**：不依赖 MCP，Arsitect 的 tool 权限由自身配置节点管控。
6. **审计闭环**：配置变更和权限决策写入操作日志，便于追溯。

---

## 4. 架构组件与职责

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LLM Config Center (DR-022)                        │
│  ┌─────────────────────┐  ┌──────────────────────────────────────┐  │
│  │ ProviderNodePanel   │  │ PermissionPolicyPanel                 │  │
│  │  Provider CRUD      │  │  allow/ask/deny rule editor           │  │
│  │  Test connection    │  │  Effective policy preview             │  │
│  └──────────┬──────────┘  └──────────────┬─────────────────────────┘  │
│             │                            │                            │
│  ┌──────────┴────────────────────────────┴────────────────────────┐  │
│  │                      ConfigNodeService (frontend)               │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                              │ REST                                   │
│  ┌───────────────────────────┴────────────────────────────────────┐  │
│  │              /api/v1/config/nodes  +  /resolve                 │  │
│  │              /api/v1/config/check-permission                   │  │
│  └───────────────────────────┬────────────────────────────────────┘  │
│                              │                                        │
│  ┌───────────────────────────┴────────────────────────────────────┐  │
│  │                         ConfigService                           │  │
│  │  - CRUD + scope resolution (global/project/user/managed)        │  │
│  │  - default provider fallback to env vars                        │  │
│  └───────────────────────────┬────────────────────────────────────┘  │
│                              │                                        │
│  ┌───────────────────────────┴────────────────────────────────────┐  │
│  │                    LLMPermissionService                         │  │
│  │  - rule matching (glob for path/command/domain)                 │  │
│  │  - builtin deny list for sensitive paths & dangerous commands   │  │
│  └───────────────────────────┬────────────────────────────────────┘  │
│                              │                                        │
│  ┌───────────────────────────┴────────────────────────────────────┐  │
│  │              Future consumers: AgentRouter, ArchGovernance, ... │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

| 组件 | 类型 | 职责 |
|------|------|------|
| `LlmConfig` | 页面 | 配置中心入口，Provider / Permission Tab 切换 |
| `ProviderNodePanel` | 页面组件 | LLM Provider 节点的增删改查、克隆、连通性测试 |
| `PermissionPolicyPanel` | 页面组件 | 权限策略编辑器，维护 allow/ask/deny 规则 |
| `ConfigNodeService` | 前端 Service | 封装 `/v1/config/*` REST API |
| `ConfigService` | 后端 Service | ConfigNode CRUD、作用域合并、生效配置解析 |
| `LLMPermissionService` | 后端 Service | 权限规则求值、内置安全策略 |
| `config_nodes` | API Router | RESTful 接口与权限检查接口 |

---

## 5. 数据模型

### 5.1 统一配置节点 `ConfigNode`

```python
class ConfigNode(Base):
    __tablename__ = "config_nodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    node_type: Mapped[str] = mapped_column(String(50), index=True)
    scope: Mapped[str] = mapped_column(String(20), index=True)       # managed/global/project/user
    scope_target: Mapped[str | None] = mapped_column(String(36), index=True)
    key: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    is_enabled: Mapped[bool] = mapped_column(default=True)
    is_default: Mapped[bool] = mapped_column(default=False)
    priority: Mapped[int] = mapped_column(default=0)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    secret_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_by / updated_by / created_at / updated_at
```

**唯一约束**：`(node_type, scope, scope_target, key)`。

### 5.2 配置节点类型扩展

| node_type | 用途 | config_json 关键字段 |
|---|---|---|
| `llm_provider` | LLM Provider 节点 | `provider`, `api_base`, `model`, `timeout`, `kimi_cli_path` |
| `llm_permission` | LLM 权限策略 | `default_mode`, `rules[]` |
| `security_policy` | 安全策略（预留） | `denied_paths`, `denied_commands`, `denied_domains` |
| `notification` | 通知渠道（预留） | `channel`, `webhook`, `events` |

---

## 6. LLM 权限模型

### 6.1 权限类别

| category | 说明 | 示例 |
|---|---|---|
| `file_read` | 读取文件/目录/Grep/Glob | 读取 `backend/app/main.py` |
| `file_write` | 创建/修改/删除文件 | 写入 `openspec/changes/.../tasks.md` |
| `terminal` | 执行终端/子进程命令 | `pytest`, `npm run build` |
| `web_fetch` | 抓取外部网页/文档 | 读取 MDN、官方文档 |
| `external_api` | 调用外部 API | LLM Provider API、包管理器 API |

### 6.2 规则模型

```json
{
  "node_type": "llm_permission",
  "key": "default-project-policy",
  "config_json": {
    "default_mode": "ask",
    "rules": [
      { "category": "file_read", "decision": "allow", "path": "${PROJECT_ROOT}/**" },
      { "category": "file_write", "decision": "ask", "path": "${PROJECT_ROOT}/openspec/changes/**" },
      { "category": "file_write", "decision": "deny", "path": "**/.env" },
      { "category": "terminal", "decision": "allow", "command": "pytest*" },
      { "category": "terminal", "decision": "deny", "command": "rm -rf*" },
      { "category": "web_fetch", "decision": "ask", "domain": "*" }
    ]
  }
}
```

### 6.3 求值规则

1. 按作用域从高到低收集规则：`managed` > `user` > `project` > `global`。
2. 同作用域内按 `priority` 升序迭代，高优先级覆盖低优先级；同 priority 以最新更新时间覆盖。
3. 对请求匹配规则：先匹配 `deny`，再匹配 `allow`，未命中则返回 `default_mode`。
4. 环境变量占位符（如 `${PROJECT_ROOT}`）在求值时替换。

### 6.4 内置安全策略

默认拒绝以下模式，除非 managed 层显式覆盖：

- 文件：`**/.env`、`**/.ssh/**`、`**/id_rsa*`、`ops/staging-config.yaml`
- 终端：`rm -rf*`、`sudo*`、`eval*`、`curl*|wget*`
- 允许的安全命令：`pytest*`、`npm run *`、`ruff check*`、`git status*`、`git diff*` 等

### 6.5 阶段模式（与 SDLC 12 阶段结合）

| 模式 | 适用阶段 | 效果 |
|---|---|---|
| `readonly` | 需求探索、概要设计、详细设计 | file_read allow；file_write/terminal/web ask |
| `accept_edits` | 编码、单元测试 | 项目内 file_write allow；terminal 仅安全命令 allow |
| `auto` | 受信重复任务 | 按策略自动执行，但仍受 deny 规则约束 |
| `human_gate` | 发布、归档、schema 迁移 | 所有写入/终端操作必须等待 Gate 签字 |

---

## 7. 接口定义

### 7.1 Config Node CRUD

```
GET    /api/v1/config/nodes                    # 列出节点
POST   /api/v1/config/nodes                    # 创建节点
GET    /api/v1/config/nodes/{node_id}          # 获取节点
PUT    /api/v1/config/nodes/{node_id}          # 更新节点
DELETE /api/v1/config/nodes/{node_id}          # 删除节点
POST   /api/v1/config/nodes/{node_id}/clone    # 克隆节点
POST   /api/v1/config/nodes/{node_id}/test     # 测试 provider 连通性
```

### 7.2 生效配置解析

```
POST /api/v1/config/resolve
Body: { "node_type": "llm_permission", "project_id": "...", "user_id": "..." }
Response: { node_type, project_id, user_id, config, source_nodes }
```

### 7.3 权限检查

```
POST /api/v1/config/check-permission
Body: {
  "category": "file_write",
  "path": "backend/app/main.py",
  "project_id": "...",
  "user_id": "..."
}
Response: { category, decision, default_mode, rules[] }
```

### 7.4 默认模板

```
GET /api/v1/config/default-llm-provider
GET /api/v1/config/default-permission-policy
```

---

## 8. 前端页面设计

### 8.1 入口

- 路由：`/settings/llm`
- 导航：侧边栏“平台管理 → LLM 配置”

### 8.2 Provider 节点管理页

- 表格：名称、类型、作用域、是否默认、测试状态、操作
- 表单抽屉：provider 选择、API Base、Model、API Key、Kimi CLI 路径、Timeout、优先级、默认开关
- 操作：测试连接、编辑、克隆、删除

### 8.3 权限策略页

- 策略列表：作用域、默认模式、规则数、操作
- 策略编辑器：
  - 默认模式选择（allow/ask/deny）
  - 规则表格：category、decision、path/command/domain、说明
  - 敏感路径/命令快捷 deny 模板（预留）

### 8.4 与 AI CLI 的联动（下游消费）

- AI CLI 页面顶部的 provider 下拉从当前项目生效的 `llm_provider` 节点读取。
- 当用户触发需要权限的 action 时，若服务端返回 `decision: ask`，前端弹出确认弹窗：
  - 显示操作类型、目标路径、风险等级、规则来源
  - 提供“允许一次 / 始终允许此模式 / 拒绝”

---

## 9. 关键集成点

1. **LLM Provider 工厂**（`backend/app/services/llm/factory.py`）
   - 从 `ConfigService.resolve_llm_provider(project_id, user_id)` 读取默认节点。
   - 保留环境变量作为 fallback。

2. **Agent Router**（`backend/app/services/chat/agent_router.py`）
   - 在调用 read/edit/bash/fetch 工具前，调用 `PermissionService.check()`。
   - 若 `ask`，通过 WebSocket 发送 `permission-request` 卡片。

3. **架构治理修复**（`backend/app/services/arch_governance_service.py`）
   - 修复计划执行前检查 `file_write` 权限。
   - 高危操作（如 `DELETE_FILE`）强制 `ask` 或走 Gate。

4. **文件/终端工具封装**（预留）
   - 后续新增 `app/tools/file_tool.py`、`app/tools/terminal_tool.py`、`app/tools/web_tool.py`。
   - 所有 tool 在入口层统一调用 `PermissionService`。

---

## 10. 实现步骤

### Phase 1：基础配置节点（已完成）
1. 新增 `ConfigNode` 模型与 Alembic 迁移。
2. 实现 `ConfigService`：CRUD、作用域合并、resolve。
3. 实现 `ConfigNode` REST API。
4. 补充单元测试。

### Phase 2：LLM Provider 节点（已完成）
1. 将现有的 env-based provider 配置映射到 `llm_provider` 节点。
2. 修改 LLM 工厂，优先从配置节点解析 provider。
3. 新增 `/api/v1/config/nodes/{id}/test` 连通性测试。

### Phase 3：LLM 权限策略（已完成）
1. 定义 `LLMPermissionService` 与规则求值引擎。
2. 新增 `POST /api/v1/config/check-permission`。
3. 内置安全策略与默认策略模板。

### Phase 4：前端配置页面（已完成）
1. 新增 `frontend/src/pages/LlmConfig/` 页面组件。
2. 新增 `ConfigNodeService` API 封装。
3. 在 `App.tsx` 路由与侧边栏注册 `/settings/llm`。

### Phase 5：AI CLI 联动（待后续实现）
1. Agent Router 在 tool 调用前检查权限，发送 `permission-request` 卡片。
2. 前端 ChatCard 支持 `permission-request` 类型。
3. AI CLI provider 下拉读取配置节点。

---

## 11. 文件清单

### 后端
- `backend/app/models/config_node.py`
- `backend/app/schemas/config_node.py`
- `backend/app/services/config_service.py`
- `backend/app/services/llm_permission_service.py`
- `backend/app/api/v1/config_nodes.py`
- `backend/app/api/v1/router.py`
- `backend/app/models/__init__.py`
- `backend/tests/conftest.py`
- `backend/tests/unit/test_config_service.py`
- `backend/migrations/versions/9ce34a2c3035_add_config_nodes.py`

### 前端
- `frontend/src/services/configNode.ts`
- `frontend/src/pages/LlmConfig/index.tsx`
- `frontend/src/pages/LlmConfig/components/ProviderNodePanel.tsx`
- `frontend/src/pages/LlmConfig/components/PermissionPolicyPanel.tsx`
- `frontend/src/App.tsx`

---

## 12. 测试与验证

- 后端全量单元测试：`738 passed, 2 skipped`
- 后端 lint：`ruff check` 通过
- 前端 lint：`eslint` 通过
- 前端类型检查：`tsc --noEmit` 通过
- 前端生产构建：`vite build` 通过
- 数据库迁移：`alembic upgrade head` 已应用

---

## 13. 风险评估

1. **secret 安全**：第一期使用 JSON 明文存储，`secret_json` 在 API 返回时已脱敏；后续必须接入加密/密钥管理。
2. **性能**：规则求值在每个 tool 调用前进行，需缓存生效配置（TTL 60s，预留）。
3. **向后兼容**：环境变量仍作为最高优先级 fallback，确保现有部署不中断。
4. **权限绕过**：所有 tool 调用必须统一走 `app/tools/*`（后续实现），禁止 LLM provider 直接读写文件系统。
