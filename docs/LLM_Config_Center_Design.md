# LLM 配置中心 — 完整设计方案

> 版本：v1.0 | 适用：前端原型 + 后端编码 | 状态：定稿

---

## 一、产品概述

### 1.1 定位
统一管理 LLM Provider 节点与 AI 工具访问权限策略。配置节点支持全局 / 项目 / 用户多层作用域，后续其他配置项统一在此扩展。

### 1.2 核心模块
| 模块 | 说明 |
|------|------|
| Provider 节点 | 管理 LLM 接入配置（Kimi CLI、OpenAI、Claude 等） |
| 权限策略 | 管理 AI 对文件、终端、外部资源的访问控制规则 |

### 1.3 设计目标
1. 高效配置：Master-Detail 分栏布局，减少页面跳转，支持键盘快捷操作
2. 场景化安全：内置「个人开发 / 团队协作 / 企业安全」三套模板，一键切换
3. 分组可读：规则按「文件系统 / 终端执行 / 网络访问 / 高危拦截」分组展示
4. 渐进授权：企业模式下支持运行时拦截 -> 一键加入白名单的闭环
5. 防错保护：未保存变更拦截、草稿自动恢复、操作二次确认

---

## 二、信息架构

```
LLM 配置中心
├── Provider 节点 (Tab)
│   ├── Master 列表
│   │   ├── 搜索 / 筛选 / 排序
│   │   ├── 列表项（名称 / key / 类型 / 作用域 / 默认标识）
│   │   └── 新增按钮
│   └── Detail 详情/编辑
│       ├── 标题栏（新增/编辑/只读）
│       ├── 基础信息表单
│       └── 底部操作栏
│
└── 权限策略 (Tab)
    ├── Master 列表
    │   ├── 搜索 / 筛选 / 排序
    │   ├── 列表项（名称 / key / 作用域 / 默认模式 / 规则数）
    │   └── 新增按钮
    └── Detail 详情/编辑
        ├── 标题栏
        ├── 场景模板选择器
        ├── 基础信息表单
        ├── 规则列表（分组卡片）
        │   ├── 文件系统规则组
        │   ├── 终端执行规则组
        │   ├── 网络访问规则组
        │   └── 高危拦截规则组
        └── 底部操作栏
```

---

## 三、页面布局设计

### 3.1 全局布局

```
┌─────────────────────────────────────────────────────────────┐
│  Header: LLM 配置中心                    [全局设置] [帮助]   │
├─────────────────────────────────────────────────────────────┤
│  Tab 栏: [ Provider 节点 ] [ 权限策略 ]                       │
├────────────────────┬──────────────────────────────────────┤
│                    │                                      │
│  Master 列表区      │  Detail 详情/编辑区                   │
│  宽度: 320px        │  宽度: calc(100% - 320px)             │
│  固定，独立滚动      │  独立滚动，内部区域自适应              │
│                    │                                      │
│  ┌──────────────┐  │  ┌──────────────────────────────┐   │
│  │ 🔍 搜索...   │  │  │  标题栏                       │   │
│  │ [筛选▼] [排序]│  │  │  ─────────────────────────   │   │
│  ├──────────────┤  │  │  场景模板（仅权限策略）        │   │
│  │ ⭐ 默认 Kimi │  │  │  ─────────────────────────   │   │
│  │    CLI       │  │  │  基础表单 / 规则分组卡片      │   │
│  │    default   │  │  │  ─────────────────────────   │   │
│  │    global    │  │  │  底部操作栏（Sticky）          │   │
│  └──────────────┘  │  └──────────────────────────────┘   │
│  [+ 新增 Provider] │                                      │
│                    │                                      │
└────────────────────┴──────────────────────────────────────┘
```

布局规则：
- 左侧最小宽度 320px，最大 400px，中间分割线可拖拽调整（cursor: col-resize），用户偏好保存到 localStorage
- 两侧各自独立滚动，互不干扰
- 移动端（< 768px）降级为「列表页 -> 详情页」串行流程

### 3.2 左侧 Master 列表区

#### 3.2.1 顶部操作栏
```
┌────────────────────┐
│ 🔍 搜索名称、key... │  ← placeholder 随 Tab 动态切换
├────────────────────┤
│ [全部作用域 ▼]  优先级↓ 更新时间 │  ← 筛选 + 排序
└────────────────────┘
```
- 搜索：实时过滤，延迟 200ms，支持名称/key 模糊匹配
- 筛选：按作用域过滤（全局 / 项目 / 用户）
- 排序：默认按优先级降序 + 更新时间降序

#### 3.2.2 列表项卡片

Provider 节点项：
```
┌────────────────────────┐
│ ⭐ 默认 Kimi CLI        │  ← 主标题 14px，默认项带 ★ 星标
│ default                │  ← key 12px 灰色等宽
│ Kimi CLI · 全局         │  ← 类型图标 + 作用域 12px
└────────────────────────┘
```

权限策略项：
```
┌────────────────────────┐
│ 默认 LLM 权限策略       │
│ default                │
│ 询问 · 全局 · 16 条规则 │  ← 默认模式 + 作用域 + 规则数
└────────────────────────┘
```

选中态：
- 左侧边框 2px solid #1890ff
- 背景色 #f0f5ff
- 其他项 hover 背景 #f5f5f5

草稿态（新增未保存）：
- 边框 1px dashed #ffa940
- 背景色 #fff7e6
- 主标题右侧显示「未保存」标签（12px，橙色）
- 保存成功后 300ms 过渡为正常实线样式

悬浮操作：
- 非默认项 hover 时显示「设为默认」按钮（⭐ 图标），平时隐藏

### 3.3 右侧 Detail 区域

#### 3.3.1 标题栏

| 状态 | 标题格式 | 示例 |
|------|---------|------|
| 新增态 | 新增 Provider 节点 / 新增权限策略 | — |
| 编辑态 | 编辑：{名称} | 编辑：默认 LLM 权限策略 |
| 只读态 | {名称} | 默认 Kimi CLI |

- 样式：16px，font-weight 600，颜色 #262626
- 底部 1px 分隔线 #f0f0f0，与下方内容间距 16px

#### 3.3.2 场景模板选择器（仅权限策略）

```
场景模板: [ 个人开发模式 ▼ ]
┌────────────────────────────────────────┐
│ 个人开发模式                            │
│ 宽松策略，减少 AI 打断，适合本地开发       │
│ [应用模板] [查看与当前差异]               │
└────────────────────────────────────────┘
```

- 切换模板时，若当前规则有修改，弹窗确认：「切换模板将覆盖当前规则，是否继续？」
- 应用模板后手动修改规则，模板选择器显示「自定义（基于个人开发模式）」
- 提供「重置为模板默认」按钮

#### 3.3.3 底部操作栏（Sticky）

```
┌────────────────────────────────────────┐
│                              [取消] [保存]│  ← 始终悬浮在右侧底部
└────────────────────────────────────────┘
```

- position: sticky; bottom: 0
- 背景 #fff，顶部阴影 box-shadow: 0 -2px 8px rgba(0,0,0,0.04)
- 快捷键：Ctrl/Cmd + S = 保存，Esc = 取消（有变更时先确认）

---

## 四、交互设计

### 4.1 状态流转图

用户进入页面
    -> 加载左侧列表，默认选中第一项（或上次选中项）
    -> 右侧显示只读态详情
    -> 点击「编辑」 -> 右侧切换为编辑态，表单回填
        -> 点击「保存」 -> 校验 -> 提交 -> 成功：回只读态，列表刷新；失败：顶部 Banner 错误，保留编辑态
        -> 点击「取消」 -> 无变更：直接回只读态；有变更：弹窗确认
    -> 点击「删除」 -> 二次确认弹窗 -> 删除 -> 列表移除，右侧显示空状态
    -> 点击「+ 新增」 -> 左侧插入草稿占位项，右侧进入新增态（表单为空）
        -> 保存后占位项替换为真实数据，标题栏同步
    -> 点击左侧其他项 -> 若当前编辑态有变更：弹窗拦截；无变更：直接切换右侧详情

### 4.2 未保存变更防丢机制（Dirty Check）

| 触发场景 | 系统行为 |
|---------|---------|
| 点击左侧其他列表项 | 弹窗：「当前有未保存的更改」-> [保存并切换] [放弃并切换] [取消] |
| 点击顶部 Tab 切换 | 同上 |
| 浏览器关闭/刷新 | beforeunload 拦截，提示「离开页面前请确认」 |
| 5 分钟无操作 | 自动保存草稿到 localStorage，下次恢复时提示「检测到未提交草稿，是否恢复？」 |

### 4.3 规则运行时拦截与渐进授权（企业模式）

AI 请求执行命令 / 访问文件 / 调用 API
    -> 规则引擎匹配
    -> 命中允许 -> 直接执行
    -> 命中拒绝 -> 拦截，提示「操作被拒绝」
    -> 命中询问 / 未命中 -> 弹窗：
        操作被拦截
        命令：npm run deploy
        类型：终端执行
        [取消] [人工执行一次] [加入白名单]
            -> 「人工执行一次」-> 本次放行，不修改规则
            -> 「加入白名单」-> 弹出规则编辑：
                操作类型：terminal
                权限：允许
                匹配模式：npm run deploy
                描述：用户于 2026-06-14 手动添加
                [确认添加]

---

## 五、权限策略规则引擎设计

### 5.1 规则分组

所有规则按业务语义分为 4 组，UI 分组展示，引擎内按组优先级匹配：

| 优先级 | 分组 | 说明 |
|--------|------|------|
| 1 | 高危拦截 | 拒绝类规则，最先匹配（rm、sudo 等） |
| 2 | 文件系统 | 文件读取、写入、删除 |
| 3 | 终端执行 | 命令行工具执行 |
| 4 | 网络访问 | 网页抓取、外部 API 调用 |

### 5.2 场景模板

#### 模板 A：个人开发模式（默认宽松）

| 分组 | 操作类型 | 权限 | 匹配模式 | 描述 |
|------|---------|------|---------|------|
| 文件系统 | file_read | 允许 | ${PROJECT_ROOT}/** | 允许读取项目内文件 |
| 文件系统 | file_write | 允许 | src/**、tests/**、config/** | 允许写入常见开发目录 |
| 文件系统 | file_write | 询问 | ${PROJECT_ROOT}/** | 其他写入需确认 |
| 文件系统 | file_delete | 询问 | * | 删除文件需确认 |
| 终端执行 | terminal | 允许 | pytest*、python -m pytest* | 允许单元测试 |
| 终端执行 | terminal | 允许 | ruff check*、ruff format* | 允许代码检查与格式化 |
| 终端执行 | terminal | 允许 | npm test、npm run build、npm run lint | 允许测试与构建 |
| 终端执行 | terminal | 允许 | npm install* | 允许安装依赖 |
| 终端执行 | terminal | 允许 | git status*、git diff*、git log* | 允许 Git 只读操作 |
| 终端执行 | terminal | 询问 | * | 其他命令需确认 |
| 网络访问 | web_fetch | 允许 | * | 允许抓取外部网页 |
| 网络访问 | external_api | 询问 | * | 外部 API 调用需确认 |
| 高危拦截 | terminal | 拒绝 | rm -rf * | 禁止递归删除 |
| 高危拦截 | terminal | 拒绝 | sudo * | 禁止提权命令 |

#### 模板 B：团队协作模式（平衡）

| 分组 | 操作类型 | 权限 | 匹配模式 | 描述 |
|------|---------|------|---------|------|
| 文件系统 | file_read | 允许 | ${PROJECT_ROOT}/** | 允许读取项目内文件 |
| 文件系统 | file_write | 允许 | src/**、tests/** | 允许写入代码目录 |
| 文件系统 | file_write | 询问 | config/**、docs/** | 配置与文档写入需确认 |
| 文件系统 | file_write | 拒绝 | ${PROJECT_ROOT}/** | 其他写入拒绝 |
| 文件系统 | file_delete | 拒绝 | * | 禁止删除文件 |
| 终端执行 | terminal | 允许 | pytest*、npm test、ruff check* | 允许测试与检查 |
| 终端执行 | terminal | 允许 | git status*、git diff*、git log* | 允许 Git 只读 |
| 终端执行 | terminal | 询问 | npm install* | 安装依赖需确认 |
| 终端执行 | terminal | 拒绝 | git commit*、git push* | 禁止自动提交代码 |
| 终端执行 | terminal | 询问 | * | 其他命令需确认 |
| 网络访问 | web_fetch | 询问 | * | 外部网页抓取需确认 |
| 网络访问 | external_api | 拒绝 | * | 禁止外部 API 调用 |
| 高危拦截 | terminal | 拒绝 | rm -rf *、sudo *、curl *\|*bash* | 高危命令拒绝 |

#### 模板 C：企业安全模式（默认拒绝，逐步放开）

| 分组 | 操作类型 | 权限 | 匹配模式 | 描述 |
|------|---------|------|---------|------|
| 文件系统 | file_read | 允许 | ${PROJECT_ROOT}/** | 允许读取项目内文件 |
| 文件系统 | file_write | 允许 | ${PROJECT_ROOT}/openspec/changes/** | 仅允许写入指定目录 |
| 文件系统 | file_write | 拒绝 | ${PROJECT_ROOT}/** | 其他写入拒绝 |
| 文件系统 | file_delete | 拒绝 | * | 禁止删除文件 |
| 终端执行 | terminal | 拒绝 | * | 默认拒绝所有命令 |
| 网络访问 | web_fetch | 拒绝 | * | 禁止外部网页抓取 |
| 网络访问 | external_api | 拒绝 | * | 禁止外部 API 调用 |
| 网络访问 | external_api | 允许 | https://internal-api.company.com/** | 允许内网白名单（需配置） |
| 高危拦截 | terminal | 拒绝 | rm -rf *、sudo *、curl *、wget * | 高危命令拒绝 |

企业模式下，终端执行默认全部拒绝。AI 运行时请求命令被拦截，用户可选择「加入白名单」，由安全管理员审批后生效。

### 5.3 规则匹配算法

推荐实现：最长匹配优先（Longest Match First）

```python
def match_rule(rules, action_type, command_or_path):
    # 1. 按分组优先级过滤（高危拦截 > 文件系统 > 终端执行 > 网络访问）
    # 2. 同分组内，按匹配模式长度降序排列
    # 3. 遍历匹配，第一条命中即返回
    # 4. 未命中任何规则，返回该操作类型的默认模式
    candidates = [r for r in rules if r.action_type == action_type]
    candidates.sort(key=lambda r: len(r.pattern), reverse=True)
    for rule in candidates:
        if fnmatch(command_or_path, rule.pattern):
            return rule.permission  # allow / ask / deny
    return default_mode  # 策略的默认模式
```

优势：精确规则（如 openspec/changes/**）自动优先于宽泛规则（/**），不受人工排序影响。

---

## 六、数据模型设计

### 6.1 数据库 Schema

#### 表：llm_providers

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT | PK, Auto | 主键 |
| name | VARCHAR(64) | NOT NULL | 显示名称 |
| key | VARCHAR(64) | NOT NULL, UNIQUE | 业务标识键 |
| scope | ENUM('global','project','user') | NOT NULL, DEFAULT 'global' | 作用域 |
| scope_target_id | VARCHAR(64) | NULL | 作用域目标 ID（项目 ID / 用户 ID） |
| priority | INT | NOT NULL, DEFAULT 0 | 优先级，数值越大越优先 |
| provider_type | ENUM('kimi_cli','openai','claude','custom') | NOT NULL | Provider 类型 |
| config_json | JSON | NOT NULL | 类型专属配置（如路径、超时、密钥引用） |
| description | VARCHAR(255) | NULL | 描述 |
| is_default | BOOLEAN | NOT NULL, DEFAULT FALSE | 是否为默认节点 |
| status | ENUM('active','inactive') | NOT NULL, DEFAULT 'active' | 状态 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

索引：key（唯一）、scope + scope_target_id（复合）、is_default + scope（查询默认节点）

#### 表：llm_policies

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT | PK, Auto | 主键 |
| name | VARCHAR(64) | NOT NULL | 显示名称 |
| key | VARCHAR(64) | NOT NULL, UNIQUE | 业务标识键 |
| scope | ENUM('global','project','user') | NOT NULL, DEFAULT 'global' | 作用域 |
| scope_target_id | VARCHAR(64) | NULL | 作用域目标 ID |
| priority | INT | NOT NULL, DEFAULT 0 | 优先级 |
| default_mode | ENUM('allow','ask','deny') | NOT NULL, DEFAULT 'ask' | 默认模式 |
| description | VARCHAR(255) | NULL | 描述 |
| template_id | VARCHAR(32) | NULL | 基于哪个模板创建（personal / team / enterprise） |
| is_customized | BOOLEAN | NOT NULL, DEFAULT FALSE | 是否基于模板手动修改过 |
| status | ENUM('active','inactive') | NOT NULL, DEFAULT 'active' | 状态 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

#### 表：llm_policy_rules

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGINT | PK, Auto | 主键 |
| policy_id | BIGINT | FK -> llm_policies.id, CASCADE | 所属策略 |
| category | ENUM('high_risk','file_system','terminal','network') | NOT NULL | 规则分组 |
| action_type | ENUM('file_read','file_write','file_delete','terminal','web_fetch','external_api') | NOT NULL | 操作类型 |
| permission | ENUM('allow','ask','deny') | NOT NULL | 权限 |
| pattern | VARCHAR(255) | NOT NULL | 匹配模式（支持 glob） |
| description | VARCHAR(255) | NULL | 描述 |
| sort_order | INT | NOT NULL, DEFAULT 0 | 组内排序 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

索引：policy_id + category + sort_order（复合，用于按分组排序查询）

#### 表：policy_templates（内置模板，可扩展）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(32) | PK | 模板标识：personal / team / enterprise |
| name | VARCHAR(64) | NOT NULL | 模板名称 |
| description | VARCHAR(255) | NULL | 描述 |
| default_mode | ENUM('allow','ask','deny') | NOT NULL | 默认模式 |
| rules_json | JSON | NOT NULL | 模板默认规则列表（结构与 llm_policy_rules 一致） |

### 6.2 关键关联关系

- llm_providers (1) -> scope_target_id 指向 project / user
- llm_policies (1) -> scope_target_id 指向 project / user
- llm_policies (1) -> llm_policy_rules (N) 按 policy_id 关联
- llm_policies (N) -> policy_templates (1) 按 template_id 关联（可选）

### 6.3 运行时拦截审计（企业增强）

#### 表：llm_policy_audit_logs

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK | 主键 |
| policy_id | BIGINT FK | 所属策略 |
| action_type | ENUM | 操作类型 |
| target | VARCHAR(255) | 具体命令或路径 |
| result | ENUM('allowed','blocked','asked','whitelisted') | 处理结果 |
| user_id | VARCHAR(64) | 操作用户 |
| session_id | VARCHAR(64) | 会话 ID |
| created_at | TIMESTAMP | 时间 |

---

## 七、API 设计

### 7.1 Provider 节点 API

| 方法 | 路径 | 说明 | 请求/响应 |
|------|------|------|----------|
| GET | /api/v1/llm/providers | 列表查询 | Query: scope, scope_target_id, keyword, page, size |
| GET | /api/v1/llm/providers/{id} | 详情 | Response: Provider 详情 + 是否默认 |
| POST | /api/v1/llm/providers | 新增 | Body: name, key, scope, provider_type, config_json, priority... |
| PUT | /api/v1/llm/providers/{id} | 编辑 | Body: 同新增，排除 key（不可改） |
| DELETE | /api/v1/llm/providers/{id} | 删除 | 默认节点禁止删除，需先切换默认 |
| POST | /api/v1/llm/providers/{id}/set-default | 设为默认 | 同作用域下其他节点取消默认 |

### 7.2 权限策略 API

| 方法 | 路径 | 说明 | 请求/响应 |
|------|------|------|----------|
| GET | /api/v1/llm/policies | 列表查询 | Query: scope, keyword |
| GET | /api/v1/llm/policies/{id} | 详情 | Response: Policy + Rules（按 category 分组） |
| POST | /api/v1/llm/policies | 新增 | Body: name, key, scope, default_mode, rules[] |
| PUT | /api/v1/llm/policies/{id} | 编辑 | Body: 全量更新（包含 rules 数组） |
| DELETE | /api/v1/llm/policies/{id} | 删除 | |
| GET | /api/v1/llm/policies/templates | 获取模板列表 | Response: 内置模板列表 |
| POST | /api/v1/llm/policies/apply-template | 应用模板 | Body: template_id, base_policy_id（可选） |
| POST | /api/v1/llm/policies/{id}/rules | 单条追加规则 | 渐进授权场景：运行时加入白名单 |

### 7.3 规则引擎 API（运行时调用）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/llm/policies/check | 权限检查 |

请求体：
```json
{
  "policy_key": "default",
  "scope": "global",
  "scope_target_id": null,
  "action_type": "terminal",
  "target": "npm run deploy"
}
```

响应体：
```json
{
  "allowed": false,
  "permission": "ask",
  "matched_rule": null,
  "message": "未命中任何规则，使用默认模式：询问",
  "suggest_whitelist": true
}
```

---

## 八、前端组件架构

### 8.1 组件拆分

```
src/pages/LLMConfig/
├── index.tsx                    # 页面入口，Tab 路由
├── components/
│   ├── MasterList.tsx           # 左侧列表（通用，Provider/Policy 复用）
│   ├── MasterListItem.tsx       # 列表项卡片（区分 Provider/Policy 类型）
│   ├── DetailContainer.tsx      # 右侧容器（管理只读/编辑/新增态）
│   ├── DetailHeader.tsx         # 标题栏
│   ├── StickyActionBar.tsx      # 底部粘性操作栏
│   ├── DirtyCheckGuard.tsx      # 未保存变更守卫（HOC/Hook）
│   ├── TemplateSelector.tsx     # 场景模板选择器（仅 Policy）
│   └── rules/
│       ├── RuleEditor.tsx       # 规则编辑器（分组卡片容器）
│       ├── RuleGroupCard.tsx    # 单分组卡片（可折叠）
│       ├── RuleGroupHeader.tsx  # 分组标题（含快捷操作）
│       ├── RuleItem.tsx         # 单条规则行（可拖拽）
│       └── RuleTableHeader.tsx  # 规则表头
├── hooks/
│   ├── useDirtyCheck.ts         # 脏检查逻辑
│   ├── usePolicyTemplate.ts     # 模板应用逻辑
│   └── useRuleMatcher.ts        # 前端模拟规则匹配（可选）
└── types/
    ├── provider.ts
    └── policy.ts
```

### 8.2 状态管理（推荐 Zustand / Pinia）

```typescript
interface LLMConfigStore {
  // 列表状态
  activeTab: 'provider' | 'policy';
  selectedId: string | null;
  masterList: MasterItem[];

  // 详情状态
  detailMode: 'view' | 'edit' | 'create';
  detailData: Provider | Policy | null;
  draftData: Partial<Provider | Policy> | null;
  isDirty: boolean;

  // 动作
  selectItem: (id: string) => void;
  startEdit: () => void;
  startCreate: () => void;
  saveDraft: () => Promise<void>;
  cancelEdit: () => void;
  applyTemplate: (templateId: string) => void;
}
```

---

## 九、响应式适配

| 断点 | 布局 |
|------|------|
| >= 1024px | 左右分栏 Master-Detail，左侧 320px |
| 768px ~ 1024px | 左侧收缩为 280px，列表项精简元信息 |
| < 768px | 串行布局：列表页全屏 -> 点击项进入详情页全屏，顶部返回按钮 |

---

## 十、验收标准

### 10.1 功能验收

| 编号 | 场景 | 预期结果 |
|------|------|---------|
| 1 | 进入 Provider 节点 Tab | 左侧加载列表，默认选中第一项，右侧显示只读详情 |
| 2 | 点击「+ 新增 Provider」 | 左侧插入橙色虚线占位卡片，右侧显示空表单，标题「新增 Provider 节点」 |
| 3 | 填写名称并保存 | 占位卡片过渡为实线，标题同步更新，列表项高亮闪烁 1 秒 |
| 4 | 编辑权限策略，修改规则后点击左侧其他项 | 弹出拦截确认窗：「保存并切换 / 放弃并切换 / 取消」 |
| 5 | 权限策略编辑页 | 规则列表按「文件系统 / 终端执行 / 网络访问 / 高危拦截」分组展示，每组有表头 |
| 6 | 切换场景模板 | 规则列表按模板重新渲染，手动修改后模板选择器显示「自定义」 |
| 7 | 企业模式下 AI 执行未授权命令 | 运行时弹窗拦截，提供「加入白名单」按钮，点击后追加规则并保存 |
| 8 | 快捷键 | Ctrl+S 保存，Esc 取消，上下箭头在左侧列表切换选中项 |

### 10.2 性能验收

- 列表页首屏加载 < 500ms（50 条数据以内）
- 规则匹配 API 响应 < 50ms（P99）
- 模板切换渲染无卡顿（规则 < 50 条）

---

## 附录：规则匹配模式语法

| 通配符 | 含义 | 示例 |
|--------|------|------|
| * | 匹配任意字符（不含 /） | pytest* 匹配 pytest、pytest-x |
| ** | 匹配任意字符（含 /） | ${PROJECT_ROOT}/** 匹配任意子路径 |
| ? | 匹配单个字符 | git ??? 匹配 git log |
| {a,b} | 匹配 a 或 b | npm run {build,lint} |

后端实现建议基于 fnmatch 或 glob 库，支持 ** 需启用 globstar 选项。
