# Frontend Design Guide

本文件供 `detailed-design` Skill 在生成 module-design.md 第 6 章（页面设计与用户旅程）时按需加载。

---

## 1. 页面布局模式库（Page Layout Patterns）

每种 `layout_type` 必须遵循默认信息架构（IA）和关键约束：

| 布局类型 | 默认结构（从上到下） | 关键约束 |
|---|---|---|
| **LIST** | 面包屑 → 页面标题+操作栏 → 筛选区 → 数据表格/卡片列表 → 分页/加载更多 → 批量操作栏 | 空状态必须有新建引导；分页与无限滚动二选一；≥10 列时定义默认展示列 |
| **FORM** | 页头（标题+返回+操作） → 分步指示器（Wizard 时） → 字段分组（≤7±2 个/组） → 操作栏 | 必填项视觉标识；提交前危险操作需二次确认；自动保存草稿策略 |
| **DETAIL** | 页头（标题+返回+操作） → 摘要卡（P0 信息） → 详情标签页/折叠面板 → 关联列表/操作 | 编辑入口明确且防误触；关联列表 ≤5 条时可省略分页 |
| **DASHBOARD** | 全局筛选/时间范围 → 指标卡（≤6 个） → 图表区 → 待办/通知 → 快捷入口 | 图表必须有 time-range；支持自定义布局；指标卡异常值标红 |
| **MODAL** | 标题栏（含关闭） → 内容区（FORM/LIST/DETAIL 的压缩版） → 底部操作栏 | 层级 ≤2（禁止弹窗套弹窗）；关闭前 dirty-check；高度适配 viewport 80% |
| **DRAWER** | 标题栏 → 内容区 → 底部操作栏（可选） | 宽度规范：md(378px)/lg(512px)/xl(640px)；复杂表单优先用 drawer 而非 modal |
| **SEARCH** | 搜索框（支持高级筛选触发） → 筛选标签 → 结果列表 → 相关性排序/分页 | 搜索建议（autocomplete）策略；无结果恢复路径（放宽条件/新建引导） |
| **WIZARD** | 步骤条（可点击已访问步骤） → 当前步骤内容 → 导航按钮（上一步/下一步/完成/保存草稿） | 步骤 ≤5 步；最后一步前展示确认摘要；进度持久化（防刷新丢失） |
| **CARD** | 媒体区/图标 → 标题 → 元信息 → 操作区 | 统一圆角/阴影 token；hover 态反馈；文本溢出处理（ellipsis 或 clamp） |

---

## 2. 设计反模式清单（Anti-Patterns）

借鉴 Impeccable / better-web-ui 设计红线，禁止以下做法：

| 等级 | 反模式 | 正确做法 |
|---|---|---|
| 🔴 | 默认使用 Inter 字体而不说明设计理由 | 根据设计系统或品牌规范指定字体栈 |
| 🔴 | 无意义紫色渐变（Purple Gradient Anti-Pattern） | 色彩必须有语义（主色/成功/警告/错误/信息） |
| 🔴 | 卡片嵌套卡片（Nested Cards） | 使用平面层级 + 分割线/留白区分信息层级 |
| 🔴 | 纯黑（#000000）作为文本或背景色 | 文本用 `gray-900`（#111827）或设计系统等价色；背景用 `gray-50` 或白色 |
| 🔴 | 页面无 `empty_state` 和 `error_state` 定义 | 每个页面/列表必须定义三种状态 |
| 🟡 | 按钮操作无反馈态（loading/disabled） | 异步操作按钮必须有 loading 态；提交后 disable 防重复 |
| 🟡 | 表单无前端校验策略 | 定义即时校验（onBlur）与提交校验（onSubmit）策略 |
| 🟡 | 无意义的装饰性动效 | 动效必须服务用户目标（引导注意力、提供状态反馈、减少认知负荷） |
| 🟡 | 移动端未定义内容优先级 | 响应式必须有内容裁减策略，而非简单缩放 |

---

## 3. 可访问性（a11y）检查表

每个页面在 PageSpec 中必须至少明确以下 a11y 项：

- [ ] **焦点管理**：页面加载后首个焦点位置；Modal/Drawer 打开时焦点陷阱（focus trap）；关闭后焦点回退
- [ ] **键盘导航**：Tab 顺序符合视觉顺序；所有交互元素可通过键盘操作；无键盘陷阱
- [ ] **ARIA 角色**： landmark 角色（main、nav、aside、search）；动态内容 `aria-live` 区域
- [ ] **对比度**：正文文字与背景对比度 ≥ 4.5:1；大文字/图标 ≥ 3:1
- [ ] **语义化 HTML**：优先使用原生语义标签（`<button>`、`<nav>`、`<main>`），而非纯 `<div>` + ARIA
- [ ] **运动敏感**：尊重 `prefers-reduced-motion`，核心功能在无动效下必须可用
- [ ] **表单可访问性**：`<label>` 与输入框显式关联（`for`+`id`）；错误提示与字段关联（`aria-describedby`）

---

## 4. 响应式设计策略

### 断点规范（默认参考 Tailwind）

| 断点 | 宽度 | 内容策略 |
|---|---|---|
| `sm` | ≥640px | 手机横屏，单列布局，部分操作收进更多菜单 |
| `md` | ≥768px | 平板，侧边栏可展开，表格支持横向滚动 |
| `lg` | ≥1024px | 小桌面，双栏/三栏布局启用 |
| `xl` | ≥1280px | 标准桌面，完整布局展示 |
| `2xl` | ≥1536px | 大屏，增加留白或展示辅助信息 |

### 内容优先策略
- **Mobile-first**：从小屏幕开始设计，逐步增强（推荐 B/C 端产品）
- **Desktop-first**：从大屏幕开始，逐步裁剪（推荐数据密集型后台）
- 必须在 `openspec/config.yaml` 中明确声明采用哪种策略

---

## 5. 动效与微交互策略

| 动效类型 | 使用场景 | 技术建议 | 性能约束 |
|---|---|---|---|
| **页面转场** | 路由切换 | 淡入淡出（150ms）或滑动（200ms） | 使用 CSS transform，避免 layout thrashing |
| **列表入场** | 数据加载完成 | Stagger 延迟（每项 30-50ms） | 最多 stagger 20 项，超出直接渲染 |
| **骨架屏** | 初始加载 | 脉冲动画（shimmer），1.5s 周期 | 使用 CSS background-position 动画，GPU 加速 |
| **按钮反馈** | hover / active / loading | scale(1.02) 或 opacity 变化，150ms ease-out | 仅 transform/opacity |
| **错误震动** | 表单校验失败 | 水平微位移（±4px，3 次，200ms） | CSS keyframes |
| **数字滚动** | 仪表盘指标更新 | CountUp 动画，300ms | `requestAnimationFrame`，避免 setState 风暴 |

> **Reduced Motion 回退**：所有动效必须提供静态替代方案。

---

## 6. 设计 Tokens 使用规范

禁止在 PageSpec 中写死 magic number。所有视觉值必须引用 token：

| Token 类别 | 示例 | 用途 |
|---|---|---|
| `color-*` | `color-primary-500`, `color-text-secondary` | 文本、背景、边框、状态色 |
| `space-*` | `space-4` (1rem/16px), `space-8` (2rem/32px) | 间距、内边距、外边距、栅格间隙 |
| `radius-*` | `radius-md` (0.375rem), `radius-lg` (0.5rem) | 圆角 |
| `shadow-*` | `shadow-sm`, `shadow-md`, `shadow-lg` | 阴影深度 |
| `font-size-*` | `font-size-sm`, `font-size-base`, `font-size-lg` | 字体比例尺 |
| `z-index-*` | `z-index-modal`, `z-index-dropdown`, `z-index-toast` | 层级管理 |

若项目无设计系统，使用框架默认值（如 Tailwind 默认 token），并在 PageSpec 中标注 `[DEFAULT]`。

---

## 7. 空状态 / 加载状态 / 错误状态策略

### 空状态（Empty State）

必须包含三要素：
1. **解释文案**：告诉用户为什么空（"暂无项目，点击上方按钮创建"）
2. **引导操作**：提供明确的下一步动作（新建、导入、调整筛选条件）
3. **视觉元素**：插图或图标，风格与整体设计系统一致

### 加载状态（Loading State）

| 场景 | 推荐策略 | 禁用策略 |
|---|---|---|
| 整页初始加载 | 骨架屏（Skeleton） | 全屏白屏或转圈 |
| 局部数据更新 | 内联 spinner + 禁用操作 | 整页刷新 |
| 表单提交 | 按钮 loading 态 + 字段禁用 | 无反馈等待 |
| 无限滚动/分页 | 底部 skeleton 条或加载指示器 | 跳转到顶部 |

### 错误状态（Error State）

| 错误类型 | UI 策略 | 用户操作 |
|---|---|---|
| 网络错误 | Toast 提示 + 页面保留已加载数据 | 重试按钮 |
| 权限不足 | 内联空状态或跳转 403 页面 | 申请权限/联系管理员 |
| 数据加载失败 | 局部 Error Boundary，降级展示 | 重试/刷新 |
| 表单提交失败 | 字段级错误提示 + 全局摘要 | 修正后重新提交 |

---

## 8. 前端组件架构对齐规范

前端组件分层必须与后端分层显式对齐，确保跨角色沟通时术语一致：

| 前端分层 | 职责 | 对应后端 | 示例 |
|---|---|---|---|
| **Page** | 路由入口，布局框架，数据注入 | Controller | `OrderListPage`, `UserDetailPage` |
| **Widget / Section** | 业务组件，复用性中等 | Service | `OrderTable`, `UserProfileCard` |
| **Base / UI Primitive** | 基础组件，纯展示/交互，无业务逻辑 | Repository/Domain | `Button`, `DataTable`, `Modal` |

### 状态管理划分

| 状态类型 | 范围 | 存储方式 | 示例 |
|---|---|---|---|
| Global State | 跨页面共享 | Redux / Pinia / Zustand Store | 用户信息、权限、全局通知 |
| URL State | 页面级，可分享/刷新恢复 | 路由参数 / Query String | 筛选条件、分页页码、当前标签页 |
| Local State | 组件级，不跨组件 | `useState` / `ref` | 表单临时值、展开/折叠 |
| Server State | 服务端数据缓存 | React Query / SWR / TanStack Query | API 响应、缓存失效策略 |

> 禁止：将 Server State 放入 Global State（除非需要离线访问）。
