# 模块索引 — SDLC Visualizer 详细需求

> 变更：sdlc-visualizer
> 基线：PRD-000 v2.0-patch2 (Gate 1 已冻结)
> 生成时间：2026-06-01

---

## 模块清单

| 编号 | 模块名称 | 目录 | 优先级 | 关联需求 | 状态 | 备注 |
|------|----------|------|--------|----------|------|------|
| DR-001 | 项目工作台 | `feature-01-project-dashboard/` | P0 | REQ-P0-001~002, REQ-P0-022~023 | ✅ 已完成 | Workspace/Application/Project/Module 四层 CRUD |
| DR-002 | SDLC 画布 | `feature-02-flow-canvas/` | P0 | REQ-P0-003~005 | ✅ 已完成 | 拓扑图/泳道/列表三视图，Stage 节点渲染 |
| DR-003 | 阶段详情面板 | `feature-03-stage-detail/` | P0 | REQ-P0-025, REQ-P0-034~038 | ✅ 已完成 | Skill 快照/产物/日志/门禁/审查 Tab |
| DR-004 | 审批中心 | `feature-04-gate-center/` | P0 | REQ-P0-008~009, REQ-P0-026 | ✅ 已完成 | AI 自检摘要/快速确认/驳回/历史追溯 |
| DR-005 | 产物浏览器 | `feature-05-artifact-viewer/` | P0 | REQ-P0-010~012, REQ-P0-024 | ✅ 已完成 | 目录树/预览/编辑/冲突检测/Git 快照 |
| DR-006 | Skill 注册与 DAG 管理 | `feature-06-skill-registry/` | P0 | REQ-P0-013~015 | ✅ 已完成 | 手动导入/Frontmatter 解析/DAG 自动解析与手动调整 |
| DR-007 | Skill Flow 编排引擎 | `feature-07-flow-engine/` | P0 | 编排核心逻辑 | ✅ 已完成 | 模块级里程碑编排/Stage 分组执行计划 |
| DR-008 | Skill 调度服务 | `feature-08-skill-executor/` | P0 | REQ-P0-006~007 | ✅ 已完成 | Kimi CLI 调用/实时状态同步/日志捕获 |
| DR-009 | 模板引擎 | `feature-09-template-engine/` | P0 | REQ-P0-002, REQ-P0-018, REQ-P0-027 | ✅ 已完成 | 四级模板/阶段-Skill 绑定/偏离记录 |
| DR-010 | 复杂度路由面板 | `feature-10-complexity-router/` | P0 | REQ-P0-016, REQ-P0-018 | ✅ 已完成 | 五维度评估/三级路径可视化/人工覆盖 |
| DR-011 | C4 架构浏览器 | `feature-11-c4-navigator/` | P0 | REQ-P0-019~021, REQ-P0-033 | ✅ 已完成 | L1/L2/L3/L4 DSL 生成/层级穿透/反向代码定位 |
| DR-012 | 架构验证中心 | `feature-12-arch-validation/` | P1 | REQ-P1-005~006 | ✅ 已完成 | 架构漂移检测/设计 vs 实际 diff 可视化 |
| DR-013 | 历史回溯 | `feature-13-history/` | P1 | REQ-P1-001~003 | ✅ 已完成 | 时间线/阶段耗时对比/返工热力图 |
| DR-014 | 监控看板 | `feature-14-monitoring/` | P1 | REQ-P1-007~008 | ✅ 已完成 | 进度追踪/Token 消耗/瓶颈识别 |
| DR-015 | Application 与模块治理 | `feature-15-app-module/` | P0/P1 | Application CRUD(P0), Module 里程碑(P1) | ✅ 已完成 | Application 管理/Module 级里程碑独立推进 |
| DR-016 | PocketFlow 执行引擎 | `feature-16-pocketflow/` | P0 | 执行生命周期 | ✅ 已完成 | prep-exec-post 三阶段/产物校验/Git 快照 |
| DR-017 | HITL 旁路审批服务 | `feature-17-bypass/` | P1 | 紧急授权/24h 补审 | ✅ 已完成 | 紧急授权执行/超时告警/事后补审 |
| DR-018 | OpenUI 原型服务 | `feature-18-openui/` | P0 | REQ-P0-028~029 | ✅ 已完成 | OpenUI 提示词生成/服务调用/内嵌预览 |
| DR-019 | WireframeEngine | `feature-19-wireframe/` | P0 | REQ-P0-030~032 | ✅ 已完成 | DomainMapper/LayoutPlanner/NavigationLinker |
| DR-020 | 原型-架构双向绑定 | `feature-20-proto-arch/` | P0 | 接口缺失检测/C4 回写 | 待编写 | 接口覆盖度检查/自动回写 C4 DSL |
| DR-021 | 需求草图服务 | `feature-21-pagespec/` | P0 | REQ-P0-040 | 待编写 | PageSpec 规则解析/低保真草图生成/缺失字段检测 |

---

## 生成批次

| 批次 | 模块 | 优先级 | 依赖 |
|------|------|--------|------|
| 第一批 | DR-001, DR-006, DR-009, DR-015 | P0 | 无（基础设施层） |
| 第二批 | DR-002, DR-008, DR-016, DR-007 | P0 | 依赖 DR-006, DR-009 |
| 第三批 | DR-003, DR-004, DR-005, DR-017 | P0 | 依赖第二批执行层 |
| 第四批 | DR-010, DR-011, DR-018, DR-019, DR-020, DR-021 | P0 | 独立或弱依赖 |
| 第五批 | DR-012, DR-013, DR-014 | P1 | 依赖对应 P0 模块 |

---

## 一致性校验报告

见 `_consistency-report.md`
