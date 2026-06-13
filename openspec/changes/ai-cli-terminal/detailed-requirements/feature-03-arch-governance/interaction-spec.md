---
doc_type: "PRD"
fragment_id: "prd-ai-cli-terminal-dr-003-interaction"
title: "架构治理 - 交互规格"
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

# 架构治理 - 交互规格 {#sec-interaction-spec}

## 1. 扫描触发交互 {#sec-scan-interaction}

### 1.1 按钮触发 {#sec-button-trigger}

- 用户在 Arch 模式下点击"扫描架构"，系统自动发送 `scan` 命令。
- 终端显示"正在扫描项目架构..."与实时进度。

### 1.2 命令触发 {#sec-command-trigger}

- 用户输入 `scan` 触发默认规则扫描。
- 用户输入 `scan --rule RULE-001` 仅扫描指定规则。
- 用户输入 `scan --all` 启用全部规则（含默认关闭规则）。

## 2. 治理项列表交互 {#sec-issue-list-interaction}

| 操作 | 触发方式 | 系统行为 |
|------|----------|----------|
| 查看方案 | 点击"查看方案" / 输入 `plan {id}` | 生成并展示治理方案卡片 |
| 跳过 | 点击"跳过" / 输入 `skip {id}` | 标记为 skipped，展示下一条 |
| 标记误报 | 点击"标记误报" / 输入 `fp {id}` | 标记为 false_positive，记录反馈 |
| 排序 | 输入 `sort by severity` / `sort by files` | 重新排序列表 |

## 3. 治理方案卡片交互 {#sec-plan-card-interaction}

| 操作 | 触发方式 | 系统行为 |
|------|----------|----------|
| 执行重构 | 点击按钮 / 输入 `fix {id}` | 校验权限后执行重构 |
| 跳过 | 点击按钮 / 输入 `skip {id}` | 标记为 skipped |
| 标记误报 | 点击按钮 / 输入 `fp {id}` | 标记为 false_positive |
| 查看 Diff | 点击 Diff 区 | 展开/折叠代码对比 |

## 4. 重构执行交互 {#sec-refactor-execution}

- 重构期间显示进度条与每步日志。
- 用户可输入 `abort` 中止执行。
- 中止后系统自动回滚已应用变更。
- 验证失败时展示失败日志与"重新规划"按钮。

## 5. ADR 编辑交互 {#sec-adr-interaction}

- 验证通过后自动弹出 ADR 草稿。
- 用户可在"原因"与"影响"字段补充内容。
- 点击"保存"后 ADR 正式发布并关联治理项。
- 点击"暂不保存"后 ADR 以草稿状态保存，用户可后续通过 `adr list` 查看。

## 6. 结果反馈 {#sec-result-feedback}

| 结果 | 终端消息 | 后续操作 |
|------|----------|----------|
| 扫描无结果 | `[系统] 未检测到架构问题` | 可调整规则重扫 |
| 治理项跳过 | `[系统] 已跳过 #{id}` | 继续处理其他项 |
| 误报标记 | `[系统] 已记录误报反馈` | 用于优化规则 |
| 重构成功 | `[成功] 已生成 ADR #{id}` | 可继续扫描 |
| 验证失败 | `[错误] 验证失败：{原因}` | 可重新规划 |
| 权限不足 | `[错误] 权限不足，无法执行重构` | 联系管理员 |
