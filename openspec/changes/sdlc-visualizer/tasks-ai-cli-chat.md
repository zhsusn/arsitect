# AI CLI Kimi 化改造实施任务清单

> 变更：sdlc-visualizer 增量改造
> 目标：将 AI CLI 页面改为 Kimi 风格对话式界面，架构治理修复复用同一 Chat 引擎
> 决策：A（右侧滑出 Chat 面板）/ 不保留旧 Terminal / Kimi CLI 路径通过配置指定 / OpenAI API 预留接口

---

## Phase 1：后端基础设施迁移（LLM Provider 上提 + 模型扩展）

### 1.1 上提 LLM Provider
- [ ] 新建 `backend/app/services/llm/__init__.py`
- [ ] 迁移 `KimiCLIGateway` → `backend/app/services/llm/kimi_cli.py`
- [ ] 迁移 `OpenAILLMGateway` → `backend/app/services/llm/openai.py`
- [ ] 迁移 `NoOpLLMGateway` → `backend/app/services/llm/noop.py`
- [ ] 新增 `backend/app/services/llm/base.py`（抽象基类）
- [ ] 新增 `backend/app/services/llm/factory.py`（`get_llm_provider`）
- [ ] 更新 `backend/app/c4/governance_fix/llm_gateway.py` 为兼容 re-export
- [ ] 更新 `backend/app/services/arch_governance_service.py` 的 import
- [ ] 自测：`pytest backend/tests/unit/services/test_arch_governance_service.py`（如存在）或通过 Python import 检查

### 1.2 扩展 CLI 会话模型
- [ ] 修改 `backend/app/models/cli_session.py`：
  - `CliSession` 新增 `task_mode`（默认 `free-chat`）
  - `CliSession` 新增 `llm_provider`
  - `CliSession` 新增 `context_json`（JSON 类型，默认 `{}`）
- [ ] 新增 `ChatMessage` 模型（如尚未存在可复用的 `CliMessage`）
- [ ] 生成 Alembic 迁移脚本
- [ ] 应用迁移
- [ ] 自测：`alembic upgrade head` 成功，`pytest backend/tests/unit/models/test_cli_session.py` 通过

---

## Phase 2：前端 Chat 基础组件

### 2.1 类型与 Hook
- [ ] 新建 `frontend/src/components/chat/types.ts`
- [ ] 新建 `frontend/src/components/chat/useChatSession.ts`（基于现有 `useCliSession` 升级）
- [ ] 支持消息列表状态、流式追加、卡片动作发送

### 2.2 输入框组件
- [ ] 新建 `frontend/src/components/chat/ChatComposer.tsx`
  - 多行 textarea
  - `/` 技能触发浮层
  - 模型选择器（kimi-cli / openai / arsitect-agent）
  - Agent 模式切换
  - 附件按钮（MVP 仅展示）

### 2.3 消息渲染组件
- [ ] 新建 `frontend/src/components/chat/MessageList.tsx`
- [ ] 新建 `frontend/src/components/chat/MessageItem.tsx`
- [ ] 支持 Markdown、代码块、思考流、AI/User/System 样式区分
- [ ] 新建 `frontend/src/components/chat/MessageActions.tsx`（复制/刷新/点赞/点踩）

### 2.4 卡片组件
- [ ] 新建 `frontend/src/components/chat/ChatCard.tsx`
- [ ] 兼容现有 `CliCard` 数据结构
- [ ] 支持 arch-decision / fix-proposal / confirm 类型

### 2.5 自测
- [ ] `npm run typecheck` 通过
- [ ] `npm run lint` 通过

---

## Phase 3：AI CLI 页面重写

### 3.1 页面结构
- [ ] 重写 `frontend/src/pages/AiCli/index.tsx`
  - 空态首页：居中 Logo + ChatComposer
  - 会话态：MessageList + ChatComposer
- [ ] 支持路由 `/cli` 与 `/cli/s/:sessionId`

### 3.2 路由更新
- [ ] 修改 `frontend/src/App.tsx` 添加 `/cli/s/:sessionId` 路由

### 3.3 后端 Chat API
- [ ] 新建 `backend/app/api/v1/chat.py`
  - `POST /chat/sessions`
  - `GET /chat/sessions/{id}/history`
  - `POST /chat/sessions/{id}/close`
  - `POST /chat/sessions/{id}/mode`
  - `WS /chat/ws/{session_id}`
- [ ] 新增 `backend/app/services/chat_service.py`（会话 CRUD + 消息历史）
- [ ] 新增 `backend/app/services/chat/agent_router.py`（模式路由）
- [ ] 在 `backend/app/api/v1/router.py` 中挂载 `/chat`

### 3.4 自测
- [ ] 前端可创建会话并发送消息
- [ ] WebSocket 能接收 text/thinking/card 消息
- [ ] `npm run typecheck && npm run lint` 通过
- [ ] `pytest backend/tests/unit/api/test_chat.py`（新增）通过

---

## Phase 4：架构治理修复接入 Chat 面板

### 4.1 架构治理页面改造
- [ ] 修改 `frontend/src/pages/ArchGovernance/index.tsx`
  - 点击“修复架构问题”后打开右侧 `ChatSidePanel`
  - 不再弹出 `FixTerminalModal`
- [ ] 新建 `frontend/src/pages/ArchGovernance/components/ChatSidePanel.tsx`

### 4.2 ChatSidePanel 实现
- [ ] 复用 `ChatComposer` / `MessageList` / `ChatCard`
- [ ] 创建 `task_mode=arch-fix` 的会话
- [ ] 自动发送 `apply_arch_fix_plan` 命令并携带 plan

### 4.3 后端修复流程接入 AgentRouter
- [ ] 在 `AgentRouter` 中实现 `arch-fix` 模式路由
- [ ] 调用 `ArchGovernanceService.apply_fix_plan`
- [ ] 复用现有 `handle_change_action` 处理用户确认

### 4.4 移除旧组件
- [ ] 删除 `frontend/src/pages/ArchGovernance/components/FixTerminalModal.tsx`
- [ ] 删除 `frontend/src/components/cli/Terminal.tsx`
- [ ] 清理 `frontend/src/components/cli/` 下不再使用的文件

### 4.5 自测
- [ ] 架构治理页面选择问题 → 生成方案 → Chat 面板出现
- [ ] 卡片正确推送，用户可确认/跳过/编辑
- [ ] 修复完成后面板可关闭并刷新问题列表

---

## Phase 5：自由对话 LLM 调用

### 5.1 LLM Provider 流式聊天
- [ ] 在 `LLMProvider` 抽象中新增 `chat_stream(messages, on_chunk)` 方法
- [ ] `KimiCLIGateway` 实现单轮 prompt 调用
- [ ] `OpenAILLMGateway` 预留接口（返回未配置提示）

### 5.2 AgentRouter 自由对话模式
- [ ] 实现 `free-chat` 模式
- [ ] 组装 system/user prompt
- [ ] 流式返回 `thinking` + `text` 消息

### 5.3 模型选择器生效
- [ ] 前端选择模型后发送到后端
- [ ] 后端根据 `llm_provider` 调用对应 Provider

### 5.4 自测
- [ ] 自由对话可收到流式回复
- [ ] 切换模型后端调用正确 Provider

---

## Phase 6：收尾与回归

### 6.1 代码质量
- [ ] 后端 `ruff check . && ruff format .`
- [ ] 后端 `mypy .`
- [ ] 前端 `npm run lint && npm run typecheck`

### 6.2 测试
- [ ] 后端新增单元测试覆盖 Chat API / AgentRouter / LLM Provider
- [ ] 前端新增 Chat 组件基础测试（可选）
- [ ] 运行 E2E smoke 测试验证路由

### 6.3 文档更新
- [ ] 更新 `openspec/changes/sdlc-visualizer/progress.md`
- [ ] 更新 `AGENTS.md` 中相关章节（如 Skill 框架未涉及可不更新）
- [ ] 更新接口契约 `openapi.yaml`（新增 `/chat/*` 端点）

---

## 验收标准

1. 访问 `/cli` 显示 Kimi 风格空态首页，输入后可进入会话。
2. 会话中 AI 回复以 Markdown 富文本气泡展示，支持代码块、思考流、操作按钮。
3. 架构治理页面选择问题后，右侧滑出 Chat 面板，用户可在面板中逐条确认修复。
4. 后端根据配置调用 Kimi CLI；OpenAI API 接口已预留。
5. 旧 Terminal 组件已从代码库移除。
6. 全部代码质量检查通过。
