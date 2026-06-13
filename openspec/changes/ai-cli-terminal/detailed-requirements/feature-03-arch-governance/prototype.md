---
doc_type: "PRD"
fragment_id: "prd-ai-cli-terminal-dr-003-prototype"
title: "架构治理 - 交互原型"
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

# 架构治理 - 交互原型 {#sec-prototype}

## 1. 扫描触发与进度 {#sec-scan-progress}

```
arch> $ scan
[系统] 正在扫描项目架构...
[系统] 已扫描 120/320 个文件 [======>    ] 40%
[系统] 发现 3 个潜在问题
```

## 2. 治理项列表 {#sec-issue-list}

```
┌─ 架构治理项 ──────────────────────────────────────────────┐
│ [1] [警告] 循环依赖: utils → helpers → utils             │
│     位置: src/utils/index.ts                             │
│     [查看方案] [标记误报] [跳过]                         │
│                                                           │
│ [2] [严重] 超大函数: processOrder() 行数 320             │
│     位置: src/order/service.ts                           │
│     [查看方案] [标记误报] [跳过]                         │
│                                                           │
│ [3] [信息] 废弃接口: /api/v1/old-auth 仍被 3 处引用      │
│     位置: src/api/auth.ts                                │
│     [查看方案] [标记误报] [跳过]                         │
└───────────────────────────────────────────────────────────┘
```

### 2.1 列表排序规则 {#sec-sorting}

- 默认按 severity 降序：critical > warning > info。
- 同等级按影响文件数降序。
- 用户可输入 `sort by {rule}` 切换排序方式。

## 3. 治理方案卡片 {#sec-governance-card}

```
┌─ 治理方案 (#ARCH-20240613-001) ───────────────────────────┐
│ 类型: 循环依赖                                             │
│ 位置: src/utils/index.ts                                   │
│ 严重性: 警告                                               │
│                                                            │
│ 影响面:                                                    │
│ - utils/index.ts 与 helpers/format.ts 相互引用             │
│ - 影响 2 个模块的初始化顺序                                │
│                                                            │
│ 方案:                                                      │
│ 1. 将公共类型抽取到 src/types/shared.ts                    │
│ 2. 调整 import 方向                                        │
│                                                            │
│ Diff:                                                      │
│ - import { format } from '../helpers/format'               │
│ + import { FormatOptions } from '../types/shared'          │
│                                                            │
│ 审查点:                                                    │
│ - 确认 shared types 不引入新的循环                         │
│                                                            │
│ [✅ 执行重构]  [❌ 跳过]  [⚠️ 标记误报]                   │
└───────────────────────────────────────────────────────────┘
```

## 4. 重构执行进度 {#sec-refactor-progress}

```
[系统] 正在创建临时分支...
[系统] 正在抽取共享类型...
[系统] 正在更新 import 路径...
[系统] 正在运行构建验证... [========>  ] 80%
[成功] 验证通过
[成功] 已生成 ADR #ADR-20240613-001
```

## 5. ADR 编辑界面 {#sec-adr-editor}

验证通过后弹出 ADR 草稿：

```
┌─ 架构决策记录草稿 ────────────────────────────────────────┐
│ 标题: 消除 utils 与 helpers 之间的循环依赖                │
│ 日期: 2024-06-13                                          │
│ 决策: 抽取共享类型到 src/types/shared.ts                  │
│ 原因: [用户可补充...]                                      │
│ 影响: [用户可补充...]                                      │
│                                                            │
│ [保存] [暂不保存]                                          │
└───────────────────────────────────────────────────────────┘
```

## 6. 快捷操作 {#sec-quick-actions}

| 按钮 | 命令 | 说明 |
|------|------|------|
| 扫描架构 | `scan` | 触发全量扫描 |
| 治理规则配置 | `config` | 查看规则列表（P2） |
| 查看架构图 | `diagram` | 唤起 Mermaid 架构图（P2） |
