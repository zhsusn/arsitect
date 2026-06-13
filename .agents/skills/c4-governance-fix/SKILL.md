---
name: c4-governance-fix
description: 当用户在架构治理中心点击“生成修复方案”、或提到“C4修复”、“治理修复”、“修复架构问题”、“修复一致性”时触发。基于后端 FixPlanner 为 C4 治理问题生成可预览的修复方案，并辅助人工确认。
version: 1.0.0
---

# C4 治理自动修复 Skill

## 触发条件

- 用户说：
  - “生成修复方案” / “帮我修复这些架构问题”
  - “C4 修复” / “治理修复” / “修复一致性”
  - “这个组件没有代码，帮我生成骨架”
  - “DSL 里缺了一条关系，补一下”
- 用户在**架构治理中心 (ArchGovernance)** 页面选中问题后点击“生成修复方案”。

## 输入

- `project_id`：当前项目 ID
- `issues`：由 `/api/v1/c4/analyze` 返回的问题列表（至少包含 `issue_id`、`rule_id`、`severity`、`message`、`node_ids`、`c4_node_id`、`code_entity_id`、`root_cause`）
- 可选 `context`：额外上下文，会透传给后端策略

## 输出

- 一份可预览的修复计划，包含多个 `ChangeSet`：
  - `action`：操作类型，如 `EDIT_DSL`、`CREATE_FILE`、`DELETE_FILE`、`TOGGLE_INTENTIONAL_ORPHAN` 等
  - `target_path`：目标文件或 DSL 路径
  - `before` / `after`：变更前后内容
  - `rationale`：变更理由
  - `risk_level`：风险等级（LOW / MEDIUM / HIGH）
  - `auto_applicable` / `requires_confirmation`：是否自动执行、是否需要人工确认

## 执行流程

### Step 1. 收集问题

从当前对话或前端页面获取 `project_id` 和 `issues`。
如果 `issues` 为空，提示用户先执行“重新分析”。

### Step 2. 调用后端生成修复计划

向后端发送请求：

```http
POST /api/v1/c4/governance/fix-plan?project_id={project_id}
Content-Type: application/json

{
  "issues": [
    {
      "issue_id": "con-0",
      "source": "consistency",
      "rule_id": "CON-C2F-001",
      "severity": "ERROR",
      "message": "组件 user-card 在代码中未找到对应实现",
      "c4_node_id": "user-card",
      "root_cause": "CODE_MISSING"
    }
  ],
  "context": {}
}
```

### Step 3. 向用户展示修复计划

按风险等级分组展示：

- **低风险 / 可自动应用**（如重命名 ID、修正 container_id）
- **中风险 / 需确认**（如新增组件、补充关系）
- **高风险 / 务必确认**（如删除孤儿文件、移除关系）

每条 ChangeSet 必须展示：
- 目标路径
- 操作类型
- 变更摘要
- 风险等级
- 理由

### Step 4. 人工确认

对每条 `requires_confirmation=true` 的 ChangeSet，必须获得用户明确同意后方可继续。

允许的确认话术：
- “应用这条”
- “全部应用”
- “确认修复”

### Step 5. 应用变更（可选，当前版本仅生成预览）

当前版本 Skill 仅生成**预览计划**，不自动应用。
如需应用，应调用对应专用接口：
- `EDIT_DSL` → `POST /api/v1/c4/dsl/edit`
- `CREATE_FILE` / `DELETE_FILE` → 由用户通过 IDE/CLI 操作，或调用后续文件操作 API
- `TOGGLE_INTENTIONAL_ORPHAN` → `POST /api/v1/c4/registry/orphans/{component_id}/intentional`

## 安全与纪律

- 禁止自动删除代码文件；`DELETE_FILE` 必须人工二次确认。
- 禁止自动覆盖无版本控制的 DSL；应用前确保已生成版本或备份。
- 如果用户未明确确认，仅返回预览计划，不执行任何写操作。
- 不要在输出中包含真实密钥、Token 或数据库连接串。

## 示例对话

**用户**：帮我修一下 C4 一致性问题。  
**Agent**：已收集到 3 条一致性问题，正在调用修复策略生成预览计划…

> 1. `CREATE_FILE` → `frontend/src/components/user-card.tsx`（中风险）  
>    理由：为 DSL 组件 `user-card` 生成 React 骨架。
>
> 2. `EDIT_DSL` → `dsl://sdlc-visualizer`（中风险）  
>    理由：补充 `dashboard -> backend-api` 依赖关系。

请确认要应用哪些变更？
