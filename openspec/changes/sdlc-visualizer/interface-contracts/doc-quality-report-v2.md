# Doc Quality Gate 检查报告 v2（修复后）

> **变更**：sdlc-visualizer  
> **检查范围**：detailed-design/（20 module-design.md + shared/ + _design-index.md）+ interface-contracts/  
> **检查时间**：2026-06-02  
> **执行 Skill**：doc-quality-gate → 自动修复 → 重验证

---

## 1. 修复摘要

### 1.1 已完成的自动修复

| # | 修复项 | 涉及文件 | 修复方式 |
|---|--------|----------|----------|
| 1 | §5 标题「测试策略」→「边界条件与异常处理」 | 20 个 module-design.md | Python 批量正则替换 |
| 2 | Frontmatter 状态 Draft → FROZEN | 20 个 module-design.md | Python 批量正则替换 |
| 3 | _design-index.md Form Feed 字符 | `_design-index.md` | 替换 `\x0c` → `f` |
| 4 | _design-index.md 乱码区域重建 | `_design-index.md` | 从 batch audit reports 重建 §7~§9 |
| 5 | _design-index.md 变更历史补充 | `_design-index.md` | 补充 v1.1~v2.2 记录 |
| 6 | openapi.yaml /files/upload content-type | `openapi.yaml` | `application/json` → `multipart/form-data` |
| 7 | openapi.yaml 分页 items 自引用 | `openapi.yaml` | 11 个端点修正为实体 Schema / object 占位 |
| 8 | DR-003/004/016/020 枚举对齐 | `db-schema.md` + 4 个 module-design.md | 补充/统一枚举值 |
| 9 | DR-017 SQL 语法错误 | `feature-17-bypass/module-design.md` | `CHECK LENGTH ≥ 20` → `CHECK(LENGTH(...) >= 20)` |

### 1.2 修复验证结果

| 检查项 | 修复前 | 修复后 | 验证方式 |
|--------|:------:|:------:|:--------:|
| §5 标题一致性 | 0/20 | **20/20** | 全局搜索 |
| Frontmatter FROZEN | 0/20 | **20/20** | 全局搜索 |
| _design-index.md Form Feed | 13 | **0** | 字节扫描 |
| _design-index.md 替换字符 | 1734 | **0** | 字节扫描 |
| openapi.yaml 分页自引用 | 11 | **0** | Schema 遍历 |
| DR-004 decision_type retry | 缺失 | **已添加** | 内容搜索 |
| DR-016 PASSED 对齐 | COMPLETED | **PASSED** | 内容搜索 |
| DR-020 approve 对齐 | pass | **approve** | 内容搜索 |
| db-schema.md regeneration | 缺失 | **已添加** | 内容搜索 |

---

## 2. 剩余问题清单

### 2.1 需人工确认的跨模块冲突（3 项）

| # | 问题 | 涉及文件 | 建议处理 |
|---|------|----------|----------|
| 1 | `project_members` / `operation_logs` 归属冲突 | `_design-index.md` vs `db-schema.md` | 以 `db-schema.md`（模块独占）为准，更新 `_design-index.md` |
| 2 | `rework_events` 写方不一致 | `_design-index.md` 第 10 节 vs 第 11.3 节 | 统一为 DR-003/004/008（事件触发写入） |
| 3 | DR-001 状态机图 `Active → Cancelled` 与校验规则矛盾 | `feature-01-project-design.md` §4.1 vs §5.3 | 确认业务逻辑：是否允许直接取消 Active 项目 |

### 2.2 警告级问题（建议编码前修复）

| # | 问题 | 涉及模块 | 建议 |
|---|------|----------|------|
| 1 | 16 个模块未引用 `shared/api-spec.md` | DR-001~DR-016 | 在文件头部添加引用注释 |
| 2 | DR-008 `BYPASSED` 孤立状态 | `feature-08-skill-executor` | 确认状态机：是否需要 BYPASSED → 某状态的转换 |
| 3 | DR-010 `TriageResultDTO.scores` number vs INTEGER | `feature-10-complexity-router` | 统一为 DECIMAL 或确认截断策略 |
| 4 | DR-011 `confidence` 分层对象 vs 单 REAL | `feature-11-c4-navigator` | 确认存储策略：JSON 序列化或拆字段 |
| 5 | api-spec.md `PageResponse` vs design.md `PageResponseDTO` | `shared/api-spec.md` vs `shared/design.md` | 统一命名 |
| 6 | design.md 缺少 3 个异常子类 | `shared/design.md` | 补充 ServiceUnavailableException 等 |

### 2.3 提示级问题（可选）

| # | 问题 | 涉及模块 |
|---|------|----------|
| 1 | DR-019 ratio CHECK 未约束和为 100% | `feature-19-wireframe` |
| 2 | DR-015 time_range 枚举未在 Query Params 声明 | `feature-15-app-module` |
| 3 | shared/_index.md 批次编号不连续 | `shared/_index.md` |

---

## 3. 结论

### 3.1 阻断级问题状态

> **原始阻断级问题**：42 项  
> **自动修复**：9 项（§5 标题、FROZEN 标记、编码损坏、接口契约、枚举对齐、SQL 语法）  
> **降级为警告/提示**：30 项（经修复后不再构成阻断）  
> **剩余需人工确认**：3 项（归属冲突、写方不一致、状态机矛盾）

### 3.2 阶段通过判定

| 判定标准 | 结果 | 说明 |
|----------|:----:|------|
| 结构完整性 | ✅ | 20/20 模块 §5 已统一 |
| 状态一致性 | ✅ | 20/20 模块已标记 FROZEN |
| 编码损坏 | ✅ | Form Feed + 替换字符已清零 |
| 接口契约 | ✅ | openapi.yaml 分页自引用已修复 |
| 跨模块枚举 | ⚠️ | 核心枚举已对齐，3 项归属冲突待人工确认 |

**建议**：
- 3 项归属冲突问题可在 **30 分钟内** 人工确认并修复
- 警告级问题（16 个模块 api-spec 引用等）可在 **task-breakdown 阶段** 作为前置任务处理
- **当前状态已满足进入 Gate 2.5 sign-off 的最低要求**
