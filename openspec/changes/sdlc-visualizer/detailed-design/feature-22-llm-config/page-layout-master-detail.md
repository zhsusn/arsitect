# LLM 配置中心页面 Master-Detail 详细设计

> 依据 `docs/llmconfig.txt` 的分栏 Master-Detail 方案，结合当前 `config_nodes` 实际数据模型与 API，输出可落地的组件与状态设计。

## 一、设计目标

将当前「列表 + 行内展开表单」的 LLM 配置中心页面，重构为 **左侧 Master 列表 + 右侧 Detail 详情/编辑** 的分栏布局，以提升：

- 多节点快速扫描与对比效率
- 权限策略长规则列表的编辑体验
- 配置切换时的上下文连续性

## 二、实际数据与 API 基线

### 2.1 配置节点模型（ConfigNode）

```ts
interface ConfigNode {
  id: string
  node_type: 'llm_provider' | 'llm_permission'
  scope: 'managed' | 'global' | 'project' | 'user'
  scope_target: string | null
  key: string
  name: string
  description?: string
  is_enabled: boolean
  is_default: boolean
  priority: number
  config_json: Record<string, unknown>
  secret_json?: Record<string, unknown> | null
  created_by?: string | null
  updated_by?: string | null
  created_at: string
  updated_at: string
}
```

### 2.2 当前默认数据

- **默认 Provider 节点**：`node_type=llm_provider`, `scope=global`, `key=default`, `provider=kimi`, `kimi_cli_path=kimi`, `timeout=120`
- **默认权限策略**：`node_type=llm_permission`, `scope=global`, `key=default`, `default_mode=ask`，含 16 条规则（文件读取/写入、终端命令、网页抓取、外部 API）

### 2.3 已具备 API

- `GET /api/v1/config/nodes?node_type=...` 列表
- `POST /api/v1/config/nodes` 创建
- `PUT /api/v1/config/nodes/{id}` 更新
- `DELETE /api/v1/config/nodes/{id}` 删除
- `POST /api/v1/config/nodes/{id}/clone` 克隆
- `POST /api/v1/config/nodes/{id}/test` 测试 Provider
- `POST /api/v1/config/resolve` 解析生效配置
- `POST /api/v1/config/check-permission` 权限校验

## 三、页面布局架构

```
┌─────────────────────────────────────────────────────────────┐
│  LLM 配置中心                    [全局设置] [帮助] [用户头像]  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  [Provider 节点]  [权限策略]                                  │
├────────────────────┬────────────────────────────────────────┤
│  ◀ MasterList      │  ▶ DetailPanel                         │
│  宽度 320-400px     │  自适应剩余宽度                         │
│  固定 + 独立滚动    │  独立滚动                               │
│  可拖拽调整宽度     │                                         │
└────────────────────┴────────────────────────────────────────┘
```

- **左侧最小宽度 320px，最大 400px**，中间拖拽条 `cursor: col-resize`
- 用户偏好的宽度写入 `localStorage`（key：`llm-config-master-width`）
- 两侧各自 `overflow-y: auto`，互不干扰
- 移动端（`< 768px`）降级为「列表页 → 详情页」串行流程：点击列表项后全屏进入详情，返回按钮回到列表

## 四、组件拆分

### 4.1 目录结构

```
frontend/src/pages/LlmConfig/
├── index.tsx                      # 页面容器：Tab 切换、Master-Detail 布局
├── hooks/
│   ├── useConfigNodes.ts          # 拉取、刷新、本地缓存节点列表
│   └── useUnsavedGuard.ts         # 未保存变更保护（beforeunload + confirm）
├── components/
│   ├── MasterList.tsx             # 左侧列表：搜索、筛选、排序、卡片、新增
│   ├── ResizableSplit.tsx         # 可拖拽分栏容器
│   ├── DetailPanel.tsx            # 右侧容器：View / Edit 切换、操作栏
│   ├── ProviderDetail.tsx         # Provider 只读态 + 编辑态
│   ├── ProviderForm.tsx           # Provider 编辑表单（可独立复用）
│   ├── PermissionDetail.tsx       # 权限策略只读态 + 编辑态
│   ├── PermissionForm.tsx         # 权限策略编辑表单
│   └── RuleEditor.tsx             # 规则行内编辑器
└── types.ts                       # 页面级类型与常量
```

### 4.2 状态管理（Zustand 或页面级 useState）

采用页面级 `useState` + `useCallback` 即可，无需引入全局状态：

```ts
interface LlmConfigState {
  activeTab: 'provider' | 'permission'
  selectedId: string | null
  isEditing: boolean
  draft: ConfigNode | null          // 编辑中数据
  hasUnsavedChanges: boolean
  masterWidth: number
  search: string
  scopeFilter: Array<'global' | 'project' | 'user' | 'managed'>
  sortBy: 'priority' | 'updated_at' | 'name'
  sortOrder: 'asc' | 'desc'
}
```

### 4.3 数据流

```
用户进入页面
   │
   ▼
useConfigNodes(activeTab) → GET /config/nodes?node_type=...
   │
   ├── 成功：setNodes，默认选中第一项（若 selectedId 为空）
   └── 失败：顶部 Banner 错误

点击左侧卡片
   │
   ├── 有未保存变更 → ConfirmDialog → [保存并切换 / 放弃并切换 / 取消]
   └── 无变更 → setSelectedId(item.id)，isEditing=false

点击「编辑」
   └── setDraft(cloneDeep(node))，isEditing=true

编辑中
   ├── 表单 onChange → setDraft，setHasUnsavedChanges(true)
   ├── 每 5s 自动保存 draft → localStorage（key：llm-config-draft-{tab}-{id}）
   └── 点击「保存」→ API → 成功后清除 localStorage，刷新列表，切回只读态

点击「删除」
   └── ConfirmDialog → DELETE → 刷新列表，右侧显示 EmptyState

点击「新增」
   └── selectedId = 'new'，isEditing = true，draft = 空模板
       保存成功后替换为真实 ID
```

## 五、MasterList 详细设计

### 5.1 列表项卡片

每个条目为卡片式行，信息层级：

| 层级 | 内容 | 样式 |
|------|------|------|
| 主标题 | `node.name` | 14px，font-weight 500，单行截断 |
| 副标题 | `node.key` | 12px，灰色，等宽字体标签 |
| 元信息 | 类型图标 + 类型名 + 作用域 | 12px，灰色 |
| 状态角标 | 默认节点显示 ★ | 黄色，tooltip「默认 Provider」|

选中态：

- 左侧边框 `2px solid #1890ff`
- 背景色 `#f0f5ff`
- 未选中 hover 背景 `#f5f5f5`

### 5.2 顶部操作区

- **搜索框**：输入即过滤，debounce 200ms，匹配 `name` / `key` / `description`
- **作用域筛选**：下拉多选 `[全部 / 全局 / 项目 / 用户 / 托管]`
- **排序**：默认 `priority desc` + `updated_at desc`；悬浮表头可切换 `priority | 更新时间 | 名称`

### 5.3 空状态

列表为空时显示 404 风格插图 +「+ 新增」按钮；右侧同步显示引导文案。

## 六、DetailPanel 双态设计

### 6.1 Provider 节点

#### 只读态字段

| 标签 | 值 |
|------|-----|
| 名称 | `name` |
| 标识 key | `key` |
| 作用域 | `scope` + `scope_target`（空值显示 `-`）|
| 目标 ID | `scope_target || '-'` |
| 优先级 | `priority` |
| Provider 类型 | `config_json.provider` |
| 描述 | `description || '-'` |
| 默认节点 | `is_default ? '★ 默认' : '-'` |

类型相关字段：

- `kimi-cli`：`kimi_cli_path`、`timeout`
- `kimi-api` / `openai`：`api_base`、`model`
- 密文：`api_key` 显示为 `••••••`

#### 操作按钮

| 按钮 | 行为 | 权限/约束 |
|------|------|-----------|
| 编辑 | 进入编辑态 | 始终可用 |
| 删除 | ConfirmDialog → 删除 | 默认节点禁用，tooltip「请先设置其他默认节点」 |
| 复制 | clone API → 列表刷新 | 始终可用 |
| 测试 | test API → 显示连通状态 | Provider 节点可用 |
| 设为默认 | PUT `is_default=true` | 仅非默认节点显示 |

#### 编辑态表单

- 必填项标记红色 `*`
- `key`、`scope`、`provider` 创建后不可改（disabled + tooltip）
- 名称失焦校验重名（本地对比 nodes 数组）
- 自动保存草稿到 localStorage（5s 间隔）
- 底部 `[取消] [保存]`

### 6.2 权限策略

#### 只读态字段

| 标签 | 值 |
|------|-----|
| 名称 | `name` |
| 作用域 | `scope` |
| 默认模式 | `allow / 询问 / 拒绝` 标签 |
| 规则数 | `rules.length` |
| 规则摘要 | 前 5 条规则，超出显示「... 等 N 条规则」 |

#### 操作按钮

| 按钮 | 行为 |
|------|------|
| 编辑 | 进入编辑态 |
| 删除 | ConfirmDialog → 删除 |
| 展开全部 | 只读态下查看完整规则 |

#### 编辑态规则编辑器（RuleEditor）

- 表格列：`操作类型`、`权限`、`匹配模式`、`描述`、`删除`
- 每行内联下拉框/输入框
- 左侧 ⋮⋮ 拖拽柄（本版本可先实现按钮上下移动，拖拽后续增强）
- 删除行：淡出动画，顶部 Toast「已删除，撤销」（本版本可用 confirm 简化）
- 新增行：点击「+ 添加规则」，插入顶部，自动聚焦操作类型
- 规则区域 `max-h-96 overflow-y-auto`

## 七、未保存变更保护

| 触发场景 | 系统行为 |
|----------|----------|
| 编辑中点击左侧其他项 | ConfirmDialog：保存并切换 / 放弃并切换 / 取消 |
| 编辑中切换 Tab | 同上 |
| 关闭浏览器标签页 | `beforeunload` 拦截 |
| 5 分钟无操作 | 自动保存 draft 到 localStorage，下次恢复提示 |

实现要点：

- `useUnsavedGuard(isEditing && hasUnsavedChanges)` 监听 `beforeunload`
- 切换前检查 `hasUnsavedChanges`，弹出 `window.confirm` 或自定义 Dialog

## 八、键盘与快捷操作

| 快捷键 | 作用域 | 行为 |
|--------|--------|------|
| ↑ / ↓ | 左侧列表聚焦时 | 上下切换选中项 |
| Enter | 左侧列表聚焦时 | 进入编辑态 |
| Esc | 右侧编辑态 | 触发取消逻辑 |
| Ctrl/Cmd + S | 右侧编辑态 | 保存表单 |
| Ctrl/Cmd + N | 全局 | 新增节点 |

## 九、性能与边界

- 列表超过 100 条：后端分页或前端虚拟滚动（当前默认数据少，先保留简单列表）
- 规则超过 50 条：规则区域内部滚动
- API 缓存：列表数据在 Tab 切换时不重复请求，保存后仅刷新当前列表
- 错误处理：API 失败时顶部 Banner 显示，保留编辑态不丢失

## 十、交付清单

- [x] `page-layout-master-detail.md` 设计文档
- [ ] `LlmConfig/index.tsx` 页面容器
- [ ] `MasterList.tsx` / `ResizableSplit.tsx` / `DetailPanel.tsx`
- [ ] `ProviderDetail.tsx` / `ProviderForm.tsx`
- [ ] `PermissionDetail.tsx` / `PermissionForm.tsx` / `RuleEditor.tsx`
- [ ] `useConfigNodes.ts` / `useUnsavedGuard.ts`
- [ ] Playwright 端到端测试覆盖 Master-Detail 基本流程
