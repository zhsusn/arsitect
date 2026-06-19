# 任务拆解与实施计划

> **基于**: `docs/page-prototype-design-v3.md` 原型设计文档
> **后端状态**: API 层已基本完善（40+ 路由，对应 services 已就位）
> **前端状态**: 页面骨架存在，20+ 页面中大部分是空白占位（仅显示 "Hello from X"），核心组件（StageNavBar, TaskTree, ArtifactRenderer, ExecutionPanel, ReviewPanel, SizeEstimateCard, UserStoryTable, AcceptanceCriteriaTable, C4Renderer, WireframeViewer, SketchViewer 等）已存在但需页面层整合
> **目标**: 按"产出-验证-调整"闭环，逐个页面修复/增强，验证通过后再进行下一个

---

## 一、后端 API 能力总览（已有，无需重复开发）

| 模块 | 路由文件 | 已有能力 | 前端需要调用 |
|------|---------|---------|------------|
| 需求设计室 | `requirement_studio.py` | status, tasks, execute, review, artifacts, edit, baseline, stale-analysis, change-request | 全部需要 |
| 用户故事 | `user_stories.py` | CRUD, import from requirements | 全部需要 |
| 草图 | `sketch.py` | CRUD, generate, generate-from-requirements, pages, validate | 全部需要 |
| 线框图 | `wireframe.py` | CRUD, generate-from-c4, pages, nav-links, validate | 全部需要 |
| C4 架构 | `c4.py` | DSL, render, analyze, sync, versions, orphans | 全部需要 |
| 接口绑定 | `binding.py` | scan, writeback, sync, coverage | 全部需要 |
| OpenUI | `open_ui.py` | health, generate, pages, preview | 全部需要 |
| Gate | `gate.py` | list, decision, history, self-check | 全部需要 |
| 项目 | `projects.py` | CRUD, size-estimate, risk, stage-progress | 全部需要 |
| Skill 执行 | `skill_executions.py` | trigger, logs, status | 全部需要 |
| 执行计划 | `execution_plans.py` | plan, tasks, issues | 新建页面需要 |
| 执行状态 | `stage_execution_status.py` | real-time status | 全部需要 |
| 产物 | `artifacts.py` | content, versions, diff | 全部需要 |
| 审查批注 | `annotations.py` | CRUD, inline, global | 全部需要 |

**结论**: 后端无需新增路由，前端只需正确调用已有 API + 页面层整合。

---

## 二、任务拆解（按依赖关系排序）

### 核心原则
- **先骨架后血肉**: 先修复核心工作区页面的三栏布局 + 数据流，再增强细节交互
- **先输入后输出**: 按数据流顺序：脑暴 → 需求 → 草图 → 设计 → 线框 → 原型 → 接口 → 定稿
- **验证闭环**: 每个页面完成后，必须能通过 UI 完成"执行 Skill → 生成产物 → 审查批注 → 重新生成"的完整流程

---

### Phase 0: 公共层增强（前置，所有页面依赖）

| 任务 | 目标文件 | 调整内容 | 工时估 | 前置 |
|------|---------|---------|--------|------|
| 0.1 | `requirementStudioStore.ts` | 扩展 store：增加 `currentView`, `selectedTab`, `annotations`, `executionProgress`, `sizeEstimate` 等字段 | 0.5h | 无 |
| 0.2 | `executionStore.ts` | 确认 SSE 日志连接、执行状态机 (idle/prep/exec/post/success/failed) | 0.5h | 无 |
| 0.3 | `services/api.ts` | 确认/补齐 `requirementStudio`, `userStories`, `sketches`, `wireframes`, `c4`, `binding`, `openUi` 的 API 调用封装 | 1h | 无 |
| 0.4 | `components/TaskTree.tsx` | 增加 `inherit` 状态样式（灰色、只读），增加节点 hover tooltip | 0.5h | 无 |
| 0.5 | `components/StageNavBar.tsx` | 增加阶段锁定/解锁状态与 Gate 关联，点击已解锁阶段路由跳转 | 0.5h | 无 |
| 0.6 | `components/StatusBar.tsx` | 增加 Gate 状态指示器、产物版本指示器 | 0.5h | 无 |
| 0.7 | 路由守卫 | 在 App.tsx 或页面入口处增加：locked 阶段禁止访问、Draft 态仅允许分析型 Skill | 0.5h | 无 |

**Phase 0 小计**: ~4h，建议一次性完成

---

### Phase 1: 需求方案页面（RequirementPlan）—— 核心骨架

**对应文件**: `frontend/src/pages/RequirementStudio/RequirementPlan/index.tsx`
**原型文档**: §2.2
**当前状态**: 空白占位
**后端依赖**: `requirement_studio.py` + `user_stories.py`

#### 1.1 页面骨架重构
- 三栏布局：左任务树 / 中产物工作区 / 右执行+审查面板
- 顶部视图切换：概要视图 / 详细视图 / 版本历史
- 引入已有组件：`StageNavBar`, `TaskTree`, `ArtifactRenderer`, `ExecutionPanel`, `ReviewPanel`, `StatusBar`

#### 1.2 概要视图 — 产物 Tab 切换
- **用户故事 Tab**: 调用 `UserStoryTable` 组件，对接 `GET /projects/{projectId}/user-stories` + `POST /projects/{projectId}/user-stories` + `POST /projects/{projectId}/user-stories/import`
  - 表格：ID, 角色, 描述, 优先级, 状态
  - 操作：[+ 新建] → 弹窗表单（标题、描述、页面描述、优先级、状态、关联脑暴）
  - [导入] → 从脑暴纪要自动提取
  - 点击行 → 展开详情抽屉（验收标准、备注）
- **PRD Tab**: Markdown 渲染 + 编辑器切换，对接 `GET /api/v1/requirement-studio/{projectId}/artifacts/{artifactId}` + `POST /edit`
  - [编辑] → 切换为 Markdown 编辑器
  - [保存] → 提交编辑，创建新版本
  - 版本历史 → 底部时间线
- **草图 Tab**: 调用 `SketchViewer` 或 iframe 渲染 SVG，对接 `GET /projects/{projectId}/sketches/{sketchId}/pages`
- **验收标准 Tab**: 调用 `AcceptanceCriteriaTable` 组件，对接验收标准数据
  - [校验] → 调用后端校验接口或前端规则检查
  - 校验结果弹窗：通过/需修改列表

#### 1.3 右侧面板 — 执行与审查
- **执行面板**: 调用 `ExecutionPanel` 组件，对接 `POST /api/v1/requirement-studio/{projectId}/stage/{stageId}/execute` + SSE 日志
- **审查面板**: 调用 `ReviewPanel` 组件，对接 `POST /api/v1/requirement-studio/{projectId}/stage/{stageId}/review`

#### 1.4 底部规模初估卡片
- 对接 `GET /api/v1/projects/{projectId}/size-estimate`
- 点击卡片 → 展开 breakdown（弹窗）

#### 1.5 验证标准
- [ ] 三栏布局正常渲染，无样式错乱
- [ ] 用户故事列表能从后端加载并展示
- [ ] 点击 [执行] 能触发 Skill 执行，SSE 日志实时更新
- [ ] 产物编辑后能保存，版本号递增
- [ ] 提交审查后阶段状态更新（review_pending → passed）
- [ ] Gate 1 通过后顶部导航解锁"详细需求"视图

**Phase 1 小计**: ~6-8h

---

### Phase 2: 脑暴室页面（Brainstorm）—— 补齐功能

**对应文件**: `frontend/src/pages/RequirementStudio/Brainstorm/index.tsx`
**原型文档**: §2.1
**当前状态**: 空白占位
**后端依赖**: `requirement_studio.py` (execute/review/artifacts) + `projects.py` (size-estimate)

#### 2.1 页面骨架
- 顶部 Tab: [脑暴纪要] [竞品分析] [规模初估]
- 中间产物区：Markdown 渲染/编辑（脑暴纪要和竞品分析）
- 右侧：执行控制台 + 审查批注面板
- 规模初估 Tab 时中间区显示 `SizeEstimateCard` 组件

#### 2.2 核心功能
- 脑暴纪要：Markdown 渲染，[编辑] [保存] [版本历史]
- 竞品分析：Markdown 渲染，可执行 Skill 重新生成
- 规模初估：展示卡片数据，点击展开 breakdown 弹窗
  - breakdown 弹窗：模块/工时/风险列表
  - 调整参数弹窗：模块数、接口数、页面数、实体数、复杂度

#### 2.3 验证标准
- [ ] 三 Tab 切换正常
- [ ] 脑暴纪要能加载/编辑/保存
- [ ] 执行 brainstorming Skill 后 SSE 日志更新
- [ ] 规模初估卡片数据正确展示
- [ ] breakdown 弹窗能展开

**Phase 2 小计**: ~4-6h

---

### Phase 3: 需求草图页面（SketchGallery）—— 增强功能

**对应文件**: `frontend/src/pages/SketchGallery/index.tsx`
**原型文档**: §2.3
**当前状态**: 有骨架代码，功能部分实现
**后端依赖**: `sketch.py` + `user_stories.py`

#### 3.1 视图切换增强
当前已有 `[用户故事] [生成草图] [草图画布] [审查]` 四个视图，需增强：
- **用户故事视图**: 增加 [📥 从需求导入] 按钮，对接 `POST /projects/{projectId}/sketches/generate-from-requirements`
- **生成草图视图**: 用户故事选择列表增加 page_desc 存在性检测（无 page_desc 的置灰不可选）
- **草图画布视图**: 左侧页面树增加跳转关系信息，右侧预览增加字段/按钮/跳转数量统计
- **审查视图**: 增加批量批准/驳回，页面状态 (APPROVED/REJECTED/DRAFT)

#### 3.2 路径验证报告
- 新增：覆盖度检测、缺失跳转、孤立页面、未知页面统计
- 对接 `GET /projects/{projectId}/sketches/{sketchId}/validate`

#### 3.3 验证标准
- [ ] 四个视图切换正常
- [ ] 从用户故事生成草图流程完整
- [ ] 路径验证报告能展示
- [ ] 审查状态能保存

**Phase 3 小计**: ~4-6h

---

### Phase 4: 设计方案页面（DesignPlan）—— 修复空页面

**对应文件**: `frontend/src/pages/SolutionStudio/DesignPlan/index.tsx`
**原型文档**: §3.1
**当前状态**: 空白占位
**后端依赖**: `requirement_studio.py` + `c4.py` + `contracts.py`

#### 4.1 页面骨架
- 顶部 Tab: [概要设计] [详细设计] [DB 设计] [接口契约] [版本历史]
- 三栏布局：左任务树 / 中产物工作区 / 右执行+审查面板
- 概要设计任务：HLD 生成、C4 Context、C4 Container、技术栈选型
- 详细设计任务：DD 生成、C4 Component、API 详细规格、OpenUI 规格

#### 4.2 各 Tab 内容
- **概要设计**: Markdown 渲染 HLD 文档，嵌入 SVG 架构图（C4 L1/L2），技术栈表格
- **详细设计**: Markdown 渲染 DD 文档，API 规格（Swagger UI），OpenUI 规格（iframe）
- **DB 设计**: ER 图 SVG 渲染 + DDL YAML 编辑器，[校验] [导出 SQL]
- **接口契约**: OpenAPI 3.0 YAML 编辑器 + Swagger UI 预览 + [校验一致性]
- **版本历史**: 产物版本列表 + diff 对比

#### 4.3 接口一致性差异弹窗
- 对接 `binding.py` 扫描结果
- 展示 OpenAPI vs OpenUI 的字段差异
- 双向同步按钮：[同步到 OpenUI] [同步到 OpenAPI] [一键同步]

#### 4.4 验证标准
- [ ] 五 Tab 切换正常
- [ ] HLD/DD Markdown 能加载/编辑/保存
- [ ] C4 SVG 能嵌入渲染
- [ ] DB 设计 ER 图 + DDL 编辑器正常
- [ ] 接口契约 YAML 编辑器 + Swagger UI 正常
- [ ] 一致性校验能展示差异弹窗

**Phase 4 小计**: ~6-8h

---

### Phase 5: 系统结构页面（C4Navigator）—— 功能增强

**对应文件**: `frontend/src/pages/C4Navigator/index.tsx`
**原型文档**: §3.2
**当前状态**: 有骨架代码，左侧 DSL 编辑器 + 右侧渲染区域已存在，但功能不完整
**后端依赖**: `c4.py`

#### 5.1 增强内容
- **节点详情面板**: 点击 SVG 中节点，底部展开节点详情（名称、技术、描述、关联代码、在 VS Code 中打开）
- **孤立节点管理抽屉**: 右侧滑出抽屉，展示有效孤立节点和已标记豁免节点，操作：[标记豁免] [添加到 DSL] [取消豁免]
- **版本历史**: 对接 `GET /api/v1/c4/{projectId}/versions`，支持版本回滚
- **关系同步**: [重新同步关系] 按钮，对接 `POST /api/v1/c4/{projectId}/sync`
- **错误提示横幅**: DSL 语法错误时顶部显示错误信息

#### 5.2 验证标准
- [ ] DSL 编辑实时渲染 SVG
- [ ] 点击节点底部展开详情
- [ ] 孤立节点抽屉能打开并操作
- [ ] 版本历史能查看并回滚
- [ ] 关系同步后 SVG 更新

**Phase 5 小计**: ~4-6h

---

### Phase 6: 页面布局页面（WireframeCanvas）—— 功能增强

**对应文件**: `frontend/src/pages/WireframeCanvas/index.tsx`
**原型文档**: §3.3
**当前状态**: 有骨架代码，页面列表 + 预览已存在
**后端依赖**: `wireframe.py`

#### 6.1 增强内容
- **跳转关系图**: 新增视图，全站页面导航关系图（可切换 Tab 或按钮）
- **页面树形导航**: 左侧页面列表增加层级结构（首页 > 子页面）
- **置信度展示**: 每个页面展示置信度百分比
- **从 C4 生成**: [从 C4 生成线框图] 按钮，对接 `POST /projects/{projectId}/wireframes/generate`
- **页面元数据展示**: 右侧预览区增加字段数、按钮数、跳转数统计

#### 6.2 验证标准
- [ ] 页面列表树形展示正常
- [ ] 从 C4 生成能触发后端接口
- [ ] 跳转关系图能展示
- [ ] 置信度数据展示正确

**Phase 6 小计**: ~3-5h

---

### Phase 7: 交互原型页面（OpenUIPreview）—— 功能增强

**对应文件**: `frontend/src/pages/OpenUIPreview/index.tsx`
**原型文档**: §3.4
**当前状态**: 有骨架代码，页面列表 + iframe 预览已存在
**后端依赖**: `open_ui.py`

#### 7.1 增强内容
- **服务健康检测**: 页面加载时检测 OpenUI 服务状态，显示 ● 可用 / ⚠ 降级横幅
- **Viewport 切换**: 桌面/平板/手机三按钮切换，调整 iframe 尺寸
- **生成原型**: [生成原型] 按钮，对接 `POST /api/v1/open-ui/{projectId}/generate`
- **降级处理**: 服务不可用时自动切换为 Wireframe 降级预览
- **服务启动指南**: 服务不可用时显示 [启动指南] 按钮，弹出配置说明

#### 7.2 验证标准
- [ ] 服务状态检测正常
- [ ] 三 viewport 切换正常
- [ ] 生成原型能触发
- [ ] 降级时切换为 Wireframe 预览

**Phase 7 小计**: ~3-4h

---

### Phase 8: 接口对照页面（BindingPanel）—— 功能增强

**对应文件**: `frontend/src/pages/BindingPanel/index.tsx`
**原型文档**: §3.5
**当前状态**: 有骨架代码，扫描历史 + 统计卡片已存在，但 Tab 内容不完整
**后端依赖**: `binding.py`

#### 8.1 增强内容
- **Tab 内容填充**: Gap/Redundant/Matched/Diff 四个 Tab 内容对接后端数据
- **缺失项操作**: [回写] [批准] [驳回] 按钮，对接 `POST /api/v1/binding/writeback`
- **差异同步弹窗**: 展示字段差异，双向同步按钮
- **批量回写**: [回写缺失接口] 按钮，批量写入 OpenAPI YAML
- **扫描历史选择**: 历史列表点击切换显示不同扫描结果

#### 8.2 验证标准
- [ ] 四类 Tab 内容能加载
- [ ] 回写操作能触发后端
- [ ] 差异同步弹窗正常
- [ ] 扫描历史切换正常

**Phase 8 小计**: ~3-5h

---

### Phase 9: 设计定稿页面（DesignFinalization）—— 修复空页面

**对应文件**: `frontend/src/pages/SolutionStudio/DesignFinalization/index.tsx`
**原型文档**: §3.6
**当前状态**: 空白占位
**后端依赖**: `c4.py` (analyze) + `gate.py` + `requirement_studio.py` (baseline)

#### 9.1 页面骨架
- 步骤进度条：[选择产物] → [锁定基线] → [提交审批] → [审批通过] → [进入开发]
- 三栏：左待基线产物 / 中基线状态+架构分析 / 右审批面板

#### 9.2 核心功能
- **待基线产物清单**: 列出全部设计产物，勾选锁定，[一键锁定基线]
- **基线状态**: 展示架构健康评分（从 C4 分析获取）
- **架构分析**: 扫描 C4 模型与代码一致性，问题列表（BLOCKER/ERROR/WARNING）
- **问题修复**: 选择问题后 [修复架构问题] → 打开 FixConfirmModal + ChatSidePanel
- **审批面板**: Gate 3 审批，[通过] [驳回] [重试]，审批历史

#### 9.3 验证标准
- [ ] 产物清单能加载并勾选
- [ ] 基线锁定后状态更新
- [ ] 架构分析能扫描并展示问题
- [ ] 审批操作能触发后端
- [ ] Gate 3 通过后解锁开发执行阶段

**Phase 9 小计**: ~5-7h

---

### Phase 10: 需求确认页面（GateCenter）—— 阶段化增强

**对应文件**: `frontend/src/pages/GateCenter/index.tsx`（需求设计室和方案设计室均复用）
**原型文档**: §2.4
**当前状态**: 有骨架代码，功能部分实现
**后端依赖**: `gate.py`

#### 10.1 增强内容
- **阶段产物清单**: 根据当前阶段（Gate 1 / 2.5 / 2 / 3）动态展示待审产物
- **自检报告**: 对接 `GET /api/v1/gates/{gateId}/self-check`，展示产物完整性、格式合规性、交叉引用
- **驳回分类弹窗**: 驳回时选择分类（需求不完整/边界不清/其他），详细说明输入框
- **审批历史**: 展示阶段审批日志

#### 10.2 验证标准
- [ ] 阶段产物清单正确展示
- [ ] 自检报告能加载
- [ ] 驳回分类弹窗正常
- [ ] 审批历史能查看

**Phase 10 小计**: ~3-4h

---

### Phase 11: 开发执行室页面（TaskOrchestration / Testing / AiCli）—— 新建页面

**对应文件**:
- `frontend/src/pages/ExecutionStudio/TaskOrchestration/index.tsx`（不存在，需新建）
- `frontend/src/pages/ExecutionStudio/Testing/index.tsx`（不存在，需新建）
- `frontend/src/pages/ExecutionStudio/AiCli/index.tsx`（不存在，需新建）
**原型文档**: 原型设计文档 §5 开发执行章节（简要）
**后端依赖**: `execution_plans.py` + `execution.py` + `cli.py`

#### 11.1 任务编排页面（TaskOrchestration）
- 三栏：左任务树（按执行计划分组）/ 中任务详情（代码编辑器 + 测试面板）/ 右执行面板
- 任务状态：not_started → in_progress → completed → failed
- 代码编辑器：Monaco 或 CodeMirror 简化版，支持代码高亮
- 测试面板：单元测试编写与执行结果展示

#### 11.2 测试调试页面（Testing）
- 测试列表：单元测试、集成测试、端到端测试
- 测试执行结果：通过/失败/覆盖率
- 失败测试详情：错误日志、堆栈、修复建议

#### 11.3 AI CLI 页面（AiCli）
- 终端模拟器：输入命令、查看输出
- 历史命令：命令历史列表
- 快捷命令：常用命令快捷按钮

#### 11.4 验证标准
- [ ] 三个页面骨架正常
- [ ] 任务编排能加载执行计划
- [ ] 测试页面能展示测试列表和结果
- [ ] AI CLI 能输入命令并展示输出

**Phase 11 小计**: ~8-10h

---

## 三、实施顺序建议

### 推荐顺序（按依赖与价值）

```
Phase 0: 公共层增强（4h）          ← 必须先完成，所有页面依赖
       ↓
Phase 1: 需求方案（6-8h）          ← 核心骨架，数据流中心
       ↓
Phase 2: 脑暴室（4-6h）             ← 需求方案的前置输入
       ↓
Phase 4: 设计方案（6-8h）          ← 方案设计室核心骨架
       ↓
Phase 5: C4Navigator（4-6h）        ← 设计方案的输入
       ↓
Phase 6: WireframeCanvas（3-5h）    ← 依赖 C4
       ↓
Phase 7: OpenUIPreview（3-4h）      ← 依赖详细设计
       ↓
Phase 8: BindingPanel（3-5h）       ← 依赖 Wireframe + OpenUI + C4
       ↓
Phase 9: 设计定稿（5-7h）           ← 设计方案收尾
       ↓
Phase 3: 需求草图（4-6h）           ← 需求方案增强（独立，可提前）
       ↓
Phase 10: 需求确认（3-4h）          ← 门控增强
       ↓
Phase 11: 开发执行室（8-10h）       ← 最后
```

### 最小可用路径（MVP）
如果希望最快看到完整闭环，按此顺序：
1. **Phase 0**（公共层）
2. **Phase 1**（需求方案）+ **Phase 2**（脑暴室）→ 需求设计室闭环
3. **Phase 4**（设计方案）+ **Phase 5**（C4Navigator）→ 方案设计室骨架
4. **Phase 9**（设计定稿）→ 设计阶段闭环
5. 其余页面逐个增强

---

## 四、验证检查清单（每页完成后）

每个 Phase 完成后，必须验证：

- [ ] **页面加载**: 页面能正常加载，无白屏/报错
- [ ] **数据加载**: 能从后端加载数据并正确展示
- [ ] **交互响应**: 按钮点击、Tab 切换、表单提交有响应
- [ ] **执行闭环**: 能触发 Skill 执行（如有）→ 产物生成 → 审查提交
- [ ] **状态同步**: 操作后页面状态与后端一致（刷新后数据不变）
- [ ] **错误处理**: 网络错误/后端错误有友好提示（非白屏）
- [ ] **响应式**: 1280px+ 屏幕布局正常，无元素溢出

---

## 五、待决策事项

1. **从哪个 Phase 开始？** 建议 Phase 0 → Phase 1，或用户指定优先页面
2. **Markdown 编辑器选型？** 现有代码使用 `react-markdown` 渲染，编辑模式用 textarea 即可，还是引入 `react-md-editor`？
3. **代码编辑器（开发执行室）？** Monaco Editor 较重，是否用 CodeMirror 轻量版或 textarea？
4. **是否先做最小可用路径（MVP）？** 还是按完整顺序逐个做？

请确认实施顺序，我将立即开始第一个 Phase 的开发。
