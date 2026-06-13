#!/usr/bin/env python3
"""Rebuild garbled sections in _design-index.md from batch audit reports."""

# Read current _design-index.md
index_path = 'openspec/changes/sdlc-visualizer/detailed-design/_design-index.md'
with open(index_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find garbled region
start = None
end = None
for i, line in enumerate(lines):
    if '\ufffd' in line:
        if start is None:
            start = i
        end = i

print(f'Garbled region: lines {start+1}-{end+1}')

# Build replacement content for sections 7, 8, 9
replacement = """## 7. 第二批模块追加（引擎层）

| 模块编号 | 模块名称 | 目录 | 优先级 | 设计状态 | 版本 | 上游追溯 | 下游消费 |
|----------|----------|------|--------|----------|------|----------|----------|
| DR-007 | Skill Flow 编排引擎 | `feature-07-flow-engine/` | P0 | ✅ FROZEN | v1.0 | DR-007 详细需求 | DR-008, DR-016 |
| DR-008 | Skill 调度服务 | `feature-08-skill-executor/` | P0 | ✅ FROZEN | v1.0 | DR-008 详细需求 | DR-016 |
| DR-016 | PocketFlow 执行引擎 | `feature-16-pocketflow/` | P0 | ✅ FROZEN | v1.0 | DR-016 详细需求 | — |

### 第二批模块接口契约矩阵

| 消费方 | 提供方 | 契约类型 | 接口范围 | 状态 |
|--------|--------|----------|----------|------|
| DR-007 | DR-008 | Service 调用 | 触发 Stage 级 Skill 执行 | ✅ 已定义 |
| DR-007 | DR-016 | 非直接调用 | 通过 DR-008 间接调用 | ✅ 边界已明确 |
| DR-008 | DR-016 | Service 调用 | 下发 PocketFlow 各阶段执行 | ✅ 已定义（DR-008 §1.4 / DR-016 §2.1） |
| DR-008 | DR-007 | Service 调用 | 读取执行计划、Stage 就绪状态 | ✅ 已定义 |
| DR-016 | DR-008 | 事件/回调 | 实时推送阶段进度、日志、结果 | ✅ 已定义（DR-016 §4.3 PocketFlowResultDTO） |

### 第二批数据表归属

| 表名 | 定义模块 | 归属 | 被引用模块 | 说明 |
|------|----------|------|-----------|------|
| `execution_plans` | DR-007 | 模块独占 | DR-008 | 执行计划主表 |
| `execution_plan_nodes` | DR-007 | 模块独占 | — | 计划节点状态 |
| `execution_plan_groups` | DR-007 | 模块独占 | — | 并行组定义 |
| `bypass_records` | DR-007 | 模块独占 | — | 旁路审批记录 |
| `skill_executions` | DR-008 | 模块独占 | DR-016 | Skill 执行记录（调度层） |
| `execution_logs` | DR-008 | 模块独占 | — | 执行日志 |
| `pocketflow_executions` | DR-016 | 模块独占 | DR-008 | PocketFlow 执行实例（执行层） |
| `artifact_validations` | DR-016 | 模块独占 | — | 产物校验记录 |

### 第二批一致性检查

- 第二批与第一批的数据模型和枚举值完全兼容（见 `_batch2-audit-report.md` §3）。
- DR-008 与 DR-016 的 `PREP`/`EXEC`/`POST`/`RUNNING`/`COMPLETED`/`FAILED` 定义完全一致。

---

## 8. 第三批模块追加（表现层 + 旁路）

| 模块编号 | 模块名称 | 目录 | 优先级 | 设计状态 | 版本 | 上游追溯 | 下游消费 |
|----------|----------|------|--------|----------|------|----------|----------|
| DR-003 | 阶段详情面板 | `feature-03-stage-detail/` | P0 | ✅ FROZEN | v1.0 | DR-003 详细需求 | DR-004, DR-005 |
| DR-004 | 审批中心 | `feature-04-gate-center/` | P0 | ✅ FROZEN | v1.0 | DR-004 详细需求 | DR-003, DR-007 |
| DR-005 | 产物浏览器 | `feature-05-artifact-viewer/` | P0 | ✅ FROZEN | v1.0 | DR-005 详细需求 | DR-003 |
| DR-017 | HITL 旁路审批服务 | `feature-17-bypass/` | P1 | ✅ FROZEN | v1.0 | DR-017 详细需求 | DR-004, DR-007 |

### 第三批模块接口契约矩阵

| 消费方 | 提供方 | 契约类型 | 接口范围 | 状态 |
|--------|--------|----------|----------|------|
| DR-003 | DR-005 | Service 调用 | 产物内容加载、版本历史、diff、回滚 | ✅ 已定义 |
| DR-003 | DR-004 | Service 调用 | Gate 审批结果同步、驳回理由写批注 | ✅ 已定义 |
| DR-003 | DR-008 | WebSocket + REST | 执行日志实时流、PocketFlow 状态 | ✅ 已定义 |
| DR-004 | DR-003 | Service 调用 | 读取批注、写入 stage_review_status | ✅ 已定义（跨模块写待 interface-first-dev 契约化） |
| DR-004 | DR-017 | Service 调用 | 旁路审批记录查询、解锁时状态流转 | ✅ 已定义 |
| DR-004 | DR-007 | Service 调用 | 读取下游 Stage 列表 | ✅ 已定义 |
| DR-005 | DR-008 | Service 调用 | Git 快照、版本历史、diff、回滚 | ✅ 已定义 |
| DR-017 | DR-004 | Service 调用 | Gate 状态查询、旁路通过后解锁 | ✅ 已定义 |
| DR-017 | DR-007 | Service 调用 | 读取 Stage 状态、解锁 | ✅ 已定义 |

### 第三批数据表归属

| 表名 | 定义模块 | 归属 | 被引用模块 | 说明 |
|------|----------|------|-----------|------|
| `stage_annotations` | DR-003 | 模块独占 | DR-004 | 产物批注 |
| `review_submissions` | DR-003 | 模块独占 | — | 审查提交记录 |
| `review_suggestions` | DR-003 | 模块独占 | — | 全局修改建议 |
| `review_references` | DR-003 | 模块独占 | — | 参考资料 |
| `stage_review_status` | DR-003 | 模块独占 | DR-004 | Stage 审查状态（DR-004 通过 REST 更新 Gate 裁决后状态） |
| `gate_decisions` | DR-004 | 模块独占 | — | Gate 决策记录 |
| `gate_decision_history` | DR-004 | 模块独占 | — | 决策历史明细 |
| `gate_related_products` | DR-004 | 模块独占 | DR-003 | Gate 关联产物 |
| `artifact_files` | DR-005 | 模块独占 | DR-003 | 产物文件索引 |
| `artifact_versions` | DR-005 | 模块独占 | DR-003 | 产物版本记录 |
| `bypass_applications` | DR-017 | 模块独占 | DR-004 | 旁路申请 |
| `bypass_authorizations` | DR-017 | 模块独占 | — | 旁路授权 |
| `bypass_executions` | DR-017 | 模块独占 | — | 旁路执行 |
| `bypass_reviews` | DR-017 | 模块独占 | — | 旁路补审 |
| `bypass_alerts` | DR-017 | 模块独占 | — | 旁路告警 |

### 第三批跨模块写声明

- DR-004 通过 REST 调用 DR-003 的专用状态更新接口更新 `stage_review_status`，不直接操作数据库（见 `_batch3-audit-report.md` §1.4）。

---

## 9. 第四批模块追加（线框图链路）

| 模块编号 | 模块名称 | 目录 | 优先级 | 设计状态 | 版本 | 上游追溯 | 下游消费 |
|----------|----------|------|--------|----------|------|----------|----------|
| DR-010 | 复杂度路由面板 | `feature-10-complexity-router/` | P0 | ✅ FROZEN | v1.0 | DR-010 详细需求 | DR-009, DR-002 |
| DR-011 | C4 架构浏览器 | `feature-11-c4-navigator/` | P0 | ✅ FROZEN | v1.0 | DR-011 详细需求 | DR-018, DR-019, DR-020 |
| DR-018 | OpenUI 原型生成 | `feature-18-openui/` | P0 | ✅ FROZEN | v1.0 | DR-018 详细需求 | DR-020 |
| DR-019 | WireframeEngine | `feature-19-wireframe/` | P0 | ✅ FROZEN | v1.0 | DR-019 详细需求 | DR-020 |
| DR-020 | 原型-架构双向绑定 | `feature-20-proto-arch/` | P1 | ✅ FROZEN | v1.0 | DR-020 详细需求 | DR-011, DR-004 |
| DR-021 | 需求草图服务 | `feature-21-pagespec/` | P0 | ✅ FROZEN | v1.0 | DR-021 详细需求 | DR-003 |

### 第四批模块接口契约矩阵

| 消费方 | 提供方 | 契约类型 | 接口范围 | 状态 |
|--------|--------|----------|----------|------|
| DR-018 | DR-011 | Service 调用 | C4 Container DSL（提示词组装输入） | ✅ 已定义 |
| DR-019 | DR-011 | Service 调用 | C4 DSL 结构化领域对象（DomainMapper 输入） | ✅ 已定义 |
| DR-020 | DR-019 | Service 调用 | Wireframe 页面接口锚点、缺失接口标记 | ✅ 已定义 |
| DR-020 | DR-018 | Service 调用 | OpenUI HTML 接口触点 | ✅ 已定义 |
| DR-020 | DR-011 | Service 调用 | C4 DSL 基线回写、差异暂存 | ✅ 已定义 |
| DR-021 | 外部需求模块 | Service 调用 | 用户故事文本输入 | ✅ 已定义（外部模块） |
| DR-021 | DR-003 | 数据消费 | 草图审查批注 Tab 展示、偏转批注关联 | ✅ 已定义 |
| DR-010 | DR-009 | Service 调用 | 读取模板定义与 Stage 列表 | ✅ 已定义 |
| DR-010 | DR-005 | Service 调用 | 读取产物统计扫描 | ✅ 已定义 |

### 第四批数据表归属

| 表名 | 定义模块 | 归属 | 被引用模块 | 说明 |
|------|----------|------|-----------|------|
| `complexity_estimates` | DR-010 | 模块独占 | DR-001 | 复杂度评估记录 |
| `path_decisions` | DR-010 | 模块独占 | DR-001 | 路径决策日志 |
| `project_path_config` | DR-010 | 模块独占 | DR-002, DR-009 | 项目路径配置 |
| `c4_dsl_store` | DR-011 | **公共表** | DR-018, DR-019, DR-020, DR-012 | C4 DSL 存储（auto/manual 双层级） |
| `c4_node_file_mappings` | DR-011 | 模块独占 | — | C4 节点文件映射（反向代码定位） |
| `openui_generations` | DR-018 | 模块独占 | DR-020 | OpenUI 生成记录 |
| `openui_generation_pages` | DR-018 | 模块独占 | DR-020 | OpenUI 生成页面明细 |
| `wireframe_pages` | DR-019 | 模块独占 | DR-020 | 线框图页面 |
| `wireframe_navigation_edges` | DR-019 | 模块独占 | DR-020 | 线框图导航关系 |
| `wireframe_page_type_configs` | DR-019 | 模块独占 | — | 页面类型配置模板 |
| `binding_scans` | DR-020 | 模块独占 | — | 接口覆盖度扫描记录 |
| `architecture_changes` | DR-020 | 模块独占 | DR-004 | 架构变更记录（Gate 评审） |
| `sketches` | DR-021 | 模块独占 | DR-003 | 草图记录 |
| `sketch_annotations` | DR-021 | 模块独占 | DR-003 | 草图审查批注 |

### 第四批跨模块写声明

- DR-020 回写 C4 DSL 至 DR-011 通过 `PUT /api/v1/c4/dsl/{project_id}/{level}` REST 接口完成，不直接操作数据库。
- DR-020 触发 Gate 评审至 DR-004 通过 `POST /api/v1/binding/review/{architecture_change_id}` 完成。

---
"""

# Replace garbled lines
new_lines = lines[:start] + [replacement] + lines[end+1:]

with open(index_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f'Replaced lines {start+1}-{end+1} with reconstructed content')
print(f'New file size: {len("".join(new_lines))} chars')
