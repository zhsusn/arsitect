---
doc_type: API_DESIGN
fragment_id: api-design-sdlc-visualizer-899
title: Doc Quality Gate 检查报告
version: 1.0.0
version_type: BASELINE
author: agent-migration
tags:
- sdlc-visualizer
- architecture
status: DRAFT
iteration: sdlc-visualizer
dependencies:
- fragment_id: arch-sdlc-visualizer-001
  version: '1.0'
- fragment_id: arch-sdlc-visualizer-002
  version: 1.0.0
- fragment_id: db-design-sdlc-visualizer-shared-607
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat01-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat03-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat04-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat05-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat06-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat07-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat08-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat09-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat10-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat11-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat12-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat13-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat14-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat15-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat16-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat17-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat18-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat19-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat20-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat21-628
  version: 1.0.0
- fragment_id: prd-sdlc-visualizer-feat02-629
  version: 1.0.0
c4_binding:
  level: L3
---

# Doc Quality Gate 检查报告

---

## 1. 摘要统计 {#sec-1-zhaiyaotongji}
| 类别 | 数量 | 状态 |
|------|:----:|------|
| 🔴 阻断级问题 | 42 | 需人工处理 |
| 🟡 警告级问题 | 20 | 建议修复 |
| 🟢 提示级问题 | 14 | 可选优化 |
| ✅ 已自动修复 | 4 | 已完成 |
| ⏳ 待人工确认 | 38 | 需 sign-off |

### 按文件分布 {#sec-anwenjianfenbu}
| 文件/目录 | 阻断 | 警告 | 提示 | 已修复 |
|-----------|:----:|:----:|:----:|:------:|
| 20 个 module-design.md | 35 | 14 | 9 | 1 |
| _design-index.md | 3 | 2 | 2 | 3 |
| shared/_index.md | 0 | 1 | 1 | 0 |
| shared/api-spec.md + design.md | 0 | 2 | 0 | 0 |
| openapi.yaml | 2 | 2 | 0 | 1 |
| parallel-dev-plan.md | 0 | 0 | 2 | 0 |

---

## 2. 已自动修复项 {#sec-2-u5df2zidongxiufuu9879}
| # | 文件 | 问题 | 修复内容 |
|---|------|------|----------|
| 1 | `_design-index.md` | 13 个 Form Feed 控制字符（`\x0c`）混入目录路径 | 将 `\x0c` 替换为 `f`，恢复 `feature-` 前缀 |
| 2 | `_design-index.md` | 变更历史仅记录第一批和第五批，缺失第二~四批 | 补充 v1.1~v1.3 及 v2.1~v2.2 变更记录 |
| 3 | `openapi.yaml` | `/files/upload` 错误声明 `application/json` | 修正为 `multipart/form-data`，补充 file/purpose/project_id 字段 |
| 4 | `feature-17-bypass/module-design.md` | SQL 语法错误：`CHECK LENGTH ≥ 20` | 修正为 `CHECK(LENGTH(review_opinion) >= 20)` |

---

## 3. 阻断级问题清单（必须修复） {#sec-3-u963bu65adjiwentiu6e05danu5fc5}
### 3.1 结构完整性（C1）— 35 项 {#sec-31-jiegouwanu6574xingc1-35-u9879}
**问题模式**：全部 20 个 module-design.md 的 §5 章节标题为「测试策略」，而非 SKILL 规范要求的「边界条件与异常处理」。

| 模块 | 当前 §5 标题 | 期望 §5 标题 | 行号 |
|------|-------------|-------------|:----:|
| DR-001 | 测试策略 | 边界条件与异常处理 | ~502 |
| DR-003 | 测试策略 | 边界条件与异常处理 | ~444 |
| DR-004 | 测试策略 | 边界条件与异常处理 | ~455 |
| DR-005 | 测试策略 | 边界条件与异常处理 | ~402 |
| DR-006 | 测试策略 | 边界条件与异常处理 | ~564 |
| DR-007 | 测试策略 | 边界条件与异常处理 | ~443 |
| DR-008 | 测试策略 | 边界条件与异常处理 | ~360 |
| DR-009 | 测试策略 | 边界条件与异常处理 | ~531 |
| DR-010 | 测试策略 | 边界条件与异常处理 | ~318 |
| DR-011 | 测试策略 | 边界条件与异常处理 | ~262 |
| DR-012 | 测试策略 | 边界条件与异常处理 | ~460 |
| DR-013 | 测试策略 | 边界条件与异常处理 | ~507 |
| DR-014 | 测试策略 | 边界条件与异常处理 | ~628 |
| DR-015 | 测试策略 | 边界条件与异常处理 | ~585 |
| DR-016 | 测试策略 | 边界条件与异常处理 | ~391 |
| DR-017 | 测试策略 | 边界条件与异常处理 | ~493 |
| DR-018 | — | 边界条件与异常处理 | — |
| DR-019 | — | 边界条件与异常处理 | — |
| DR-020 | — | 边界条件与异常处理 | — |
| DR-021 | — | 边界条件与异常处理 | — |

> **说明**：部分模块（DR-018~021）§5 可能以其他形式存在，需人工确认。

**附加问题**：DR-001~DR-017 中 §2 与 §3 编号/内容互换（§2 为「接口定义」、§3 为「数据表结构」），与标准原子章节顺序（§2 数据模型、§3 接口设计）不一致。

### 3.2 状态一致性（I3）— 17 项 {#sec-32-zhuangtaiyiu81f4xingi3-17-u98}
**问题模式**：全部 20 个 module-design.md 的 YAML Frontmatter 状态标记为 `Draft` 或 `Draft → Active`，未标记为 `FROZEN` 或「已完成」。

### 3.3 数据一致性（C2）— 4 项 {#sec-33-shujuyiu81f4xingc2-4-u9879}
| # | 涉及模块 | 问题描述 | 严重程度 |
|---|----------|----------|:--------:|
| 1 | DR-001 | 状态机图允许 `Active → Cancelled`，但校验规则表明确写「直接阻断，提示先归档而非取消」 | 高 |
| 2 | DR-003 | `VersionHistoryItemDTO.operation_type` 含 `regeneration`，但 `artifact_versions` 表枚举不含此值 | 高 |
| 3 | DR-004 | `GateHistoryRecordDTO.decision_type` 枚举缺 `retry`（表定义含 `retry`） | 高 |
| 4 | DR-017 | `bypass_applications.status` 为 TEXT 无 CHECK 约束，与 DTO 的 9 状态枚举不一致 | 高 |
| 5 | DR-017 | `bypass_reviews.conclusion` 为 TEXT NOT NULL 无 CHECK，与 DTO 的 3 值枚举不一致 | 高 |

### 3.4 跨文档冲突 — 3 项 {#sec-34-u8de8wendangu51b2u7a81-3-u987}
| # | 涉及文件 | 问题描述 |
|---|----------|----------|
| 1 | `_design-index.md` vs `db-schema.md` | `project_members`、`operation_logs` 归属冲突：前者标为「公共表（待提取）」，后者明确列为「模块独占」 |
| 2 | `_design-index.md` 内部 | `rework_events` 写方：第 10 节写 DR-013，第 11.3 节写 DR-003/004/008，自相矛盾 |
| 3 | `openapi.yaml` | 分页响应 `data.items` 均引用 `PageResponse` 而非对应实体 Schema（系统性问题，影响 11 个接口） |

### 3.5 编码损坏 — 1 项 {#sec-35-bianmau635fu574f-1-u9879}
| # | 文件 | 问题描述 |
|---|------|----------|
| 1 | `_design-index.md` | 第 7~9 节（第二批/第三批/第四批追加）含 1734 个 UTF-8 替换字符（U+FFFD），内容不可读。**Form Feed 已修复，乱码区域待人工重建。** |

---

## 4. 警告级问题清单（建议修复） {#sec-4-jinggaojiwentiu6e05danjianu8ba}
### 4.1 引用完整性（C3） {#sec-41-yinyongwanu6574xingc3}
| # | 涉及模块 | 问题描述 |
|---|----------|----------|
| 1 | DR-001~DR-016 | 共 16 个模块未引用 `shared/api-spec.md`（公共 REST 接口规范） |
| 2 | DR-010 | 未引用 `shared/db-schema.md`（模块独占表含外键依赖） |
| 3 | DR-017 | 未引用 `shared/db-schema.md`（定义了 5 张数据表） |
| 4 | DR-005 | `ArtifactTreeNodeDTO` 引用未定义的 `StageStatus` 类型 |

### 4.2 数值/术语不一致（C2/I2） {#sec-42-shuu503cu672fu8bedbuyiu81f4c2}
| # | 涉及模块 | 问题描述 |
|---|----------|----------|
| 1 | DR-006 | `SkillResponseDTO` 缺少 `parse_error_reason` 字段（表中有） |
| 2 | DR-007 | `PlanValidationResultDTO.error_code` 前缀与 §2.3 错误码定义不一致（无 `PLAN_` 前缀） |
| 3 | DR-008 | `BYPASSED` 状态无任何源状态指向（孤立状态） |
| 4 | DR-008 | `ExecutionStatusDTO.overall_status` 未覆盖内部状态机的 `REVIEW_PENDING`/`REVISION_REQUESTED` |
| 5 | DR-010 | `TriageResultDTO.scores` 为 number（可小数），但表字段为 INTEGER |
| 6 | DR-011 | `C4GenerationResultDTO.confidence` 为分层对象，但表 `c4_dsl_store.confidence` 为单个 REAL |
| 7 | DR-014 | `StageProgressCardDTO.status` 缺少 `rework` 状态（状态机已定义） |
| 8 | DR-016 | `PhaseResultDTO.status` 用 `COMPLETED`，但表用 `PASSED` |
| 9 | DR-017 | `UNIQUE(gate_id, status)` 约束语义与业务意图（仅一条活跃申请）不符 |
| 10 | DR-020 | `ReviewResultDTO.decision` 用 `pass`，但 `gate_decisions.decision_type` 用 `approve` |
| 11 | api-spec.md vs design.md | 分页 DTO 命名不一致：`PageResponse` vs `PageResponseDTO` |

### 4.3 其他 {#sec-43-qita}
| # | 涉及模块 | 问题描述 |
|---|----------|----------|
| 1 | DR-001 | `uq_project_name_per_app` 含 `project_status`，约束范围与注释意图（允许 Archived 重名）存在歧义 |
| 2 | shared/_index.md | 公共表清单批次编号不连续（缺第二批说明） |

---

## 5. 提示级问题清单（可选优化） {#sec-5-tiu793ajiwentiu6e05danu53efxua}
| # | 涉及文件 | 问题描述 |
|---|----------|----------|
| 1 | DR-012 | `DetectSessionDTO.baseline_version` 含 `updated_at`，但 `arch_validation_sessions` 表无对应快照字段 |
| 2 | DR-013 | DTO `scope` 与表 `export_scope` 命名不一致 |
| 3 | DR-015 | `ApplicationCostStatsDTO.time_range` 枚举未在 REST 端点 Query Params 中声明 |
| 4 | DR-018 | `PrototypeGenerateResponseDTO.status` (`error`) 与 `openui_generations.status` (`failed`) 命名不一致 |
| 5 | DR-019 | `wireframe_page_type_configs` 三个 ratio CHECK 未约束和为 100% |
| 6 | DR-020 | `architecture_changes` 表支持 6 种状态，但 `WritebackResultDTO.status` 仅返回 `pending_review` |
| 7 | design.md | 缺少 `ServiceUnavailableException`、`PayloadTooLargeException`、`UnsupportedMediaTypeException`（对应 503/413/415） |
| 8 | parallel-dev-plan.md | 风险项描述与 openapi.yaml 状态基本吻合 |
| 9 | _design-index.md | 模块编号 DR-001~DR-021 连续，但 feature-02 物理目录缺失（已注明原因） |
| 10 | _design-index.md | 变更历史已自动修复 |

---

## 6. 修复日志（YAML） {#sec-6-xiufurizhiyaml}
```yaml
doc_quality_gate:
  version: "1.0.0"
  run_id: "sdlc-visualizer-20260602"
  documents_checked:
    - detailed-design/feature-01-project-dashboard/module-design.md
    - detailed-design/feature-03-stage-detail/module-design.md
    - detailed-design/feature-04-gate-center/module-design.md
    - detailed-design/feature-05-artifact-viewer/module-design.md
    - detailed-design/feature-06-skill-registry/module-design.md
    - detailed-design/feature-07-flow-engine/module-design.md
    - detailed-design/feature-08-skill-executor/module-design.md
    - detailed-design/feature-09-template-engine/module-design.md
    - detailed-design/feature-10-complexity-router/module-design.md
    - detailed-design/feature-11-c4-navigator/module-design.md
    - detailed-design/feature-12-arch-validation/module-design.md
    - detailed-design/feature-13-history/module-design.md
    - detailed-design/feature-14-monitoring/module-design.md
    - detailed-design/feature-15-app-module/module-design.md
    - detailed-design/feature-16-pocketflow/module-design.md
    - detailed-design/feature-17-bypass/module-design.md
    - detailed-design/feature-18-openui/module-design.md
    - detailed-design/feature-19-wireframe/module-design.md
    - detailed-design/feature-20-proto-arch/module-design.md
    - detailed-design/feature-21-pagespec/module-design.md
    - detailed-design/shared/_index.md
    - detailed-design/shared/api-spec.md
    - detailed-design/shared/db-schema.md
    - detailed-design/shared/design.md
    - detailed-design/_design-index.md
    - interface-contracts/openapi.yaml
    - interface-contracts/parallel-dev-plan.md
  auto_fixes:
    - file: detailed-design/_design-index.md
      issue: "Form Feed (0x0c) characters in directory paths"
      action: "Replaced 13 occurrences of 0x0c with 'f'"
      lines: [120, 127, 128, 130, 137, 138, 140, 147, 148, 150, 157, 158, 160]
    - file: detailed-design/_design-index.md
      issue: "Incomplete change history (only batch 1 and 5 recorded)"
      action: "Added v1.1, v1.2, v1.3, v2.1, v2.2 change history entries"
    - file: interface-contracts/openapi.yaml
      issue: "/files/upload declared application/json instead of multipart/form-data"
      action: "Changed content-type to multipart/form-data with file/purpose/project_id fields"
    - file: detailed-design/feature-17-bypass/module-design.md
      issue: "Invalid SQL syntax: CHECK LENGTH ≥ 20"
      action: "Corrected to CHECK(LENGTH(review_opinion) >= 20)"
  manual_fixes_required:
    - count: 42
      categories:
        - "C1 结构完整性: 20 个模块 §5 标题需从'测试策略'改为'边界条件与异常处理'"
        - "C1 结构完整性: 17 个模块 §2/§3 顺序需调整"
        - "I3 状态一致性: 20 个模块 Frontmatter 需标记 FROZEN"
        - "C2 数据一致性: 5 项跨模块枚举值冲突"
        - "C3 引用完整性: 16 个模块需引用 shared/api-spec.md"
        - "跨文档冲突: project_members/operation_logs 归属需统一"
        - "编码损坏: _design-index.md 第7~9节乱码区域需人工重建"
  pending_items:
    - "确认 openapi.yaml 分页响应 data.items 的具体实体 Schema 引用"
    - "确认 DR-002（SDLC 画布）接口在 openapi.yaml 中的补充方式"
    - "确认 SSE 端点 subscribeExecutionSSE 的事件 Schema"
```

---

## 7. 结论与建议 {#sec-7-jieu8bbayujianu8bae}
### 7.1 关键发现 {#sec-71-guanu952efaxian}
1. **系统性结构偏差**：全部 20 个 module-design.md 的 §5 标题均为「测试策略」，与 `detailed-design` SKILL 规范要求的「边界条件与异常处理」存在系统性偏差。这表明在详细设计执行阶段，模板或指南可能存在歧义，或各批次执行时未严格执行原子章节规范。

2. **状态标记不一致**：_design-index.md 声称 20/21 模块已 FROZEN，但模块文件本身的 YAML Frontmatter 仍标记为 Draft/Draft→Active。这种「索引状态」与「文件实际状态」的不一致会破坏自动化工具对文档状态的解析。

3. **跨模块枚举冲突**：DR-003/004/005/016/017 等模块的 DTO 枚举值与 shared/db-schema.md 中的表 CHECK 约束存在多处不一致，编码阶段可能引发运行时校验失败。

4. **_design-index.md 编码损坏**：第 7~9 节（第二批~第四批追加内容）存在严重的 UTF-8 替换字符（1734 个），导致关键索引信息不可读。Form Feed 字符已修复，但乱码区域需人工重建。

### 7.2 修复优先级 {#sec-72-xiufuyouu5148ji}
| 优先级 | 问题 | 建议处理方式 |
|:------:|------|-------------|
| P0 | _design-index.md 乱码区域 | 从 batch audit reports 重建第二批~第四批索引内容 |
| P0 | 20 个模块 §5 标题 | 统一修改为「边界条件与异常处理」，或更新 SKILL 规范允许「测试策略」 |
| P1 | 跨模块枚举冲突（5 项） | 召开简短评审，以 db-schema.md 为基准统一 DTO 枚举 |
| P1 | 模块 Frontmatter FROZEN 标记 | 批量更新 20 个 module-design.md 的 status 字段 |
| P2 | 16 个模块补充 shared/api-spec.md 引用 | 在文件头部或 §3 开头添加引用注释 |
| P2 | openapi.yaml 分页 items Schema | 在 task-breakdown 前明确各分页接口的实体类型 |

### 7.3 阻断判定 {#sec-73-u963bu65adu5224u5b9a}
> **存在 42 项 🔴 阻断级问题，其中 38 项需人工处理。**
>
> 根据 `doc-quality-gate` 规则，**阻断级问题未清零前，禁止进入下一阶段**。
>
> 建议：**先完成 P0/P1 修复（约 2 小时工作量），重新执行 doc-quality-gate 确认通过后，再进入 task-breakdown 阶段。**
