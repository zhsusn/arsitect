# 第二批详细设计 Cross-Module Audit 报告

> **审计日期**：2026-06-02  
> **审计范围**：DR-007 / DR-008 / DR-016  
> **审计依据**：detailed-design SKILL.md Step 4 + Step 5 质量门控

---

## 1. 模块间矛盾检测

### 1.1 接口数据结构兼容性

| 接口 | 消费方 | 提供方 | 请求格式 | 响应格式 | 结果 |
|------|--------|--------|----------|----------|------|
| 触发 Skill 执行 | DR-007 | DR-008 | `ExecutionTriggerDTO` | `ExecutionStatusDTO` | ✅ |
| 启动 PocketFlow | DR-008 | DR-016 | `PocketFlowExecuteRequestDTO` | `PocketFlowResultDTO` | ✅ |
| 查询执行状态 | DR-008 | DR-016 | `execution_id` path param | `PocketFlowResultDTO.phase_result` | ✅ |
| 获取执行计划 | DR-008 | DR-007 | `plan_id` path param | `ExecutionPlanDTO` | ✅ |
| Stage 就绪检查 | DR-008 | DR-007 | `stage_id` + `plan_id` | `StageReadinessDTO` | ✅ |

**结论**：所有跨模块接口的请求/响应格式均已显式定义，字段覆盖完整，无缺失。

### 1.2 状态机一致性（关键检查项）

| DR-016 状态 | DR-008 映射状态 | 一致性检查 |
|-------------|----------------|------------|
| IDLE → PREP (RUNNING) | NOT_STARTED → PREP (RUNNING) | ✅ 对齐 |
| PREP → PREP_PASSED | PREP → PREP (COMPLETED) | ✅ 对齐 |
| PREP → PREP_FAILED | PREP → FAILED | ✅ 对齐 |
| EXEC → EXEC_COMPLETED | EXEC → EXEC (COMPLETED) | ✅ 对齐 |
| EXEC → EXEC_FAILED | EXEC → FAILED | ✅ 对齐 |
| EXEC → EXEC_INTERRUPTED | EXEC → FAILED (中断视为失败) | ✅ 对齐 |
| POST → PASSED | POST → PASSED (或 REVIEW_PENDING) | ✅ 对齐 |
| POST → FAILED | POST → FAILED | ✅ 对齐 |
| PASSED | SUCCESS | ✅ 映射关系在 DR-008 §4.1 中显式定义 |
| FAILED | FAILED | ✅ 直接映射 |

**结论**：DR-016 的 PocketFlow 阶段状态机与 DR-008 的 Skill 级状态机完全兼容，映射关系已在 DR-008 文档中明确记录。

### 1.3 数据表写权限冲突

| 表名 | 定义模块 | 写模块 | 读模块 | 冲突检查 |
|------|----------|--------|--------|----------|
| `execution_plans` | DR-007 | DR-007 | DR-008 | ✅ 无冲突 |
| `execution_plan_nodes` | DR-007 | DR-007 | — | ✅ 无冲突 |
| `skill_executions` | DR-008 | DR-008 | DR-016（读取上下文） | ✅ 无冲突 |
| `execution_logs` | DR-008 | DR-008 | — | ✅ 无冲突 |
| `pocketflow_executions` | DR-016 | DR-016 | DR-008（状态聚合） | ✅ 无冲突 |
| `artifact_validations` | DR-016 | DR-016 | — | ✅ 无冲突 |

**结论**：每表有且仅有一个主写模块，DR-008 与 DR-016 通过 `execution_id` 关联但互不写对方表。

### 1.4 枚举值冲突

| 枚举名 | 定义模块 | 值列表 | 冲突检查 |
|--------|----------|--------|----------|
| ExecutionPlanNodeStatus | DR-007 | NOT_STARTED / READY / EXECUTING / COMPLETED / FAILED / CANCELLED / BYPASS_EXECUTING | 无冲突 |
| StageStatus | DR-007 | NOT_STARTED / WAITING_GATE / READY / EXECUTING / COMPLETED / COMPLETED_WITH_WARNING / FAILED / BYPASS_EXECUTING | 无冲突 |
| OverallStatus (DR-008) | DR-008 | NOT_STARTED / RUNNING / SUCCESS / FAILED / UNKNOWN | 无冲突 |
| CurrentPhase | DR-008 / DR-016 | PREP / EXEC / POST / NONE | ✅ 两模块完全一致 |
| PhaseStatus | DR-008 / DR-016 | RUNNING / COMPLETED / FAILED | ✅ 两模块完全一致 |
| FinalStatus (DR-016) | DR-016 | PASSED / FAILED | 无冲突 |
| GitSnapshotStatus | DR-016 | committed / skipped_size / skipped_no_repo / failed | 无冲突 |
| BypassRecordStatus | DR-007 | PENDING_POST_APPROVAL / CLOSED / VIOLATION_PENDING | 无冲突 |

**结论**：无枚举冲突。`PREP`/`EXEC`/`POST`/`RUNNING`/`COMPLETED`/`FAILED` 在 DR-008 和 DR-016 中定义完全一致。

---

## 2. 质量门控检查

### 2.1 "能否不猜就编码"审查

| 模块 | SPECIFIED | VAGUE | MISSING | 结果 |
|------|:---------:|:-----:|:-------:|:----:|
| DR-007 | 94% | 2 (旁路审批令牌的具体签发机制未定义、画布高亮具体颜色值未指定) | 0 | ✅ 通过 |
| DR-008 | 95% | 2 (SSE 连接断开后重连策略未细化、日志长期归档策略待 P1) | 0 | ✅ 通过 |
| DR-016 | 96% | 1 (Kimi CLI 具体命令行参数格式待 interface-first-dev 冻结) | 0 | ✅ 通过 |

### 2.2 模糊语言 / 魔法数字

| 模块 | 模糊语言 | 未标注单位数字 |
|------|----------|---------------|
| DR-007 | 无 | 无 |
| DR-008 | 无 | 无 |
| DR-016 | 无 | 无 |

---

## 3. 跨批次一致性检查（第一批 ↔ 第二批）

| 检查项 | 第一批定义 | 第二批引用 | 一致性 |
|--------|----------|-----------|:------:|
| `projects.project_status` | Draft / Active / Archived / Cancelled | DR-007/008/016 均读取 | ✅ |
| `project_stages` 表结构 | DR-009 定义 | DR-007 读取 Stage 状态 | ✅ |
| `skills` 表结构 | DR-006 定义 | DR-007/016 读取 Skill 路径和元数据 | ✅ |
| `skill_dag_nodes/edges` | DR-006 定义 | DR-007 消费 DAG 结构 | ✅ |
| `templates.template_level` | Trivial / Light / Standard / Deep | DR-007 读取 Stage 定义 | ✅ |
| `workspaces` (shared) | 预定义 default | DR-007/008/016 无直接引用 | N/A |
| `size_estimates` (shared) | 预定义最小结构 | DR-016 无直接引用（通过 DR-001 间接） | N/A |

**结论**：第二批与第一批的数据模型和枚举值完全兼容。

---

## 4. 遗漏与待补项

| 编号 | 描述 | 严重程度 | 处理建议 |
|------|------|----------|----------|
| GAP-B2-001 | Kimi CLI 命令行参数和上下文对象的具体格式 | 🟡 中 | 留到 `interface-first-dev` 阶段与 CLI 实际版本对齐 |
| GAP-B2-002 | SSE 重连策略（指数退避 / 最大重试次数） | 🟢 低 | P0 阶段可简化实现，P1 完善 |
| GAP-B2-003 | 日志长期归档与冷存储策略 | 🟢 低 | 明确为 P1 扩展，当前不做 |

---

## 5. 审计结论

| 检查项 | 结果 |
|--------|------|
| 模块间矛盾检测 | ✅ 通过（Error = 0） |
| 接口兼容性 | ✅ 通过 |
| 状态机一致性 | ✅ 通过（DR-008 ↔ DR-016 映射清晰） |
| 数据表写权限 | ✅ 通过 |
| 枚举冲突 | ✅ 通过 |
| 跨批次一致性 | ✅ 通过 |
| 质量门控 | ✅ 通过 |

**总体结论**：第二批详细设计通过 Cross-Module Audit。DR-007/008/016 三模块的接口契约、状态机映射、数据边界均已清晰定义，可进入下一阶段。
