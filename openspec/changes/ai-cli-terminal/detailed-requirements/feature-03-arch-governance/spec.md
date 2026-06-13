---
doc_type: "PRD"
fragment_id: "prd-ai-cli-terminal-dr-003-spec"
title: "架构治理 - 模块规格"
version: "1.0.0"
status: "DRAFT"
iteration: "ai-cli-terminal"
dependencies:
  - fragment_id: "prd-ai-cli-terminal-000"
    version: "1.0.0"
  - fragment_id: "prd-ai-cli-terminal-001"
    version: "1.0.0"
  - fragment_id: "prd-ai-cli-terminal-002"
    version: "1.0.0"
---

# 架构治理 - 模块规格 {#sec-spec}

## 1. 模块定位 {#sec-module-position}

本模块面向 Tech Lead 与架构师，提供项目级架构坏味道扫描、治理项管理、AI 生成治理方案、重构执行与 ADR 记录的完整能力。模块默认采用保守扫描规则以降低误报，所有重构执行前必须经用户确认。

## 2. 功能边界 {#sec-functional-scope}

### 2.1 In-Scope {#sec-in-scope}

- 触发项目架构扫描并实时展示进度。
- 按规则匹配代码库，生成治理项列表。
- 对治理项按严重性与影响面排序。
- 为每个治理项生成 AI 治理方案卡片。
- 接收用户确认、跳过或标记误报的操作。
- 在临时工作区执行重构并运行验证。
- 验证通过后生成 ADR 记录。

### 2.2 Out-of-Scope {#sec-out-of-scope}

- 复杂分布式架构治理（Non-goal）。
- 自动 PR 创建与合并（P2）。
- 治理规则的可视化配置编辑器（P2）。
- 跨仓库/跨服务架构扫描（P2）。

## 3. 用户场景 {#sec-user-scenarios}

### 3.1 场景一：一键扫描项目 {#sec-scenario-scan}

Tech Lead 在 Arch 模式下点击"扫描架构"，系统按默认规则扫描项目，首屏治理项在 3s 内渲染。

### 3.2 场景二：查看并选择治理项 {#sec-scenario-select}

用户浏览治理项列表，点击某一项查看详细描述与影响面，决定执行、跳过或标记误报。

### 3.3 场景三：执行重构并记录 ADR {#sec-scenario-adr}

用户确认治理方案后，系统在临时工作区执行多文件重构，验证通过后自动生成 ADR 草稿，用户可补充决策理由后保存。

## 4. 验收标准 {#sec-acceptance-criteria}

| 编号 | 场景 | 验收标准 | 优先级 |
|------|------|----------|--------|
| AC3-001 | 触发扫描 | 点击扫描后 3s 内展示首屏治理项 | P0 |
| AC3-002 | 无效路径 | 项目路径无效时提示"项目路径不存在" | P0 |
| AC3-003 | 空结果 | 无问题时提示"未检测到架构问题" | P0 |
| AC3-004 | 治理项列表 | 列表展示问题类型、位置、严重性与操作入口 | P0 |
| AC3-005 | 治理方案卡片 | 卡片展示影响面、重构步骤、Diff、审查点 | P0 |
| AC3-006 | 执行验证 | 重构后自动运行构建/测试，失败时回滚 | P0 |
| AC3-007 | ADR 记录 | 验证通过后生成 ADR 草稿并支持用户补充 | P0 |

## 5. 依赖与约束 {#sec-dependencies}

- 依赖 CLI 会话模块提供 sessionId 与消息通道。
- 依赖代码扫描引擎提供规则匹配能力。
- 依赖 AI Gateway 生成治理方案。
- 依赖 Exec Service 在临时工作区执行重构。
- 默认关闭高误报规则，用户可手动开启（P1）。
- 本期聚焦单仓库代码级坏味道。
