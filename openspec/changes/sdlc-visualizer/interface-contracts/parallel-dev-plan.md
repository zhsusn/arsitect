# Parallel Development Plan

## 接口依赖 DAG

### P0（无依赖，可先行）
- System: `healthCheck`, `globalSearch`, `uploadFile`
- Applications: `createApplication`, `listApplications`, `getApplication`, `updateApplication`, `deleteApplication`
- Projects: `listProjects`, `createProject`, `getProject`, `updateProject`
- Skills: `scanSkills`, `confirmSkillImport`, `listSkills`, `getSkill`, `deleteSkill`, `getDAG`, `addDAGNode`, ...
- Templates: `listTemplates`, `getTemplate`

### P1（依赖 P0 资源创建）
- Projects 状态流转: `archiveProject`, `activateProject`, `cancelProject`
- Stages: `getStageDetail`, `listAnnotations`, `createAnnotation`, ...（依赖 Project 创建）
- Gates: `listGates`, `getGate`, `approveGate`, `rejectGate`, ...（依赖 Stage 推进）
- Artifacts: `getArtifactTree`, `getArtifactContent`, ...（依赖 Stage 执行产物）
- Execution Plans: `createExecutionPlan`, `getExecutionPlan`, ...（依赖 DAG + Template）
- Executions: `triggerExecution`, `getExecutionStatus`, ...（依赖 Execution Plan）

### P2（依赖 P1 执行数据）
- Monitoring: `getMonitoringOverview`, `getStageStats`, ...（依赖 Execution 完成数据）
- History: `getHistorySummary`, `getHistoryTimeline`, ...（依赖 Project 完成归档）
- Arch Validation: `triggerArchDetection`, `listArchDiffs`, ...（依赖 C4 DSL 基线）
- Bypass: `createBypassApplication`, ...（依赖 Gate 阻塞场景）

## 前端任务边界（基于 Mock 可独立完成）

| 页面 | 依赖 Mock 接口 | 可独立度 |
|------|---------------|:-------:|
| 项目工作台 | `listApplications`, `listProjects`, `createProject` | ✅ 完全独立 |
| Skill 注册中心 | `listSkills`, `scanSkills`, `getDAG` | ✅ 完全独立 |
| 模板管理 | `listTemplates`, `getTemplate` | ✅ 完全独立 |
| 阶段详情 | `getStageDetail`, `listAnnotations` | ⚠️ 需 Mock Project/Stage 数据 |
| 审批中心 | `listGates`, `getGate`, `approveGate` | ⚠️ 需 Mock Gate 数据 |
| 产物浏览器 | `getArtifactTree`, `getArtifactContent` | ⚠️ 需 Mock Artifact 数据 |
| 监控看板 | `getMonitoringOverview` | ❌ 依赖真实执行数据 |
| 历史回溯 | `getHistorySummary` | ❌ 依赖真实归档数据 |

## 后端任务边界

| 模块 | 端点数 | 优先级 | 说明 |
|------|:------:|:------:|------|
| System | 3 | P0 | 健康检查、搜索、上传 |
| DR-015 App | 15 | P0 | Application/Module CRUD |
| DR-001 Projects | 11 | P0 | 项目生命周期管理 |
| DR-006 Skills | 14 | P0 | Skill 注册与 DAG |
| DR-009 Templates | 9 | P0 | 模板与 Stage 序列 |
| DR-003 Stages | 10 | P1 | 阶段详情与批注 |
| DR-004 Gates | 7 | P1 | 审批与决策历史 |
| DR-005 Artifacts | 7 | P1 | 产物浏览与版本 |
| DR-007 Plans | 8 | P1 | 执行计划编排 |
| DR-008 Executions | 6 | P1 | Skill 调度执行 |
| DR-010 Complexity | 5 | P1 | 复杂度评估 |
| DR-011 C4 | 5 | P1 | C4 DSL 管理 |
| DR-012 Validation | 9 | P2 | 架构漂移检测 |
| DR-013 History | 6 | P2 | 历史分析 |
| DR-014 Monitoring | 9 | P2 | 监控看板 |
| DR-016 PocketFlow | 4 | P1 | 执行引擎（内部） |
| DR-017 Bypass | 9 | P2 | 旁路审批 |
| DR-018 OpenUI | 4 | P2 | 原型服务 |
| DR-019 Wireframe | 4 | P2 | 线框图引擎 |
| DR-020 Binding | 4 | P2 | 双向绑定 |
| DR-021 Sketches | 6 | P2 | 草图服务 |

## 联调时间点

| 批次 | 接口范围 | 联调条件 | 预计时间 |
|------|----------|----------|----------|
| 联调 1 | System + App + Projects + Skills + Templates | P0 后端完成 | T+3d |
| 联调 2 | Stages + Gates + Artifacts + Plans + Executions | P1 后端完成 | T+7d |
| 联调 3 | Complexity + C4 + Monitoring | P2 后端完成 | T+12d |
| 联调 4 | OpenUI + Wireframe + Binding + Sketches + History | P2 后端全部完成 | T+18d |

## 版本规划

- 当前基线：`/api/v1`
- 破坏性变更需升级至 `/api/v2`
- 小版本通过 `Accept-Version` Header 协商
- 废弃接口保留 2 个版本周期，返回 `Deprecation` Header

## 风险项

1. **DR-002 画布组件缺失**：SDLC 画布公共组件尚未产出详细设计，其接口将在编码阶段补充。
2. **SSE 端点未完整定义**：`subscribeExecutionSSE` 的事件格式需在编码阶段细化。
3. **Mock 数据占位**：部分复杂嵌套 DTO 使用 `TODO` 占位，需在 task-breakdown 前补充真实示例。
