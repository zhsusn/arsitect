# Arsitect — AI 驱动软件工程全生命周期管理平台

> **项目定位**：Arsitect（AI Architect / AI Code 研发平台）是一个面向 AI 编程助手（Agent）的**技能框架（Skill Framework）**与**工程纪律规范集**，同时正在建设配套的**可视化驾驶舱（SDLC Visualizer）**前后端应用。它通过标准化的 Markdown Skill 定义、OpenSpec 文档体系与可视化界面，编排 AI 完成从需求分析到线上监控的完整 SDLC。
>
> **目标读者**：本文件面向 AI Coding Agent。你应当把本项目理解为"一套可编排的 AI 软件开发工作流模板 + 一个正在建设中的 Web 应用"，其中 Skill 框架是核心，前后端应用是 Skill 的消费界面之一。
>
> **主要语言**：项目所有文档、Skill 定义、配置模板均以**简体中文**编写。代码注释与文档以中文为主，少量 TypeScript/Python 文件使用英文注释。

---

## 1. 项目概览

### 1.1 三层构成

| 层级 | 目录 | 说明 |
|------|------|------|
| **Skill 框架** | `.agents/skills/` | 41 个自包含 Markdown 工作流定义，覆盖完整 12 阶段 SDLC |
| **可视化驾驶舱后端** | `backend/` | FastAPI + SQLAlchemy + Pydantic 后端服务（MVP 阶段） |
| **可视化驾驶舱前端** | `frontend/` | React 19 + Vite 6 + TypeScript 单页应用（MVP 阶段） |
| **OpenSpec 变更管理** | `openspec/` | 全局规范配置、变更产物归档、进度追踪 |
| **运维模板** | `ops/` | 监控规则骨架、回滚方案、预发布配置模板 |
| **产品文档** | `docs/` | PRD、架构设计、竞品分析等产物 |

### 1.2 Skill 框架覆盖的 12 阶段链路

| 阶段 | Skill | 职责 |
|------|-------|------|
| 需求探索 | `brainstorming`, `competitive-analysis`, `requirement-analysis` | 市场定位、竞品分析、需求澄清 |
| 概要需求 | `prd-generation`, `project-size-estimate` | 产出 PRD-000（五文件概要需求）、规模评估 |
| 详细需求 | `detailed-requirements` | 按模块拆解 spec / prototype / io-table / logic / interaction-spec |
| 概要设计 | `high-level-design`, `functional-architecture-generator` | 系统分层、技术选型、数据架构、Mermaid 图 |
| 详细设计 | `detailed-design` | 模块级技术细节、接口定义、状态机、DDL |
| 接口契约 | `interface-first-dev` | 生成 OpenAPI / 前后端接口契约 |
| 任务拆解 | `task-breakdown`, `writing-plans` | 将设计文档拆为 ≤30 分钟/任务的 `tasks.md`，生成 plan.md |
| 编码实现 | `executing-plans` | 按 Batch 执行任务，含强制自测、接口校验 |
| 单元测试 | `unit-test`, `unit-test-generator`, `test-driven-development` | TDD 内循环 + 模块级边界测试，覆盖率 ≥70% |
| 集成测试 | `integration-test` | 端到端验证、UAT 检查清单 |
| 代码审查 | `code-review-pipeline`, `code-reviewer`, `code-review-skill`, `requesting-code-review`, `receiving-code-review` | 四阶段×五轴结构化审查 |
| UAT | `uat-verification` | 基于用户故事的验收测试 |
| 发布上线 | `release-management`, `git-automation`, `conventional-commit-generator` | 发布清单、风险评估、发布说明、规范提交信息 |
| 收尾归档 | `finish` | 分支合并、OpenSpec 归档、CHANGELOG |
| 线上监控 | `monitoring-setup`, `monitoring-analysis` | 监控规则、健康报告、反馈闭环 |

此外还包含跨阶段支撑 Skill：
- `progress-tracker` — 进度治理中枢（SSOT、双轨制进度、人工闸门）
- `self-check` — 产出物质量自查
- `human` — 四道人工闸门（Gate 1 / 2.5 / 2 / 3）的统一载体
- `systematic-debugging`, `debug-assistant` — 问题定位与调试
- `documentation`, `code-documenter` — 技术文档与代码注释
- `mermaid-diagrams` — 架构图与流程图生成
- `python-google-style`, `java-alibaba-style` — 语言强规范
- `regex-builder-explainer` — 正则构建与解释
- `workflow-automation-agent` — 通用流程编排
- `c4-governance-fix` — C4 架构治理问题自动修复方案生成

---

## 2. 技术栈与运行架构

### 2.1 技术栈

#### Skill 框架层
| 层级 | 技术/格式 | 说明 |
|------|----------|------|
| 核心载体 | Markdown + YAML Frontmatter | 每个 Skill 由 `SKILL.md`（主定义）+ `meta.json`（元数据）组成 |
| 辅助脚本 | JavaScript (Node.js)、Shell、TypeScript | 仅在少数 Skill 中提供辅助工具 |
| 配置 | YAML / JSON | `openspec/config.yaml`、各 Skill 的 `meta.json` 等 |
| 消费平台 | Kimi、Claude、Cursor、Codex、Gemini、Windsurf | `meta.json` 中 `platforms` 字段声明支持的平台 |

#### 后端应用层（`backend/`）
| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 运行时 |
| FastAPI | 0.115.x | Web 框架 |
| Uvicorn | 0.32.x | ASGI 服务器 |
| SQLAlchemy | 2.0.x | ORM |
| Pydantic | 2.9.x | 数据校验与配置 |
| Pydantic-Settings | 2.6.x | 环境配置管理 |
| Alembic | 1.14.x | 数据库迁移 |
| HTTPX | 0.27.x | 异步 HTTP 客户端 |
| python-multipart | 0.0.12+ | 文件上传支持 |
| aiofiles | 24.0.0+ | 异步文件操作 |
| pytest / pytest-asyncio / pytest-cov | 8.3+ | 测试框架与覆盖率 |
| ruff | 0.8+ | Python 代码格式与 lint |
| mypy | 1.13+ | 静态类型检查 |

#### 前端应用层（`frontend/`）
| 技术 | 版本 | 用途 |
|------|------|------|
| React | 19.x | UI 框架 |
| React DOM | 19.x | 渲染层 |
| TypeScript | ~5.6 | 类型系统 |
| Vite | 6.x | 构建工具与开发服务器 |
| React Router | 7.x | 客户端路由 |
| @xyflow/react | 12.x | React Flow 流程图/画布（SDLC 可视化核心） |
| Zustand | 5.x | 状态管理 |
| React-Markdown | 9.x | Markdown 渲染 |
| remark-gfm | 4.x | GitHub Flavored Markdown 支持 |
| Mermaid | 10.9.x | 图表渲染 |
| Axios | 1.7.x | HTTP 客户端 |
| ESLint | 9.x | TypeScript/TSX 代码检查 |

#### 数据层
| 阶段 | 数据库 | 说明 |
|------|--------|------|
| MVP（当前） | SQLite | 本地文件数据库，零配置启动 |
| P1（+2 周） | PostgreSQL 15+ | 持久化关系型数据库 |

### 2.2 运行架构

#### Skill 框架运行时
运行时并非传统进程，而是**被 AI 平台加载并解释的 Skill 工作流**：
1. **触发层**：用户输入自然语言指令 → AI 匹配 `SKILL.md` Frontmatter 中的 `description` 触发条件。
2. **编排层**：Skill 内部定义了严格的步骤（Step 1→2→3…）、上下游依赖、门控条件。
3. **产出层**：Skill 驱动 AI 生成 Markdown/YAML 文档，写入 `openspec/changes/{变更名}/` 目录。
4. **审计层**：`progress-tracker` 维护 `progress.md`（SSOT），`human-decisions.md` 记录人工签字。

#### 可视化驾驶舱运行时（MVP）
```
┌─────────────────┐      proxy(/api, /sse)      ┌─────────────────┐
│  Frontend       │  ─────────────────────────> │  Backend        │
│  Vite dev 5173  │                             │  Uvicorn 8000   │
│  React 19 + TS  │                             │  FastAPI + SQLite│
└─────────────────┘                             └─────────────────┘
```
- 前端开发服务器运行于 `localhost:5173`，通过 Vite proxy 将 `/api` 与 `/sse` 转发至后端 `localhost:8000`。
- 后端入口为 `backend/main.py`，CORS 仅允许 `http://localhost:5173`。
- 当前后端处于骨架阶段，仅提供 `/health` 健康检查端点，各业务模块（`api/v1/`, `services/`, `models/` 等）尚未填充。

---

## 3. 目录结构与模块划分

```
Arsitect/
├── .agents/skills/              # 核心：全部 41 个 Skill 定义
│   ├── {skill-name}/
│   │   ├── SKILL.md             # 主定义（必须存在，首行 YAML Frontmatter）
│   │   ├── meta.json            # 元数据：name, version, pattern, tags, platforms
│   │   ├── references/          # 参考资料（可选）
│   │   ├── examples/            # 示例（可选）
│   │   ├── scripts/             # 辅助脚本（可选）
│   │   ├── templates/           # 模板（可选）
│   │   ├── assets/              # 静态资源（可选）
│   │   └── *.md / *.ts / *.sh / *.yaml  # 其他附属文件
│   └── ... (41 skills)
├── backend/                     # FastAPI 后端应用
│   ├── main.py                  # 应用入口：FastAPI 实例 + CORS + /health
│   ├── pyproject.toml           # Python 项目配置、依赖、工具链设置
│   ├── requirements.txt         # 运行时依赖清单
│   ├── app/
│   │   ├── api/                 # REST API 路由层
│   │   │   └── v1/              # API v1 版本命名空间
│   │   ├── core/                # 核心配置（settings、常量、异常基类）
│   │   ├── infrastructure/      # 基础设施（数据库连接、缓存、外部客户端）
│   │   ├── models/              # SQLAlchemy ORM 模型
│   │   ├── schemas/             # Pydantic 序列化/反序列化模型
│   │   └── services/            # 业务逻辑层
│   ├── migrations/              # Alembic 数据库迁移脚本
│   └── tests/                   # pytest 测试目录
├── frontend/                    # React 前端应用
│   ├── index.html               # HTML 入口
│   ├── package.json             # Node 依赖与脚本
│   ├── vite.config.ts           # Vite 配置（含后端代理）
│   ├── tsconfig*.json           # TypeScript 配置（app + node 双配置）
│   └── src/
│       ├── main.tsx             # React 应用挂载点（StrictMode）
│       ├── App.tsx              # 根组件
│       ├── components/          # 通用 UI 组件
│       ├── hooks/               # 自定义 React Hooks
│       ├── pages/               # 页面级组件
│       │   ├── Dashboard/       # 项目仪表盘
│       │   ├── Canvas/          # SDLC 流程画布（React Flow）
│       │   ├── GateCenter/      # 人工闸门审批中心
│       │   ├── ArtifactViewer/  # 产物浏览器
│       │   ├── C4Navigator/     # C4 架构导航器
│       │   └── PrototypeViewer/ # 原型查看器
│       ├── services/            # API 请求封装
│       ├── stores/              # Zustand 状态管理
│       └── utils/               # 工具函数
├── docs/
│   ├── ai-output/               # AI 生成的文档输出目录（运行时填充）
│   ├── AI_Code_v3.2.md          # 平台自身的产品需求文档（PRD，v3.3 基线）
│   ├── brainstorming/           # 头脑风暴产物
│   ├── high-level-requirements/ # 概要需求产物
│   ├── high-level-design/       # 概要设计产物
│   └── ...                      # 其他设计阶段产物
├── openspec/                    # OpenSpec 变更管理体系
│   ├── config.yaml              # 项目级规范配置（schema、artifact_specs、门控规则、red_flags）
│   ├── archive/                 # 已归档的变更历史
│   ├── changes/                 # 活跃变更目录
│   │   ├── sdlc-visualizer/     # 当前活跃变更：可视化驾驶舱
│   │   └── ...                  # 其他变更
│   └── specs/                   # 基线规格库
├── ops/                         # 运维模板与配置
│   ├── monitoring-rules.yaml    # 监控规则骨架（基础设施/应用/前端/业务/安全/可观测性）
│   ├── rollback-plan.md         # 回滚方案模板（三级回滚：产物级/数据库级/项目级）
│   └── staging-config.yaml      # 预发布环境配置模板（含占位符）
├── tests/                       # 框架级测试占位目录（供被管理的项目使用）
│   ├── integration/
│   └── unit/
└── .kimi/skills/                # 外部/平台级 Skill 挂载点
```

### 3.1 Skill 目录规范

每个 Skill 目录必须遵守以下约定：
- **`SKILL.md`**：文件首行必须是 YAML Frontmatter（`---` 包裹），至少包含 `name` 和 `description`。`description` 同时也是**触发条件**的自然语言描述。
- **`meta.json`**：标准结构如下，禁止缺失 `platforms` 字段：
  ```json
  {
    "name": "skill-name",
    "version": "x.y.z",
    "pattern": "generator|pipeline|reviewer|analyzer|inversion|tool-wrapper",
    "tags": ["sdlc", "..."],
    "platforms": ["kimi", "claude", "cursor", "codex", "gemini", "windsurf"]
  }
  ```
- **子目录命名**：`references/`、`examples/`、`scripts/`、`templates/`、`assets/` 为约定俗成的可选目录，不得随意自创。

### 3.2 OpenSpec 变更目录规范

当 Skill 运行时，产出物按以下路径存放：
```
openspec/changes/{变更名}/
├── high-level-requirements/     # 概要需求（PRD-000）
├── detailed-requirements/
│   └── feature-XX-{模块}/
│       ├── module-requirements.md
│       ├── spec.md
│       ├── prototype.md
│       ├── io-table.md
│       ├── logic.md
│       └── interaction-spec.md
├── high-level-design/           # 6 个主题文件 + 1 份自检报告
│   ├── 00-design-overview.md
│   ├── 01-architecture-core.md
│   ├── 02-data-flow.md
│   ├── 03-runtime-behavior.md
│   ├── 04-quality-attributes.md
│   ├── 05-ops-governance.md
│   └── self-check-report.md
├── detailed-design/
│   └── feature-XX-{模块}/
│       ├── design.md
│       └── api-spec.md
├── interface-contracts/
│   └── openapi.yaml
├── tasks.md                     # 任务清单（Checkbox + verified_by）
├── progress.md                  # 单一可信进度源（SSOT）
├── human-decisions.md           # 人工决策审计日志
├── uat/
│   └── uat-report.md
├── code-review/
│   ├── review-request.yaml
│   ├── review-report.yaml
│   └── fix-plan.yaml
└── release-notes.md
```

---

## 4. 开发约定与工作流

### 4.1 12 阶段 SDLC 与人工闸门

项目采用严格的 12 阶段交付链路，其中存在 4 道**人工闸门（Gate）**：

| 闸门 | 所在阶段 | 含义 | 未通过后果 |
|------|----------|------|-----------|
| Gate 1 | 概要需求完成后 | 需求基线冻结确认 | 禁止进入详细需求与概要设计 |
| Gate 2.5 | 详细需求完成后 | 模块级需求评审通过 | 禁止进入详细设计 |
| Gate 2 | 概要设计完成后 | 架构决策确认 | 禁止进入详细设计 |
| Gate 3 | UAT 完成后 | 业务流程验收通过 | 禁止进入发布阶段 |

**Rule RF-02**：禁止无规格编码。`executing-plans`（编码实现）必须等待 `interface-first-dev`（接口契约）和 `task-breakdown`（任务拆解）完成后方可启动。

**Rule RF-06**：禁止跳过人工闸门。具体映射见 `openspec/config.yaml` 中的 `red_flags` 与 `progress_caps`。

### 4.2 Draft / Active 双态模型

Skill 和变更产物均存在两种状态：
- **Draft（草稿态）**：探索性、可随意修改、不触发严格门控。
- **Active（执行态）**：经人工确认后进入，受进度追踪、门控、审计约束。

### 4.3 TDD 与自测门控

编码阶段强制嵌入 TDD 内循环（由 `test-driven-development` Skill 定义）：
1. **RED**：先写失败测试，临时存放于 `.kimi/temp-tests/{任务ID}_red.py`
2. **GREEN**：写最小实现让测试通过
3. **REFACTOR**：清理代码，严禁顺手重构相邻文件
4. **Self-Check**：调用 `self-check` Skill 校验代码 vs 设计一致性、异常处理完整性、无硬编码密钥

---

## 5. 构建、测试与部署

### 5.1 后端构建与运行

**安装依赖**（在 `backend/` 目录下）：
```bash
# 使用 pip + requirements.txt
pip install -r requirements.txt

# 或使用 pyproject.toml（推荐）
pip install -e ".[dev]"
```

**运行开发服务器**：
```bash
cd backend
python main.py
# 或
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**代码质量检查**：
```bash
cd backend
ruff check .          # Lint 检查（行宽 100，目标 Python 3.11）
ruff format .         # 自动格式化
mypy .                # 静态类型检查（strict 模式）
```

**运行测试**：
```bash
cd backend
pytest
# 默认启用 coverage，阈值 ≥70%，未达标则失败
# 配置见 pyproject.toml [tool.pytest.ini_options]
```

前端单元测试使用 Vitest + React Testing Library：
```bash
cd frontend
npm run test        # 单次运行
npm run test:watch  # 监听模式
```

### 5.2 前端构建与运行

**安装依赖**（在 `frontend/` 目录下）：
```bash
cd frontend
npm install
```

**运行开发服务器**：
```bash
cd frontend
npm run dev
# 服务启动于 http://localhost:5173
# API 代理至 http://localhost:8000
```

**构建生产包**：
```bash
cd frontend
npm run build
# 输出至 frontend/dist/
```

**代码质量检查**：
```bash
cd frontend
npm run lint       # ESLint 检查 ts/tsx
npm run typecheck  # TypeScript 无 emit 编译检查
npm run test       # Vitest 单元测试
```

### 5.3 Skill 框架校验

"构建"在 Skill 框架语境下指：
- Skill 定义的完整性与一致性校验（检查 `SKILL.md` 是否存在 YAML Frontmatter、`meta.json` 是否完整）
- OpenSpec 目录结构的合规性检查
- Markdown 内部交叉引用有效性检查
- `openspec/config.yaml` 的 schema 合法性校验

### 5.4 部署

Arsitect 的 Skill 框架本身不以传统方式"部署"。其分发形式为：
- Git 仓库克隆到本地工作区
- AI 平台（如 Kimi CLI）通过 `.agents/skills/` 路径发现并加载 Skill
- 被管理项目的"部署"由 `release-management` Skill 产出发布清单与回滚方案，**人工最终执行**

前后端应用的部署由 `release-management` Skill 在 UAT 通过后产出发布清单，遵循 `ops/rollback-plan.md` 中定义的三级回滚策略：
- **层级 A**：产物级回滚（Git checkout 历史版本）
- **层级 B**：数据库级回滚（SQLite 备份替换 / PostgreSQL 回滚脚本）
- **层级 C**：项目级回滚（整体 Git reset + 状态重置）

---

## 6. 代码风格指南

### 6.1 Python（后端）

项目使用 `ruff` + `mypy` 进行代码质量管控，配置位于 `backend/pyproject.toml`：

- **行宽**：100 字符（`tool.ruff.line-length = 100`）
- **目标版本**：Python 3.11（`target-version = "py311"`）
- **Lint 规则**：E, F, I, N, W, UP, B, C4, SIM（忽略 E501，因行宽已单独设定）
- **Docstring 规范**：Google Style（`tool.ruff.lint.pydocstyle.convention = "google"`）
- **类型检查**：mypy strict 模式（`strict = true`）

生成 Python 代码时，应调用 `python-google-style` Skill，遵循 Google Python Style Guide（4 空格缩进、类型注解、Google docstring）。

### 6.2 TypeScript / React（前端）

- 使用 TypeScript 5.6，严格类型检查由 `tsconfig.app.json` 控制
- React 函数组件优先，使用 Hooks 管理状态
- 状态管理使用 Zustand（避免过度使用 Context）
- HTTP 请求封装在 `src/services/`
- 页面组件置于 `src/pages/{PageName}/`

---

## 7. 安全考量

1. **禁止 AI 自动执行高危操作**
   - `release-management`：AI 只生成文档，上线按钮必须由人按。
   - `finish`：必须收到用户输入"确认归档"或同等明确信号后方可执行。
   - `workflow-automation-agent`：涉及文件删除、数据覆盖、外部 API 调用（邮件、付款）的步骤，默认设为"人工确认"。

2. **代码审查角色隔离**
   - `code-reviewer` 必须跳出实现者视角，在无 subagent 环境下通过会话内角色轮替完成多轮审查。禁止为代码辩护或假设作者有未说明的好理由。

3. **无密钥硬编码**
   - `self-check` 强制检查：产出物中不得出现硬编码密钥、Token、密码。
   - `backend/main.py` 中 CORS `allow_origins` 当前仅开放 `http://localhost:5173`，生产环境必须收紧。

4. **回滚就绪**
   - 每个变更必须产出 `rollback-plan.md`，含回滚触发条件、步骤、数据库回滚脚本清单、灰度策略。
   - 优先新增文件（易回滚），DB 迁移需配套回滚脚本。

5. **数据安全**
   - `openspec/config.yaml` 中的占位符、`ops/staging-config.yaml` 中的 `{连接串}`、`ops/monitoring-rules.yaml` 中的 `{PAGERDUTY_SERVICE_KEY}` / `{SLACK_OPS_WEBHOOK_URL}` 均为占位符，**禁止填入真实凭证**。
   - MVP 阶段 SQLite 数据库文件位于 `data/sdlc-visualizer.db`，需确保 `.gitignore` 排除数据库文件与备份文件。

---

## 8. 修改与扩展指南

### 8.1 新增 Skill

1. 在 `.agents/skills/` 下创建目录 `{skill-name}/`。
2. 编写 `SKILL.md`，首行为 YAML Frontmatter，包含准确的 `name` 和触发条件 `description`。
3. 编写 `meta.json`，声明 `version`、`pattern`、`tags`、`platforms`。
4. 如有参考资料，放入 `references/`；如有示例，放入 `examples/`；如有脚本，放入 `scripts/`。
5. 在 `AGENTS.md` 的 Skill 列表中补充新 Skill 的说明（即更新本文件）。
6. 若新 Skill 需要产出 OpenSpec 产物，检查 `openspec/config.yaml` 中对应阶段的 `artifact` 与 `gate_to_next` 规则是否已覆盖。

### 8.2 修改现有 Skill

- **禁止破坏下游契约**：修改 `SKILL.md` 中的步骤、输出格式或文件路径时，必须检查所有引用该 Skill 的上游/下游 Skill，确保衔接点一致。
- **版本管理**：`meta.json` 中的 `version` 应遵循语义化版本。重大变更需升级主版本号。
- **最小变更原则**：遵循本项目自身的 `executing-plans` 纪律——每个增量只改一个逻辑事物，禁止顺手重构相邻文件。

### 8.3 前后端应用开发

- 后端新增业务模块时，按 `api/` → `schemas/` → `services/` → `models/` 顺序填充，保持分层清晰。
- 前端新增页面时，在 `src/pages/` 下创建目录，路由配置由 `App.tsx` 或路由组件统一管理。
- 前后端接口变更必须先更新 `interface-contracts/openapi.yaml`，遵循 "先契约、后编码" 原则（`interface-first-dev` Skill）。

### 8.4 OpenSpec 配置调整

`openspec/config.yaml` 是项目级规范模板，修改其 `artifact_specs.*.required_sections` 或 `gate_to_next` 规则时，需同步检查所有依赖该配置的生成类 Skill（如 `prd-generation`、`high-level-design`、`progress-tracker`）。

---

## 9. 关键文件速查

| 文件 | 作用 |
|------|------|
| `openspec/config.yaml` | 全局规范：阶段定义、产出物规格、门控规则、Red Flags、进度上限 |
| `.agents/skills/{name}/SKILL.md` | Skill 主定义 |
| `.agents/skills/{name}/meta.json` | Skill 元数据、版本与平台兼容性 |
| `backend/pyproject.toml` | Python 后端：依赖、构建、ruff/mypy/pytest 配置 |
| `backend/main.py` | FastAPI 应用入口 |
| `frontend/package.json` | 前端依赖与 npm 脚本 |
| `frontend/vite.config.ts` | Vite 配置：开发服务器端口、后端代理规则 |
| `ops/monitoring-rules.yaml` | 监控规则骨架（基础设施/应用/前端/业务/安全/可观测性） |
| `ops/rollback-plan.md` | 回滚方案模板（三级回滚策略） |
| `ops/staging-config.yaml` | 预发布环境配置模板 |
| `docs/AI_Code_v3.2.md` | 平台自身的产品需求文档（PRD，当前基线 v3.3） |
| `openspec/changes/sdlc-visualizer/progress.md` | 当前活跃变更的 SSOT 进度 |
| `openspec/changes/sdlc-visualizer/human-decisions.md` | 当前活跃变更的人工决策审计日志 |
