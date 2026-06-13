# C4 关系抽取工具产品化设计

> **变更**: sdlc-visualizer  
> **功能**: C4 架构治理 — 从设计文档 + 代码自动提取并同步 `_c4-registry.yaml`  
> **状态**: MVP 实现已完成（后端 API + 前端 C4Navigator 入口 + 统计面板）  
> **日期**: 2026-06-12

---

## 1. 背景与目标

`backend/app/c4/extractor.py` 已从一次性脚本演进为可复用的 C4 抽取引擎：

- 基于 AST 解析 Python 多行 import，自动识别 Router → Service、Service → Repository、Service → Service 等关系。
- 识别 FastAPI router、前端 Zustand store / service-module、React 组件。
- 通过 ID 归一化合并文档与代码中的同名组件。
- 自动愈合 Service → Repository 关系并标记 `intentional_orphan`。

产品化目标：把该能力变成驾驶舱内的标准功能，让架构师/TL 能一键同步设计文档与代码，实时看到架构健康度。

---

## 2. 用户故事

| 角色 | 故事 | 验收标准 |
|------|------|----------|
| 架构师 | 在 C4 架构页点击“重新同步关系”，系统从最新设计文档和代码重新生成 registry | 按钮调用后端 API，成功后刷新 DSL 与统计 |
| Tech Lead | 同步完成后看到组件数、关系数、孤立节点数 | 统计面板展示 components / relationships / orphan / effective orphan / intentional orphan |
| 开发者 | 在治理页面看到哪些文档组件尚未实现 | 有效孤立节点列表可展开，显示来源文件与实现状态 |

---

## 3. 功能设计

### 3.1 触发入口

| 页面/节点 | 入口 | 行为 |
|-----------|------|------|
| **C4Navigator（C4 架构）** | 工具栏 `↻ 重新同步关系` | 调用 `POST /api/v1/c4/registry/extract`，完成后刷新 DSL 渲染与统计 |
| **ArchGovernance（架构治理）** | “C4 健康度”卡片 | 展示最新统计，点击跳转 C4Navigator 并触发同步 |
| **后台定时/CI** | 通过 `ops/c4_registry_gate.py` 在提交前运行 | 作为代码门禁的一部分 |

### 3.2 同步流程

```
用户点击同步
  │
  ▼
POST /api/v1/c4/registry/extract?project_id=sdlc-visualizer
  │
  ▼
后端调用 `app.c4.extractor.build_registry()`
  │
  ▼
生成 _c4-registry.yaml
  │
  ▼
读取 registry 计算统计指标
  │
  ▼
返回 C4ExtractResponseDTO { message, stats }
  │
  ▼
前端刷新 C4Renderer 与统计面板
```

### 3.3 统计面板

在 C4Navigator 工具栏下方展示紧凑统计条：

```
组件: 304 | 关系: 403 | 孤立: 63 | 有效孤立: 0 | intentional: 63 | 接口: 143
```

- **有效孤立** 用橙色高亮，点击可展开孤立节点列表。
- P1 可在 ArchGovernance 中升级为完整表格，支持：
  - 按容器、来源、实现状态过滤
  - 标记为 intentional_orphan
  - 一键创建 TODO / issue

### 3.4 孤立节点管理（P1）

| 操作 | 说明 |
|------|------|
| 查看详情 | 显示节点名称、来源文档、代码文件、是否已实现 |
| 标记 intentional | 在 registry 中设置 `intentional_orphan: true`，降低分析器告警级别 |
| 创建任务 | 对未实现组件生成 implementation task，写入 tasks.md（待设计） |
| 删除占位 | 对设计文档中的纯占位节点，提供“从文档移除”快捷入口（需人工确认） |

---

## 4. 后端 API 设计

### 4.1 已实现的端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/c4/registry/extract` | 执行抽取脚本并返回统计 |
| `GET`  | `/api/v1/c4/registry/stats` | 仅读取当前 registry 统计 |

### 4.2 请求/响应示例

**POST /api/v1/c4/registry/extract?project_id=sdlc-visualizer**

响应：

```json
{
  "project_id": "sdlc-visualizer",
  "message": "C4 registry written to .../_c4-registry.yaml",
  "stats": {
    "project_id": "sdlc-visualizer",
    "systems": 5,
    "actors": 1,
    "containers": 10,
    "components": 317,
    "interfaces": 142,
    "relationships": 399,
    "orphan_count": 77,
    "intentional_orphan_count": 61,
    "effective_orphan_count": 16,
    "orphans": [
      {
        "id": "riskalertrepository",
        "name": "RiskAlertRepository",
        "container_id": "backend-api",
        "source": "doc",
        "implemented": false,
        "source_file": "detailed-design/feature-01-project-dashboard/module-design.md"
      }
    ]
  }
}
```

### 4.3 实现文件

- `backend/app/api/v1/c4.py` — 新增 `/c4/registry/extract` 与 `/c4/registry/stats`
- `backend/app/schemas/c4.py` — 新增 `C4ExtractResponseDTO`、`C4RegistryStatsDTO`、`C4OrphanComponentDTO`
- `backend/app/c4/extractor.py` — 抽取引擎（backend service + CLI）
- `backend/app/c4/registry_extractor.py` — 抽取服务封装、快照、diff、intentional orphan 管理
- `ops/c4_registry_gate.py` — CI 门禁脚本

---

## 5. 前端设计

### 5.1 已挂载的页面/节点

- **C4Navigator 工具栏**：真实同步按钮 + 统计条
- **服务层**：`frontend/src/services/c4.ts` 新增 `extractC4Registry`、`getC4RegistryStats`
- **状态层**：`frontend/src/stores/c4NavigatorStore.ts` 新增 `syncRegistry`、`fetchRegistryStats`、`registryStats`、`syncLoading`

### 5.2 交互细节

- 同步按钮 loading 状态由 `syncLoading` 控制，避免重复点击。
- 同步成功后自动 `setRefreshKey` 触发 C4Renderer 重新渲染。
- 统计条仅在非全屏模式下显示。

### 5.3 P1 扩展

- 在 `ArchGovernance` 页面新增 “C4 架构健康度” 卡片：
  - 显示最近一次同步时间、组件/关系/孤立数
  - 提供 “查看详情” 跳转 C4Navigator
- 新增 `C4OrphanPanel` 抽屉组件：
  - 按容器筛选
  - 显示节点 source_file 链接
  - 支持标记 intentional_orphan（需后端写 registry 接口）

---

## 6. 数据与产物

| 产物 | 路径 | 说明 |
|------|------|------|
| 抽取引擎 | `backend/app/c4/extractor.py` | backend service，也可直接作为 CLI 运行 |
| 抽取服务 | `backend/app/c4/registry_extractor.py` | 提供 extract、stats、diff、intentional orphan 管理 |
| CI 门禁 | `ops/c4_registry_gate.py` | 提交前校验有效孤立节点不增加 |
| Registry | `openspec/changes/{change}/baseline/_c4-registry.yaml` | C4 治理单一数据源 |
| 分析结果 | 由 `/api/v1/c4/analyze` 实时生成 | 不持久化，基于最新 registry |

---

## 7. 非功能需求

- **幂等性**：重复执行抽取结果一致（registry 完全重写）。
- **性能**：单次抽取在 MVP 项目（~300 组件）上 < 5s。
- **安全**：仅允许本地项目路径，不接收用户上传路径。
- **可观测性**：抽取 stdout/stderr 返回给前端，便于排查。

---

## 8. 后续建议

1. **~~将抽取引擎模块化为 backend service~~**：已完成。核心逻辑已移入 `backend/app/c4/extractor.py`，由 `backend/app/c4/registry_extractor.py` 封装为 service 调用。
2. **增量 diff**：在同步后展示本次新增/删除/变更的组件与关系。
3. **CI 集成**：在 `ops/staging-config.yaml` 中增加 pre-commit hook 配置，自动校验 registry 孤立率。
4. **权限控制**：P2 阶段给同步操作增加 Gate 2+ 权限校验。
