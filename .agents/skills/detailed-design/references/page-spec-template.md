# Page Specification Template

本模板供 `detailed-design` Skill 生成 module-design.md 第 6.3 节「页面规格表」时直接引用。

---

## 使用说明

1. 为模块涉及的每个页面创建一行记录
2. `page_id` 必须与 6.1 节页面拓扑图中的节点 ID 一致（去掉 `Pg_` 前缀）
3. `fields` 列若过长，可在表格后追加「字段明细」子表格
4. `design_tokens` 列引用项目设计系统 token，无设计系统时标注 `[DEFAULT]`

---

## PageSpec 标准表格

| page_id | page_level | layout_type | layout_pattern | route_path | fields | actions | empty_state | loading_state | error_state | responsive | a11y | motion | design_tokens |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 示例-首页 | entry | DASHBOARD | `layout-sidebar-content` | `/home` | 见下方字段明细 | 新建项目、查看全部 | 引导创建首个项目 | skeleton | toast+降级 | ≥lg:3列; md:2列; sm:1列 | role=main, 焦点在搜索框 | 页面进入 fade-in 200ms | color-bg-surface, space-16, radius-lg |
| 示例-项目创建 | modal | FORM | `layout-modal-form` | `/projects/new` | 项目名称、描述、模板选择 | 确认创建、取消 | - | 按钮loading | inline错误 | 固定宽度 640px | aria-modal=true, focus trap | modal进入 scale-up 150ms | color-primary-500, shadow-xl |

### 字段明细子表格（可选，当 fields 列过长时展开）

| page_id | 字段名 | 接口字段映射 | 展示方式 | 校验规则 | 是否只读 | 默认值 |
|---|---|---|---|---|---|---|
| 示例-首页 | 项目名称 | `projects.name` | 文本链接 | - | 是 | - |
| 示例-首页 | 项目状态 | `projects.status` | Tag 标签 | - | 是 | - |
| 示例-项目创建 | 项目名称 | `projects.name` | Input 输入框 | 必填, 2-50字符, 唯一性校验 | 否 | "" |
| 示例-项目创建 | 模板选择 | `projects.template_id` | Select 下拉单选 | 必填 | 否 | 第一个模板 |

### actions 明细子表格（可选）

| page_id | 操作标签 | 类型 | 触发事件 | 目标页面/接口 | 权限要求 |
|---|---|---|---|---|---|
| 示例-首页 | 新建项目 | primary | click | 打开 modal `示例-项目创建` | `project:create` |
| 示例-首页 | 查看全部 | secondary | click | push `/projects` | `project:read` |
| 示例-项目创建 | 确认创建 | primary | submit | POST `/api/v1/projects` | `project:create` |
| 示例-项目创建 | 取消 | text | click | 关闭 modal | - |

---

## page_level 枚举

| 值 | 说明 | 路由特征 |
|---|---|---|
| `entry` | 入口页，用户旅程起点 | `/`, `/home`, `/login` 或入度为 0 |
| `sub` | 子页，通过导航进入 | 有明确上级页面，URL 通常含路径参数 |
| `modal` | 弹窗，覆盖在当前页上方 | 无独立路由或 hash 路由 (`#/modal/xxx`) |
| `drawer` | 抽屉，侧滑面板 | 无独立路由或 query 参数控制 (`?drawer=xxx`) |

## layout_type 枚举

`LIST`, `FORM`, `DETAIL`, `DASHBOARD`, `MODAL`, `SEARCH`, `WIZARD`, `CARD`, `BLANK`

## layout_pattern 说明

引用 `frontend-design-guide.md` 中定义的 8 种标准布局模式名称，或项目自定义模式（需在设计系统中注册）。
