# 开发任务拆分与依赖关系

> **版本**: v1.0  
> **日期**: 2026-06-17  
> **依据**: `docs/tech-design-ui-restructure-v1.md`

---

## 任务总览

| 编号 | 任务名称 | 优先级 | 依赖 | 预估工时 |
|------|----------|--------|------|----------|
| T1 | 后端数据库 Migration（ExecutionTask + ExecutionIssue） | P0 | 无 | 2h |
| T2 | 后端新增数据模型 | P0 | T1 | 1h |
| T3 | 后端新增 Pydantic Schemas | P0 | T2 | 1h |
| T4 | 后端新增 Services（TaskCenter + Issue + RequirementStudio） | P0 | T2, T3 | 4h |
| T5 | 后端新增 API Routes（requirement_studio + execution） | P0 | T3, T4 | 4h |
| T6 | 后端修改现有路由注册（router.py） | P0 | T5 | 1h |
| T7 | 前端导航和路由重组（App.tsx） | P0 | 无 | 2h |
| T8 | 前端新增 API 服务封装 | P0 | T5 | 1h |
| T9 | 前端新建页面目录结构和骨架组件 | P0 | T7 | 2h |
| T10 | 前端需求设计室页面（RequirementStudio） | P0 | T8, T9 | 4h |
| T11 | 前端开发执行页面（TaskCenter + Issues） | P0 | T8, T9 | 4h |
| T12 | 前端产物验证 + 治理审批 + 平台管理页面迁移 | P0 | T7, T9 | 2h |
| T13 | 前端项目中心页面调整 | P0 | T7 | 1h |
| T14 | 后端单元测试 | P0 | T4, T5 | 3h |
| T15 | 前端单元测试 | P0 | T9-T13 | 2h |
| T16 | 集成测试 | P0 | T14, T15 | 2h |
| T17 | E2E 测试 | P0 | T16 | 2h |

---

## 任务依赖图

```
T1 (Migration)
  └── T2 (Models)
        └── T3 (Schemas)
              ├── T4 (Services)
              │     └── T5 (API Routes)
              │           └── T6 (Router Registration)
              │                 └── T14 (Backend Unit Tests)
              │                       └── T16 (Integration Tests)
              │                             └── T17 (E2E Tests)
              │
              └── T8 (Frontend API Services)
                    └── T10-T13 (Frontend Pages)
                          └── T15 (Frontend Unit Tests)
                                └── T16 (Integration Tests)
                                      └── T17 (E2E Tests)

T7 (Navigation & Routing) ──→ T9 (Page Skeletons)
                                  └── T10-T13 (Frontend Pages)
```

---

## 关键依赖说明

1. **后端链路**：Migration → Models → Schemas → Services → API Routes → Router → 测试
2. **前端链路**：导航路由 → 页面骨架 → API 封装 → 页面填充 → 测试
3. **前后端汇合**：Integration Tests 需要前后端都完成
4. **并行开发**：T1-T6（后端）和 T7-T9（前端骨架）可以并行启动

---

## 执行批次

### 批次 1（并行启动）
- T1: 后端 Migration
- T7: 前端导航和路由重组

### 批次 2（依赖批次 1）
- T2: 后端模型
- T9: 前端页面骨架

### 批次 3（依赖批次 2）
- T3: 后端 Schemas
- T8: 前端 API 封装

### 批次 4（依赖批次 3）
- T4: 后端 Services
- T10-T13: 前端页面填充

### 批次 5（依赖批次 4）
- T5: 后端 API Routes

### 批次 6（依赖批次 5）
- T6: 后端 Router 注册
- T14: 后端单元测试

### 批次 7（依赖 T6 + T10-T13）
- T15: 前端单元测试
- T16: 集成测试
- T17: E2E 测试

---

## 子代理分配建议

| 子代理 | 任务 | 说明 |
|--------|------|------|
| Sub-agent A | T1-T6 | 后端开发（数据库 → API） |
| Sub-agent B | T7-T9, T13 | 前端骨架和导航 |
| Sub-agent C | T10-T11 | 前端需求设计室 + 开发执行页面 |
| Sub-agent D | T12 | 前端迁移页面 |
| Sub-agent E | T14-T17 | 测试（前后端 + 集成 + E2E） |
