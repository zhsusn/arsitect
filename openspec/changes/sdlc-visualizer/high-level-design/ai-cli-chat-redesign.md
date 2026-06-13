# AI CLI 页面 Kimi 化改造与架构治理修复共用方案

## 1. 背景与目标

### 1.1 背景
当前 `AI CLI` 页面（`/cli`）采用 xterm.js 终端风格，黑色背景、命令行提示符 `$ `、纯文本流式输出。架构治理中心（`/arch-governance`）的修复执行弹窗 `FixTerminalModal` 也复用了同一套 Terminal 组件，交互体验偏开发者工具，对非技术用户不够友好。

### 1.2 目标
参考截图 `docs/ScreenShot_2026-06-13_143358_895.png` 与 `docs/ScreenShot_2026-06-13_143412_853.png`，将 AI CLI 页面改造为类似 **Kimi 网页版** 的极简对话式界面：

- 首页：居中 Logo + 大输入框，placeholder 提示“输入‘/’可快捷使用技能”。
- 会话页：类聊天应用布局，顶部项目/会话选择器，中间消息气泡列表，底部多功能输入框。
- 支持两种 AI 后端：
  1. **Kimi CLI 本地调用**：通过 `kimi --print --quiet --input-format text` 子进程交互。
  2. **LLM HTTP API**：OpenAI 兼容接口。
- 保留并增强卡片式人机交互（确认/编辑/执行等动作卡片）。
- 探讨与架构治理中心的“修复架构问题”共用同一套会话/执行引擎。

## 2. 现状分析

### 2.1 前端现状

| 模块 | 文件 | 现状 |
|------|------|------|
| AI CLI 页面 | `frontend/src/pages/AiCli/index.tsx` | xterm 终端 + Bug/架构模式切换 + 底部操作栏 |
| 终端组件 | `frontend/src/components/cli/Terminal.tsx` | 基于 `@xterm/xterm`，仅支持单行输入 |
| 卡片组件 | `frontend/src/components/cli/CliCard.tsx` | 右下角浮层卡片，支持按钮动作 |
| 会话 Hook | `frontend/src/components/cli/hooks/useCliSession.ts` | WebSocket 长连接，共享同一 session，支持 command/action |
| 架构治理修复弹窗 | `frontend/src/pages/ArchGovernance/components/FixTerminalModal.tsx` | 复用 Terminal + useCliSession，自动派发 `apply_arch_fix_plan` |
| 架构治理页面 | `frontend/src/pages/ArchGovernance/index.tsx` | 问题列表 + 生成修复方案 + 确认/执行弹窗 |

### 2.2 后端现状

| 模块 | 文件 | 现状 |
|------|------|------|
| CLI API | `backend/app/api/v1/cli.py` | REST + WebSocket (`/ws/api/v1/cli/ws/{session_id}`) |
| CLI Service | `backend/app/services/cli_service.py` | 会话生命周期 + 消息历史 |
| Bug 修复 | `backend/app/services/bug_fix_service.py` | bug 模式处理 |
| 架构治理 | `backend/app/services/arch_governance_service.py` | C4 扫描、修复计划生成、apply_fix_plan / handle_change_action |
| LLM Gateway | `backend/app/c4/governance_fix/llm_gateway.py` | 已存在 KimiCLIGateway / OpenAILLMGateway 抽象 |
| AI Gateway | `backend/app/services/ai_gateway.py` | MVP mock 网关 |

**关键发现**：架构治理修复已经通过 `LLMGateway` 调用了 Kimi CLI / OpenAI API，并且已经通过 WebSocket CLI 通道推送卡片。这意味着底层能力已经部分具备，只需在前端统一成对话式 UI。

## 3. 目标 UI 解析

从两张截图提炼出关键交互元素：

### 3.1 首页（Empty State）

```
+----------------------------------+
|                                  |
|            KIMI                  |   <- 居中 Logo
|                                  |
|  +------------------------------+|
|  | 输入“/”可快捷使用技能        ||   <- 圆角大输入框
|  |                              ||
|  +------------------------------+|
|  [+] [🤖 Agent]      [K2.6 ▼] [⬆]|
+----------------------------------+
```

- **左侧**：附件/扩展按钮 `+`，Agent 模式切换。
- **右侧**：模型/思考深度选择器（如 `K2.6 思考 ▼`）、发送按钮。

### 3.2 会话页（Chat State）

```
+----------------------------------+
| Python lint 项目        [下拉 ▼] |   <- 顶部项目选择器
+----------------------------------+
| AI:                              |
| 1. 点击底部的 "More workflows"   |
| 2. 在搜索框输入 `pylint` 或 ...  |
|                                  |
| 建议：如果你的 Python 项目需要... |
| [复制] [刷新] [分享] [👍] [👎]   |   <- 消息操作栏
+----------------------------------+
|  +------------------------------+|
|  | 问点难的，让我多想一步       ||
|  |                              ||
|  +------------------------------+|
|  [+] [🤖 Agent]      [K2.6 ▼] [⬆]|
+----------------------------------+
```

- 消息区分用户/AI/系统/卡片。
- AI 消息支持富文本（Markdown、代码高亮、有序列表、建议卡片）。
- 每条消息底部支持复制、重发、点赞/点踩。
- 输入框支持多行、技能快捷触发 `/`、模型选择。

## 4. 整体架构设计

### 4.1 核心思想

将 AI CLI 从“终端模拟器”升级为“**统一 Agent 会话界面（Unified Agent Chat）**”。架构治理修复、Bug 修复、自由对话都作为该会话界面上的不同**任务模式（Task Mode）**或**技能触发（Skill Invocation）**。

后端保留 WebSocket 长连接作为实时通道，新增 **Chat Message 协议** 以支持富文本、思考流、卡片、文件引用。后端引入 **Agent Runner** 统一调度 Kimi CLI、OpenAI API、以及内部 Service（BugFix、ArchGovernance）。

### 4.2 高层数据流

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ ChatHome    │  │ ChatSession  │  │ MessageRenderer  │   │
│  │  (Empty)    │  │   (List)     │  │ (Markdown/Card)  │   │
│  └──────┬──────┘  └──────┬───────┘  └──────────────────┘   │
│         │                │                                  │
│         └────────────────┘                                  │
│                   │                                         │
│         ┌─────────▼─────────┐                               │
│         │   ChatComposer    │  <-- 输入框 / 技能 / 模型选择 │
│         └─────────┬─────────┘                               │
│                   │                                         │
│         ┌─────────▼─────────┐                               │
│         │   useChatSession  │  <-- WebSocket + 状态管理    │
│         └─────────┬─────────┘                               │
└───────────────────┼─────────────────────────────────────────┘
                    │ WebSocket /api/v1/chat/ws/{session_id}
┌───────────────────▼─────────────────────────────────────────┐
│                        Backend                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ ChatSession │  │ AgentRouter  │  │ AgentRunner      │   │
│  │   Service   │──│              │──│ (Kimi/OpenAI/    │   │
│  │             │  │ 模式/技能路由 │  │  Internal Svc)   │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
│         │                │                    │             │
│         ▼                ▼                    ▼             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  Message    │  │  Skill/      │  │ LLM Provider     │   │
│  │  Store      │  │  Task Registry│  │ (Kimi CLI / API) │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 5. 前端方案

### 5.1 页面路由调整

| 路由 | 用途 |
|------|------|
| `/cli` | 默认进入 ChatHome（空态大输入框） |
| `/cli/s/:sessionId` | 具体会话页面 |
| `/arch-governance` | 保留问题列表，但“修复”改为在侧边 Chat 面板或跳转 `/cli/s/:sessionId?task=arch-fix&plan=...` |

### 5.2 组件拆分

在 `frontend/src/components/chat/` 下新建组件：

```
components/chat/
├── ChatHome.tsx              # 空态首页
├── ChatSession.tsx           # 会话页容器
├── MessageList.tsx           # 消息列表
├── MessageItem.tsx           # 单条消息（用户/AI/系统/卡片）
├── MessageActions.tsx        # 复制/刷新/点赞/点踩
├── ChatComposer.tsx          # 底部输入框
├── SkillTrigger.tsx          # / 技能选择浮层
├── ModelSelector.tsx         # 模型/思考深度选择
├── AgentToggle.tsx           # Agent 模式开关
├── ChatCard.tsx              # 通用动作卡片（替代 CliCard）
├── useChatSession.ts         # WebSocket + 消息状态 Hook
├── types.ts                  # Chat 消息类型
└── markdown-renderer.tsx     # Markdown + 代码高亮
```

### 5.3 消息模型

```ts
export type MessageRole = 'user' | 'ai' | 'system' | 'thinking'

export interface ChatMessage {
  id: string
  session_id: string
  role: MessageRole
  content?: string
  card?: ChatCard
  attachments?: ChatAttachment[]
  metadata?: Record<string, unknown>
  created_at: string
  // UI 状态
  status: 'sending' | 'streaming' | 'done' | 'error'
}

export interface ChatCard {
  type: 'fix-proposal' | 'arch-decision' | 'confirm' | 'progress' | 'bug-report'
  title: string
  description?: string
  data: Record<string, unknown>
  actions: ChatCardAction[]
}

export interface ChatCardAction {
  label: string
  command: string
  style?: 'primary' | 'danger' | 'default'
}

export interface ChatAttachment {
  type: 'file' | 'image' | 'code-snippet'
  name: string
  content?: string
}
```

### 5.4 输入框设计（ChatComposer）

- 多行 textarea，支持 `Shift+Enter` 换行，`Enter` 发送。
- 输入 `/` 弹出 Skill 浮层：
  - `/bug` — 进入 Bug 修复模式
  - `/arch` — 进入架构治理模式
  - `/fix` — 调用修复计划
  - `/scan` — 触发架构扫描
  - `/explain` — 解释代码
- 左侧 `+` 支持粘贴代码片段、上传文件（MVP 可只做剪贴板/文本附件）。
- 右侧模型选择器映射后端 `provider` + `model`：
  - `kimi-cli` — 调用本地 Kimi CLI
  - `kimi-api` / `openai` — 调用 HTTP API
  - `arsitect-agent` — 调用内部 Agent（BugFix / ArchGovernance）

### 5.5 状态管理

- 本地状态：当前会话消息列表、输入框内容、流式消息 buffer。
- 共享状态：会话列表、当前项目、可用模型/技能，使用 `zustand` 存储在 `stores/chatStore.ts`。

## 6. 后端方案

### 6.1 LLM Provider 抽象复用

当前 `backend/app/c4/governance_fix/llm_gateway.py` 已经实现了：

- `KimiCLIGateway` — 子进程调用 `kimi --print --quiet --input-format text`
- `OpenAILLMGateway` — OpenAI 兼容 HTTP API
- `NoOpLLMGateway` — 兜底

建议将其上提到 `backend/app/services/llm/` 作为全局 LLM Provider，供 CLI Chat、架构治理、Bug 修复统一使用。

```
backend/app/services/llm/
├── __init__.py
├── base.py                   # LLMProvider 抽象
├── kimi_cli.py               # KimiCLIGateway
├── openai.py                 # OpenAILLMGateway
├── noop.py                   # NoOpLLMGateway
├── factory.py                # get_llm_provider(provider: str)
└── streaming.py              # 统一流式回调封装
```

### 6.2 Agent Router / Runner

新增 `backend/app/services/chat/agent_router.py`：

```python
class AgentRouter:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.bug_svc = BugFixService(db)
        self.arch_svc = ArchGovernanceService(db)
        self.llm = get_llm_provider(settings.DEFAULT_LLM_PROVIDER)

    async def handle(
        self,
        session: ChatSession,
        message: UserMessage,
        sender: Sender,
    ) -> None:
        # 1. 判断是技能命令还是自由对话
        if message.text.startswith('/'):
            await self._run_skill(session, message, sender)
            return

        # 2. 当前会话任务模式
        if session.task_mode == 'bug':
            await self._run_bug_mode(session, message, sender)
        elif session.task_mode == 'arch-fix':
            await self._run_arch_fix_mode(session, message, sender)
        elif session.task_mode == 'free-chat':
            await self._run_llm_chat(session, message, sender)
        else:
            await self._run_llm_chat(session, message, sender)
```

### 6.3 消息协议扩展

保留现有 WebSocket JSON 协议，扩展 `type` 字段：

```ts
// 下行消息
export type ServerMessageType =
  | 'text'           // 普通文本（Markdown）
  | 'thinking'       // 思考过程流
  | 'card'           // 动作卡片
  | 'progress'       // 进度条
  | 'error'          // 错误
  | 'done'           // 任务完成
  | 'pong'

// 上行消息
export type ClientMessageType =
  | 'command'        // 用户文本
  | 'action'         // 卡片按钮动作
  | 'abort'          // 中止
  | 'ping'
```

新增 `thinking` 类型用于展示 Kimi 的“思考中”内容（类似截图中的 `K2.6 思考`）。

### 6.4 会话模型扩展

在 `backend/app/models/cli_session.py` 中扩展 `CliSession`：

```python
class CliSession(Base):
    # 已有字段
    task_mode: Mapped[str] = mapped_column(default='free-chat')  # free-chat | bug | arch-fix
    llm_provider: Mapped[str | None] = mapped_column(default=None)  # kimi-cli | openai | kimi-api
    context_json: Mapped[dict] = mapped_column(default=dict)  # 当前任务上下文，如 arch fix plan
```

## 7. 与架构治理修复的共用方案

### 7.1 结论：可以共用一套方案

架构治理修复与 AI CLI 聊天的本质都是：**长时运行的 Agent 任务 + 流式输出 + 人机确认卡片 + 执行动作**。当前代码中已经共用 `useCliSession` 和 WebSocket 通道，只是前端 UI 一个是弹窗终端、一个是页面终端。

改造后统一为：**架构治理页面选择问题并生成修复方案 → 跳转/打开右侧 Chat 面板 → 在 Chat 会话中推送 arch-decision 卡片 → 用户逐条确认/编辑/跳过 → 后端调用 LLM Provider 生成代码并应用**。

### 7.2 共用组件建议

| 当前实现 | 共用后 |
|----------|--------|
| `FixTerminalModal`（弹窗终端） | 移除或改为 `ChatSidePanel` / `ChatModal` |
| `CliCard` | 统一为 `ChatCard` |
| `useCliSession` | 升级为 `useChatSession` |
| `Terminal`（xterm） | 降级为可选调试视图，或完全移除 |
| `arch_governance_service.apply_fix_plan` | 由 `AgentRouter` 统一调度 |

### 7.3 架构治理页面改造

在 `ArchGovernancePage` 中：

1. 保留问题列表、筛选、健康评分。
2. 用户点击“修复架构问题”后，不再弹出 Terminal Modal，而是：
   - 方案 A：在当前页右侧滑出 `ChatSidePanel`，创建 `task_mode=arch-fix` 的会话。
   - 方案 B：跳转至 `/cli/s/:sessionId?task=arch-fix&plan_id=...`。
3. `apply_fix_plan` 通过 WebSocket 推送 `arch-decision` 卡片到 Chat 消息列表。
4. 用户在 Chat 中点击“执行/跳过/编辑”，发送 `action` 消息。

**推荐方案 A**（侧边 Chat 面板），因为用户可以在不离开治理页面的情况下完成修复确认，同时保留问题列表上下文。

### 7.4 后端共用路径

```
ArchGovernancePage
    │ 选择问题 → 生成修复方案
    ▼
POST /api/v1/c4/governance/fix-plan
    │
    ▼
创建/复用 ChatSession(task_mode='arch-fix', context={plan})
    │
    ▼
WebSocket /api/v1/chat/ws/{session_id}
    │
    ▼
AgentRouter → ArchGovernanceService.apply_fix_plan
    │
    ▼
推送 arch-decision 卡片 → 用户确认 → handle_change_action → LLM Provider → 应用变更
```

## 8. 接口契约变更

### 8.1 新增/修改端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/chat/sessions` | 创建 Chat 会话，替代 `/cli/sessions` |
| GET | `/api/v1/chat/sessions/{id}/history` | 获取会话历史 |
| WS | `/ws/api/v1/chat/ws/{session_id}` | 替代 `/ws/api/v1/cli/ws/{session_id}` |
| POST | `/api/v1/chat/sessions/{id}/mode` | 切换 task_mode / llm_provider |
| POST | `/api/v1/chat/sessions/{id}/close` | 关闭会话 |
| POST | `/api/v1/c4/governance/fix-plan` | 已存在，返回 plan |
| POST | `/api/v1/c4/governance/apply` | 可选：显式触发 apply_fix_plan |

### 8.2 兼容性

- 保留 `/cli/*` 旧端点 1-2 个迭代，前端切换完成后废弃。
- WebSocket 协议保持字段兼容，新增 `thinking` / `card` 类型。

## 9. 实施路线图

### Phase 1：基础设施（1-2 天）

1. 将 `llm_gateway.py` 上提到 `app/services/llm/`。
2. 扩展 `CliSession` 模型：`task_mode`、`llm_provider`、`context_json`。
3. 新增 `ChatMessage` 模型与 Schema。

### Phase 2：前端 Chat 组件（2-3 天）

1. 新建 `components/chat/` 目录与基础类型。
2. 实现 `ChatComposer`（多行输入、`/` 技能浮层、模型选择）。
3. 实现 `MessageList` / `MessageItem`（Markdown 渲染、代码块、操作栏）。
4. 实现 `useChatSession`（WebSocket + 消息状态）。
5. 实现 `ChatCard` 通用卡片组件。

### Phase 3：AI CLI 页面改造（1-2 天）

1. 重写 `AiCliPage`：空态首页 + 会话页两种视图。
2. 路由支持 `/cli/s/:sessionId`。
3. 后端新增 `/chat/*` 路由并接入 `AgentRouter`。

### Phase 4：架构治理修复接入（2-3 天）

1. 新增 `ChatSidePanel` 组件。
2. `ArchGovernancePage` 点击修复后打开 ChatSidePanel。
3. 移除/重构 `FixTerminalModal`。
4. 后端 `apply_fix_plan` 接入 `AgentRouter`。

### Phase 5：LLM Provider 打通（1-2 天）

1. `AgentRouter` 自由对话模式调用 `LLMProvider.chat_stream()`。
2. 支持 `kimi-cli`、`openai` 切换。
3. 配置 `KIMI_CLI_PATH`、`OPENAI_API_BASE`、`OPENAI_API_KEY`。

### Phase 6：打磨与测试（2 天）

1. 流式输出稳定性、断线重连。
2. 卡片动作回环测试。
3. 架构治理修复端到端测试。
4. 代码审查与文档更新。

## 10. 风险与注意事项

1. **Kimi CLI 子进程调用**：
   - Windows 下需确保 `PYTHONIOENCODING=utf-8`。
   - 长时间运行可能阻塞，需要超时与取消机制。
   - 子进程输出需继续过滤 surrogate characters。

2. **流式 Markdown 渲染**：
   - 流式文本直接渲染 Markdown 可能导致闪烁，建议使用增量文本 + 完成后再渲染 Markdown，或对流式内容使用纯文本。

3. **会话状态共享**：
   - 当前 `useCliSession` 使用全局共享 session，改造后如需多标签页独立会话，应避免全局共享。

4. **架构治理卡片兼容**：
   - 旧 `arch-decision` 卡片数据结构需与新的 `ChatCard` 兼容。

5. **安全**：
   - Kimi CLI 执行的是本地命令，后端需限制可执行路径与工作目录。
   - LLM API Key 仅保存在后端环境变量，禁止返回前端。

## 11. 建议的下一步

1. 确认是否采用“侧边 Chat 面板”方案接入架构治理修复。
2. 确认 Kimi CLI 在本机已安装且 `kimi` 命令可用路径。
3. 确认是否保留旧的 Terminal 调试入口（可作为 `/cli/debug` 保留）。
4. 开始 Phase 1 基础设施迁移。
