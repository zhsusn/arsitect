# AI CLI Terminal - Implementation Tasks

> 本清单覆�?AI CLI Terminal MVP（Phase 1 基础会话 + Phase 2 Bug 修复核心 + Phase 3 架构治理最小实现）。每个任务应控制�?30 分钟内完成；若超时，应进一步拆分�?

## Phase 1: Foundation

- [x] 1.1 [Backend] Add CLI session models and repository
  - **Description**: �?`backend/app/models/` 新增 `CliSession` �?`CliMessage` SQLAlchemy 模型；在 `backend/app/services/` �?`backend/app/repositories/` 新增会话仓储接口�?SQLite 实现�?
  - **Acceptance Criteria**: 模型可正确创建表结构；仓储支�?create/get/list/close 四个基本操作；单元测试覆�?happy path�?

- [x] 1.2 [Backend] Implement POST /api/v1/cli/sessions and GET/close/mode endpoints
  - **Description**: �?`backend/app/api/v1/` 新增 `cli.py` 路由，实现会话创建、历史消息查询、关闭会话、切换模式四�?REST 接口；接�?Pydantic schema 校验�?
  - **Acceptance Criteria**: 通过 FastAPI TestClient 可完成创�?�?查询历史 �?切换模式 �?关闭的完整流程；返回结构符合 `openapi.yaml`�?

- [x] 1.3 [Backend] Implement WebSocket endpoint /api/v1/cli/ws/{session_id}
  - **Description**: �?`cli.py` 中新�?WebSocket 路由，维护连接状态，解析 `CliRequest`，按 `CliResponse` 格式回显基础消息（text/pong/done）�?
  - **Acceptance Criteria**: 客户端可通过 WebSocket 发�?`ping` 并收�?`pong`；发�?`command` 后收�?`text` + `done` 回显；会话不存在时返�?`error` 并关闭连接�?

- [x] 1.4 [Frontend] Add AI CLI page route and xterm.js terminal component
  - **Description**: �?`frontend/src/pages/` 新增 `AiTerminal/` 页面；使�?React + xterm.js 创建可输入的终端组件；在 `App.tsx` 或路由配置中添加 `/cli` 路由�?
  - **Acceptance Criteria**: 访问 `/cli` 可看到终端界面；键盘输入可显示在终端中；页面不报错且适配深色主题�?

- [x] 1.5 [Frontend] Connect WebSocket and render basic message types
  - **Description**: 在终端页面初始化 WebSocket 连接；将服务�?`text/error/done` 消息渲染�?xterm；用户输入通过 `command` 消息发送�?
  - **Acceptance Criteria**: 打开页面后自动连�?`/api/v1/cli/ws/{session_id}`；输入文本后能在终端看到服务端回显；断线后给出视觉提示�?

## Phase 2: Bug Fix Flow

- [x] 2.1 [Backend] Implement BugFixService skeleton and AI Gateway adapter
  - **Description**: 新建 `BugFixService` 骨架�?AI Gateway 适配器接口（�?mock AI 响应）；定义异常签名生成逻辑；支持根据错误文本调�?AI 分析�?
  - **Acceptance Criteria**: 服务接口稳定；提�?mock 实现用于本地开发；异常签名对相同输入稳定；单元测试覆盖签名与调用流程�?

- [x] 2.2 [Backend] Generate and stream fix-proposal cards
  - **Description**: �?WebSocket 收到用户错误文本时，后台生成 `fix-proposal` 类型�?`CliCard` 并通过 WebSocket 推送给前端；卡片包�?Diff、风险等级与 Y/N/Edit 操作�?
  - **Acceptance Criteria**: 发送错误堆栈后，前端收�?`card` 消息；卡�?`type=fix-proposal`，`actions` 包含 Y、N、edit；数据字段包�?`diff` �?`risk`�?

- [x] 2.3 [Backend] Implement user confirmation handling and exec simulation
  - **Description**: 处理前端 `action` 消息中的 `Y`/`N`/`edit`；Y 时模拟执�?Diff 并返�?`success`/`ExecResult`；N 时忽略；edit 时使用用户编辑后�?Diff�?
  - **Acceptance Criteria**: 点击 Y 后终端打印执行结果；点击 N �?Bug 状态变�?ignored；edit 后使用编�?Diff 执行；所有分支通过单元测试�?

- [x] 2.4 [Frontend] Render fix-proposal cards with Y/N/Edit actions
  - **Description**: 在终端组件中识别 `card.type=fix-proposal` 并在终端下方渲染可交互卡片；提供 Y、N、编辑三个按钮；编辑时弹出简单文本框�?
  - **Acceptance Criteria**: 卡片正确渲染 Diff 与风险等级；点击按钮后发送对�?`action` WebSocket 消息；编辑后可提交修改后�?Diff�?

- [x] 2.5 [Backend+Frontend] Persist bug records and show success messages
  - **Description**: 后端�?Bug 记录持久化到 `BugRecord` 表；修复成功后更新状态并返回 `success` 消息；前端收�?success 消息后渲染绿色提示�?
  - **Acceptance Criteria**: 修复成功后数据库记录状态为 `executed` �?`verified`；前端终端显示成功提示；可通过 REST 查询到该 Bug 记录�?

## Phase 3: Arch Governance (MVP minimal)

- [x] 3.1 [Backend] Implement ArchGovernanceService scanner stub
  - **Description**: 新建 `ArchGovernanceService` 扫描器桩；提供默认规则列表；`POST /api/v1/arch/scan` 返回 `scan_id` 并通过 WebSocket 异步推�?progress�?
  - **Acceptance Criteria**: 调用扫描接口返回 202；前端收�?progress 消息；规则配置可通过 `GET /api/v1/arch/rules` 获取�?

- [x] 3.2 [Backend] Generate arch-decision cards
  - **Description**: 扫描完成后生成若�?`arch-decision` 类型 `CliCard` 并推送；卡片包含治理项标题、影响分析与 fix/skip 操作�?
  - **Acceptance Criteria**: 扫描结束后前端收�?`card` 消息�?`type=arch-decision`；卡�?actions 包含 fix、skip；数据字段包�?`issue_id`、`title`、`impact`�?

- [x] 3.3 [Frontend] Render arch-decision cards
  - **Description**: 前端识别 `arch-decision` 卡片并渲染；提供 fix/skip 按钮，点击后发送对�?`action` 消息�?
  - **Acceptance Criteria**: 架构治理卡片正确显示；fix 调用后端 `POST /api/v1/arch/issues/{issue_id}/execute`；skip 调用 `POST /api/v1/arch/issues/{issue_id}/skip`；操作后终端显示反馈�?

## Phase 3.5: ArchGovernance 页面内嵌 AI CLI 修复终端

- [x] 3.5.1 [Frontend] 重构 Terminal/CliCard 为通用 CLI 组件
  - **Description**: 将 `pages/AiCli/components/Terminal.tsx` 和 `CliCard.tsx` 上提至 `src/components/cli/`，更新 `AiCli` 页面引用。
  - **Acceptance Criteria**: `AiCli` 页面构建通过；组件 props 不变；类型检查无报错。

- [x] 3.5.2 [Frontend] 在 ArchGovernance 页面增加 issue 选择能力
  - **Description**: issue 表格增加复选框；维护选中状态；工具栏按钮改为「修复架构问题」并在选中时启用。
  - **Acceptance Criteria**: 支持单选/全选/反选；按钮状态随选择变化；未选择时禁用。

- [x] 3.5.3 [Frontend] 实现 FixTerminalModal 方案预览与编辑能力
  - **Description**: 在 `FixTerminalModal` 内展示 fix-plan；支持 Diff 编辑、AI 优化提示词、HIGH 风险高亮。
  - **Acceptance Criteria**: 弹窗正确展示方案；编辑后 Diff 可随 action 提交；AI 优化调用后端接口。
  - **Description**: 展示 fix-plan、支持 Diff 编辑、AI 优化提示词、HIGH 风险高亮。
  - **Acceptance Criteria**: 弹窗正确展示方案；编辑后 Diff 可传递到修复终端；AI 优化调用后端接口。

- [x] 3.5.4 [Frontend] 实现 FixTerminalModal（AI CLI 修复终端）
  - **Description**: 新建模态框组件，内嵌 Terminal 和 CliCard，使用 `useCliSession`，发送 apply_arch_fix_plan 命令。
  - **Acceptance Criteria**: 模态框可正常打开/关闭；终端显示系统提示；卡片操作正常；修复完成后触发 onCompleted 刷新父页面。

- [x] 3.5.5 [Backend] 新增 FileBackupService 与真实源码写入能力
  - **Description**: 实现文件备份、Diff 应用、校验、恢复；路径越界校验。
  - **Acceptance Criteria**: 单元测试覆盖备份/应用/校验/恢复；越界路径抛出异常。

- [x] 3.5.6 [Backend] 扩展 WebSocket 路由支持 apply_arch_fix_plan
  - **Description**: 在 `cli.py` WebSocket handler 中新增 action 分支，调用 `ArchGovernanceService.apply_fix_plan`。
  - **Acceptance Criteria**: 发送 plan 后后端返回 progress 和 card 消息；fix/skip/edit action 被正确路由。

- [x] 3.5.7 [Backend] 实现 ArchGovernanceService 修复执行流程
  - **Description**: 实现 apply_fix_plan、handle_change_action、execute_change；写前备份；更新 arch_issues 状态；返回 text/done 消息。
  - **Acceptance Criteria**: 单元测试覆盖三种 action；HIGH 风险变更需二次确认；执行结果持久化。

- [x] 3.5.8 [Backend] 新增 POST /c4/governance/optimize-change 端点
  - **Description**: 根据用户提示词调用 AI Gateway 优化单条变更。
  - **Acceptance Criteria**: 接口返回优化后的 change；单元测试覆盖。

- [ ] 3.5.9 [E2E] 新增 ArchGovernance → AI CLI 修复黄金流程测试
  - **Description**: Playwright 覆盖勾选 issue、确认方案、执行修复、关闭后刷新列表。
  - **Acceptance Criteria**: 新 E2E 通过；不影响现有 `/cli` 测试。
  - **Description**: Playwright 覆盖勾选 issue、确认方案、执行修复、关闭后刷新列表。
  - **Acceptance Criteria**: 新 E2E 通过；不影响现有 `/cli` 测试。

## Testing

- [x] 4.1 [Backend] Unit tests for session service (coverage >= 70%)
  - **Description**: �?CliSession 仓储、BugFixService、ArchGovernanceService 编写 pytest 单元测试；确保整体后端覆盖率 �?70%�?
  - **Acceptance Criteria**: `pytest --cov` 输出 backend 整体覆盖�?�?70%；所有新增测试通过；关键分支（创建/关闭/模式切换/Bug 执行）均被覆盖�?

- [x] 4.2 [Backend] Integration tests for session and bug fix endpoints
  - **Description**: 使用 `TestClient` 编写集成测试，覆盖会�?REST 流程�?Bug 修复端到点；覆盖 WebSocket 连接与消息收发�?
  - **Acceptance Criteria**: 集成测试可在 CI 中通过；包含创建会话、发送错误、接收卡片、执行修复、查询记录完整链路�?

- [x] 4.3 [E2E] Playwright test for basic CLI page and WebSocket
  - **Description**: �?`e2e/` 目录新增 Playwright 测试；打开 `/cli` 页面，输入文本，验证终端出现回显；验证连接建立与心跳�?
  - **Acceptance Criteria**: `npx playwright test` 通过；测试不依赖真实 AI 服务（使�?mock）；录制失败用例截图保存�?`test-results/`�?
