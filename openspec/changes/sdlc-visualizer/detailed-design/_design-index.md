# 详细设计全局索引

> **变更**：sdlc-visualizer  
> **基线**：PRD-000 v2.0-patch2（Gate 1）/ HLD-001~003（Gate 2）/ DR-001~021（Gate 2.5）  
> **生成日期**：2026-06-02  
> **批次**：第一批~第五批（全 21 模块：DR-001~DR-021）

---

## 1. 模块设计状态总览

| 模块编号 | 模块名称 | 目录 | 优先级 | 设计状态 | 版本 | 上游追溯 | 下游消费 |
|----------|----------|------|--------|----------|------|----------|----------|
| DR-001 | 项目工作台 | `feature-01-project-dashboard/` | P0 | ✅ 已完成 | v1.0 | DR-001 详细需求 | DR-003, DR-004, DR-005 |
| DR-006 | Skill 注册与 DAG 管理 | `feature-06-skill-registry/` | P0 | ✅ 已完成 | v1.0 | DR-006 详细需求 | DR-007, DR-008 |
| DR-009 | 模板引擎 | `feature-09-template-engine/` | P0 | ✅ 已完成 | v1.0 | DR-009 详细需求 | DR-001, DR-002, DR-007 |
| DR-015 | Application 与模块治理 | `feature-15-app-module/` | P0/P1 | ✅ 已完成 | v1.0 | DR-015 详细需求 | DR-001, DR-007, DR-014 |
| DR-012 | 架构验证中心 | `feature-12-arch-validation/` | P1 | ✅ 已完成 | v1.0 | DR-012 详细需求 | DR-011 |
| DR-013 | 历史回溯 | `feature-13-history/` | P1 | ✅ 已完成 | v1.0 | DR-013 详细需求 | DR-014 |
| DR-014 | 监控看板 | `feature-14-monitoring/` | P1 | ✅ 已完成 | v1.0 | DR-014 详细需求 | — |

---

## 2. 模块间接口契约矩阵

| 消费方 | 提供方 | 契约类型 | 接口范围 | 状态 |
|--------|--------|----------|----------|------|
| DR-001 | DR-015 | Service 调用 | Application 存在性校验、App 列表查询 | ✅ 已定义（DR-001 §1.4 / DR-015 §2.1） |
| DR-001 | DR-009 | Service 调用 | 模板定义查询、模板绑定 | ✅ 已定义（DR-001 §1.4 / DR-009 §2.1） |
| DR-001 | DR-010 | Service 调用 | 复杂度等级查询、规模评估计算 | ⚠️ 接口范围已定义，详细参数待 DR-010 设计后确认 |
| DR-001 | DR-003 | Service 调用 | 阶段进度、状态、阻塞信息 | ⚠️ 接口范围已定义，详细参数待 DR-003 设计后确认 |
| DR-001 | DR-005 | Service 调用 | 产物统计、STALE/CONFLICT 检测 | ⚠️ 接口范围已定义，详细参数待 DR-005 设计后确认 |
| DR-006 | — | 文件系统 | SKILL.md / meta.json 解析 | ✅ 已定义（DR-006 §1.3 SkillParser） |
| DR-009 | DR-010 | Service 调用 | 复杂度等级 → 模板推荐映射 | ⚠️ 接口范围已定义，详细参数待 DR-010 设计后确认 |
| DR-009 | DR-006 | Service 调用 | Skill 元数据查询（Stage 绑定展示） | ✅ 已定义（DR-009 §1.4 / DR-006 §2.1 GET /skills） |
| DR-015 | DR-001 | Service 调用 | 项目存在性、项目计数、状态查询 | ✅ 已定义（DR-015 §1.4 / DR-001 §2.1） |
| DR-015 | DR-008 | 事件上报 | Skill 执行 Token/耗时上报 | ⚠️ 上报格式已定义（DR-015 §2.1 POST /stats/report），消费端待 DR-008 设计后确认 |
| DR-015 | DR-005 | Service 调用 | 契约产物存在性检测 | ⚠️ 接口范围已定义，详细参数待 DR-005 设计后确认 |

---

## 3. 数据表归属与共享规划

### 3.1 第一批已定义表

| 表名 | 定义模块 | 归属 | 被引用模块 | 说明 |
|------|----------|------|-----------|------|
| `projects` | DR-001 | **公共表**（待提取） | DR-009, DR-015 | 项目主数据，含状态/模板/进度 |
| `project_timeboxes` | DR-001 | 模块独占 | — | Timebox 配置 |
| `risk_alerts` | DR-001 | 模块独占 | — | 风险预警记录 |
| `skills` | DR-006 | **公共表**（待提取） | DR-009 | Skill 元数据 |
| `skill_dag_nodes` | DR-006 | 模块独占 | — | DAG 节点坐标 |
| `skill_dag_edges` | DR-006 | 模块独占 | — | DAG 边关系 |
| `skill_change_logs` | DR-006 | 模块独占 | — | 变更审计日志 |
| `templates` | DR-009 | **公共表**（待提取） | DR-001, DR-015 | 系统预置模板定义 |
| `template_stages` | DR-009 | 模块独占 | — | 模板内 Stage 定义 |
| `template_deviations` | DR-009 | 模块独占 | — | 模板偏离记录（每项目一条） |
| `project_stages` | DR-009 | **公共表**（待提取） | DR-001, DR-015 | 项目级 Stage 运行时实例 |
| `applications` | DR-015 | **公共表**（待提取） | DR-001 | Application 主数据 |
| `modules` | DR-015 | 模块独占 | — | Module 定义（P1） |
| `module_dependencies` | DR-015 | 模块独占 | — | 跨模块契约依赖（P1） |
| `application_cost_stats` | DR-015 | 模块独占 | — | 研发管理费统计（P1） |

### 3.2 shared/ 目录提取计划（全部批次完成后执行）

```
detailed-design/shared/
├── _index.md
├── db-schema.md          # 公共表：projects, applications, skills, templates, project_stages, workspaces
├── api-spec.md           # 公共接口：文件上传、全局搜索、认证鉴权（MVP 暂无）
└── design.md             # 公共组件：分页 DTO、全局异常处理基类、文件系统适配器
```

> **提取时机**：全部 21 个模块的详细设计完成后，统一执行 Cross-Module Audit，将 ≥2 个模块引用的表/接口/组件提取到 `shared/`。

---

## 4. 关键枚举值全局对照

| 枚举名 | 值列表 | 定义位置 | 引用位置 | 一致性 |
|--------|--------|----------|----------|:------:|
| ProjectStatus | Draft / Active / Archived / Cancelled | DR-001 §3.1 | DR-009 §3.1, DR-015 §3.1 | ✅ |
| TemplateLevel | Trivial / Light / Standard / Deep | DR-009 §3.1 | DR-001 §2.2, DR-015 §3.1 | ✅ |
| RiskLevel | None / Low / Medium / High | DR-001 §3.1 | — | ✅ |
| RiskType | TimeboxExpiring / TimeboxExpired / StageBlocked / ArtifactStale / ArtifactConflict | DR-001 §3.1 | — | ✅ |
| SkillPattern | generator / pipeline / reviewer / analyzer / inversion / tool-wrapper | DR-006 §2.2 | DR-009 §3.1（template_stages） | ✅ |
| SkillParseStatus | PARSED / MANUAL_REQUIRED | DR-006 §3.1 | — | ✅ |
| ProjectStageStatus | DEFINED / SKIPPED / SCHEDULED / EXECUTED / REMOVED / FROZEN / ARCHIVED | DR-009 §3.1 | — | ✅ |
| ApplicationPathStatus | ACTIVE / PATH_INVALID | DR-015 §4.1 | — | ✅ |
| ModuleMilestoneStatus | NOT_STARTED / IN_PROGRESS / COMPLETED / BLOCKED / REMOVED | DR-015 §3.1 | — | ✅ |
| DependencyState | PENDING / SATISFIED / STALE | DR-015 §3.1 | — | ✅ |

---

## 5. 变更历史

| 日期 | 版本 | 变更内容 | 作者 |
|------|------|----------|------|
| 2026-06-02 | v1.0 | 第一批详细设计完成：DR-001 / DR-006 / DR-009 / DR-015 | AI Agent |
| 2026-06-02 | v1.1 | 第二批详细设计完成：DR-007 / DR-008 / DR-016（引擎层） | AI Agent |
| 2026-06-02 | v1.2 | 第三批详细设计完成：DR-003 / DR-004 / DR-005 / DR-017（表现层+旁路） | AI Agent |
| 2026-06-02 | v1.3 | 第四批详细设计完成：DR-010 / DR-011 / DR-018 / DR-019 / DR-020 / DR-021（线框图链路） | AI Agent |
| 2026-06-02 | v2.0 | 第五批详细设计完成：DR-012 / DR-013 / DR-014（P1 增强层） | AI Agent |
| 2026-06-02 | v2.1 | shared/ 目录提取完成（15 公共表 + 4 公共文件） | AI Agent |
| 2026-06-02 | v2.2 | interface-first-dev 完成：OpenAPI 3.1 契约（154 端点） | AI Agent |

---

## 6. 待办与阻塞项

| 编号 | 描述 | 影响批次 | 状态 |
|------|------|----------|------|
| TBD-001 | DR-010 复杂度路由面板设计完成后，需与 DR-001/DR-009 确认接口参数细节 | 第二批/第四批 | ⏳ 阻塞 |
| TBD-002 | DR-003/DR-005 设计完成后，需与 DR-001 确认产物/阶段查询接口契约 | 第二批/第三批 | ⏳ 阻塞 |
| TBD-003 | DR-008 设计完成后，需与 DR-015 确认 Skill 执行上报协议 | 第二批 | ⏳ 阻塞 |
| TBD-004 | 全部批次完成后，执行 shared/ 提取和最终 Cross-Module Audit | 第五批后 | ✅ 已完成（Batch 5 Audit 通过）|


---

## 7. 第二批模块追加（引擎层）

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



---

## 10. 第五批模块追加（P1 增强层）

| 模块编号 | 模块名称 | 目录 | 优先级 | 设计状态 | 版本 | 上游追溯 | 下游消费 |
|----------|----------|------|--------|----------|------|----------|----------|
| DR-012 | 架构验证中心 | `feature-12-arch-validation/` | P1 | ✅ 已完成 | v1.0 | DR-012 详细需求 | DR-011 |
| DR-013 | 历史回溯 | `feature-13-history/` | P1 | ✅ 已完成 | v1.0 | DR-013 详细需求 | DR-014 |
| DR-014 | 监控看板 | `feature-14-monitoring/` | P1 | ✅ 已完成 | v1.0 | DR-014 详细需求 | — |

### 第五批模块接口契约矩阵

| 消费方 | 提供方 | 契约类型 | 接口范围 | 状态 |
|--------|--------|----------|----------|------|
| DR-012 | DR-011 | SQLite 表读取 | C4 DSL 基线快照（`c4_dsl_store`） | ✅ 已定义（DR-012 §1.3 / DR-011 §3.1） |
| DR-012 | DR-011 | 前端状态传递 | C4 渲染状态（节点坐标、连线关系） | ✅ 已定义（DR-012 §1.3） |
| DR-011 | DR-012 | 前端事件总线 | 差异数据 Overlay 渲染输入 | ✅ 已定义（DR-012 §1.3 / DR-011 §2.1） |
| DR-013 | DR-001 | REST | 已完成项目列表与元数据 | ✅ 已定义（DR-013 §2.2） |
| DR-013 | DR-009 | REST | 模板定义与 Stage 列表 | ✅ 已定义（DR-013 §2.2） |
| DR-013 | DR-003 | REST | Stage 执行记录（起止时间、耗时、状态） | ✅ 已定义（DR-013 §2.2） |
| DR-013 | DR-004 | REST | Gate 审批记录 | ✅ 已定义（DR-013 §2.2） |
| DR-013 | DR-005 | REST | 产物版本历史 | ✅ 已定义（DR-013 §2.2） |
| DR-013 | DR-008 | REST | Skill 调用日志 | ✅ 已定义（DR-013 §2.2） |
| DR-014 | DR-013 | REST | 返工统计数据、瓶颈识别结果 | ✅ 已定义（DR-014 §2.2 / DR-013 §2.1） |
| DR-014 | DR-001 | REST | 项目列表、项目选择器数据 | ✅ 已定义（DR-014 §2.2） |
| DR-014 | DR-003 | REST | 阶段进度、子任务状态、阻塞标记 | ✅ 已定义（DR-014 §2.2） |
| DR-014 | DR-004 | REST | Gate 审批状态、签字记录 | ✅ 已定义（DR-014 §2.2） |
| DR-014 | DR-008 | REST | Skill 执行日志、Token 消耗上报 | ✅ 已定义（DR-014 §2.2） |
| DR-014 | progress-tracker | 文件系统 | progress.md SSOT 解析 | ✅ 已定义（DR-014 §1.3） |

### 第五批数据表归属

| 表名 | 定义模块 | 归属 | 被引用模块 | 说明 |
|------|----------|------|-----------|------|
| `arch_validation_sessions` | DR-012 | 模块独占 | — | 漂移检测会话记录 |
| `arch_validation_diffs` | DR-012 | 模块独占 | — | 差异项快照（每次检测独立快照） |
| `arch_scan_configs` | DR-012 | 模块独占 | — | 扫描频率配置 |
| `rework_events` | DR-013 | 模块独占（写方：DR-003/004/008事件触发） | DR-013/014 | 返工事件记录（热力图数据源） |
| `history_export_records` | DR-013 | 模块独占 | — | 历史报告导出记录 |
| `project_members` | DR-014 | **模块独占** | — | 项目成员角色（MVP 本地用户，P1 多用户后再评估） |
| `operation_logs` | DR-014 | **模块独占** | — | 操作日志（只追加，不可变，P1 多用户后再评估） |
| `token_consumption_records` | DR-014 | 模块独占 | DR-013 | Token 消耗明细（DR-008 写入，DR-014 读取） |
| `monitoring_refresh_configs` | DR-014 | 模块独占 | — | 看板自动刷新配置 |

### 新增/更新枚举值

| 枚举名 | 值列表 | 定义位置 | 引用位置 | 一致性 |
|--------|--------|----------|----------|:------:|
| DiffType | added / removed / modified | DR-012 §3.1 | DR-011（Overlay 渲染） | ✅ 新增 |
| DiffLevel | L1 / L2 / L3 / L4 | DR-012 §3.1 | DR-011 | ✅ 新增 |
| DetectionStatus | completed / partial_failure / failed | DR-012 §3.1 | — | ✅ 新增 |
| ReworkEventType | skill_retry / gate_reject / artifact_conflict | DR-013 §3.1 | DR-014（瓶颈分析） | ✅ 新增 |
| ChartType | bar / boxplot | DR-013 §2.1 | — | ✅ 新增 |
| ViewMode | gantt / list | DR-013 §2.1 | — | ✅ 新增 |
| HeatmapGranularity | day / week / month | DR-013 §2.1 | — | ✅ 新增 |
| TimeRangePreset | 1m / 3m / 6m / 1y / all | DR-013 §2.1 | — | ✅ 新增 |
| UserRole | tech_lead / developer | DR-014 §3.1 | — | ✅ 新增 |
| BottleneckType | time_bottleneck / rework_bottleneck / gate_failed | DR-014 §2.1 | — | ✅ 新增 |
| BottleneckSeverity | high / medium / low | DR-014 §2.1 | — | ✅ 新增 |
| StageCardStatus | not_started / active / blocked / completed / rework | DR-014 §4.2 | — | ✅ 新增 |
| OperationActionType | permission_change / stage_advance / data_export / config_change | DR-014 §3.2 | — | ✅ 新增 |
| RefreshInterval | 10 / 30 / 60 / 300 / 0(off) | DR-014 §3.4 | — | ✅ 新增 |

---

## 11. 全模块一致性检查（Batch 5 Audit）

### 11.1 枚举冲突检查

| 检查项 | 结果 | 说明 |
|--------|:----:|------|
| 跨模块枚举值冲突 | ✅ 通过 | 新增 12 个枚举，与已有枚举无值重叠 |
| 枚举引用一致性 | ✅ 通过 | 所有引用位置均指向明确定义位置 |
| 布尔型/状态型枚举穷尽性 | ✅ 通过 | 所有状态机状态均有对应枚举值 |

### 11.2 接口循环依赖检查

| 检查项 | 结果 | 说明 |
|--------|:----:|------|
| DR-012 ↔ DR-011 | ✅ 通过 | DR-012 消费 DR-011 的基线与渲染状态，DR-011 消费 DR-012 的差异数据；无循环调用 |
| DR-013 → DR-014 | ✅ 通过 | 单向依赖，DR-014 消费 DR-013 返工数据，无反向依赖 |
| DR-014 → DR-001/003/004/008 | ✅ 通过 | 均为单向消费，无循环 |

### 11.3 表写权限检查

| 表名 | 唯一写方 | 读方 | 检查结果 |
|------|----------|------|:--------:|
| `arch_validation_sessions` | DR-012 | — | ✅ |
| `arch_validation_diffs` | DR-012 | — | ✅ |
| `arch_scan_configs` | DR-012 | — | ✅ |
| `rework_events` | DR-003/004/008（事件触发写入） | DR-013, DR-014 | ✅ 写方分散但逻辑一致 |
| `project_members` | DR-014 | — | ✅ |
| `operation_logs` | DR-014 | — | ✅ 只追加 |
| `token_consumption_records` | DR-008 | DR-014 | ✅ |
| `monitoring_refresh_configs` | DR-014 | — | ✅ |

### 11.4 设计决策审计

| 决策编号 | 决策内容 | 涉及模块 | 状态 |
|----------|----------|----------|:----:|
| DEC-012-001 | 差异项上限 500 条截断，避免前端渲染性能问题 | DR-012 | ✅ 已落实 |
| DEC-012-002 | 检测准确率估算采用匹配覆盖率 × 置信度权重 | DR-012 | ✅ 已落实 |
| DEC-012-003 | MVP 阶段定时扫描仅本地触发，无服务端异步队列 | DR-012 | ✅ 已落实 |
| DEC-013-001 | 返工事件独立成表，支持灵活时间周期聚合 | DR-013 | ✅ 已落实 |
| DEC-013-002 | 历史数据仅消费 Completed/Archived 项目，排除 Active/Draft | DR-013 | ✅ 已落实 |
| DEC-014-001 | 操作日志表设计为只追加（append-only），禁止 UPDATE/DELETE | DR-014 | ✅ 已落实 |
| DEC-014-002 | 瓶颈识别引擎阈值：耗时瓶颈 150%，返工瓶颈 ≥2 次 | DR-014 | ✅ 已落实 |
| DEC-014-003 | 自动刷新策略：连续 3 次失败进入 Stale，页面不可见时暂停 | DR-014 | ✅ 已落实 |

---

## 12. 设计完成度统计

| 批次 | 模块 | 状态 | 累计完成 |
|------|------|------|:--------:|
| 第一批（地基） | DR-001 / DR-006 / DR-009 / DR-015 | ✅ FROZEN | 4/21 |
| 第二批（引擎） | DR-007 / DR-008 / DR-016 | ✅ FROZEN | 7/21 |
| 第三批（表现+旁路） | DR-003 / DR-004 / DR-005 / DR-017 | ✅ FROZEN | 11/21 |
| 第四批（线框图链路） | DR-010 / DR-011 / DR-018 / DR-019 / DR-020 / DR-021 | ✅ FROZEN | 17/21 |
| 第五批（P1 增强） | DR-012 / DR-013 / DR-014 | ✅ FROZEN | **20/21** |

> **说明**：DR-002（SDLC 画布）为前端核心可视化组件，已在各批次设计中持续引用，其详细设计将在 interface-first-dev 阶段作为公共组件统一补充。

---

## 13. 下一阶段工作

| 编号 | 工作项 | 说明 | 优先级 |
|------|--------|------|--------|
| NEXT-001 | shared/ 目录提取 | ✅ 已完成：db-schema.md（15 表）+ api-spec.md + design.md + _index.md | P0 |
| NEXT-002 | 最终 Cross-Module Audit | 全量 21 模块一致性校验 | P0 |
| NEXT-003 | ✅ interface-first-dev | OpenAPI 3.1 契约已生成：154 端点 / 138 路径 / 18 schemas / 22 tags | P0 |
| NEXT-004 | DR-002 画布组件设计补充 | 作为公共可视化组件统一设计 | P1 |

---

## 14. Interface Contracts 产出

| 产物 | 路径 | 大小 | 说明 |
|------|------|------|------|
| `openapi.yaml` | `interface-contracts/openapi.yaml` | 270,713 B | OpenAPI 3.1 完整契约，含 154 端点、18 核心 schemas、RFC 7807 错误模型 |
| `mock-data.json` | `interface-contracts/mock-data.json` | 57,091 B | 按 operationId 分组的 Mock 示例（正常+异常路径） |
| `mock-server-config.md` | `interface-contracts/mock-server-config.md` | 1,002 B | Prism / JSON Server 启动方案 |
| `parallel-dev-plan.md` | `interface-contracts/parallel-dev-plan.md` | 4,481 B | 前后端任务边界、联调时间点、版本规划 |

### 质量检查报告

| 检查项 | 结果 | 说明 |
|--------|:----:|------|
| operationId 唯一性 | ✅ 通过 | 154 个端点无重复 |
| $ref 有效性 | ✅ 通过 | 11 个 schema 引用全部存在 |
| 分页参数完整性 | ✅ 通过 | 所有分页 GET 端点含 page/page_size |
| Problem 错误响应 | ✅ 通过 | 所有 4xx/5xx 响应均引用 Problem schema |

### 已知限制

1. **DR-002 画布组件接口缺失**：SDLC 画布公共组件尚未产出详细设计，其接口在编码阶段补充。
2. **SSE 事件格式占位**：`subscribeExecutionSSE` 的事件流格式待编码阶段细化。
3. **部分复杂 DTO 为骨架**：模块专用 DTO（如 `MonitoringOverviewDTO`、`HistorySummaryDTO` 等）在 `openapi.yaml` 中标记为内联对象，待编码阶段补充完整字段。
