---
doc_type: "PRD"
fragment_id: "prd-ai-cli-terminal-dr-003-logic"
title: "架构治理 - 业务逻辑"
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

# 架构治理 - 业务逻辑 {#sec-logic}

## 1. 总体流程 {#sec-main-flow}

```mermaid
flowchart TD
    Start([用户点击扫描]) --> Validate{项目路径有效?}
    Validate -->|否| Invalid[提示路径不存在]
    Validate -->|是| Scan[扫描代码库]
    Scan --> Progress[流式返回扫描进度]
    Scan --> Match[规则匹配生成治理项]
    Match --> Sort[按严重性与影响面排序]
    Sort --> List[渲染治理项列表卡片]
    List --> Select{用户选择治理项}
    Select -->|查看方案| Plan[AI 生成治理方案]
    Select -->|跳过| Skip[记录为 skipped]
    Select -->|标记误报| FP[记录为 false_positive]
    Plan --> Confirm{用户操作}
    Confirm -->|执行重构| Auth{权限足够?}
    Confirm -->|跳过| Skip
    Confirm -->|标记误报| FP
    Auth -->|否| Deny[提示权限不足]
    Auth -->|是| Exec[临时工作区执行重构]
    Exec --> Verify{验证通过?}
    Verify -->|是| ADR[生成 ADR 草稿]
    Verify -->|否| Rollback[自动回滚]
    ADR --> SaveADR[保存 ADR 记录]
    SaveADR --> Close[关闭治理项]
    Invalid --> End([结束])
    Skip --> End
    FP --> End
    Deny --> End
    Close --> End
    Rollback --> Retry{重新规划?}
    Retry -->|是| Plan
    Retry -->|否| End
```

## 2. 扫描规则 {#sec-scan-rules}

### 2.1 默认规则集 {#sec-default-rules}

| 规则 ID | 名称 | 默认启用 | 严重级别 |
|---------|------|----------|----------|
| RULE-001 | 循环依赖检测 | 是 | warning |
| RULE-002 | 超大函数检测 | 是 | critical |
| RULE-003 | 废弃接口引用 | 是 | info |
| RULE-004 | 重复代码块 | 否 | warning |
| RULE-005 | 未使用导入 | 是 | info |

### 2.2 规则配置 {#sec-rule-config}

- 默认关闭高误报规则（如重复代码块）。
- 用户可通过 `config` 命令查看规则列表（P2 支持编辑）。
- 扫描时只启用已启用规则，未启用规则不进入匹配流程。

## 3. 治理项排序规则 {#sec-sorting-rules}

1. 严重级别降序：critical > warning > info。
2. 同等级按影响文件数降序。
3. 再按发现时间升序。

## 4. AI 治理方案生成 {#sec-ai-plan}

1. 扫描引擎将 issue 描述、位置、相关代码片段传递给 AI Gateway。
2. AI 返回治理方案，需包含：
   - 影响面分析。
   - 分步骤重构计划。
   - 具体 Diff。
   - 人工审查点。
3. 后端将方案封装为治理方案卡片，流式推送至前端。

## 5. 架构问题状态机 {#sec-arch-state-machine}

```mermaid
stateDiagram-v2
    [*] --> detected: 扫描发现
    detected --> planned: 生成方案
    detected --> skipped: 用户跳过
    detected --> false_positive: 用户标记误报
    planned --> executed: 用户确认
    executed --> verified: 验证通过
    executed --> failed: 验证失败
    failed --> planned: 重新规划
    verified --> closed: 保存 ADR
    skipped --> [*]
    false_positive --> [*]
    closed --> [*]
```

## 6. 重构执行规则 {#sec-refactor-rules}

- 执行前校验用户写入权限与项目路径。
- 在临时 Git 工作区创建新分支并应用重构。
- 重构步骤按 AI 方案分步执行，每步失败即停止并回滚。
- 验证至少包含构建与单元测试。
- 验证通过后保留变更并生成 ADR 草稿。

## 7. ADR 生成规则 {#sec-adr-rules}

- ADR 编号格式：`#ADR-{YYYYMMDD}-{序号}`。
- 默认标题："消除 {location} 的 {issueType}"。
- 默认决策：使用 AI 方案中的核心步骤。
- 原因与影响字段留空，由用户补充后保存。
- 用户选择"暂不保存"时，ADR 以草稿状态保存，可后续编辑。
