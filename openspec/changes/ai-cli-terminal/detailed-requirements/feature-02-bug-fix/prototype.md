---
doc_type: "PRD"
fragment_id: "prd-ai-cli-terminal-dr-002-prototype"
title: "Bug 修复 - 交互原型"
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

# Bug 修复 - 交互原型 {#sec-prototype}

## 1. 异常输入区 {#sec-error-input}

```
bug> $ Module not found: './utils/helper'
[系统] 正在解析异常签名...
[系统] 发现历史同类问题 #BUG-20240612-003（匹配度 87%），输入 `similar` 查看
[AI] 根因：文件重命名后引用未更新
[AI] 定位：src/components/List.vue:12
```

## 2. 修复方案卡片 {#sec-fix-card}

```
┌─ 修复方案 (#BUG-20240613-001) ─────────────────────────────┐
│ 文件: src/components/List.vue                              │
│ 风险: 低                                                   │
│                                                            │
│ 变更:                                                      │
│ - import { format } from './utils/helper'                  │
│ + import { format } from './utils/helper.ts'               │
│                                                            │
│ [✅ 执行修复]  [✏️ 编辑后执行]  [❌ 忽略]                   │
└────────────────────────────────────────────────────────────┘
```

### 2.1 卡片元素 {#sec-card-elements}

| 元素 | 说明 |
|------|------|
| 标题 | 修复方案编号与文件路径 |
| 风险标签 | 低/中/高，颜色区分 |
| Diff 区 | 使用 diff2html 渲染，支持展开/折叠 |
| 操作按钮 | 执行修复、编辑后执行、忽略 |

## 3. 执行进度展示 {#sec-execution-progress}

```
[系统] 正在创建临时工作区...
[系统] 正在应用补丁... [=====>    ] 60%
[系统] 正在运行验证...
[成功] 构建通过，测试通过
[成功] 已记录问题 #BUG-20240613-001
```

## 4. 高风险确认弹窗 {#sec-high-risk-confirm}

当风险为 high 时，点击"执行修复"后弹出二次确认：

```
┌─ 高风险确认 ─────────────────────────────┐
│ 该方案涉及多处文件修改，建议先生成 PR。   │
│                                           │
│ [继续执行（需 Tech Lead 权限）]           │
│ [取消并生成 PR]                           │
└───────────────────────────────────────────┘
```

## 5. 编辑后执行界面 {#sec-edit-mode}

用户选择"编辑后执行"时，在卡片下方展开代码编辑器：

```
┌─ 编辑修复方案 ─────────────────────────────┐
│ < Monaco 编辑器展示 Diff >                 │
│                                             │
│ [放弃] [预览效果] [确认执行]               │
└─────────────────────────────────────────────┘
```

## 6. 快捷操作 {#sec-quick-actions}

| 按钮 | 命令 | 说明 |
|------|------|------|
| 粘贴异常 | `paste` | 读取剪贴板 |
| 查看历史Bug | `history bug` | 展示本项目 Bug 记录 |
| 上传截图 | `upload` | 触发 OCR（P2） |
