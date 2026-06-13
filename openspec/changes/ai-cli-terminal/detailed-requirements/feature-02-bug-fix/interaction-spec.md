---
doc_type: "PRD"
fragment_id: "prd-ai-cli-terminal-dr-002-interaction"
title: "Bug 修复 - 交互规格"
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

# Bug 修复 - 交互规格 {#sec-interaction-spec}

## 1. 异常输入交互 {#sec-error-input-interaction}

### 1.1 粘贴触发 {#sec-paste-trigger}

- 用户在 Bug 模式下粘贴多行文本，系统自动识别为异常输入。
- 若内容包含常见错误关键词（如 `Error`、`Exception`、`Failed`），自动触发分析。
- 用户也可输入 `analyze {文本}` 手动触发。

### 1.2 历史推荐交互 {#sec-similar-interaction}

- 系统提示"发现历史同类问题 #{id}（匹配度 {percent}%），输入 `similar` 查看"。
- 用户输入 `similar` 后，终端展示历史方案摘要。
- 用户可输入 `use {id}` 直接应用历史方案，仍需经过确认流程。

## 2. 修复方案卡片交互 {#sec-card-interaction}

| 操作 | 触发方式 | 系统行为 |
|------|----------|----------|
| 执行修复 | 点击按钮 / 输入 `Y` | 校验权限与风险后执行 |
| 忽略 | 点击按钮 / 输入 `N` | 记录状态为 ignored，发送确认消息 |
| 编辑后执行 | 点击按钮 / 输入 `edit` | 展开编辑器，用户确认后执行 |
| 查看历史 | 输入 `similar` | 展示历史同类方案 |

## 3. 高风险确认交互 {#sec-high-risk-interaction}

- 高风险方案点击"执行修复"后，弹出模态框。
- 模态框提供两个选项："继续执行（需权限）"、"取消并生成 PR（P2）"。
- 用户选择"继续执行"后，系统再次要求输入 `confirm high-risk` 防止误触。

## 4. 执行过程交互 {#sec-execution-interaction}

- 执行期间显示进度条与实时日志。
- 用户可点击"中止"或输入 `abort` 终止当前执行。
- 中止后系统回滚已应用变更并提示"已中止，未保存修改"。

## 5. 结果反馈 {#sec-result-feedback}

| 结果 | 终端消息 | 后续操作 |
|------|----------|----------|
| 验证通过 | `[成功] 已修复 #{id}` | 可继续输入新异常 |
| 验证失败 | `[错误] 验证失败：{原因}` | 可重新生成方案或放弃 |
| 忽略 | `[系统] 已忽略该问题` | 记录已保存 |
| 权限不足 | `[错误] 权限不足，无法执行修复` | 联系管理员 |

## 6. 编辑器交互 {#sec-editor-interaction}

- 编辑器默认展示 Diff 视图，支持左侧只读、右侧可编辑。
- 用户修改后点击"预览效果"，系统展示修改后的 Diff。
- 点击"确认执行"后，使用编辑后的 Diff 进入执行流程。
