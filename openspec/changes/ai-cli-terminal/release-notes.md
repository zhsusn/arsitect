# AI CLI 终端 - 发布说明

## 1. 版本与变更摘要

| 项目 | 内容 |
|------|------|
| **变更名称** | ai-cli-terminal |
| **版本** | 1.0.0 |
| **发布日期** | 2026-06-13 |
| **状态** | MVP 已完成并测试 |
| **变更摘要** | 在 Arsitect 可视化驾驶舱中嵌入 AI CLI 终端页面，提供类终端交互体验，支持 Bug 修复与架构治理两种核心工作模式，并与后端 AI Gateway、执行引擎、问题库打通。 |
| **关联文档** | `high-level-requirements/00-requirements-overview.md`、`high-level-design/00-design-overview.md`、`interface-contracts/openapi.yaml`、`tasks.md` |

---

## 2. 新增功能

本次 MVP 覆盖以下三大功能模块：

### 2.1 AI CLI 终端页面

- 新增前端页面 `frontend/src/pages/AiCli/`，基于 **React 19 + xterm.js** 实现类终端交互界面。
- 支持深色主题下的命令输入、流式输出渲染与断线视觉提示。
- 通过 WebSocket 与后端保持双向实时通信，适配 Bug 与 Arch 两种工作模式。
- 前端路由已挂载，可通过 `/cli` 访问。

### 2.2 Bug 修复流程

- 后端新增 `BugFixService`，支持异常签名提取、AI 根因分析、修复方案生成与执行。
- 终端内可粘贴异常堆栈，系统流式返回分析结论。
- 修复方案以可交互卡片形式展示，包含 Diff、风险等级与操作按钮：
  - **Y**：执行修复
  - **N**：忽略该方案
  - **Edit**：编辑后执行
- 修复结果持久化至 `BugRecord` 表，支持通过 REST 接口查询历史记录。
- 高风险修复强制提示生成 PR，禁止直推主分支（业务规则 BR-002）。

### 2.3 架构治理桩（Arch Governance Stubs）

- 后端新增 `ArchGovernanceService` 扫描器桩，提供默认规则列表。
- 提供 `POST /api/v1/arch/scan` 接口，返回 `scan_id` 并通过 WebSocket 异步推送扫描进度。
- 扫描完成后生成 `arch-decision` 类型治理卡片，展示治理项标题、影响分析与操作：
  - **fix**：执行重构
  - **skip**：跳过该项
- 前端已适配架构治理卡片渲染与模式切换。

---

## 3. 已知限制

以下功能已在本期明确列为 **Out-of-Scope**，将在 P1/P2 阶段逐步引入：

| 限制项 | 说明 | 计划阶段 |
|--------|------|----------|
| **OCR 截图识别** | 本期仅支持文本粘贴异常，不支持上传截图自动识别 | P2 |
| **Docker 沙箱执行** | 执行引擎当前基于临时 Git 工作区，未引入容器化隔离 | P2 |
| **自动 PR 创建与合并** | 高风险修复仅提示生成 PR，未自动创建或合并 | P2 |
| **多 AI Provider 适配** | MVP 仅支持 Kimi API，Claude / Cursor / GPT 等适配接口已预留 | P2 |
| **复杂分布式架构治理** | 本期聚焦单仓库代码级坏味道，不涉及分布式系统治理 | P2 |
| **会话历史恢复** | 支持查看历史消息，但页面刷新后的完整会话恢复为 P1 增强项 | P1 |

---

## 4. 部署说明

### 4.1 部署拓扑

本次发布为本地单体运行，部署拓扑如下：

| 组件 | 运行方式 | 端口 | 说明 |
|------|----------|------|------|
| 前端 | Vite dev server / 静态托管 | 5173 | 代理 `/api` 与 `/cli` 到后端 |
| FastAPI 后端 | uvicorn | 8000 | REST API + WebSocket |
| SQLite | 本地文件 | - | 数据文件位于 `data/ai-cli.db` |
| 临时 Git 工作区 | 本地文件系统 | - | 执行引擎按需创建 |

### 4.2 启动步骤

```bash
# 1. 启动后端
cd backend
python main.py
# 或
uvicorn main:app --host 0.0.0.0 --port 8000

# 2. 启动前端
cd frontend
npm install
npm run dev
```

前端默认访问地址：`http://localhost:5173`  
后端默认访问地址：`http://localhost:8000`  
WebSocket 端点：`ws://localhost:8000/api/v1/cli/ws/{session_id}`

### 4.3 关键配置项

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `CLI_SESSION_TIMEOUT` | 30 分钟 | 无操作会话自动关闭 |
| `MESSAGE_RETENTION` | 100 条 | 单会话保留最近消息数 |
| `ARCH_SCAN_RULES` | 保守规则集 | 默认关闭高误报规则 |
| `HIGH_RISK_THRESHOLD` | high | 高风险修复强制建议 PR |
| `MAX_RETRY_COUNT` | 3 次 | AI 调用失败最大重试次数 |

---

## 5. 回滚参考

回滚策略详见：

> **`openspec/changes/ai-cli-terminal/high-level-design/05-ops-governance.md`**

该文档定义了三级回滚机制：

- **层级 A：产物级回滚**
  - 前端构建产物异常：回退 `frontend/dist/`
  - 后端代码缺陷：Git checkout 上一个稳定 tag/commit
  - Prompt 模板问题：还原 `openspec/changes/ai-cli-terminal/config/`

- **层级 B：数据库级回滚**
  - 触发条件：数据迁移脚本异常、错误数据写入、配置表损坏
  - SQLite 回滚：备份当前 `data/ai-cli.db`，恢复上一次备份
  - PostgreSQL 回滚（P1）：`alembic downgrade {target_revision}`

- **层级 C：整体回滚**
  - 触发条件：发布后严重功能缺陷或安全漏洞
  - 步骤：停止服务 → Git 回退到稳定 tag → 恢复数据库备份 → 重新部署 → 验证核心流程

生产发布前请至少完成一次层级 A 回滚演练。

---

## 6. 测试证据摘要

本次发布已通过以下测试层级验证：

### 6.1 后端单元测试

| 测试文件 | 覆盖范围 |
|----------|----------|
| `backend/tests/unit/cli/test_cli_service.py` | 会话创建、模式切换、关闭、查询、异常处理 |
| `backend/tests/unit/cli/test_bug_fix_service.py` | 异常解析、AI 分析、修复方案生成、执行分支 |
| `backend/tests/unit/models/test_arch_validation.py` | 架构验证模型 |
| `backend/tests/unit/services/test_arch_validation_service.py` | 架构验证服务 |

- 后端整体覆盖率目标：≥ 70%
- 关键分支覆盖：创建/关闭/模式切换/Bug 执行/异常处理

### 6.2 后端集成测试

| 测试文件 | 覆盖范围 |
|----------|----------|
| `backend/tests/integration/test_cli.py` | REST 会话接口、WebSocket 命令交换、消息历史、模式切换 |

- 测试编号：CLI-001 ~ CLI-005
- 覆盖：创建会话、获取历史、关闭会话、切换模式、WebSocket 交互

### 6.3 前端 E2E 测试

| 测试文件 | 覆盖范围 |
|----------|----------|
| `tests/e2e/ai_cli/test_golden_cli.py` | 页面加载、终端渲染、Bug 报告分析、修复卡片执行、Bug/Arch 模式切换 |
| `tests/e2e/ai_cli/pages/cli_page.py` | E2E 页面对象封装 |

- 框架：Playwright
- 测试使用 Mock AI 服务，不依赖真实 Kimi API
- 失败用例自动截图保存至 `test-results/`

### 6.4 人工闸门状态

| 闸门 | 状态 | 评审人 | 日期 | 备注 |
|------|------|--------|------|------|
| Gate 1 | 已通过 | user | 2026-06-13 | 概要需求确认 |
| Gate 2.5 | 已通过 | user | 2026-06-13 | 详细需求/原型确认 |
| Gate 2 | 已通过 | user | 2026-06-13 | 概要设计确认，授权编码 |
| Gate 3 | 待评审 | — | — | 等待 UAT 评审通过后进入发布 |

> **注意**：Gate 3 尚未完成签字。正式发布前需完成 UAT 评审并更新 `human-decisions.md`。

---

## 7. 后续计划

| 阶段 | 目标 |
|------|------|
| P1 | 会话历史恢复、PostgreSQL 迁移、HTTP 长轮询降级 |
| P2 | OCR 截图识别、Docker 沙箱、自动 PR、多 AI Provider 适配 |

---

*本发布说明由 `release-management` Skill 依据 `high-level-requirements`、`high-level-design`、`tasks.md` 及测试产物自动生成。*
