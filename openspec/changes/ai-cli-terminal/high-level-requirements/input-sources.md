# 输入来源索引

| 来源 ID | 来源类型 | 路径/描述 | 关键条目数 | 处理状态 |
|---------|----------|-----------|-----------|----------|
| SRC-001 | external_doc | docs/aicli.txt | 7 | 已解析 |

## SRC-001 关键条目摘要

1. 产品定位：在 AI 研发平台中嵌入类终端交互界面，核心场景为 Bug 修复与架构治理。
2. 前端方案：基于 xterm.js 的终端渲染层、消息类型与样式、交互卡片（Overlay Widget）、模式切换（Bug/Arch）。
3. 后端方案：CLI Service、Bug Service、Arch Service、Exec Service、AI Gateway、存储层（PostgreSQL/Redis/S3）。
4. 通信协议：WebSocket（Socket.io）双向流式消息协议。
5. API 设计：会话创建、历史查询、中止任务、Bug 记录、Arch 扫描等接口。
6. 数据模型：bug_records、arch_issues、cli_sessions、cli_messages。
7. Phase 迭代：Phase 1 基础 CLI，Phase 2 Bug 修复，Phase 3 架构治理，Phase 4 智能化。
