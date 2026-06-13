---
doc_type: ARCH
fragment_id: arch-sdlc-visualizer-000
title: 设计总览
version: 1.0.0
version_type: BASELINE
author: agent-migration
tags:
- sdlc-visualizer
- architecture
status: DRAFT
iteration: sdlc-visualizer
dependencies:
- fragment_id: prd-sdlc-visualizer-000
  version: 2.0-patch2
c4_binding:
  level: L2
---

# 设计总览


> **C4 绑定引用**：
> - `@C4-L1-System:git`
> - `@C4-L1-System:kimi-cli`
> - `@C4-L1-System:local-filesystem`
> - `@C4-L1-System:openui-service`
> - `@C4-L1-System:sdlc-visualizer`
> - `@C4-L2-Container:artifact-store`
> - `@C4-L2-Container:backend-api`
> - `@C4-L2-Container:frontend-spa`
> - `@C4-L2-Container:kimi-cli-process`
> - `@C4-L2-Container:openui-docker`
> - `@C4-L2-Container:sqlite-db`
> - `@C4-L2-Container:wireframe-engine`

---

## 1. 引言 {#sec-1-yinu8a00}
### 1.1 目的 {#sec-11-mude}
本文档为 SDLC Visualizer（Arsitect 可视化驾驶舱）的概要设计总览，定义系统级架构决策、技术选型、数据流、运行时行为、质量属性与运维治理策略。本文档覆盖影响 ≥2 个模块的架构决策，不涉及模块内部类设计、接口字段定义、数据库 DDL 或算法参数配置。

### 1.2 范围 {#sec-12-fanwei}
| In-Scope | Out-of-Scope |
|----------|--------------|
| 系统分层与服务划分 | 模块内部类图/函数签名 |
| 技术栈选型与版本约束 | 具体 ORM 映射配置 |
| 全局状态机与跨模块数据流 | 单接口请求/响应 Schema |
| 部署拓扑与运维架构 | 缓存 Key 设计与过期策略 |
| 安全策略与性能基线 | 单测用例与 Mock 策略 |
| 回滚方案与治理规则 | Dashboard JSON 配置 |

### 1.3 术语与缩写 {#sec-13-u672fu8bedyusuou5199}
| 术语 | 定义 | 来源 |
|------|------|------|
| **Arsitect** | AI 驱动软件工程全生命周期管理平台 | PRD-000 |
| **SDLC Visualizer** | Arsitect 的可视化驾驶舱，管理 AI Skill 执行过程 | PRD-000 |
| **Skill** | AI 能力单元，由 SKILL.md + meta.json 定义 | PRD-000 |
| **Stage** | 软件交付标准阶段（需求探索→监控分析共 12 阶段） | PRD-000 |
| **PocketFlow** | Skill 执行三阶段生命周期：prep → exec → post | PRD-000 |
| **Gate** | 人工审批节点，共四道（Gate-1/2.5/2/3） | PRD-000 |
| **HITL** | Human-in-the-Loop，人工参与关键决策 | PRD-000 |
| **Artifact** | Skill 执行生成的产物文件 | PRD-000 |
| **复杂度路由** | 基于五维度规模评估的 Trivial/Light/Standard/Deep 路径推荐 | PRD-000 |
| **C4** | C4 模型（Context/Container/Component/Code） | PRD-000 |
| **OpenUI** | 可选的前端原型渲染服务（Docker HTTP API） | PRD-000 |
| **WireframeEngine** | 领域感知线框图生成引擎 | PRD-000 |
| **SSE** | Server-Sent Events，服务端单向推送 | design-input.md |
| **MCP** | Model Context Protocol，预留的多平台适配协议 | PRD-000 |

> **BLOCKER 检查**：术语表与 `high-level-requirements/01-requirements-list.md` 第 2 节严格一致，无冲突。

### 1.4 参考资料 {#sec-14-u53c2u8003u8d44u6599}
| 编号 | 文档 | 版本 | 用途 |
|------|------|------|------|
| REF-001 | `high-level-requirements/00-requirements-overview.md` | v2.0-patch2 | 产品范围、NFR、里程碑 |
| REF-002 | `high-level-requirements/01-requirements-list.md` | v2.0-patch2 | 需求清单、业务规则、RTM |
| REF-003 | `high-level-requirements/02-functional-requirements.md` | v2.0-patch2 | 模块清单、状态机、用户旅程 |
| REF-004 | `competitive-analysis.md` | v1.0 | 技术选型论证支撑 |
| REF-005 | `design-input.md` | v1.0 | 组件选型评分、架构模式参考 |
| REF-006 | `detailed-requirements/feature-*/module-requirements.md` | DR-001~DR-021 | 模块功能细节（覆盖度校验） |
| REF-007 | `openspec/config.yaml` | v2.1 | 阶段定义与门控规则 |

---

## 2. 设计考量 {#sec-2-shejiu8003liang}
### 2.1 假设 {#sec-21-u5047she}
| 编号 | 假设描述 | 影响域 | 置信度 |
|------|----------|--------|--------|
| ASM-HLD-001 | 目标用户本地已安装 Kimi CLI 且可正常执行 | Skill 调度层 | 高 |
| ASM-HLD-002 | 用户工作站具备运行 Node.js 18+ 和 Python 3.10+ 的环境 | 技术栈选型 | 高 |
| ASM-HLD-003 | 产物文件（Markdown/YAML/JSON）体积 < 10MB，适合内存渲染 | 产物服务 | 中 |
| ASM-HLD-004 | 本地文件系统性能满足 SQLite 单连接读写（无高并发） | 存储层 | 高 |
| ASM-HLD-005 | OpenUI Docker 服务为可选依赖，不影响核心链路闭环 | 原型验证层 | 中 |
| ASM-HLD-006 | 浏览器为 Chrome/Edge/Firefox/Safari 最新 2 个主版本 | 前端兼容 | 高 |

### 2.2 约束 {#sec-22-yueshu}
| 类别 | 约束描述 | 来源 |
|------|----------|------|
| **技术** | MVP 仅支持 Kimi CLI，Adapter 层预留多平台接口（NG-004） | PRD Non-goals |
| **技术** | 本地单机部署，零运维，10 Project 上限 | PRD 技术约束 |
| **技术** | 前端通过浏览器访问 localhost，非 Electron | 用户决策（问题 4-A） |
| **技术** | C4 架构浏览器自研渲染，不依赖 C4 InterFlow CLI（NG-010） | 用户决策（问题 2-A） |
| **技术** | OpenHands 彻底排除，执行器层仅 Kimi CLI | 用户决策（问题 1-A） |
| **业务** | 产物存储兼容 `openspec/changes/{change}/` 目录结构 | PRD 技术约束 |
| **预算** | MVP 周期 W1-W10，2-3 人团队 | PRD 里程碑 |
| **合规** | 所有数据本地存储，不上传云端 | PRD 安全需求 |

### 2.3 依赖 {#sec-23-yiu8d56}
| 依赖项            | 类型       | 版本/范围  | 用途             | 缺失影响               |
| -------------- | -------- | ------ | -------------- | ------------------ |
| Kimi CLI       | 外部工具     | 最新稳定版  | Skill 执行引擎     | 核心功能不可用            |
| Git            | 外部工具     | 2.30+  | 产物快照与版本管理      | Git 快照功能不可用        |
| Node.js        | 运行时      | 18+    | 前端构建 + 后端文件服务  | 前端无法启动             |
| Python         | 运行时      | 3.10+  | FastAPI 后端     | 后端无法启动             |
| OpenUI Docker  | 外部服务（可选） | 最新镜像   | 高保真原型渲染        | 降级为 Wireframe 静态预览 |
| React Flow 12  | 前端库      | ^12.0  | SDLC 拓扑画布      | 核心可视化不可用           |
| FastAPI 0.115  | 后端框架     | ^0.115 | REST API + SSE | 后端服务不可用            |
| SQLAlchemy 2.0 | ORM      | ^2.0   | 数据库访问层         | 数据持久化不可用           |

### 2.4 风险 {#sec-24-fengxian}
| 风险 ID | 描述 | 等级 | 缓解策略 |
|---------|------|------|----------|
| R-HLD-001 | React Flow 12 与 React 19 兼容性边缘 case 导致画布异常 | **高** | 锁定 React Flow 12.4+（明确支持 React 19）；W1 建立画布冒烟测试；预留降级为列表视图 |
| R-HLD-002 | Kimi CLI 输出格式不稳定，JSON Lines 解析失败 | **高** | 实现多级解析 fallback（结构化 JSON → 正则提取 → 原始文本）；解析失败时标记 BLOCKED 并保留原始日志 |
| R-HLD-003 | SQLite WAL 锁竞争导致 API 500 错误 | **中** | 单 worker FastAPI 部署（uvicorn --workers 1）；写操作队列化；预留 aiosqlite 连接池 |
| R-HLD-004 | Zustand 前端状态与后端 SSE 推送漂移 | **中** | 每次 SSE 重连时全量同步；关键操作（Gate 提交）后主动拉取状态校验；页面刷新从后端恢复 |
| R-HLD-005 | Draft → Active 状态迁移涉及产物路径固化，设计不当导致数据丢失 | **中** | 迁移前自动创建 Git 快照；迁移操作可回滚；迁移日志写入 human-decisions.md |
| R-HLD-006 | OpenUI Docker 未启动时用户困惑 | **低** | 启动时检测 OpenUI 健康状态；未启动时显式提示并提供 Wireframe 降级；一键启动脚本 |
| R-HLD-007 | 10 Project 上限 + 完整 Git 历史导致存储膨胀 | **低** | 单 Project > 1GB 时预警；提供一键归档压缩；大文件（>10MB）不纳入 Git 快照 |
| R-HLD-008 | C4 L3/L4 自动生成准确率不足（基于概要设计文档推断） | **中** | 允许用户手动覆盖；准确率 < 60% 时降级为仅 L1/L2；标记自动生成置信度 |

---

## 3. 设计索引与检查清单 {#sec-3-shejisuoyinyujianchau6e05dan}
| 主题文件 | 核心决策点 | 风险等级 | 检查状态 |
|---------|-----------|---------|---------|
| 01-architecture-core.md | 分层策略、技术选型、目录结构 | 高 | ☐ |
| 02-data-flow.md | 存储选型、接口模式、模块边界 | 高 | ☐ |
| 03-runtime-behavior.md | 状态流转、核心链路、错误处理 | 高 | ☐ |
| 04-quality-attributes.md | 安全方案、性能基线、部署拓扑 | 中 | ☐ |
| 05-ops-governance.md | 监控覆盖、回滚可操作性 | 高 | ☐ |

---

## 4. 跨文件一致性重点 {#sec-4-u8de8wenjianyiu81f4xingchongu7}
> 源自 `self-check-report.md`，检查者重点确认以下项：

| 检查项 | 涉及文件 | 结论等级 | 说明 |
|--------|---------|---------|------|
| 技术栈覆盖度 | 01 ↔ 02 | ✅ | FastAPI + SQLAlchemy 覆盖全部存储与接口需求 |
| 架构-目录一致性 | 01（系统架构 vs 项目结构） | ✅ | self-check-report.md 已验证：五层架构与目录树一一对应 |
| 状态机-模块职责兼容性 | 03 ↔ 02 | ✅ | 全局状态机中的每个状态在模块职责中均有处理方 |
| 异常-回滚联动 | 03 ↔ 05 | ✅ | 异常处理中标记"触发回滚"的类别在回滚方案中有对应步骤 |
| 性能-部署匹配 | 04（性能 vs 部署） | ✅ | 单进程 SQLite 部署满足 < 200ms P95 查询目标 |
| 安全-接口契约一致性 | 04 ↔ 02 | ✅ | 本地单机免认证策略与 REST API 通信模式兼容 |
| ADR 溯源 | 01 ↔ competitive-analysis.md | ✅ | 每个 ADR 均可在竞品分析中找到支撑 |

---

## 5. Gate 2 评审签字区 {#sec-5-gate-2-pingshenqianu5b57u533a}
- [ ] 技术选型符合团队能力栈（React 19 / FastAPI / SQLite）
- [ ] 数据流与部署架构满足 NFR（首屏 < 2s、拓扑 60fps、状态同步 < 5s）
- [ ] 全局状态机与模块职责兼容（21 个模块全部覆盖）
- [ ] 回滚步骤可操作（产物 Git 回滚 + 数据库备份恢复）
- [ ] 告警策略覆盖核心链路（Gate 超时、执行失败、存储膨胀）
- [ ] 目录分层与架构分层一致（frontend ↔ Web Container / backend ↔ API Container）

**评审人**：________ **日期**：________

---

### 需求可追溯性 {#sec-xuqiuu53efzhuiu6eafxing}
| 需求编号 | 需求描述 | 本文件对应章节 | 验证方式 |
|---------|----------|-------------|---------|
| REQ-P0-001 | 项目 CRUD，Draft/Active/Archived 状态流转 | §2.2 约束 | 架构评审 |
| REQ-P0-022 | 项目健康度卡片 | §2.4 风险表 | 架构评审 |
| REQ-P0-023 | 风险预警 | §2.4 风险表 | 架构评审 |
| ASM-001~009 | 假设登记册 | §2.1 假设 | 架构评审 |
| R-001~R-011 | 风险与缓解 | §2.4 风险 | 架构评审 |
| NG-001~NG-010 | Non-goals 边界 | §1.2 范围 | 架构评审 |

---

## 附录：历史补充内容（来自 docs/ 目录） {#sec-u9644luu5386u53f2u8865u5145u5185}
本文档为 SDLC Visualizer（Arsitect 可视化驾驶舱）的概要设计总览，定义系统级架构决策、数据流、运行时行为、质量属性与运维治理方案。本文档面向技术负责人、架构师与核心开发者，作为详细设计（detailed-design）的前置基线。

- **In-Scope**：系统分层策略、技术栈选型、模块职责边界、数据架构、全局状态机、核心链路时序、非功能需求策略、运维监控与回滚方案。
- **Out-of-Scope**：单模块内部类设计、接口字段定义、数据库 DDL、算法参数、Prompt 模板、具体测试用例、Dashboard JSON 配置。

> 与 `high-level-requirements/01-requirements-list.md` 第 2 节术语表严格保持一致。

| 术语 | 定义 |
|------|------|
| **Arsitect** | AI 驱动软件工程全生命周期管理平台 |
| **Skill** | AI 能力单元，由 SKILL.md + meta.json 定义 |
| **Stage** | 软件交付标准阶段，可绑定 0-n 个 Skill |
| **Gate** | 人工审批节点，共四道（1/2.5/2/3） |
| **Draft/Active** | 项目双态：预立项 Draft 与正式执行 Active |
| **HITL** | Human-in-the-Loop，人工参与关键决策 |
| **产物（Artifact）** | Skill 执行生成的文件（Markdown/YAML/JSON 等） |
| **拓扑图** | SDLC 流程画布，以 Skill 为节点、依赖为连线 |
| **超级个体** | 独立开发者或全栈自由职业者 |

| 文档 | 路径 | 用途 |
|------|------|------|
| PRD-000 v1.1-draft | `high-level-requirements/00-02.md` | 需求基线 |
| 技术深度竞品分析 | `competitive-analysis/competitive-analysis.md` | 技术选型论证 |
| 设计输入 | `competitive-analysis/design-input.md` | 技术选型约束与评分 |
| 详细需求 | `detailed-requirements/feature-*/module-requirements.md` | 模块级校验基准 |
| OpenSpec 配置 | `openspec/config.yaml` | 阶段定义与门控规则 |

| 假设 ID | 假设内容 | 置信度 | 若推翻的 Plan B |
|---------|----------|--------|-----------------|
| A-001 | 目标用户本地已安装 Kimi CLI 且可正常执行 | 高 | 平台提供安装引导 + 版本检测 + 降级为手动模式 |
| A-002 | Skill 产物单文件 < 10MB | 中 | 产物分页加载 + 大文件警告 + 可选外部编辑器打开 |
| A-003 | 用户愿意手动注册/导入 Skill 路径 | 高 | 增加"最近使用"快捷导入 + 目录批量扫描向导 |
| A-004 | 本地 CLI 调用可通过 stdout/stderr + 产物目录轮询获取足够实时状态 | 中 | 引入文件系统事件监听（watchdog）或 CLI 进度输出协议 |
| A-005 | SQLite 在单用户场景下可支撑 10 活跃项目 + 历史数据查询 | 高 | P1 提前迁移至 PostgreSQL |
| A-006 | 超级个体的 Gate 审批可在 30 秒内完成 | 中 | 提供"快速通过"和"深度检查"两种模式 |

| 约束类型 | 约束内容 | 来源 |
|---------|---------|------|
| 技术约束 | MVP 必须封装 Kimi CLI 命令，依赖本地预装 Kimi 客户端 | PRD &sect;10 |
| 技术约束 | Skill 遵循 SKILL.md（YAML Frontmatter）+ meta.json 规范 | PRD &sect;10 |
| 部署约束 | MVP 为单实例本地部署，不依赖外部 SaaS | PRD &sect;10 |
| 合规约束 | 产物数据存储于用户本地，不上传至第三方云 | PRD &sect;11.2 |
| 安全约束 | AI 禁止自动执行 release-management / finish | BR-010 |
| 性能约束 | 首屏 < 2s、拓扑图 &ge; 60fps、产物渲染 < 500ms、状态同步 < 5s | NFR |

| 依赖项 | 版本/规格 | 用途 | 替代方案 |
|--------|----------|------|---------|
| Kimi CLI | 最新稳定版 | AI 执行引擎 | 无（MVP 唯一绑定） |
| Node.js | 20+ | 前端运行时 | 无 |
| Python | 3.11+ | 后端运行时 | 无 |
| React Flow 12 | ^12.0.0 | 画布引擎 | AntV X6（备选） |
| FastAPI 0.115 | ^0.115.0 | API 框架 | Django-Ninja（不推荐） |
| SQLite | 3.39+ | MVP 数据库 | PostgreSQL 15+（P1+） |

| 风险 ID | 描述 | 级别 | 缓解策略 |
|---------|------|------|----------|
| R-001 | Kimi CLI 进程级执行难以提供实时中间状态，导致画布"假死"感 | 高 | 三级伪状态 + 产物目录实时监听 + 预期耗时显示 + 实时日志面板 |
| R-002 | SQLite 频繁写入成为性能瓶颈 | 中 | 日志批量写入 + 状态变更 debounce + 预留 PostgreSQL 迁移路径 |
| R-003 | Skill YAML 格式不统一导致节点无法渲染 | 中 | 前置校验 + 容错渲染（缺失字段显示默认值 + 警告提示） |
| R-004 | 超级个体对"四道 Gate"产生流程负担 | 中 | Gate UI 极简设计（一键确认+风险提示折叠）+ 允许关闭非关键 Gate |
| R-005 | Jira/Dify 等竞品推出原生 AI SDLC 可视化功能 | 中 | 聚焦"Arsitect 生态深度兼容 + 本地私有化"差异化 |
| R-006 | 产物文件与数据库状态不一致 | 低 | 产物文件哈希校验 + 手动刷新按钮 + 文件系统事件监听 |
| R-007 | React Flow 12 在 50+ 节点场景下性能不足 | 中 | 预研虚拟滚动 + 节点懒加载，或降级为列表视图 |
| R-008 | SQLite 并发写入 WAL 锁等待 | 低 | WAL 模式 + 写操作序列化 + P1 前完成 PostgreSQL 迁移方案设计 |

| 主题文件 | 核心决策点 | 风险等级 | 检查状态 |
|---------|-----------|---------|---------|
| 01-architecture-core.md | 分层策略、技术选型、目录结构、3 个 ADR | 高 | ☐ |
| 02-data-flow.md | 存储选型、接口模式、模块边界、ER 图 | 高 | ☐ |
| 03-runtime-behavior.md | 状态流转、核心链路、错误处理、算法选型 | 高 | ☐ |
| 04-quality-attributes.md | 安全方案、性能基线、部署拓扑、测试策略 | 中 | ☐ |
| 05-ops-governance.md | 监控覆盖、回滚可操作性、治理规则 | 高 | ☐ |

> 以下警告项源自 `self-check-report.md`，检查者在此重点确认。

### ⚠️ WARN-1：产物监听依赖未显式列入技术栈清单 {#sec-warn1chanu7269jianu542cyiu8d56we}
- **位置**：03-runtime-behavior.md &sect;2.1 / 04-quality-attributes.md &sect;2.3
- **问题**：`watchdog` / `inotify` / `aiofiles` 未在 01-architecture-core.md &sect;2.1 技术栈清单中列出。
- **确认要点**：是否在详细设计阶段补充产物监听库选型？

### ⚠️ WARN-2：回滚脚本清单与数据库表结构存在隐含依赖 {#sec-warn2huigunu811abenu6e05danyushu}
- **位置**：05-ops-governance.md &sect;2.3
- **问题**：`rollback-stage-instance.sql` 提到"恢复 gate_decisions 字段"，但 02-data-flow.md &sect;1.4 核心表清单中未定义该字段（仅有 `hitl_record` 表）。
- **确认要点**：Gate 审批状态是否独立存储于 `hitl_record` 表？回滚脚本术语是否与详细设计后的表结构一致？

### ⚠️ WARN-3：HTTPS 演进与 API 版本策略的兼容性未明确 {#sec-warn3https-u6f14jinyu-api-banben}
- **位置**：04-quality-attributes.md &sect;1.1 / 02-data-flow.md &sect;2.2
- **问题**：P1+ HTTPS 引入后，WebSocket 协议从 `ws://` 切换为 `wss://`，前端协议配置策略未说明。
- **确认要点**：是否在详细设计阶段补充协议自适应策略（开发环境 HTTP/WS，生产环境 HTTPS/WSS）？

- [ ] 技术选型符合团队能力栈（React 19 / Vite 6 / FastAPI / SQLite）
- [ ] 数据流与部署架构满足 NFR（首屏 < 2s、拓扑图 &ge; 60fps、状态同步 < 5s）
- [ ] 全局状态机与模块职责兼容（Project / Stage / SkillExecution 三层状态均有处理方）
- [ ] 回滚步骤可操作（代码 &rarr; 配置 &rarr; 数据三级回滚，每级含验证检查点）
- [ ] 告警策略覆盖核心链路（P0：崩溃/哈希失败；P1：性能劣化；P2：到期预警）
- [ ] 目录分层与架构分层一致（4 层架构对应 14 个目录，无悬空）
- [ ] 跨文件一致性警告已审阅并同意在详细设计阶段闭环（WARN-1/2/3）
- [ ] 3 个 ADR 均有竞品分析支撑（ADR-001/002/003）

评审人：________ 日期：________

## 6. 需求可追溯性 {#sec-6-xuqiuu53efzhuiu6eafxing}
| 需求编号 | 需求描述 | 本文件对应章节 | 验证方式 |
|---------|---------|-------------|---------|
| REQ-P0-001 ~ REQ-P0-024 | 全部 P0 需求架构覆盖 | &sect;3 设计索引 | 逐条映射至 01-05 主题文件 |
| NFR-001 ~ NFR-008 | 非功能需求架构支撑 | &sect;2.2 约束 / &sect;2.4 风险 | 评审 |
| BR-001 ~ BR-023 | 业务规则与架构兼容 | &sect;2.2 约束 | 评审 |
