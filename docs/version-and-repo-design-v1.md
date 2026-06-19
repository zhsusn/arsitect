# SDLC Visualizer — 版本管理与仓库规范设计文档

> **版本**: v1.0  
> **日期**: 2026-06-18  
> **适用范围**: Application 版本号、Git 分支策略、产物与代码仓库管理、提交规则

---

## 1. 核心原则

1. **Monorepo**：产物（设计文档）与代码在同一个仓库，同分支同演进。  
2. **Project 驱动分支**：每个 Project 对应一个 feature 分支，周期内产物和代码都在该分支上提交。  
3. **半自动版本管理**：Project 完成自动打候选 tag，版本号由人确认后发布。  
4. **产物自动快照**：平台内编辑保存时自动 Git commit，代码由开发者手动提交。  
5. **Master 为稳定基线**：始终可发布，仅通过 PR 合并进入。

---

## 2. 仓库结构

```
{application-repo}/                  # 应用级 Git 仓库（Monorepo）
├── openspec/                        # 产物目录（平台管理的设计文档）
│   └── changes/
│       ├── project-12/              # Project-12 的产物
│       │   ├── prd.md
│       │   ├── c4-l2.dsl.yml
│       │   └── api-contract.yaml
│       └── project-13/              # Project-13 的产物
│           ├── prd.md
│           ├── c4-l2.dsl.yml
│           └── api-contract.yaml
├── src/                             # 代码目录（实际业务代码）
│   ├── order/
│   └── pay/
├── version.json                     # 当前版本号：{"version": "2.2.0"}
├── CHANGELOG.md                     # 版本变更日志
└── README.md
```

**规则**：
- `openspec/` 下的产物按 Project 隔离目录，避免不同 Project 产物覆盖冲突。  
- `src/` 为业务代码，按模块/服务组织。  
- `version.json` 为唯一版本号来源，手工维护，发版时由平台自动修改。

---

## 3. 分支策略（简化 Git Flow）

### 3.1 分支定义

| 分支 | 用途 | 生命周期 | 写入规则 |
|------|------|----------|----------|
| **master** | 稳定基线，始终可发布 | 长期 | 仅通过 PR 合并，禁止直接 push |
| **feature/project-{id}** | Project 开发分支，产物+代码同分支 | Project 周期（1~8 周） | Project 期间自由提交，结束后合并到 master 并删除 |
| **hotfix/** | 紧急修复（可选） | 临时 | 从 master 切出，修复后合并回 master 并打 patch 版本 |

### 3.2 Project 分支生命周期

```
Project 创建（Draft → Active）
    │
    ▼
从 master 切出 feature/project-{id}
    │
    ▼
Project 进行中 ───────────────────────────────┐
    │                                         │
    ├── 产物修改（openspec/）→ 平台自动 commit  │
    ├── 代码修改（src/）→ 开发者手动 commit     │
    └── 设计定稿基线化 → 产物自动 commit        │
    │                                         │
    ▼                                         │
Project 结束（编码测试完成）                     │
    │                                         │
    ▼                                         │
PR 合并到 master ←────────────────────────────┘
    │
    ├── 平台自动打 tag: project-{id}-complete
    └── 产物最终版本归档到 openspec/changes/project-{id}/
    │
    ▼
Tech Lead/PM 确认发布版本
    │
    ▼
修改 version.json → 打 tag: v{major}.{minor}.{patch}
    │
    ▼
删除 feature/project-{id} 分支（保留 tag）
```

**关键规则**：
- **Project 开始时自动切分支**：项目状态从 Draft → Active 时，平台调用 Git 命令 `git checkout -b feature/project-{id}`。  
- **Project 分支上产物和代码共存**：设计文档修改和代码开发在同一个分支上，一起演进。  
- **Project 结束必须合并到 master**：不合并的 Project 视为未完结，不能归档。  
- **合并后自动打候选 tag**：`project-{id}-complete`，标记该 Project 的代码和产物最终状态。

---

## 4. 版本管理规则

### 4.1 版本号格式

```
{major}.{minor}.{patch}
```

- **major**：架构级重构、不兼容变更、产品里程碑。  
- **minor**：新功能模块、较大特性迭代（通常由多个 Project 累积）。  
- **patch**：Bug 修复、小优化、单个 Project 的常规迭代。

### 4.2 版本号维护

| 操作 | 触发方式 | 自动/手动 | 说明 |
|------|----------|-----------|------|
| **Project 完成打候选 tag** | Project 测试通过、合并到 master 后 | **自动** | 打 `project-{id}-complete` tag，不改 version.json |
| **发布版本** | Tech Lead/PM 在项目管理页面点击"发布版本" | **手动** | 选择 major/minor/patch，平台自动修改 version.json 并打 `v{x}.{y}.{z}` tag |
| **紧急 hotfix** | 从 master 切 hotfix 分支 | **手动** | 修复后合并回 master，自动打 patch 版本 tag |

**为什么不是全自动？**  
三个 Project 做完可能只发一次 minor 版本，一个 Project 做完也可能只是 patch。版本号是**业务发布决策**，不是技术结果。

### 4.3 版本发布流程

```
Project-12 完成 → 合并 master → tag: project-12-complete
Project-13 完成 → 合并 master → tag: project-13-complete
    │
    ▼
PM 在项目管理页面点击"发布版本"
    │
    ▼
弹窗：选择版本类型 [major] [minor] [patch]
    │
    ▼
平台自动：
  1. git checkout master
  2. 修改 version.json: "2.2.0" → "2.3.0"（minor）
  3. git commit -m "release: v2.3.0 (Project-12, Project-13)"
  4. git tag v2.3.0
  5. 生成 CHANGELOG.md 片段（基于 Project 产物和代码提交记录）
```

---

## 5. 提交规则

### 5.1 产物提交（openspec/）

| 场景 | 提交方式 | Commit Message 规则 | 示例 |
|------|----------|---------------------|------|
| 平台内编辑保存 | **自动** | `auto: {产物名} v{版本} by {操作}` | `auto: prd.md v3 by 重新生成` |
| 审查后重新生成 | **自动** | `auto: {产物名} v{版本} by 携带批注重生成` | `auto: c4-l2.dsl.yml v2 by 携带批注重生成` |
| 设计定稿基线化 | **自动** | `baseline: {产物名} v{版本} 基线化` | `baseline: api-contract.yaml v1 基线化` |
| 回滚到历史版本 | **自动** | `rollback: {产物名} 回滚至 v{版本}` | `rollback: prd.md 回滚至 v2` |
| 手动编辑（IDE） | **手动** | 遵循开发者自己的 commit 规范 | — |

**规则**：
- 平台内所有保存操作（编辑、重新生成、基线化、回滚）**自动触发 Git commit**，不需要用户写 message。  
- 自动 commit 使用平台预设模板，包含产物名、版本、操作类型。  
- 用户通过 IDE 手动修改 openspec/ 下的文件时，按常规 Git 流程手动提交。

### 5.2 代码提交（src/）

| 场景 | 提交方式 | 说明 |
|------|----------|------|
| 编码开发 | **手动** | 开发者自行 commit/push，写有意义的 message |
| 测试修复 | **手动** | Bug 修复后手动提交 |
| 代码生成（AI） | **手动** | AI 生成的代码由开发者 review 后手动提交 |

**规则**：代码提交完全由开发者控制，平台不自动 commit 代码。

### 5.3 合并提交

Project 结束合并到 master 时，**建议用 squash merge** 或 **rebase merge**，将 Project 分支上的多次自动/手动提交整理为一条清晰的合并记录：

```
Merge Project-13: 支付接口重构
- 产物: 更新 PRD v3, C4 L2 DSL v2, 接口契约 v1
- 代码: 重构支付模块，新增订单查询接口
- 基线: api-contract.yaml v1 基线化
```

---

## 6. 与平台实体的映射关系

| 平台实体 | Git 概念 | 映射规则 |
|----------|----------|----------|
| **Application** | 仓库（Repository） | 1 Application = 1 Git 仓库（Monorepo） |
| **Project** | feature 分支 | 1 Project = 1 feature/project-{id} 分支 |
| **ProjectStage** | 分支上的提交区间 | 一个 Project 内多个 Stage 的提交都在同一分支上，通过 tag 或 commit message 区分阶段 |
| **Artifact** | 文件（openspec/ 下的具体文件） | 1 Artifact = 1 个产物文件（如 prd.md） |
| **ArtifactVersion** | Git commit（产物快照） | 1 ArtifactVersion = 1 次 Git commit（平台自动提交） |
| **Application 版本** | Git tag（v{x}.{y}.{z}） | 1 版本 = 1 个 Git tag，由人确认后发布 |
| **Project 完成标记** | Git tag（project-{id}-complete） | 1 Project 完成 = 1 个候选 tag，自动打 |

---

## 7. 关键约束与异常处理

| 场景 | 处理规则 |
|------|----------|
| **Project 分支未合并就归档** | 禁止。Project 状态变为 Archived 前必须检测 feature 分支是否已合并到 master，未合并则阻塞归档并提示。 |
| **产物自动 commit 冲突** | 平台自动 commit 前检测是否有未提交的本地修改（如 IDE 手动编辑），有冲突时提示用户先处理。 |
| **version.json 手动修改** | 平台自动发布版本时会检测 version.json 是否被手动修改过，若手动修改过则弹窗确认是否覆盖。 |
| **回滚到旧版本** | 回滚操作在平台内完成（ArtifactVersion 回滚），平台自动执行 `git revert` 或 `git checkout` 到指定 commit，并打 `rollback` 标签。 |
| **多 Project 并行** | 允许。多个 feature 分支从同一 master 切出，各自独立演进，按完成顺序依次合并。 |

---

## 8. 与现有设计的衔接

| 现有设计 | 衔接点 | 说明 |
|----------|--------|------|
| **项目工作台-项目管理** | Project 创建时自动切 feature 分支 | 状态 Draft → Active 时触发 |
| **项目工作台-项目管理** | Project 归档时检测分支合并 | 未合并到 master 则阻塞 |
| **项目工作台-项目管理** | "发布版本"按钮 | 手动触发版本发布流程 |
| **方案设计室-设计定稿** | 基线化自动 commit | 锁定产物版本时自动 Git commit |
| **产物浏览器-版本历史** | 展示 Git commit 历史 | ArtifactVersion 直接对应 Git commit |
| **产物浏览器-回滚** | 执行 Git revert/checkout | 平台自动操作 Git |
| **开发执行室-任务编排** | 代码开发在 feature 分支上 | 开发者手动 commit 到当前 Project 分支 |
| **开发执行室-测试调试** | 测试通过后合并到 master | Project 结束流程的一部分 |

---

## 附录：变更日志

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| v1.0 | 2026-06-18 | 初始版本：定义 Monorepo 结构、简化 Git Flow、半自动版本管理、产物自动提交规则、与平台实体映射 |
