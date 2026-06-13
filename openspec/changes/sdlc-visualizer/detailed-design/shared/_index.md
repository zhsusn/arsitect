# shared/ 目录索引

> **变更**：sdlc-visualizer
> **提取批次**：第一批~第五批详细设计完成后统一提取（2026-06-02）
> **维护规则**：新增公共组件需经 Cross-Module Audit 确认 ≥2 模块引用后方可加入本目录。

---

## 目录结构

```
detailed-design/shared/
├── _index.md          # 本文件：公共组件目录索引与使用规范
├── db-schema.md       # 公共数据表定义（SQLite DDL + 设计说明）
├── api-spec.md        # 公共 REST 接口规范（分页、搜索、上传、认证）
└── design.md          # 公共设计组件（分页 DTO、异常基类、文件适配器）
```

---

## 文件职责

| 文件 | 职责 | 引用方式 |
|------|------|----------|
| `db-schema.md` | 定义被 ≥2 模块依赖的公共数据表 | 模块内通过 `shared/db-schema.md#{表名}` 引用 |
| `api-spec.md` | 定义全局公共 REST 接口 | 模块内通过 `shared/api-spec.md#{接口名}` 引用 |
| `design.md` | 定义跨模块复用的设计组件与规范 | 模块内通过 `shared/design.md#{组件名}` 引用 |

---

## 公共表清单（15 张）

详见 `db-schema.md`，按批次组织：

- **第一批**：`workspaces`, `size_estimates`, `applications`, `projects`, `skills`, `templates`, `template_stages`, `project_stages`
- **第三批**：`stage_review_status`, `gate_decisions`, `gate_decision_history`, `artifact_files`, `artifact_versions`
- **第四批**：`c4_dsl_store`

---

## 公共接口清单

详见 `api-spec.md`：

- 分页查询接口规范
- 全局搜索接口
- 文件上传接口
- 统一错误响应格式

---

## 公共设计组件清单

详见 `design.md`：

- 分页 DTO（PageRequest / PageResponse）
- 全局异常处理基类
- 文件系统适配器接口
- Zustand Store 模式规范

---

## 使用规范

1. **禁止重复定义**：模块 `module-design.md` 中引用公共表时，禁止使用 `CREATE TABLE` 重复定义 DDL，应通过链接引用 `shared/db-schema.md`。
2. **最小依赖原则**：仅当被 ≥2 个模块明确依赖时，方可将表/接口/组件提取到 `shared/`。
3. **版本同步**：修改 `shared/` 中任何定义时，必须同步更新所有引用该定义的模块设计文件，并重新执行 Cross-Module Audit。
4. **模块独占保留**：即使未来某模块独占表被其他模块引用，也应先经 Audit 确认，再迁移到 `shared/`，禁止随意移动。
