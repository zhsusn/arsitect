# 会话记录：C4 架构治理修复与治理中心建设

> 会话时间：2026-06-11
> 涉及模块：backend/app/c4/、frontend/src/components/C4Renderer.tsx、docs/ai-output/

---

## 一、紧急 Bug 修复（已完成）

### 1.1 C4 架构页面 L1-L4 图形消失

**根因**：`backend/app/c4/renderer.py` 的 `MermaidOutput` 给 `consistency_report` 默认赋了空字典 `{}`。当 `api/v1/c4.py` 构造 `C4RenderResponseDTO` 时，把这个 `{}` 传给 `consistency_report` 字段。但 `ConsistencyReportDTO` 要求 `passed` / `issues` / `summary` / `code_scan_summary` 四个字段必填，FastAPI 序列化时触发 Pydantic `ValidationError`，API 返回 **500**，前端拿不到图。

**修复内容**：
- `MermaidOutput` 两个报告字段默认值改为 `None`
- `render()` 里给 `analyzer.analyze()` 和 `consistency_checker.check()` 加了 `try/except`，即使分析失败也**不阻断渲染**
- 重启后端服务（PID 30392）

**验证**：
```bash
cd backend && python -c "..."  # C4RenderResponseDTO 序列化通过，JSON 长度 3755
```

### 1.2 诊断面板找不到"检查和修复工具"

**根因**：`renderer.py` 虽然 `import` 了 `ConsistencyChecker`，但 `render()` 方法里**根本没调用它**，所以 `consistency_report` 永远是空的。

**修复内容**：在 `render()` 中补充了 `ConsistencyChecker(CodeScanner()).check()` 的调用。

### 1.3 诊断面板 UI 优化

**改动文件**：`frontend/src/components/C4Renderer.tsx`

- 将诊断区域抽取为独立 `DiagnosticsPanel` 组件
- **支持折叠/展开**：默认折叠，点击"诊断信息 ▼/▲"切换
- 按钮上显示未通过的架构问题数（红）和一致性问题数（橙）
- **删除无用信息**：`expanded` 状态、`URL`、后端 `debug_info`、`lastMermaidPreview`（Mermaid 源码片段）
- **保留有效信息**：架构检查报告、文档与代码一致性报告、后端参数不匹配自诊断警告

### 1.4 CodeScanner 健壮性增强

**改动文件**：`backend/app/c4/code_scanner.py`

- `read_text(encoding="utf-8")` 增加 `UnicodeDecodeError` / `OSError` 容错，自动降级为 `errors="replace"`
- 防止扫描到非 UTF-8 文件（如 GBK 编码日志、二进制缓存文件）时整个分析流程崩溃

### 1.5 前端 API 错误处理增强

**改动文件**：`frontend/src/components/C4Renderer.tsx`

- fetch 后增加 `!res.ok` 判断，API 返回 500 时前端显示明确错误提示"后端错误 xxx: 请检查后端日志或联系管理员"
- 避免后端异常时前端静默空白

---

## 二、架构治理中心建设（进行中）

### 2.1 背景：当前诊断规则的合理性分析

| 规则 | 原逻辑 | 问题 | 修复后逻辑 |
|------|--------|------|-----------|
| **孤儿节点** | 所有层级 WARNING | L1 Actor/ExternalSystem 本来就是单向触达；L3 工具类/配置组件本就没有关系 | 按层级分级：L2/L4 WARNING，L1/L3 INFO；支持 `intentional_orphan` 豁免 |
| **不连通子图** | 所有层级 WARNING | L1 的多个 Actor 之间本来就没关系 | L1 不再检查 |
| **命名规范** | WARNING | 中文项目里中文 ID 完全合理 | 降为 INFO |
| **循环依赖** | L2/L3 ERROR | 合理 | 保持 ERROR，预留豁免机制 |
| **层级一致性** | L3 ERROR | 合理 | 保持 ERROR |

### 2.2 Analyzer 规则修复

**改动文件**：`backend/app/c4/analyzer.py`

- `_check_orphan_nodes`：增加 `ws` 和 `level` 参数，按层级分配严重级别，过滤 `properties.intentional_orphan = true` 的节点
- 新增 `_find_node_by_id` 辅助方法，用于查找节点 properties
- `_check_disconnected_subgraphs`：调用前增加 `view_level != "L1"` 判断
- `_check_naming_conventions`：严重级别从 WARNING 降为 INFO，提示文案更宽松

### 2.3 新增全层级分析能力

**改动文件**：
- `backend/app/schemas/c4.py`：新增 `C4LevelAnalysisDTO`、`C4AnalyzeResponseDTO`
- `backend/app/c4/renderer.py`：新增 `C4Renderer.analyze_all(project_id)` 方法，对 L1-L4 分别运行 `C4Analyzer`，不生成 Mermaid 代码
- `backend/app/api/v1/c4.py`：新增 `GET /c4/analyze` 端点，返回 `C4AnalyzeResponseDTO`
  - 调用 `renderer.analyze_all()` 获取四个层级的分析结果
  - 调用 `ConsistencyChecker` 获取 L2 层级的代码一致性报告
  - `overall_passed` = 所有层级通过且一致性通过

### 2.4 待完成项

| 序号 | 任务 | 状态 | 备注 |
|------|------|------|------|
| 1 | 后端新增 `/c4/analyze` 端点 | ✅ 已完成 | 已添加，调用 `renderer.analyze_all()` 和 `ConsistencyChecker` |
| 2 | 前端新建 `ArchGovernancePage` | ⏳ 待实现 | 路径 `src/pages/ArchGovernance/index.tsx`，含健康评分、问题表格、规则配置面板 |
| 3 | App.tsx 添加路由和侧边栏导航 | ⏳ 待实现 | 路由 `/arch-governance/:projectId`，导航放在"产物验证"组下 |

### 2.5 治理中心页面设计草案

```
┌─────────────────────────────────────────────────────────────┐
│  架构健康评分: 78  │  架构问题 3  │  一致性问题 5  │  [重新分析] │
├─────────────────────────────────────────────────────────────┤
│  [规则配置]  [问题列表]  [依赖矩阵]  [修复向导]                │
├─────────────────────────────────────────────────────────────┤
│  问题列表（表格）                                              │
│  ┌────────┬────────┬──────────┬──────────┬────────┬────────┐ │
│  │ 级别   │ 规则   │ 节点/文件│ 严重级别 │ 修复方向│ 操作   │ │
│  ├────────┼────────┼──────────┼──────────┼────────┼────────┤ │
│  │ L3     │ ORPHAN │ Config   │ INFO     │ 标记意图│ [豁免] │ │
│  │ L2     │ CYCLE  │ A→B→C→A  │ ERROR    │ 破环    │ [查看] │ │
│  │ L2     │ CON-C2M│ frontend │ WARNING  │ 改设计  │ [映射] │ │
│  └────────┴────────┴──────────┴──────────┴────────┴────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、业界方案参考

| 产品 | 核心模式 | 规则配置 | 修复方式 |
|------|---------|---------|---------|
| **SonarQube Architecture** (2025) | 预期架构 vs 实际代码 | Quality Profile + Quality Gate | 依赖图高亮 + Issue 列表 |
| **ArchUnit** | 规则即代码 | `@ArchIgnore` 豁免 | 单元测试失败阻断构建 |
| **Structure101** | 分层依赖矩阵 | 矩阵中标记允许/禁止 | 重构建议 + 影响分析 |
| **JetBrains Dep. Analysis** | 实时检测未使用依赖 | IDE 内联提示 | 一键移除/优化 import |

**关键洞察**：业界不把"发现所有异常"当目标，而是**"发现违背设计意图的异常"**。需要两个前提：
1. 设计意图可声明（`intentional_orphan`、`allow_cycle` 等豁免标记）
2. 分析结果可行动（不止报问题，还要告诉用户"点哪里、改哪里"）

---

## 四、修改文件清单

### 后端
- `backend/app/c4/renderer.py` — MermaidOutput 默认值修复、ConsistencyChecker 调用、analyze_all 方法
- `backend/app/c4/analyzer.py` — 规则分级、intentional_orphan 支持、_find_node_by_id 方法
- `backend/app/c4/code_scanner.py` — UnicodeDecodeError 容错
- `backend/app/schemas/c4.py` — C4LevelAnalysisDTO、C4AnalyzeResponseDTO
- `backend/app/api/v1/c4.py` — 新增 `/c4/analyze` 端点、导入新 DTO

### 前端
- `frontend/src/components/C4Renderer.tsx` — DiagnosticsPanel 可折叠组件、res.ok 错误处理

### 文档
- `docs/ai-output/session-c4-governance-fixes.md` — 本会话记录
