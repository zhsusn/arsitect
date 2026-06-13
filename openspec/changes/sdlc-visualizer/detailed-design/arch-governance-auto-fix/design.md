# 架构治理中心自动修复能力设计

## 变更背景

架构治理中心（`ArchGovernancePage`）目前只能展示结构分析、设计↔代码一致性、跨层文档一致性三类问题，但修复仍依赖人工定位文档/代码/DSL/registry。随着项目规模扩大，warn/info 数量持续增加，需要引入可解释、可回滚、带人工闸门的自动修复能力。

## 设计目标

1. 对治理中心的问题自动判定根因（文档不规范 / 文档缺漏 / 文档与代码不一致 / 代码未实现 / 关系缺失 /  intentional 设计 / 需人工决策）。
2. 根据根因调用规则修复、C4 工具或 LLM（Kimi CLI 方式）生成修复方案。
3. 所有变更先以 diff 预览，经用户确认后再应用；高风险变更必须人工确认。
4. 支持单条修复、批量修复、一键回滚与审计日志。

## 问题来源与根因分类

| 来源 | 模块 | 已有字段 |
|---|---|---|
| 结构分析 | `app/c4/analyzer.py` | `fix_hint` |
| 设计↔代码一致性 | `app/c4/consistency_checker.py` | `fix_action`（UPDATE_DOC / UPDATE_CODE / BOTH） |
| 跨层文档一致性 | `app/c4/cross_layer_validator.py` | `suggestion` |
| 文档入站检查 | `app/docforge/doc_linter.py` | `auto_fixable`、`fix_strategy` |

根因类型：

- `DOC_NON_COMPLIANT`：文档本身不规范（命名、Front Matter、container_id 写错）。
- `DOC_INCOMPLETE`：文档缺定义（容器、组件、实体、接口、关系）。
- `DOC_CODE_MISMATCH`：文档与代码命名/归属不一致。
- `CODE_MISSING`：设计里有，代码没实现。
- `RELATIONSHIP_MISSING`：实体存在，但关系抽取遗漏。
- `INTENTIONAL_DESIGN`：本身就是合理的孤立/未实现（UI primitive、P1 概念类、跨领域 helper）。
- `NEEDS_HUMAN_DECISION`：循环依赖、页面类型冲突等需要人判断。

## LLM 选型

- **主入口**：Kimi CLI Client。
  - 命令：`kimi --print --quiet --prompt "..."`
  - 优点：复用当前 Kimi 账号与模型配置，无需额外 API Key。
  - 约束：Prompt 必须要求仅返回结构化结果（JSON），禁止执行文件操作。
- **可插拔**：同时保留 OpenAI-compatible HTTP Gateway，便于后续切换。

新增配置项（`backend/app/core/config.py`）：

```python
GOVERNANCE_LLM_PROVIDER: str = "kimi"          # kimi | openai | none
KIMI_CLI_PATH: str = "kimi"
OPENAI_API_BASE: str | None = None
OPENAI_API_KEY: str | None = None
OPENAI_MODEL: str = "gpt-4o-mini"
```

## 新增模块

```
backend/app/c4/governance_fix/
├── __init__.py
├── models.py              # GovernanceIssue / ChangeSet / FixPlan / FixResult
├── classifier.py          # 根因分类器
├── context.py             # 为 LLM 构造上下文（文档/代码片段）
├── planner.py             # FixPlanner：issue + 根因 -> FixPlan
├── applier.py             # 应用 ChangeSet（dry-run / apply）
├── backup.py              # 文件备份与回滚
├── history.py             # 审计日志读写
├── llm_gateway.py         # LLMGateway / KimiCLIGateway / OpenAILLMGateway
├── service.py             # 对外服务
└── strategies/
    ├── base.py
    ├── mark_intentional.py
    ├── reextract_registry.py
    ├── rename_node.py
    ├── fix_container_id.py
    ├── add_container.py
    ├── add_component_doc.py
    ├── create_code_skeleton.py
    ├── add_relationship.py
    ├── llm_generate_doc.py
    └── manual.py
```

## 修复策略矩阵

| 规则 | 根因 | 策略 | 风险 |
|---|---|---|---|
| `C4-ORPHAN-001` | `INTENTIONAL_DESIGN` | 标记 `intentional_orphan: true` | LOW |
| `C4-ORPHAN-001` | `RELATIONSHIP_MISSING` | 运行 `registry_extractor.extract_registry` | LOW |
| `C4-ORPHAN-001` | `CODE_MISSING` | 生成代码骨架或从 DSL 移除 | MEDIUM |
| `C4-NAME-001` | `DOC_NON_COMPLIANT` | 规范化 ID，保留 alias | LOW |
| `C4-LEVEL-001` | `DOC_NON_COMPLIANT` | 根据文件路径修正 `container_id` | LOW |
| `C4-DISCONN-001` | `RELATIONSHIP_MISSING` | 先重抽 registry；仍残留则 LLM 建议关系 | MEDIUM |
| `C4-CYCLE-*` | `NEEDS_HUMAN_DECISION` | LLM 生成打破循环方案，不自动改代码 | HIGH |
| `CON-C2M-001` | `CODE_MISSING` | 创建目录骨架或标记 intentional | LOW/MEDIUM |
| `CON-M2C-001` | `DOC_INCOMPLETE` | 从代码目录名补 L2 容器（模板/LLM） | MEDIUM |
| `CON-C2F-001` | `DOC_CODE_MISMATCH` | 更新文档组件名/alias | LOW |
| `CON-C2F-001` | `CODE_MISSING` | 生成类/函数骨架 | MEDIUM |
| `CON-F2C-001` | `DOC_INCOMPLETE` | 补 L3 组件定义（模板/LLM） | MEDIUM |
| `VAL-001` | `RELATIONSHIP_MISSING` | 在 ARCH 中补 external_system 关系 | MEDIUM |
| `VAL-002/006/007` | `DOC_INCOMPLETE` | 补 entity 属性 / table 字段 | MEDIUM |
| `VAL-003/004` | `DOC_NON_COMPLIANT` | 修正 `container_id` 或补容器 | LOW/MEDIUM |
| `VAL-005` | `DOC_INCOMPLETE` | 补 API_DESIGN 接口契约 | MEDIUM |
| `VAL-008` | `NEEDS_HUMAN_DECISION` | 仅建议，不自动修 | HIGH |
| DocLinter | 多种 | 复用 `DocLinter.fix()` | LOW |

## API 设计

挂载在 `app/api/v1/c4.py`：

- `POST /c4/governance/fix-plan`
  - Body: `{ project_id, issue_ids[], dry_run: true }`
  - Response: `FixPlanDTO`
- `POST /c4/governance/fix-apply`
  - Body: `{ project_id, plan_id, confirmed: true }`
  - Response: `FixResultDTO`（包含 applied_changes、new_analysis）
- `POST /c4/governance/fix-batch`
  - Body: `{ project_id, severity[], auto_only: true }`
  - Response: `FixPlanDTO` 或 `FixResultDTO`
- `POST /c4/governance/fix-rollback`
  - Body: `{ project_id, fix_session_id }`
  - Response: `{ restored: true }`
- `GET /c4/governance/fix-history`
  - Query: `project_id`
  - Response: `list[FixHistoryDTO]`

## 关键流程

1. 用户勾选 issue → 点击「生成修复方案」。
2. 后端：`IssueNormalizer` 统一格式 → `Classifier` 判定根因 → `Planner` 选择 `Strategy` → 生成 `ChangeSet` 列表。
3. `Applier` 在 dry-run 模式下计算每个 `ChangeSet` 的 `before/after` diff。
4. 前端弹窗展示：根因、风险等级、diff、影响文件数。
5. 用户确认后 → `fix-apply`。
6. 后端：`Backup` 备份 → 顺序应用 → 对 DSL 变更同步 DB → 重新运行三类验证 → 返回新结果。

## 安全与回滚

- 仅 `LOW` 风险且 `auto_applicable=True` 的变更可一键应用；`MEDIUM/HIGH` 默认不勾选。
- 代码生成只出骨架（签名 + 空实现 + TODO），不写业务逻辑。
- 所有文件修改前复制到 `.arsitect/backups/{timestamp}/{path}`。
- 提供 `fix-rollback` 一键恢复。
- 审计日志记录：issue、根因、变更路径、操作人、回滚标记。
- 禁止自动执行 git commit/push、数据库迁移、删除已有业务代码。

## 实现阶段

### Phase 1：基础设施 + 低风险自动修复
- 配置、LLM Gateway、models、classifier、backup、applier、service。
- 策略：MarkIntentional、ReExtractRegistry、RenameNode、FixContainerId、DocLinter。
- API：`fix-plan`、`fix-apply`、`fix-batch`、`fix-rollback`、`fix-history`。
- 审计表与迁移。

### Phase 2：LLM 辅助与中风险修复
- Kimi CLI prompt 工程，要求返回 JSON。
- 策略：AddContainer、AddComponentDoc、CreateCodeSkeleton、AddRelationship、LLMGenerateDoc。
- 前端修复方案弹窗与批量选择。

### Phase 3：智能化
- 批量计划冲突检测。
- 根据用户接受/拒绝记录优化策略优先级。
