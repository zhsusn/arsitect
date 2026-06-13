---
doc_type: "PRD"
fragment_id: "prd-ai-cli-terminal-dr-002-spec"
title: "Bug 修复 - 模块规格"
version: "1.0.0"
status: "DRAFT"
iteration: "ai-cli-terminal"
dependencies:
  - fragment_id: "prd-ai-cli-terminal-000"
    version: "1.0.0"
  - fragment_id: "prd-ai-cli-terminal-001"
    version: "1.0.0"
  - fragment_id: "prd-ai-cli-terminal-002"
    version: "1.0.0"
---

# Bug 修复 - 模块规格 {#sec-spec}

## 1. 模块定位 {#sec-module-position}

本模块面向开发者在 AI CLI 终端中修复代码异常的场景，覆盖异常输入、根因分析、修复方案生成、用户确认、执行验证与记录归档的完整闭环。所有自动修复操作必须获得用户显式授权，高风险方案必须引导用户创建 PR。

## 2. 功能边界 {#sec-functional-scope}

### 2.1 In-Scope {#sec-in-scope}

- 解析用户粘贴的异常堆栈或错误描述，提取错误签名。
- 基于错误签名查询历史同类 Bug 记录。
- 调用 AI Gateway 进行根因分析并流式返回结论。
- 生成可交互的修复方案卡片，展示 Diff 与风险等级。
- 接收用户确认、忽略或编辑后执行的操作。
- 在临时 Git 工作区执行修复并运行验证。
- 保存 Bug 记录与修复方案。

### 2.2 Out-of-Scope {#sec-out-of-scope}

- OCR 截图识别异常（P2）。
- 自动创建 PR 与合并（P2）。
- 多语言 LSP 深度定位（P2）。
- 零确认自动修复（Non-goal）。

## 3. 用户场景 {#sec-user-scenarios}

### 3.1 场景一：粘贴异常并自动分析 {#sec-scenario-paste}

用户在 Bug 模式下粘贴构建异常堆栈，系统自动识别为错误输入并触发分析流程，无需手动输入命令。

### 3.2 场景二：历史 Bug 推荐 {#sec-scenario-similar}

当错误签名与历史记录匹配度 ≥80% 时，系统在分析前先提示"发现历史同类问题"，用户可查看历史修复方案。

### 3.3 场景三：高风险方案确认 {#sec-scenario-high-risk}

AI 生成的修复方案风险等级为 high 时，用户点击"执行修复"后系统提示"该方案风险较高，建议生成 PR"，用户可选择继续执行或取消。

## 4. 验收标准 {#sec-acceptance-criteria}

| 编号 | 场景 | 验收标准 | 优先级 |
|------|------|----------|--------|
| AC2-001 | 异常粘贴 | 粘贴堆栈后 3s 内开始流式输出分析 | P0 |
| AC2-002 | 空输入拦截 | 空内容提交时提示"请输入异常信息" | P0 |
| AC2-003 | 历史推荐 | 匹配度 ≥80% 时展示历史推荐入口 | P1 |
| AC2-004 | 卡片展示 | 修复方案卡片展示 Diff、风险、操作按钮 | P0 |
| AC2-005 | 权限校验 | 无写入权限用户点击执行时提示权限不足 | P0 |
| AC2-006 | 执行验证 | 修复后自动运行构建/测试，失败时回滚 | P0 |
| AC2-007 | 记录保存 | 修复完成后保存 Bug 记录并返回记录编号 | P0 |

## 5. 依赖与约束 {#sec-dependencies}

- 依赖 CLI 会话模块提供 sessionId 与消息通道。
- 依赖 AI Gateway 提供流式分析能力。
- 依赖 Exec Service 提供临时工作区执行能力。
- 依赖用户权限模块校验代码写入权限。
- 修复操作必须在临时 Git 工作区执行，禁止直接修改主分支。
