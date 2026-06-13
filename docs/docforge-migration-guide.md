# DocForge 文档迁移使用手册

> **版本**：v1.0  
> **适用对象**：Arsitect 平台管理员、架构师、AI Agent  
> **最后更新**：2026-06-10

---

## 1. 功能概述

**文档迁移（Document Migration）** 是 DocForge 文档标准化流水线的第一步，负责将项目历史遗留的**自由格式 Markdown 文档**批量转换为符合 **DocForge 标准规范**的结构化文档。

### 1.1 核心能力

| 能力 | 说明 |
|------|------|
| **YAML Front Matter 生成** | 从旧文档提取/推断元信息，生成标准化的 YAML 头部 |
| **章节锚点注入** | 为 `##` / `###` 标题自动生成 `{#sec-xxx}` 锚点，支持中文转拼音 |
| **旧元信息清理** | 移除 `> 版本：xxx` 引用块、内嵌修改记录表格等冗余内容 |
| **文档类型推断** | 根据文件路径自动推断 `doc_type`（PRD/ARCH/DETAIL_DESIGN 等） |
| **Fragment ID 生成** | 为每份文档生成全局唯一的 `fragment_id`，作为跨文档引用的唯一标识 |
| **迁移清单输出** | 生成 `_migration-manifest.md`，记录源文件 → 新文件的完整映射 |

### 1.2 处理范围

- **输入**：`openspec/changes/{变更名}/` 下的所有 `.md` 文件（排除进度追踪、计划清单等管理文件）
- **输出**：`openspec/changes/{变更名}/baseline/` 目录下的标准化文档
- **当前基线**：已针对 `sdlc-visualizer` 变更完成 91 份文档的标准化迁移

---

## 2. 背景与动机

### 2.1 旧格式的问题

在项目早期阶段，文档由 AI Agent 和人类交替编写，元信息格式不统一：

```markdown
> **版本**：v1.2.0  
> **状态**：FROZEN  
> **作者**：AI Architect  
> **设计日期**：2026-05-20

# 系统架构设计

## 1. 架构概述

| 版本 | 日期 | 修改人 | 变更内容 |
|------|------|--------|----------|
| v1.0 | 2026-05-15 | agent | 初稿 |
| v1.1 | 2026-05-18 | human | 补充数据流 |
```

**问题**：
- 元信息散落在正文各处，机器难以解析
- 修改记录表格占用篇幅，且与 Git 历史重复
- 标题无锚点，交叉引用只能依赖行号或模糊匹配
- 文档间缺乏显式的依赖声明

### 2.2 DocForge 标准格式

迁移后的标准格式：

```markdown
---
doc_type: "ARCH"
fragment_id: "arch-sdlc-visualizer-001"
title: "系统架构设计"
version: "1.2.0"
version_type: "BASELINE"
author: "agent-architect"
tags: ["sdlc-visualizer", "architecture"]
status: "FROZEN"
iteration: "sdlc-visualizer"
dependencies:
  - fragment_id: "prd-sdlc-visualizer-000"
    version: "1.0.0"
c4_binding:
  level: "L2"
---

# 系统架构设计

> **C4 绑定引用**：
> - `@C4-L1-System:sdlc-visualizer`
> - `@C4-L2-Container:frontend-spa`

## 架构概述 {#sec-jia_gou_gai_shu}

## 数据流 {#sec-shu_ju_liu}
```

**优势**：
- 元信息结构化：YAML Front Matter 可被任何工具解析
- 锚点规范化：支持精确跳转和交叉引用
- 与 C4 架构体系打通：`c4_binding.level` 决定文档在架构中的层级
- 依赖显性化：`dependencies` 字段声明上游基线文档

---

## 3. 迁移规则详解

### 3.1 文档类型推断（doc_type）

系统根据文件的**目录路径**和**文件名**推断文档类型：

| 目录特征 | 推断 doc_type | C4 层级 |
|----------|--------------|---------|
| `high-level-requirements/` | `PRD` | L1 |
| `high-level-design/` | `ARCH` | L2 |
| `detailed-requirements/` | `PRD` | L1 |
| `detailed-design/` | `DETAIL_DESIGN` | L3 |
| `interface-contracts/` | `API_DESIGN` | L3 |
| `uat/` | `TEST_PLAN` | - |
| `brainstorming/`, `competitive-analysis/`, `sign-off/`, `code-review/` | `CHANGELOG` | - |
| 文件名为 `db-schema.md` | `DB_DESIGN` | L2 |
| 文件名为 `api-spec.md` | `API_DESIGN` | L3 |

**特殊处理**：
- `feature-XX-模块名/` 路径中的模块编号会被提取到 `fragment_id` 中
- `shared/` 路径会被标记为跨模块共享文档

### 3.2 Fragment ID 生成规则

Fragment ID 是文档在全局范围内的唯一标识，格式为：

```
{doc_type}-{iteration}{-featXX}{-shared}-{seq:03d}
```

**示例**：

| 源文件路径 | 生成的 fragment_id |
|-----------|-------------------|
| `high-level-requirements/01-overview.md` | `prd-sdlc-visualizer-001` |
| `detailed-design/feature-01-auth/02-flow.md` | `detail-design-sdlc-visualizer-feat01-002` |
| `interface-contracts/shared/api-spec.md` | `api-design-sdlc-visualizer-shared-824` |

**序号（seq）推导规则**：
1. 优先从文件名前缀提取数字（如 `01-overview.md` → `1`）
2. 无数字前缀时，使用文件名 MD5 哈希的后 3 位（保证唯一性）

### 3.3 YAML Front Matter 生成规则

系统从旧文档中提取以下元信息：

| 字段 | 提取来源 | 默认值 |
|------|---------|--------|
| `title` | 第一个 `# 标题` | 文件名（无扩展名） |
| `version` | `> 版本：xxx` 引用块 | `1.0.0` |
| `status` | `> 状态：xxx` 引用块 | `DRAFT` |
| `author` | `> 作者：xxx` 引用块 | `agent-migration` |
| `iteration` | 当前变更名（如 `sdlc-visualizer`） | - |
| `version_type` | 固定值 | `BASELINE` |
| `tags` | 自动附加 `iteration` + `architecture`（如适用） | - |

**状态值映射**：
- 包含 "frozen" / "冻结" / "已通过" → `FROZEN`
- 包含 "draft" / "草稿" → `DRAFT`
- 包含 "review" / "评审" → `REVIEW`

**作者值映射**：
- 包含 "AI" / "Agent" → `agent-pm`
- 包含 "architect" → `agent-architect`
- 包含 "developer" → `agent-developer`

### 3.4 章节锚点注入规则

对于所有 `##` 和 `###` 级别的标题，系统会：

1. **检查是否已有锚点**：如果标题已包含 `{#...}`，则跳过
2. **生成锚点 ID**：将中文标题转为拼音，保留数字，去除特殊字符
3. **去重**：如遇重名，自动追加 `_1`, `_2` 等后缀
4. **格式**：`## 标题 {#sec-锚点id}`

**示例**：

| 原标题 | 注入后 |
|--------|--------|
| `## 架构概述` | `## 架构概述 {#sec-jia_gou_gai_shu}` |
| `## 数据流` | `## 数据流 {#sec-shu_ju_liu}` |
| `## API 设计` | `## API 设计 {#sec-api_she_ji}` |

**拼音转换说明**：
- 内置 300+ 常用汉字拼音映射表
- 未收录汉字使用 Unicode 编码替代（如 `u4e00`）
- 英文和数字原样保留

### 3.5 旧元信息清理规则

系统会移除以下冗余内容：

1. **顶部引用块**：以 `>` 开头的版本/状态/作者/日期信息块
2. **修改记录表格**：包含 "修改记录" / "版本历史" / "版本 + 日期 + 修改人" 关键词的 Markdown 表格
3. **正文中的元信息引用块**：包含特定关键词（如 "模块编号"、"关联需求"、"上游基线" 等）的引用块

**注意**：清理仅针对元信息引用块，正文内容、Mermaid 图表、代码块完全保留。

### 3.6 跳过文件规则

以下文件会被自动跳过，不执行迁移：

| 文件名模式 | 跳过原因 |
|-----------|---------|
| `progress.md` | 进度追踪文件，非架构文档 |
| `plan.md` | 执行计划文件 |
| `tasks.md` | 任务清单文件 |
| `human-decisions.md` | 人工决策审计日志 |
| `master-flow.md` | 流程总线文件 |
| `prd-000-toc.md` | 目录索引文件 |
| `release-notes.md` | 发布说明文件 |
| 已位于 `baseline/` / `delta/` / `compiled/` / `_meta/` 目录下的文件 | 避免重复处理 |

---

## 4. 使用方式

### 4.1 方式一：前端界面（推荐）

1. 登录 Arsitect 平台
2. 在左侧导航栏选择 **平台管理 → 文档标准化**
3. 在配置面板中确认"源文档目录"（默认：`openspec/changes/sdlc-visualizer`）
4. 勾选需要执行的步骤（至少勾选"文档迁移"）
5. 点击**执行流水线**按钮
6. 在执行日志区域查看实时进度
7. 完成后在结果面板查看迁移清单和摘要

**界面功能说明**：

| 区域 | 功能 |
|------|------|
| 源文档目录 | 指定输入路径，输出会自动放到该路径的 `baseline/` 子目录 |
| 步骤选择 | 点击切换启用/禁用，数字徽章表示执行顺序 |
| 执行流水线 | 触发异步执行，按钮在执行期间禁用 |
| 执行日志 | 带时间戳的彩色日志，成功为绿色，错误为红色 |
| 迁移清单 | 完成后自动加载，显示源文件 → fragment_id 的完整映射 |
| C4 注册表 | 若执行了"C4 实体提取"步骤，可预览生成的注册表 |

### 4.2 方式二：REST API

#### 单步执行：文档迁移

```bash
curl -X POST http://localhost:8000/api/v1/docforge/migrate \
  -H "Content-Type: application/json" \
  -d '{
    "src_root": "openspec/changes/sdlc-visualizer",
    "dst_root": null
  }'
```

**响应示例**：

```json
{
  "success": true,
  "migrated": 91,
  "skipped": 12,
  "errors": []
}
```

#### 完整流水线执行

```bash
curl -X POST http://localhost:8000/api/v1/docforge/run-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "src_root": "openspec/changes/sdlc-visualizer",
    "steps": ["migrate", "extract_c4", "inject_tags", "fill_deps"]
  }'
```

**响应示例**：

```json
{
  "success": true,
  "results": [
    {
      "step": "migrate",
      "success": true,
      "detail": {
        "migrated": 91,
        "skipped": 12,
        "errors": []
      }
    },
    {
      "step": "extract_c4",
      "success": true,
      "detail": {
        "systems": 5,
        "actors": 1,
        "containers": 10,
        "components": 150,
        "interfaces": 143
      }
    },
    {
      "step": "inject_tags",
      "success": true,
      "detail": {
        "modified": 56,
        "skipped": 35
      }
    },
    {
      "step": "fill_deps",
      "success": true,
      "detail": {
        "modified": 72,
        "skipped": 19
      }
    }
  ],
  "completed_steps": 4,
  "failed_steps": 0
}
```

#### 查询可用步骤

```bash
curl http://localhost:8000/api/v1/docforge/pipeline-steps
```

#### 获取迁移清单

```bash
curl "http://localhost:8000/api/v1/docforge/migration-manifest?src_root=openspec/changes/sdlc-visualizer"
```

### 4.3 方式三：命令行脚本（遗留方式）

如需在服务器环境直接执行（不经过 HTTP API），可以直接调用 Python 模块：

```python
from pathlib import Path
from app.docforge.doc_migration_engine import migrate_legacy_docs

result = migrate_legacy_docs(
    src_root=Path("openspec/changes/sdlc-visualizer"),
    dst_root=Path("openspec/changes/sdlc-visualizer/baseline")
)

print(f"迁移完成：{len(result.migrated)} 份")
print(f"跳过：{len(result.skipped)} 份")
for rel, fid in result.migrated:
    print(f"  {rel} -> {fid}")
```

---

## 5. 产物说明

### 5.1 标准化文档

位于 `baseline/` 目录下，保持原始目录结构。每份文档包含：

- YAML Front Matter（元信息头部）
- C4 绑定引用块（由后续"C4 标签注入"步骤填充）
- 带锚点的正文内容

### 5.2 迁移清单（_migration-manifest.md）

位于 `baseline/_migration-manifest.md`，记录：

- 迁移总数和跳过总数
- 每份源文件的相对路径及其对应的 fragment_id
- 被跳过的文件列表

**用途**：
- 审计：追溯每份旧文档对应的标准化文档
- 回滚：根据清单删除或替换已迁移的文件
- 索引：快速查找特定 fragment_id 的源文件

### 5.3 C4 注册表（_c4-registry.yaml）

由"C4 实体提取"步骤生成，位于 `baseline/_c4-registry.yaml`，包含：

- `systems`：L1 系统级实体
- `actors`：参与者
- `containers`：L2 容器级实体
- `components`：L3 组件级实体
- `interfaces`：接口定义（METHOD + path）

---

## 6. 常见问题

### Q1：迁移会修改原始文件吗？

**不会**。迁移是**只读输入、写入新目录**的操作。原始文件保持不变，输出到 `baseline/` 子目录。

### Q2：可以重复执行迁移吗？

**可以**。重复执行会覆盖 `baseline/` 中的同名文件。建议在重复执行前备份已手动修改过的 baseline 文件，或使用 Git 管理变更。

### Q3：某些文件被跳过了，如何排查？

查看 `baseline/_migration-manifest.md` 中的 "Skipped files" 章节。常见原因：
- 文件名匹配跳过规则（如 `progress.md`）
- 文件位于 `baseline/` 等排除目录中

### Q4：生成的锚点是中文拼音，可以自定义吗？

当前版本锚点由系统自动生成。如需自定义，可在迁移完成后手动编辑 `{#sec-xxx}` 部分。注意：**修改锚点后需同步更新所有引用该锚点的交叉链接**。

### Q5：YAML Front Matter 中的 dependencies 为什么是空的？

dependencies 字段在"文档迁移"步骤中仅生成占位结构（`fragment_id: ""`）。实际的依赖关系由流水线的第四步"依赖填充"基于默认规则和正文引用自动推断并填充。

### Q6：迁移后的文档可以直接用于生产环境吗？

迁移后的文档格式已符合 DocForge 规范，但建议：
1. 抽样检查几份关键文档的格式正确性
2. 确认 fragment_id 命名符合团队约定
3. 运行完整的四步流水线（迁移 → 提取 C4 → 注入标签 → 填充依赖）
4. 通过人工闸门（Gate）审批后再冻结为基线

### Q7：如何处理新加入的文档？

对于新编写的文档，建议直接按 DocForge 标准格式编写，无需经过迁移。只有历史遗留的旧格式文档才需要执行迁移。

---

## 7. 完整流水线执行顺序

文档迁移通常是四步标准化流水线的第一步，完整顺序如下：

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  1. 文档迁移  │ -> │ 2. C4 实体提取│ -> │ 3. C4 标签注入│ -> │ 4. 依赖填充  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

| 步骤 | 输入 | 输出 | 耗时估计 |
|------|------|------|---------|
| 文档迁移 | `changes/` 旧文档 | `baseline/` 标准化文档 + `_migration-manifest.md` | < 1s（91 份） |
| C4 实体提取 | `changes/` 设计文档 | `baseline/_c4-registry.yaml` | < 1s |
| C4 标签注入 | `baseline/` + `_c4-registry.yaml` | 带 `@C4-` 引用块的 baseline 文档 | < 1s |
| 依赖填充 | `baseline/` 文档（含依赖占位） | 填充好 dependencies 的 baseline 文档 | < 1s |

**建议**：首次标准化时执行全部四步；后续增量更新时，可仅执行特定步骤（如仅"依赖填充"）。

---

## 8. 附录：Fragment ID 命名规范

```
{doc_type}-{iteration}{-featXX}{-shared}-{seq:03d}
│           │           │        │       │
│           │           │        │       └── 3 位序号（001-999）
│           │           │        └── 跨模块共享标记（可选）
│           │           └── 功能模块编号（可选，如 feat01）
│           └── 迭代/变更名（如 sdlc-visualizer）
└── 文档类型（prd/arch/detail-design/api-design/db-design/changelog/test-plan）
```

**示例**：

| fragment_id | 含义 |
|------------|------|
| `prd-sdlc-visualizer-000` | PRD 总览文档（序号 0） |
| `arch-sdlc-visualizer-001` | 架构核心设计文档 |
| `detail-design-sdlc-visualizer-feat03-002` | 功能模块 03 的详细设计第 2 份 |
| `api-design-sdlc-visualizer-shared-824` | 跨模块共享的 API 设计文档 |
| `db-design-sdlc-visualizer-shared-607` | 数据库设计文档 |

---

## 9. 相关文档

- `docs/Kimi_Agent_design/c4-binding-schema.md` — C4 Binding JSON Schema 规范
- `docs/Kimi_Agent_design/C4-doc-rules.md` — 文档类型矩阵与 C4 标签规范
- `docs/Kimi_Agent_design/doc-management-design.md` — 基线 + Delta 编译模式设计
- `scripts/migrate_docs.py` — 原始命令行脚本（遗留参考）
