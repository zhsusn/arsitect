---
doc_type: "PRD"
fragment_id: "prd-sdlc-visualizer-823"
title: "全量缺失功能实施计划"
version: "1.0.0"
version_type: "BASELINE"
author: "agent-migration"
tags: ['sdlc-visualizer', 'architecture']
status: "DRAFT"
iteration: "sdlc-visualizer"
dependencies:
  - fragment_id: ""
    version: ""
c4_binding:
  level: "L1"
---

# 全量缺失功能实施计划

> 制定时间：2026-06-05
> 基于 DR-001 ~ DR-021 详细需求核对结果

---

## 一、优先级划分 {#sec-yiyouu5148jihuafen}
### P0 — 阻塞性缺口（用户核心流程无法闭环） {#sec-p0-u963bu585exingu7f3akouyonghuh}
| 模块 | 缺失内容 | 影响 |
|------|----------|------|
| DR-003 | 阶段详情面板6个Tab全部占位 | 用户无法查看Skill快照、产物、日志、审查等核心信息 |
| DR-007 | Flow编排引擎页面未挂载路由 | 用户完全无法访问执行计划功能 |
| DR-010 | 复杂度路由面板无前端页面 | 项目创建时无法完成规模评估与路径选择 |

### P1 — 高价值缺口（显著提升用户体验） {#sec-p1-u9ad8u4ef7u503cu7f3akouu663eu}
| 模块 | 缺失内容 |
|------|----------|
| DR-001 | 项目详情侧滑面板、规模评估向导、删除确认、视图切换 |
| DR-002 | 泳道/列表视图、筛选面板、Stage合并、右键菜单 |
| DR-004 | 旁路审批弹层完整接入、低置信度禁用、24h倒计时 |
| DR-005 | 双栏编辑器、行级Diff、冲突检测、版本回滚确认 |

### P2 — 功能完善（模块高级特性） {#sec-p2-gongnengwanu5584mokuaiu9ad8ji}
| 模块 | 缺失内容 |
|------|----------|
| DR-006 | Skill详情抽屉、冲突处理弹窗、节点库拖拽、环检测 |
| DR-008 | Stage节点执行按钮、批量执行浮层、发布确认弹窗 |
| DR-009 | 偏离确认弹窗、Stage定义管理面板、决策日志 |
| DR-011 | DSL编辑器行号高亮、节点交互、导出面板、节点详情侧板 |

### P3 — 增强特性（可视化与分析） {#sec-p3-u589eu5f3atexingu53efu89c6hua}
| 模块 | 缺失内容 |
|------|----------|
| DR-012 | Diff Overlay、扫描历史、导出报告 |
| DR-013 | 甘特图、柱状图/箱线图、热力图、筛选器 |
| DR-014 | 阶段矩阵、Token统计、瓶颈告警 |
| DR-015 | 编辑/详情页、Module里程碑、依赖管理 |
| DR-016 | 三阶段控制台、产物列表、执行确认弹窗 |
| DR-017 | 补审工作台、授权结果页、倒计时告警 |
| DR-018 | 服务启动引导、取消生成、多页面导航 |
| DR-019 | 领域映射管理、跳转关系网络图、SVG交互 |
| DR-020 | 独立回写预览页、独立评审页（MVP标注暂不实现） |
| DR-021 | 审查面板、缺失字段提示、状态管理列表 |

---

## 二、批次规划 {#sec-erpiu6b21guihua}
### Batch 1（P0 核心补全） {#sec-batch-1p0-hexinu8865quan}
- [ ] DR-003: 阶段详情面板6个Tab真实数据加载与渲染
- [ ] DR-007: Flow编排引擎路由挂载 + 执行计划列表/详情页
- [ ] DR-010: 复杂度路由面板基础页面 + 规模评估表单

### Batch 2（P1 体验提升） {#sec-batch-2p1-tiyantisheng}
- [ ] DR-001: 项目详情侧滑面板 + 规模评估向导
- [ ] DR-002: 泳道视图 + 列表视图 + 筛选面板
- [ ] DR-004: 旁路审批弹层完整功能
- [ ] DR-005: 双栏编辑器 + Diff对比弹窗

### Batch 3（P2 功能完善） {#sec-batch-3p2-gongnengwanu5584}
- [ ] DR-006: Skill详情抽屉 + 冲突处理
- [ ] DR-008: Stage执行按钮 + 批量执行
- [ ] DR-009: 偏离确认弹窗 + Stage定义管理
- [ ] DR-011: DSL编辑器增强 + 节点交互

### Batch 4（P3 增强特性） {#sec-batch-4p3-u589eu5f3atexing}
- [ ] DR-012 ~ DR-021 按模块逐个补齐

---

## 三、技术方案要点 {#sec-sanu6280u672fu65b9u6848yaou70b9}
### 前端通用规范 {#sec-u524du7aeftongyongguifan}
- 新增页面统一在 `frontend/src/pages/{PageName}/index.tsx`
- 新增共享组件放在 `frontend/src/components/`
- 新增API封装在 `frontend/src/services/api.ts`
- 路由统一在 `frontend/src/App.tsx` 注册
- 使用现有设计系统：浅色主题、TailwindCSS、shadcn/ui 风格

### 后端通用规范 {#sec-u540eu7aeftongyongguifan}
- 新增路由在 `backend/app/api/v1/` 下
- 新增模型在 `backend/app/models/` 下
- 新增Schema在 `backend/app/schemas/` 下
- 已有表通过 Alembic 迁移，新增表通过 `init_db()` 自动创建

### 数据流规范 {#sec-shujuliuguifan}
- 前端通过 Axios 调用 REST API
- 实时数据（日志流）通过 SSE 端点 `/api/sse/{channel}`
- 状态管理使用 React Hooks（useState/useEffect/useCallback）

---

## 四、验收标准 {#sec-siyanshoubiaozhun}
每个模块完成后需满足：
1. 所有新页面在路由中可访问
2. 所有按钮有实际功能（非alert占位）
3. 前后端联调通过
4. 不破坏现有测试（保持 555 passed 基准）
5. 代码符合项目风格规范
