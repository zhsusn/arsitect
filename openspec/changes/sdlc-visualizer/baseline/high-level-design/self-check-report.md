---
doc_type: ARCH
fragment_id: arch-sdlc-visualizer-436
title: 跨文件一致性自检报告
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
- fragment_id: prd-sdlc-visualizer-000
  version: 2.0-patch2
- fragment_id: prd-sdlc-visualizer-feat02-629
  version: 1.0.0
c4_binding:
  level: L2
---

# 跨文件一致性自检报告


> **C4 绑定引用**：
> - `@C4-L1-System:git`
> - `@C4-L1-System:kimi-cli`
> - `@C4-L1-System:local-filesystem`
> - `@C4-L2-Container:artifact-store`
> - `@C4-L2-Container:backend-api`
> - `@C4-L2-Container:frontend-spa`
> - `@C4-L2-Container:git-repo`
> - `@C4-L2-Container:kimi-cli-process`
> - `@C4-L2-Container:skill-orchestrator`
> - `@C4-L2-Container:sqlite-db`
> - `@C4-L2-Container:wireframe-engine`

---

## 自检结论总览 {#sec-zijianjieu8bbazonglan}
| 检查项 | 结论等级 | 说明 |
|--------|---------|------|
| 技术栈覆盖度 | ✅ | FastAPI + SQLAlchemy + SQLite + Git 覆盖全部存储与接口需求 |
| 架构-目录一致性 | ✅ | 五层架构（表现/接口/应用/领域/基础设施）与目录树一一对应 |
| 状态机-模块职责兼容性 | ✅ | 全局状态机 10 个状态在 21 个模块职责中均有明确处理方 |
| 异常-回滚联动 | ✅ | 4 类触发回滚的异常在回滚方案中均有对应层级步骤 |
| 性能-部署匹配 | ✅ | 单用户本地场景下的 QPS 预估与单进程部署拓扑匹配 |
| 安全-接口契约一致性 | ✅ | 本地免认证策略与 REST + SSE 通信模式完全兼容 |
| ADR 溯源 | ✅ | 5 项 ADR 均可在 competitive-analysis.md / design-input.md 中找到支撑 |
| 模块遗漏检查 | ✅ | 21/21 模块全部被覆盖，P0 模块 18 个、P1 模块 3 个 |
| Mermaid 规范合规 | ✅ | 全部图表使用 `<br>`、节点 ID 语义化、subgraph 分组、回流虚线 |
| 边界红线检查 | ✅ | 未发现字段类型、类图、DDL、具体脚本内容越界 |

**最终结论：无 ❌ 阻断项，无 ⚠️ 警告项。满足 Gate 2 进入条件。**

---

## 详细检查记录 {#sec-xiangu7ec6jianchajilu}
### 1. 技术栈覆盖度（01-architecture-core ↔ 02-data-flow） {#sec-1-u6280u672fu6808fugaidu01archit}
**检查逻辑**：验证 01 §2.1 选型清单中的存储/数据组件是否覆盖 02 §1.3 存储策略的全部数据类型。

| 数据类型 | 02 存储策略声明 | 01 技术栈支撑 | 匹配 |
|----------|----------------|--------------|------|
| 元数据 | SQLite | SQLite + SQLAlchemy 2.0 AsyncSession | ✅ |
| 产物文件 | 本地文件系统 | FastAPI File Response + Python pathlib | ✅ |
| 产物版本 | Git 仓库 | simple-git（前端）+ GitPython（后端） | ✅ |
| 执行日志 | SQLite + 文件 | SQLite 存摘要，文件系统存大日志 | ✅ |
| C4 DSL | 本地文件系统 | Python YAML 库 + Mermaid.js | ✅ |
| 线框图/原型 | 本地文件系统 | SVG/HTML 文件服务 | ✅ |
| 配置 | SQLite + YAML | SQLAlchemy + PyYAML | ✅ |

**结论**：✅ 通过。7 类数据存储均有对应技术组件支撑。

---

### 2. 架构-目录一致性（01-architecture-core） {#sec-2-jiagoumuluyiu81f4xing01archite}
**检查逻辑**：验证 C4 Container/Component 分层与 01 §3.1 目录树是否一一对应。

| 架构层 | C4 对应 | 目录路径 | 对应关系 |
|--------|---------|----------|----------|
| 表现层 | Web SPA | `frontend/src/pages/`, `stores/`, `services/` | ✅ 一一对应 |
| 接口层 | FastAPI Routes | `backend/app/api/v1/` | ✅ 一一对应 |
| 应用层 | Domain Services | `backend/app/services/` | ✅ 一一对应 |
| 领域层 | Models / Schemas | `backend/app/models/`, `schemas/` | ✅ 一一对应 |
| 基础设施层 | Repository / Adapter | `backend/app/infrastructure/` | ✅ 一一对应 |

**结论**：✅ 通过。目录职责说明表（01 §3.2）进一步强化了映射关系。

---

### 3. 状态机-模块职责兼容性（03-runtime-behavior ↔ 02-data-flow） {#sec-3-zhuangtaijimokuaiu804cu8d23jia}
**检查逻辑**：验证 03 §1 全局状态机中的每个状态在 02 §3.1 模块职责中是否有处理方。

| 状态 | 处理模块 | 职责匹配 |
|------|----------|----------|
| NOT_STARTED | SDLC 画布 (DR-002)、编排引擎 (DR-007) | ✅ 渲染 + 依赖校验 |
| PREP/EXEC/POST | Skill 调度 (DR-008)、PocketFlow (DR-016) | ✅ 三阶段生命周期管理 |
| REVIEW_PENDING | 阶段详情面板 (DR-003)、产物浏览器 (DR-005) | ✅ 审查 Tab + 批注 |
| REVISION_REQUESTED | 阶段详情面板 (DR-003)、Skill 调度 (DR-008) | ✅ 重新生成触发 |
| GATE_PENDING | 审批中心 (DR-004) | ✅ AI 摘要 + 审批 |
| BYPASSED | HITL 旁路审批 (DR-017) | ✅ 紧急授权 + 超时告警 |
| PASSED | 编排引擎 (DR-007)、SDLC 画布 (DR-002) | ✅ 下游解锁 + 节点变色 |
| BLOCKED | 编排引擎 (DR-007)、Skill 调度 (DR-008) | ✅ 重试 + 错误展示 |

**结论**：✅ 通过。全部 10 个状态均有明确模块处理方。

---

### 4. 异常-回滚联动（03-runtime-behavior ↔ 05-ops-governance） {#sec-4-yichanghuigunu8054dong03runtim}
**检查逻辑**：验证 03 §3.4 中标记"触发回滚"的异常类别是否在 05 §2 中有对应步骤。

| 异常类别 | 03 标记 | 05 回滚步骤 | 匹配 |
|----------|---------|------------|------|
| 产物误删/损坏 | 触发回滚 | 层级 A：产物级 Git 回滚 | ✅ |
| 数据库损坏 | 触发回滚 | 层级 B：数据库备份恢复 | ✅ |
| 旁路审批超时 | 触发回滚 | 层级 C：项目级状态重置 | ✅ |
| 模板切换异常 | 触发回滚 | 层级 C：项目级 Git 检出 | ✅ |
| AI 错误（Skill 失败） | 不触发回滚 | — | ✅ 一致（标记 BLOCKED） |
| POST 阶段失败 | 不触发回滚 | — | ✅ 一致（保留产物重试） |

**结论**：✅ 通过。4 类触发回滚的异常均有可操作步骤，2 类不触发回滚的异常与方案一致。

---

### 5. 性能-部署匹配（04-quality-attributes） {#sec-5-xingnengbushuu5339pei04quality}
**检查逻辑**：验证 04 §2.1 QPS 预估与 05 §5.1 部署拓扑是否匹配。

| 性能指标 | 目标值 | 部署拓扑支撑 | 匹配 |
|----------|--------|-------------|------|
| 首屏 < 2s | P95 | Vite 单页应用 + 本地网络零延迟 | ✅ |
| 拓扑 60fps | 本地渲染 | React Flow 虚拟化 + 单线程无竞争 | ✅ |
| 状态同步 < 5s | 轮询/SSE | 单进程 Uvicorn，无网络跳数 | ✅ |
| 数据库 < 200ms | P95 | SQLite 嵌入式，单连接无网络开销 | ✅ |
| Git 快照 < 1s | 本地 Git | GitPython 本地操作 | ✅ |

**结论**：✅ 通过。本地单机部署拓扑完全支撑所有性能目标。

---

### 6. 安全-接口契约一致性（04-quality-attributes ↔ 02-data-flow） {#sec-6-anquanjiekouqiyueyiu81f4xing04}
**检查逻辑**：验证 04 §1 安全方案与 02 §2.1 通信模式是否兼容。

| 安全要求 | 通信模式 | 兼容性 |
|----------|----------|--------|
| 本地免认证 | REST + SSE（同源 localhost） | ✅ CORS 限制为同源即足够 |
| 无 API Key 存储 | STDIO 管道调用 Kimi CLI | ✅ 认证由 CLI 自身管理 |
| 产物隔离 | 本地文件系统直接 IO | ✅ 项目目录物理隔离 |
| CLI 沙箱 | 白名单命令限制 | ✅ Adapter 层过滤 |

**结论**：✅ 通过。安全策略与通信模式无冲突。

---

### 7. ADR 溯源（01-architecture-core ↔ competitive-analysis.md / design-input.md） {#sec-7-adr-u6eafu6e9001architectureco}
**检查逻辑**：验证每项 ADR 是否能在竞品分析或设计输入中找到支撑。

| ADR | 决策内容 | 溯源依据 | 匹配 |
|-----|----------|----------|------|
| ADR-001 纯 SPA | React 19 + Vite 6，浏览器访问 | design-input.md §2.1：React 19 + Vite 6 推荐（4.70 分） | ✅ |
| ADR-002 C4 自研 | 不依赖 C4 InterFlow CLI | 用户决策（问题 2-A）+ PRD NG-010 | ✅ |
| ADR-003 OpenUI 可选 | 有则调用，无则 Wireframe 降级 | 用户决策（问题 3-B）+ design-input.md OpenUI 为可选 | ✅ |
| ADR-004 Kimi 单一 | 预留 MCP 接口，当前仅 Kimi | competitive-analysis.md：MVP 仅 Kimi CLI 为最大短板但已预留 Adapter | ✅ |
| ADR-005 单进程 SQLite | uvicorn --workers 1，预留 PostgreSQL | design-input.md §2.1：SQLite 推荐 4.15 分（MVP） | ✅ |

**结论**：✅ 通过。5/5 ADR 均有明确溯源。

---

### 8. 模块遗漏检查 {#sec-8-mokuaiu9057u6f0fjiancha}
**检查逻辑**：验证 21 个详细需求模块（DR-001~DR-021）是否在概要设计中有覆盖。

| 编号 | 模块 | 01 架构图 | 02 模块职责 | 03 时序图 | 覆盖 |
|------|------|----------|------------|----------|------|
| DR-001 | 项目工作台 | ✅ | ✅ | — | ✅ |
| DR-002 | SDLC 画布 | ✅ | ✅ | ✅ | ✅ |
| DR-003 | 阶段详情面板 | ✅ | ✅ | ✅ | ✅ |
| DR-004 | 审批中心 | ✅ | ✅ | ✅ | ✅ |
| DR-005 | 产物浏览器 | ✅ | ✅ | ✅ | ✅ |
| DR-006 | Skill 注册 | ✅ | ✅ | — | ✅ |
| DR-007 | Skill Flow 编排 | ✅ | ✅ | ✅ | ✅ |
| DR-008 | Skill 调度 | ✅ | ✅ | ✅ | ✅ |
| DR-009 | 模板引擎 | ✅ | ✅ | — | ✅ |
| DR-010 | 复杂度路由 | ✅ | ✅ | — | ✅ |
| DR-011 | C4 架构浏览器 | ✅ | ✅ | ✅ | ✅ |
| DR-012 | 架构验证中心 | ✅ | ✅ | — | ✅ |
| DR-013 | 历史回溯 | ✅ | ✅ | — | ✅ |
| DR-014 | 监控看板 | ✅ | ✅ | — | ✅ |
| DR-015 | Application 与模块治理 | ✅ | ✅ | — | ✅ |
| DR-016 | PocketFlow 执行引擎 | ✅ | ✅ | ✅ | ✅ |
| DR-017 | HITL 旁路审批 | ✅ | ✅ | — | ✅ |
| DR-018 | OpenUI 原型服务 | ✅ | ✅ | — | ✅ |
| DR-019 | WireframeEngine | ✅ | ✅ | — | ✅ |
| DR-020 | 原型-架构双向绑定 | ✅ | ✅ | ✅ | ✅ |
| DR-021 | 需求草图服务 | ✅ | ✅ | — | ✅ |

**结论**：✅ 通过。21/21 模块全部被覆盖，无遗漏。

---

### 9. Mermaid 规范合规 {#sec-9-mermaid-guifanu5408gui}
**检查逻辑**：验证所有 Mermaid 图表是否符合 `mermaid-diagrams` Skill 工程化规范。

| 规范项 | 检查结果 | 说明 |
|--------|---------|------|
| 换行符标准化 | ✅ | 全部使用 `<br>`，无 `<br/>` |
| 样式集中声明 | ✅ | 使用 `style` 语句集中定义，无内联样式 |
| Subgraph 分组 | ✅ | 按阶段/层级/领域分组 |
| 形状语义化 | ✅ | 用户用圆形/椭圆，系统用矩形，可选依赖用虚线边框 |
| 回流虚线 | ✅ | 重新生成、超时告警等回流使用虚线（`-.->`） |
| 节点 ID 语义化 | ✅ | 使用 `Pg_`（物理组件）、`Dec_`（决策/逻辑）、`St_`（状态）前缀 |
| 路由分离 | ✅ | 正常流与异常流、可选依赖流分离 |

**结论**：✅ 通过。全部 12 张 Mermaid 图表合规。

---

### 10. 边界红线检查 {#sec-10-u8fb9u754cu7ea2xianjiancha}
**检查逻辑**：验证各主题文件是否越界输出详细设计内容。

| 红线项 | 00 | 01 | 02 | 03 | 04 | 05 | 结论 |
|--------|----|----|----|----|----|----|------|
| 字段类型（varchar/int 等） | — | — | — | — | — | — | ✅ 全无 |
| 请求/响应 Schema | — | — | — | — | — | — | ✅ 全无 |
| 类图/函数签名 | — | — | — | — | — | — | ✅ 全无 |
| DDL/SQL 语句 | — | — | — | — | — | — | ✅ 全无 |
| 缓存 Key 设计 | — | — | — | — | — | — | ✅ 全无 |
| 单测用例/Mock | — | — | — | — | — | — | ✅ 全无 |
| Dashboard JSON | — | — | — | — | — | — | ✅ 全无 |
| 具体脚本内容 | — | — | — | — | — | — | ✅ 全无 |
| 监控阈值数值 | — | — | — | — | — | — | ✅ 全无 |

**结论**：✅ 通过。全部主题文件严守边界红线。

---

## 自检执行信息 {#sec-zijianzhixingxinxi}
| 属性 | 值 |
|------|-----|
| 执行者 | high-level-design Skill（AI Agent） |
| 检查时间 | 2026-06-01T17:38:00+08:00 |
| 检查范围 | 6 个主题文件 + 竞品分析 + 设计输入 + 21 个详细需求模块 |
| ❌ 阻断项 | 0 |
| ⚠️ 警告项 | 0 |
| ✅ 通过项 | 10/10 |
| **建议** | 可直接进入 Gate 2 人工评审 |

---

## 附录：历史补充内容（来自 docs/ 目录） {#sec-u9644luu5386u53f2u8865u5145u5185}
> 检查阶段：high-level-design（概要设计）
> 涉及主题文件：01-architecture-core.md ~ 05-ops-governance.md
> 生成时间：2026-05-31
> 总体结论：通过（无阻断项，3 项警告需人工确认）

## 检查结果汇总 {#sec-jianchajieu679cu6c47zong}
| 检查项 | 涉及主题文件 | 自动检查逻辑 | 结论等级 |
|--------|-------------|-------------|---------|
| 技术栈覆盖度 | 01-architecture-core ↔ 02-data-flow | 技术栈中声明的存储组件是否覆盖数据架构中的全部存储需求 | ✅ |
| 架构-目录一致性 | 01-architecture-core（系统架构 vs 项目结构） | 架构分层与目录层级是否一一对应 | ✅ |
| 状态机-模块职责兼容性 | 03-runtime-behavior ↔ 02-data-flow | 全局状态机中的状态是否在模块职责中有对应处理方 | ✅ |
| 异常-回滚联动 | 03-runtime-behavior ↔ 05-ops-governance | 异常处理中标记"触发回滚"的类别是否在回滚方案中有步骤 | ✅ |
| 性能-部署匹配 | 04-quality-attributes（性能 vs 部署） | QPS 预估与部署拓扑的节点数/规格是否匹配 | ✅ |
| 安全-接口契约一致性 | 04-quality-attributes ↔ 02-data-flow | 安全方案要求的认证方式是否与接口契约中的通信模式兼容 | ✅ |
| ADR 溯源 | 01-architecture-core ↔ competitive-analysis.md | 每个 ADR 是否能在竞品分析中找到支撑 | ✅ |

## ✅ 通过项 {#sec-tongguou9879}
### 1. 技术栈覆盖度 {#sec-1-u6280u672fu6808fugaidu}
- **证据**：01-architecture-core.md &sect;2.1 声明了 SQLite（MVP）/ PostgreSQL（P1+）+ 本地文件系统。
- **覆盖**：02-data-flow.md &sect;1.3 明确数据库承载结构化元数据，文件系统承载产物实体，两者分离策略清晰。
- **结论**：存储组件 100% 覆盖数据架构需求。

### 2. 架构-目录一致性 {#sec-2-jiagoumuluyiu81f4xing}
- **证据**：01-architecture-core.md &sect;1.2 定义了四层架构（交互呈现 / 引擎调度 / 治理管理 / 基础设施）。
- **对应**：01-architecture-core.md &sect;3.1 目录树中 `apps/web/src/views/` + `features/` 对应交互呈现层；`apps/api/src/services/` 对应引擎调度+治理管理；`adapters/` + `infrastructure/` 对应基础设施层。
- **结论**：一一对应，无悬空目录、无架构层遗漏。

### 3. 状态机-模块职责兼容性 {#sec-3-zhuangtaijimokuaiu804cu8d23jia_1}
- **证据**：03-runtime-behavior.md &sect;1.1 定义了 Project / Stage / SkillExecution 三层状态机。
- **覆盖**：02-data-flow.md &sect;3 模块职责表中：
  - Flow Engine 负责 YAML DAG 解析与状态机推进
  - Skill Executor 负责 SkillExecution 生命周期管理
  - Gate Center 负责 GATE_PENDING / REVISION_REQUESTED 状态处理
  - Project Governance 负责 Draft/Active 双态转换
- **结论**：全部状态均有明确模块处理方，无 orphaned 状态。

### 4. 异常-回滚联动 {#sec-4-yichanghuigunu8054dong}
- **证据**：03-runtime-behavior.md &sect;3.4 明确列出 5 类触发回滚的错误场景。
- **覆盖**：05-ops-governance.md &sect;2.1/2.2/2.4 中：
  - CLI 崩溃 &rarr; 清理产物 + Stage 回退（&sect;2.2）
  - DB 不一致 &rarr; 事务回滚 + 快照恢复（&sect;2.2）
  - Gate 驳回覆盖 &rarr; 保留前序版本至 archive（&sect;2.3）
  - 上游漂移 &rarr; 下游批量回退至 REVISION_REQUESTED（&sect;2.4）
  - 死信任务 &rarr; 冻结 Project 等待人工裁决（&sect;2.1）
- **结论**：全部异常类别在回滚方案中均有明确步骤。

### 5. 性能-部署匹配 {#sec-5-xingnengbushuu5339pei}
- **证据**：04-quality-attributes.md &sect;2.1 预估峰值 QPS < 50，并发 Project &le; 10。
- **匹配**：04-quality-attributes.md &sect;5.1 部署拓扑为单进程 Uvicorn + FastAPI + SQLite WAL，无分布式节点。
- **结论**：单机部署规格与低 QPS 预估完全匹配，无过度设计。

### 6. 安全-接口契约一致性 {#sec-6-anquanjiekouqiyueyiu81f4xing}
- **证据**：04-quality-attributes.md &sect;1.1/1.3 采用本地信任模型 + Loopback 绑定 + 无 RBAC。
- **匹配**：02-data-flow.md &sect;2.1 通信模式为 REST + WebSocket，均走本地 Loopback，无公网暴露。
- **结论**：安全方案与通信模式无冲突，本地信任模型在 Loopback 场景下合理。

### 7. ADR 溯源 {#sec-7-adr-u6eafu6e90}
- **证据**：01-architecture-core.md &sect;2.3 包含 ADR-001/002/003。
- **溯源**：
  - ADR-001（React 19 + Vite 6）&rarr; design-input.md &sect;2.1 前端框架选型表已锁定
  - ADR-002（React Flow 12）&rarr; design-input.md &sect;2.1 画布组件评分表 4.80 分推荐
  - ADR-003（SQLite &rarr; PostgreSQL）&rarr; design-input.md &sect;2.1 数据库评分表 MVP 推荐 SQLite
- **结论**：全部 ADR 均有竞品分析评分表支撑。

## ⚠️ 警告（需人工确认） {#sec-jinggaoxurengongqueren}
### WARN-1：产物监听依赖未显式列入技术栈清单 {#sec-warn1chanu7269jianu542cyiu8d56we}
- **位置**：03-runtime-behavior.md &sect;2.1 提到"产物目录增量监听"，04-quality-attributes.md &sect;2.3 提到 `watchdog` / `inotify`。
- **问题**：01-architecture-core.md &sect;2.1 技术栈选型清单中未列出 `watchdog` 或 `aiofiles` 等文件监听库。
- **建议**：在详细设计阶段明确产物监听的技术选型（`watchdog` vs `fsevents` vs 轮询兜底），并补充至技术栈清单。
- **影响级别**：低（不影响架构评审，属实现细节）

### WARN-2：回滚脚本清单与数据库表结构存在隐含依赖 {#sec-warn2huigunu811abenu6e05danyushu}
- **位置**：05-ops-governance.md &sect;2.3 列出 `rollback-project-status.sql` / `rollback-stage-instance.sql` / `cleanup-orphan-artifacts.sql`。
- **问题**：02-data-flow.md &sect;1.4 核心表清单中未定义 `gate_decisions` 字段（仅 hitl_record 表），而回滚脚本 &sect;2.3 提到"恢复 gate_decisions 字段"。
- **建议**：在详细设计阶段统一 Gate 审批状态存储方案（hitl_record 表独立存储 vs stage_instance 表内嵌字段），消除术语不一致。
- **影响级别**：中（可能导致回滚脚本与实际表结构不匹配）

### WARN-3：HTTPS 演进与 API 版本策略的兼容性未明确 {#sec-warn3https-u6f14jinyu-api-banben}
- **位置**：04-quality-attributes.md &sect;1.1 提到 P1+ 引入 HTTPS 自签名证书；02-data-flow.md &sect;2.2 提到 REST API 版本通过 URL 路径声明。
- **问题**：若 P1+ 引入 HTTPS，WebSocket 从 `ws://` 切换为 `wss://`，前端协议配置是否需要动态适配？未在文档中说明。
- **建议**：在详细设计阶段补充协议自适应策略（开发环境 HTTP/WS，生产环境 HTTPS/WSS）。
- **影响级别**：低（P1 远期事项，不影响 MVP）

## ❌ 阻断项 {#sec-u963bu65adu9879}
**无阻断项。**

## 检查方法与样本 {#sec-jianchau65b9u6cd5yuu6837ben}
| 检查项 | 检查方法 | 样本量 |
|--------|----------|--------|
| 技术栈覆盖度 | 关键词匹配 + 存储需求对照 | 5 个主题文件 + design-input.md |
| 架构-目录一致性 | 层级映射表 | 4 层架构 vs 14 个目录 |
| 状态机-模块职责兼容性 | 状态枚举 vs 模块职责表 | 15 个状态 vs 10 个模块 |
| 异常-回滚联动 | 异常类别逐项核对 | 5 类异常 vs 回滚方案 5 个章节 |
| 性能-部署匹配 | QPS 预估 vs 部署节点数 | 5 个场景 vs 4 层部署拓扑 |
| 安全-接口契约一致性 | 认证方案 vs 通信模式 | 4 个安全维度 vs 2 种通信模式 |
| ADR 溯源 | ADR 编号 vs 竞品分析评分表 | 3 个 ADR vs design-input.md |

## 与 Gate 2 的衔接 {#sec-yu-gate-2-deu8854jie}
`00-design-overview.md` 的"跨文件一致性重点"章节已自动引用本报告中所有 ⚠️ 警告项。检查者可在此文件中完成重点确认。

**门控判断**：
- 无 BLOCKER &rarr; **允许进入 Gate 2 签字流程**
- 3 个 WARNING &rarr; 记录风险，签字后需在 detailed-design 阶段跟踪闭环
