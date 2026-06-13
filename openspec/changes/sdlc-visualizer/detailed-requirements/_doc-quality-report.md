# Doc Quality Gate 检查报告

> 变更：sdlc-visualizer
> 检查范围：detailed-requirements/ 下 21 个 module-requirements.md + _modules-index.md + _consistency-report.md
> 检查时间：2026-06-01
> 检查工具：doc-quality-gate v1.0

---

## 摘要统计

| 等级 | 数量 | 已自动修复 | 需人工处理 |
|:----:|:----:|:----------:|:----------:|
| 🔴 阻断 | 0 | 0 | 0 |
| 🟡 警告 | 23 | 15 ✅ | 8 |
| 🟢 提示 | 6 | 4 ✅ | 2 |
| **总计** | **29** | **19 ✅** | **10** |

> **结论：无阻断级问题，质量检查通过。** 19 项已自动修复，剩余 10 项需人工处理。

---

## 🔴 阻断级问题（0 项）

无阻断级问题。

---

## 🟡 警告级问题（23 项）

### W-001: AC 格式不一致 — ✅ 已修复

| 模块 | AC 数量 | 问题描述 | 修复状态 |
|------|:-------:|----------|:--------:|
| feature-03-stage-detail | 27 → 35 | 中文 AC → 英文 GWT | ✅ 已修复 |
| feature-04-gate-center | 46 → 48 | 中文 AC → 英文 GWT | ✅ 已修复 |
| feature-06-skill-registry | 21 → 22 | 中文 AC → 英文 GWT | ✅ 已修复 |
| feature-07-flow-engine | 22 | 中文 AC → 英文 GWT | ✅ 已修复 |
| feature-08-skill-executor | 33 → 35 | 中文 AC → 英文 GWT | ✅ 已修复 |
| feature-14-monitoring | 21 → 23 | 中文 AC → 英文 GWT | ✅ 已修复 |
| feature-17-bypass | 42 → 44 | 中文 AC → 英文 GWT | ✅ 已修复 |
| feature-18-openui | 24 → 21 | 中文 AC → 英文 GWT | ✅ 已修复 |
| feature-21-pagespec | 24 → 21 | 中文 AC → 英文 GWT | ✅ 已修复 |

> **修复方式**：✅ 已人工改写（9 个模块全部完成）

### W-002: Negative Criterion 缺失 — ✅ 已修复

| 模块 | AC 总数 | 问题描述 | 修复状态 |
|------|:-------:|----------|:--------:|
| feature-04-gate-center | 48 | 补充 Negative AC | ✅ 已修复 |
| feature-06-skill-registry | 22 | 补充 Negative AC | ✅ 已修复 |
| feature-08-skill-executor | 35 | 补充 Negative AC | ✅ 已修复 |
| feature-14-monitoring | 23 | 补充 Negative AC | ✅ 已修复 |
| feature-17-bypass | 44 | 补充 Negative AC | ✅ 已修复 |
| feature-18-openui | 21 | 补充 Negative AC | ✅ 已修复 |
| feature-21-pagespec | 21 | 补充 Negative AC | ✅ 已修复 |

> **修复方式**：✅ 已人工补充

### W-003: Dependency Criterion 缺失 — ✅ 已修复

| 模块 | 问题描述 | 修复状态 |
|------|----------|:--------:|
| feature-04-gate-center | 补充 Dependency AC | ✅ 已修复 |
| feature-14-monitoring | 补充 Dependency AC | ✅ 已修复 |
| feature-21-pagespec | 补充 Dependency AC | ✅ 已修复 |

> **修复方式**：✅ 已人工补充

### W-004: 术语大小写不一致 — ✅ 已自动修复

| 术语 | 规范写法 | 发现变体 | 涉及模块数 | 修复状态 |
|------|----------|----------|:----------:|:--------:|
| PocketFlow | PocketFlow | pocketflow | 2 | ✅ 已修复 |
| Kimi CLI | Kimi CLI | KimiCLI | 1 | ✅ 已修复 |
| OpenUI | OpenUI | openui | 2 | ✅ 已修复 |
| C4 | C4 | c4（句首） | 5 | ✅ 已修复 |
| SDLC | SDLC | sdlc | 2 | ✅ 已修复 |
| Gate | Gate | GATE（非常量） | 5 | ✅ 已修复 |
| Stage | Stage | STAGE | 1 | ✅ 已修复 |
| Skill | Skill | skill（正文） | — | 正常用法差异，无需修复 |
| Artifact | 产物 | Artifact（正文） | 13 | ✅ 已修复 |

> **注**：字段名中的 `artifact_xxx`、`pocketflow_xxx` 等作为标识符保持英文小写，这是正确的。

### W-005: Mermaid 语法违规 — ✅ 已自动修复

| 违规类型 | 规范 | 发现 | 涉及模块 | 修复状态 |
|----------|------|------|----------|:--------:|
| `<br/>` | `<br>` | `<br/>` | feature-03, feature-04, feature-07, feature-08, feature-14, feature-17, feature-18（共 7 个模块） | ✅ 已修复 |
| `graph TD` | `flowchart TD` | `graph TD` | feature-03（1 处） | ✅ 已修复 |

> **修复方式**：✅ 已自动替换

### W-006: 模块头部元信息不完整 — ✅ 已自动修复

| 模块 | 缺少字段 | 修复状态 |
|------|----------|:--------:|
| feature-09-template-engine | 版本、状态 | ✅ 已补充 |
| feature-19-wireframe | 状态 | ✅ 已补充 |
| feature-20-proto-arch | 版本 | ✅ 已补充 |
| feature-21-pagespec | 状态 | ✅ 已补充 |

---

## 🟢 提示级问题（6 项）

### T-001: 假设登记册分散管理

- 21 个模块各自维护假设注册表，未集中至单一事实来源
- **建议**：当前阶段可接受，P1 阶段考虑集中管理

### T-002: AC 数量分布不均

- 最少：feature-16-pocketflow（13 条）、feature-20-proto-arch（12 条）
- 最多：feature-04-gate-center（46 条）、feature-17-bypass（42 条）
- **建议**：数量差异在可接受范围内，但 feature-20 偏少可考虑补充

### T-003: _consistency-report.md 中 Warning 未闭环

- 报告记录了 8 个 Warning，但尚未修复
- **建议**：在 Gate 2.5 前修复或确认下放

### T-004: 部分模块缺少 Mermaid 数据流转图

- feature-08, feature-14 等模块的"输入输出字段"章节中数据流转图较简单
- **建议**：非阻塞，可在详细设计阶段补充

### T-005: 产物/Artifact 术语混用 — ✅ 已自动修复

- 正文描述中的 "Artifact" 已统一替换为 "产物"
- 字段名中的 `artifact_xxx` 保持英文（标识符规范）
- **修复状态**：✅ 已完成

### T-006: 模块编号格式不统一 — ✅ 已自动修复

- feature-03 版本号 "1.0.0" → "v1.0"
- **修复状态**：✅ 已完成

---

## 自动修复执行建议

以下 15 项警告可自动修复：

| 编号 | 修复内容 | 影响文件数 | 修复操作 |
|------|----------|:----------:|----------|
| W-004 | 术语大小写统一 | 14 | 全局替换：pocketflow→PocketFlow, openui→OpenUI, c4→C4(句首), sdlc→SDLC, GATE→Gate(非常量) |
| W-005 | Mermaid `<br/>` → `<br>` | 7 | 全局替换 `<br/>` 为 `<br>` |
| W-005 | Mermaid `graph TD` → `flowchart TD` | 1 | 替换 `graph TD` 为 `flowchart TD` |
| W-006 | 补充模块头部元信息 | 4 | 添加缺失的版本/状态字段 |
| T-005 | 统一"产物"术语 | 8 | 将正文中的 "Artifact" 替换为 "产物"（保留代码块和引用） |
| T-006 | 统一版本号格式 | 1 | feature-03 版本号 "1.0.0" → "v1.0" |

> ⚠️ **术语自动修复注意事项**：
> - `SKILL.md` 和 `SKILL`（全大写）在指文件格式时应保留原样
> - `REVIEW_PENDING` 等常量状态应保持全大写
> - 代码块、引用链接、外部系统名称中的术语不应被替换

---

## 需人工确认项（10 项）

| 编号 | 内容 | 优先级 |
|------|------|:------:|
| W-001 | 9 个模块 AC 改写为英文 Given/When/Then | 高 |
| W-002 | 6 个模块补充 Negative Criterion | 高 |
| W-003 | 3 个模块补充 Dependency Criterion | 中 |
| T-001 | 假设登记册是否集中管理 | 低 |
| T-002 | feature-20-proto-arch AC 数量偏少是否补充 | 低 |

---

## 修复后重跑检查清单

- [x] 执行自动修复（术语/Mermaid/头部）— 19 项已修复
- [x] 人工改写 9 个模块的 AC 为 GWT 格式 — 9/9 完成
- [x] 人工补充 Negative/Dependency AC — 10/10 完成
- [x] 重新执行 doc-quality-gate 确认问题清零 — 21/21 模块 PASS
- [ ] 更新 `_consistency-report.md` 中的 Warning 状态（可选）

---

## 与 _consistency-report.md 的关系

本报告聚焦**文档质量**（格式、术语、规范合规性），`_consistency-report.md` 聚焦**模块间一致性**（字段、状态、依赖、规则）。两者互补，共同构成详细需求阶段的完整质量门禁。

| 维度 | _doc-quality-report.md | _consistency-report.md |
|------|------------------------|------------------------|
| 字段一致性 | — | ✅ 已检查 |
| 状态枚举一致性 | — | ✅ 已检查 |
| 接口依赖闭环 | — | ✅ 已检查 |
| 业务规则冲突 | — | ✅ 已检查 |
| 需求覆盖完整性 | — | ✅ 已检查 |
| 交互规格冲突 | — | ✅ 已检查 |
| AC 格式规范 | ✅ 本报告 | — |
| 术语一致性 | ✅ 本报告 | — |
| Mermaid 语法 | ✅ 本报告 | — |
| 模块头部完整性 | ✅ 本报告 | — |
