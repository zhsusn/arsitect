---
doc_type: DB_DESIGN
fragment_id: db-design-sdlc-visualizer-shared-607
title: shared/db-schema.md — 公共数据表定义
version: 1.0.0
version_type: BASELINE
author: agent-migration
tags:
- sdlc-visualizer
- architecture
status: DRAFT
iteration: sdlc-visualizer
dependencies:
- fragment_id: arch-sdlc-visualizer-001
  version: '1.0'
- fragment_id: arch-sdlc-visualizer-002
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat01-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat03-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat04-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat05-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat06-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat07-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat08-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat09-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat10-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat11-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat12-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat13-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat14-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat15-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat18-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat19-628
  version: 1.0.0
- fragment_id: detail-design-sdlc-visualizer-feat20-628
  version: 1.0.0
c4_binding:
  level: L2
---

# shared/db-schema.md — 公共数据表定义


> **C4 绑定引用**：
> - `@C4-L1-System:git`
> - `@C4-L2-Container:skill-orchestrator`
> - `@C4-L2-Container:sqlite-db`
> - `@C4-L2-Container:wireframe-engine`

> **说明**：本文件包含被 ≥2 个模块依赖的公共数据表。模块级 `module-design.md` 中对这些表的引用通过本文件实现，禁止在模块目录内重复定义 DDL。
>
> **提取批次**：第一批~第五批详细设计完成后统一提取（2026-06-02）。
> **维护规则**：新增公共表需经 Cross-Module Audit 确认 ≥2 模块引用后方可加入本文件。

---

## 1. workspaces — 工作区表 {#sec-1-workspaces-gongu4f5cu533abiao}
**定义批次**：第一批（GAP-002 预定义）
**归属模块**：全局基础设施（MVP 单例）
**被依赖模块**：DR-015（Application 治理）
**写方**：全局基础设施初始化脚本
**读方**：DR-015

```sql
CREATE TABLE workspaces (
    workspace_id        VARCHAR(36) PRIMARY KEY DEFAULT 'default',
    workspace_name      VARCHAR(100) NOT NULL DEFAULT 'Default Workspace',
    description         VARCHAR(256),
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- MVP 预置单条记录
-- INSERT INTO workspaces (workspace_id, workspace_name) VALUES ('default', 'Default Workspace');
```

> **设计说明**：
> - MVP 阶段 Workspace 为本地单机默认单例，固定 `workspace_id = 'default'`。
> - P1 阶段如需支持多 Workspace，将 `workspace_id` 从默认值改为动态生成，并在 `applications` 等表上增加外键约束。

---

## 2. size_estimates — 项目规模评估表 {#sec-2-sizeestimates-u9879muguimoping}
**定义批次**：第一批（GAP-001 预定义），第四批完善
**归属模块**：DR-010 复杂度路由面板
**被依赖模块**：DR-001（项目工作台，`projects.size_estimate_id` 外键）
**写方**：DR-010
**读方**：DR-001

```sql
CREATE TABLE size_estimates (
    estimate_id         VARCHAR(36) PRIMARY KEY,
    project_id          VARCHAR(36) NOT NULL,
    module_count        INTEGER NOT NULL CHECK (module_count BETWEEN 1 AND 50),
    interface_count     INTEGER NOT NULL DEFAULT 0 CHECK (interface_count BETWEEN 0 AND 100),
    page_count          INTEGER NOT NULL DEFAULT 0 CHECK (page_count BETWEEN 0 AND 50),
    tech_complexity     VARCHAR(16) NOT NULL CHECK (tech_complexity IN ('Low', 'Medium', 'High')),
    risk_level          VARCHAR(16) NOT NULL CHECK (risk_level IN ('Low', 'Medium', 'High')),
    optimistic_score    INTEGER,                         -- 乐观得分
    expected_score      INTEGER,                         -- 预期得分
    conservative_score  INTEGER,                         -- 保守得分
    complexity_level    VARCHAR(16) CHECK (complexity_level IN ('Trivial', 'Light', 'Standard', 'Deep')),
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_estimate_project FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE INDEX idx_estimates_project ON size_estimates(project_id);
```

> **设计说明**：
> - `complexity_level` 为评估输出结果，与 `templates.template_id` 枚举值对齐。
> - 三档得分（optimistic / expected / conservative）为 `project-size-estimate` Skill 的标准输出。

---

## 3. applications — Application 主表 {#sec-3-applications-application-u4e3b}
**定义批次**：第一批
**归属模块**：DR-015 Application 与模块治理
**被依赖模块**：DR-001（项目工作台，项目选择器）
**写方**：DR-015
**读方**：DR-001, DR-013

```sql
CREATE TABLE applications (
    application_id      VARCHAR(36) PRIMARY KEY,
    application_name    VARCHAR(100) NOT NULL,
    description         VARCHAR(500),
    local_path          VARCHAR(4096) NOT NULL,
    workspace_id        VARCHAR(36) NOT NULL DEFAULT 'default',
    path_accessible     BOOLEAN NOT NULL DEFAULT TRUE,
    last_active_at      TIMESTAMP,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_app_name_per_ws UNIQUE (workspace_id, application_name)
);

CREATE INDEX idx_applications_ws ON applications(workspace_id);
CREATE INDEX idx_applications_name ON applications(application_name);
```

---

## 4. projects — 项目主表 {#sec-4-projects-u9879muu4e3bbiao}
**定义批次**：第一批
**归属模块**：DR-001 项目工作台
**被依赖模块**：DR-009（模板引擎）、DR-015（Application 治理）、DR-003/005/007/008/012/013/014 等
**写方**：DR-001
**读方**：DR-003, DR-004, DR-005, DR-007, DR-009, DR-012, DR-013, DR-014, DR-015

```sql
CREATE TABLE projects (
    project_id          VARCHAR(36) PRIMARY KEY,        -- UUID v4
    project_name        VARCHAR(64) NOT NULL,
    project_description VARCHAR(256),
    project_status      VARCHAR(16) NOT NULL DEFAULT 'Draft'
                        CHECK (project_status IN ('Draft', 'Active', 'Archived', 'Cancelled')),
    application_id      VARCHAR(36) NOT NULL,
    template_level      VARCHAR(16) NOT NULL
                        CHECK (template_level IN ('Trivial', 'Light', 'Standard', 'Deep')),
    progress_percent    INTEGER NOT NULL DEFAULT 0
                        CHECK (progress_percent BETWEEN 0 AND 100),
    current_stage       VARCHAR(32),                     -- 当前阶段名称
    risk_level          VARCHAR(16) DEFAULT 'None'
                        CHECK (risk_level IN ('None', 'Low', 'Medium', 'High')),
    last_activity_at    TIMESTAMP,
    last_activity_type  VARCHAR(32),
    size_estimate_id    VARCHAR(36),                     -- 关联 size_estimates 表
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_project_name_per_app UNIQUE (application_id, project_name, project_status)
);

CREATE INDEX idx_projects_app_id ON projects(application_id);
CREATE INDEX idx_projects_status ON projects(project_status);
CREATE INDEX idx_projects_risk ON projects(risk_level);
CREATE INDEX idx_projects_updated ON projects(updated_at DESC);
```

> **设计说明**：
> - 重名校验在应用层实现：同一 `application_id` 下，`project_status` 为 `Active`/`Draft`/`Cancelled` 时，`project_name` 大小写不敏感唯一。
> - SQLite 不支持条件唯一索引，`idx_projects_risk` 为普通索引，PostgreSQL 迁移后可改为部分索引。

---

## 5. skills — Skill 注册表 {#sec-5-skills-skill-zhucebiao}
**定义批次**：第一批
**归属模块**：DR-006 Skill 注册与 DAG 管理
**被依赖模块**：DR-009（模板引擎 Stage-Skill 绑定展示）
**写方**：DR-006
**读方**：DR-009

```sql
CREATE TABLE skills (
    skill_id            VARCHAR(36) PRIMARY KEY,        -- UUID v4
    skill_name          VARCHAR(128) NOT NULL,
    version             VARCHAR(32) NOT NULL,
    pattern             VARCHAR(32) NOT NULL
                        CHECK (pattern IN ('generator', 'pipeline', 'reviewer', 'analyzer', 'inversion', 'tool-wrapper')),
    tags                TEXT,                            -- JSON 数组序列化
    platforms           TEXT,                            -- JSON 数组序列化
    description         VARCHAR(512),
    directory_path      VARCHAR(4096) NOT NULL,          -- Skill 所在本地绝对路径
    parse_status        VARCHAR(32) NOT NULL DEFAULT 'PARSED'
                        CHECK (parse_status IN ('PARSED', 'MANUAL_REQUIRED')),
    parse_error_reason  VARCHAR(256),                    -- MANUAL_REQUIRED 时的错误描述
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_skill_name_version UNIQUE (skill_name, version)
);

CREATE INDEX idx_skills_name ON skills(skill_name);
CREATE INDEX idx_skills_pattern ON skills(pattern);
CREATE INDEX idx_skills_status ON skills(parse_status);
```

> **设计说明**：
> - `tags` 和 `platforms` 使用 JSON 文本序列化存储；PostgreSQL 迁移后可改为 `JSONB`。
> - `directory_path` 用于快速定位 Skill 文件，支持"查看 SKILL.md"功能。

---

## 6. templates — 模板主表 {#sec-6-templates-mobanu4e3bbiao}
**定义批次**：第一批
**归属模块**：DR-009 模板引擎
**被依赖模块**：DR-001（项目工作台，模板绑定）、DR-015（模块治理）
**写方**：DR-009（系统预置，MVP 用户不可编辑）
**读方**：DR-001, DR-010, DR-015

```sql
CREATE TABLE templates (
    template_id         VARCHAR(16) PRIMARY KEY
                        CHECK (template_id IN ('Trivial', 'Light', 'Standard', 'Deep')),
    template_name       VARCHAR(64) NOT NULL,
    description         VARCHAR(256) NOT NULL,
    stage_count         INTEGER NOT NULL,
    estimated_skill_count INTEGER NOT NULL,
    applicable_complexity VARCHAR(16) NOT NULL,
    config_json         TEXT NOT NULL,                   -- 模板完整配置 JSON
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- MVP 预置数据（4 条）
-- INSERT INTO templates (...) VALUES ('Trivial', ...), ('Light', ...), ('Standard', ...), ('Deep', ...);
```

> **设计说明**：
> - MVP 阶段模板为系统预置，用户不可增删改。`config_json` 存储完整的模板配置。
> - P1 阶段如需支持自定义模板，可增加 `is_system` 标记字段。

---

## 7. template_stages — 模板 Stage 定义表 {#sec-7-templatestages-moban-stage-u5b}
**定义批次**：第一批
**归属模块**：DR-009 模板引擎
**被依赖模块**：DR-001（项目工作台 Stage 展示）、DR-015（模块治理 Stage 状态）
**写方**：DR-009
**读方**：DR-001, DR-015

```sql
CREATE TABLE template_stages (
    stage_id            VARCHAR(36) PRIMARY KEY,        -- 全局 Stage 标识
    stage_name          VARCHAR(64) NOT NULL,
    order_index         INTEGER NOT NULL,                -- 在模板内的排序
    template_id         VARCHAR(16) NOT NULL
                        CHECK (template_id IN ('Trivial', 'Light', 'Standard', 'Deep')),
    primary_skill_id    VARCHAR(36),                     -- 主 Skill 关联
    auxiliary_skill_ids TEXT,                            -- 辅助 Skill ID 列表（JSON）
    gate_id             VARCHAR(36),                     -- 关联 Gate 定义
    skippable           BOOLEAN NOT NULL DEFAULT FALSE,
    merge_group_id      VARCHAR(36),                     -- 合并组标识
    is_present_in       VARCHAR(16) NOT NULL DEFAULT 'Standard'
                        CHECK (is_present_in IN ('Trivial', 'Light', 'Standard', 'Deep')),

    CONSTRAINT fk_stage_template FOREIGN KEY (template_id) REFERENCES templates(template_id) ON DELETE CASCADE
);

CREATE INDEX idx_template_stages_template ON template_stages(template_id, order_index);
```

> **设计说明**：
> - `is_present_in` 用于裁剪逻辑：Trivial/Light 模板中不展示的 Stage 仍保留在表中，但标记为不生效。
> - 同一 `stage_id` 可在不同模板中有不同 `order_index` 和 `skill_binding`。

---

## 8. project_stages — 项目级 Stage 实例表 {#sec-8-projectstages-u9879muji-stage-}
**定义批次**：第一批
**归属模块**：DR-009 模板引擎
**被依赖模块**：DR-001（进度展示）、DR-003（阶段详情）、DR-005（产物关联）、DR-015（状态同步）
**写方**：DR-009（初始化）、DR-008（执行状态更新）
**读方**：DR-001, DR-003, DR-005, DR-014, DR-015

```sql
CREATE TABLE project_stages (
    project_stage_id    VARCHAR(36) PRIMARY KEY,
    project_id          VARCHAR(36) NOT NULL,
    stage_id            VARCHAR(36) NOT NULL,
    order_index         INTEGER NOT NULL,
    status              VARCHAR(16) NOT NULL DEFAULT 'DEFINED'
                        CHECK (status IN ('DEFINED', 'SKIPPED', 'SCHEDULED', 'EXECUTED', 'REMOVED', 'FROZEN', 'ARCHIVED')),
    primary_skill_id    VARCHAR(36),
    skippable           BOOLEAN NOT NULL DEFAULT FALSE,
    is_frozen           BOOLEAN NOT NULL DEFAULT FALSE,
    merge_group_id      VARCHAR(36),
    execution_status    VARCHAR(16) DEFAULT 'NOT_STARTED',
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_pstage_project FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    CONSTRAINT fk_pstage_stage FOREIGN KEY (stage_id) REFERENCES template_stages(stage_id)
);

CREATE INDEX idx_pstages_project ON project_stages(project_id, order_index);
CREATE INDEX idx_pstages_status ON project_stages(project_id, status);
```

> **设计说明**：
> - `project_stages` 是模板在项目上的运行时实例。项目创建时根据所选模板生成初始记录。
> - 模板切换时：已执行 Stage（EXECUTED）标记 `is_frozen = TRUE`；未执行且不在新模板中的 Stage 标记为 REMOVED。

---

## 9. stage_review_status — Stage 审查状态表 {#sec-9-stagereviewstatus-stage-shench}
**定义批次**：第三批
**归属模块**：DR-003 阶段详情面板
**被依赖模块**：DR-004（审批中心，裁决后更新状态）、DR-007（Flow 编排引擎，读取状态）
**写方**：DR-003（初始化）、DR-004（裁决后更新 `current_status`）
**读方**：DR-003, DR-004, DR-007

```sql
CREATE TABLE stage_review_status (
    stage_id            VARCHAR(36) PRIMARY KEY,
    current_status      VARCHAR(32) NOT NULL
                        CHECK (current_status IN ('REVIEW_PENDING', 'GATE_PENDING', 'PASSED', 'REVISION_REQUESTED', 'REGENERATING')),
    previous_status     VARCHAR(32),                     -- 用于重新生成失败时回退
    current_version     INTEGER NOT NULL DEFAULT 1,      -- 当前产物版本号
    regeneration_batch_id VARCHAR(36),                   -- 重新生成任务 ID
    last_submission_id  VARCHAR(36),                     -- 最近一次提交
    gate_decision_id    VARCHAR(36),                     -- Gate 裁决记录 ID
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_srs_stage FOREIGN KEY (stage_id) REFERENCES project_stages(project_stage_id) ON DELETE CASCADE
);

CREATE INDEX idx_srs_status ON stage_review_status(current_status);
```

---

## 10. gate_decisions — Gate 决策记录表 {#sec-10-gatedecisions-gate-juecejilub}
**定义批次**：第三批
**归属模块**：DR-004 审批中心
**被依赖模块**：DR-003（阶段详情，读取决策状态）
**写方**：DR-004
**读方**：DR-003, DR-004

```sql
CREATE TABLE gate_decisions (
    decision_id         VARCHAR(36) PRIMARY KEY,        -- UUID v4
    gate_id             VARCHAR(36) NOT NULL UNIQUE,     -- 每 Gate 仅一条最终决策
    project_id          VARCHAR(36) NOT NULL,
    gate_type           VARCHAR(16) NOT NULL
                        CHECK (gate_type IN ('1', '2', '2.5', '3', 'initiation')),
    status              VARCHAR(16) NOT NULL
                        CHECK (status IN ('pending', 'passed', 'rejected', 'bypassed')),
    confidence          VARCHAR(16)
                        CHECK (confidence IN ('high', 'medium', 'low')),
    decision_type       VARCHAR(16)
                        CHECK (decision_type IN ('approve', 'reject', 'retry', 'bypass')),
    decision_by         VARCHAR(36),                     -- 决策人
    decision_at         TIMESTAMP,
    duration_sec        INTEGER CHECK (duration_sec >= 0), -- 审批耗时（秒）
    reason              VARCHAR(500),                    -- 驳回理由（5-500 字符）
    self_check_summary  TEXT,                            -- JSON 字符串
    unlocked_stages     TEXT,                            -- JSON 数组：已解锁下游 Stage ID
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_gd_project FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE INDEX idx_gd_project ON gate_decisions(project_id);
CREATE INDEX idx_gd_status ON gate_decisions(status);
CREATE INDEX idx_gd_decision_at ON gate_decisions(decision_at);
```

> **设计说明**：
> - `gate_id` 设置 `UNIQUE` 约束，确保每 Gate 仅保留一条最终决策记录。
> - `unlocked_stages` 存储 JSON 数组，记录审批通过后解锁的下游 Stage 标识。

---

## 11. gate_decision_history — Gate 决策历史明细表 {#sec-11-gatedecisionhistory-gate-juec}
**定义批次**：第三批
**归属模块**：DR-004 审批中心
**被依赖模块**：—（DR-004 内部使用）
**写方**：DR-004
**读方**：DR-004

```sql
CREATE TABLE gate_decision_history (
    history_id          VARCHAR(36) PRIMARY KEY,        -- UUID v4
    gate_id             VARCHAR(36) NOT NULL,
    decision_type       VARCHAR(16) NOT NULL
                        CHECK (decision_type IN ('approve', 'reject', 'retry', 'bypass')),
    decision_by         VARCHAR(36) NOT NULL,
    decision_at         TIMESTAMP NOT NULL,
    duration_sec        INTEGER,
    reason              VARCHAR(500),
    metadata            TEXT,                            -- JSON：附加信息

    CONSTRAINT fk_gdh_gate FOREIGN KEY (gate_id) REFERENCES gate_decisions(gate_id) ON DELETE CASCADE
);

CREATE INDEX idx_gdh_gate ON gate_decision_history(gate_id, decision_at DESC);
```

---

## 12. artifact_files — 产物文件索引表 {#sec-12-artifactfiles-chanu7269wenjia}
**定义批次**：第三批
**归属模块**：DR-005 产物浏览器
**被依赖模块**：DR-003（阶段详情面板产物预览）
**写方**：DR-005
**读方**：DR-003, DR-005

```sql
CREATE TABLE artifact_files (
    artifact_id         VARCHAR(36) PRIMARY KEY,        -- UUID v4
    project_id          VARCHAR(36) NOT NULL,
    stage_id            VARCHAR(36),
    skill_id            VARCHAR(36),
    file_name           VARCHAR(256) NOT NULL,
    file_path           VARCHAR(4096) NOT NULL,
    file_type           VARCHAR(16) NOT NULL
                        CHECK (file_type IN ('md', 'yaml', 'json', 'mermaid', 'openapi', 'txt', 'other')),
    file_size_bytes     INTEGER NOT NULL DEFAULT 0,
    current_version     INTEGER NOT NULL DEFAULT 1,
    external_status     VARCHAR(16) NOT NULL DEFAULT 'normal'
                        CHECK (external_status IN ('normal', 'modified', 'deleted')),
    last_synced_hash    VARCHAR(64),
    last_synced_at      TIMESTAMP,
    stale_flag          BOOLEAN NOT NULL DEFAULT FALSE,  -- 上游基线变更标记（BR-019）
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_af_project FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    CONSTRAINT uq_af_project_path UNIQUE (project_id, file_path)
);

CREATE INDEX idx_af_project ON artifact_files(project_id);
CREATE INDEX idx_af_stage ON artifact_files(stage_id);
CREATE INDEX idx_af_skill ON artifact_files(skill_id);
```

---

## 13. artifact_versions — 产物版本记录表 {#sec-13-artifactversions-chanu7269ban}
**定义批次**：第三批
**归属模块**：DR-005 产物浏览器
**被依赖模块**：DR-003（阶段详情面板版本历史）
**写方**：DR-005
**读方**：DR-003, DR-005

```sql
CREATE TABLE artifact_versions (
    version_id          VARCHAR(36) PRIMARY KEY,        -- UUID v4
    artifact_id         VARCHAR(36) NOT NULL,
    version_number      INTEGER NOT NULL,
    operation_type      VARCHAR(16) NOT NULL
                        CHECK (operation_type IN ('auto_snapshot', 'manual_save', 'rollback', 'regeneration')),
    snapshot_id         VARCHAR(36),                     -- Git 快照 ID
    snapshot_status     VARCHAR(16)
                        CHECK (snapshot_status IN ('committed', 'skipped_size', 'skipped_no_repo', 'failed')),
    content_hash        VARCHAR(64),                     -- 内容哈希（用于 diff）
    summary             VARCHAR(512),                    -- 版本摘要
    created_by          VARCHAR(36) NOT NULL,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_av_artifact FOREIGN KEY (artifact_id) REFERENCES artifact_files(artifact_id) ON DELETE CASCADE
);

CREATE INDEX idx_av_artifact ON artifact_versions(artifact_id, version_number DESC);
```

---

## 14. c4_dsl_store — C4 DSL 存储表 {#sec-14-c4dslstore-c4-dsl-cunu50a8bia}
**定义批次**：第四批
**归属模块**：DR-011 C4 架构浏览器
**被依赖模块**：DR-018（OpenUI 原型服务）、DR-019（WireframeEngine）、DR-020（原型-架构双向绑定）、DR-012（架构验证中心）
**写方**：DR-011
**读方**：DR-012, DR-018, DR-019, DR-020

```sql
CREATE TABLE c4_dsl_store (
    store_id            VARCHAR(36) PRIMARY KEY,        -- UUID v4
    project_id          VARCHAR(36) NOT NULL,
    level               VARCHAR(4) NOT NULL
                        CHECK (level IN ('L1', 'L2', 'L3', 'L4')),
    dsl_text            TEXT NOT NULL,                   -- Mermaid DSL 文本
    generation_mode     VARCHAR(16) NOT NULL DEFAULT 'auto'
                        CHECK (generation_mode IN ('auto', 'manual')),
    confidence          REAL CHECK (confidence BETWEEN 0 AND 1),
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_c4ds_project FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    CONSTRAINT uq_c4ds_project_level_mode UNIQUE (project_id, level, generation_mode)
);

CREATE INDEX idx_c4ds_project_level ON c4_dsl_store(project_id, level);
CREATE INDEX idx_c4ds_project_mode ON c4_dsl_store(project_id, generation_mode);
```

> **设计说明**：
> - 每项目每层级最多两条记录（auto + manual 各一），由 `uq_c4ds_project_level_mode` 约束保证。
> - `dsl_text` 存储完整 Mermaid DSL 文本，支持 C4 架构图的生成、编辑和渲染。
> - DR-012 架构验证中心读取此表作为漂移检测的基线数据源。

---

## 15. 公共表索引速查 {#sec-15-u516cgongbiaosuoyinsucha}
| 表名 | 归属模块 | 写方 | 读方 | 批次 |
|------|----------|------|------|------|
| `workspaces` | 全局基础设施 | 初始化脚本 | DR-015 | 第一批 |
| `size_estimates` | DR-010 | DR-010 | DR-001 | 第一批 |
| `applications` | DR-015 | DR-015 | DR-001, DR-013 | 第一批 |
| `projects` | DR-001 | DR-001 | DR-003/004/005/007/009/012/013/014/015 | 第一批 |
| `skills` | DR-006 | DR-006 | DR-009 | 第一批 |
| `templates` | DR-009 | DR-009 | DR-001, DR-010, DR-015 | 第一批 |
| `template_stages` | DR-009 | DR-009 | DR-001, DR-015 | 第一批 |
| `project_stages` | DR-009 | DR-009, DR-008 | DR-001/003/005/014/015 | 第一批 |
| `stage_review_status` | DR-003 | DR-003, DR-004 | DR-003, DR-004, DR-007 | 第三批 |
| `gate_decisions` | DR-004 | DR-004 | DR-003, DR-004 | 第三批 |
| `gate_decision_history` | DR-004 | DR-004 | DR-004 | 第三批 |
| `artifact_files` | DR-005 | DR-005 | DR-003, DR-005 | 第三批 |
| `artifact_versions` | DR-005 | DR-005 | DR-003, DR-005 | 第三批 |
| `c4_dsl_store` | DR-011 | DR-011 | DR-012, DR-018, DR-019, DR-020 | 第四批 |

---

## 16. 已明确为模块独占的表（不纳入 shared/） {#sec-16-u5df2u660equeweimokuaiu72ecu5}
以下表虽在 _design-index.md 早期规划中被列为公共候选，但经 Audit 确认写方单一且读方不超过 1 个其他模块，维持模块独占：

| 表名 | 定义模块 | 写方 | 读方 | 不提取原因 |
|------|----------|------|------|-----------|
| `skill_dag_nodes` | DR-006 | DR-006 | — | 仅 DR-006 内部使用 |
| `skill_dag_edges` | DR-006 | DR-006 | — | 仅 DR-006 内部使用 |
| `skill_change_logs` | DR-006 | DR-006 | — | 仅 DR-006 内部使用 |
| `execution_plans` | DR-007 | DR-007 | DR-008 | 仅 DR-008 消费，未达 ≥2 模块阈值 |
| `skill_executions` | DR-008 | DR-008 | DR-015 | 仅 DR-015 消费，未达 ≥2 模块阈值 |
| `template_deviations` | DR-009 | DR-009 | — | 仅 DR-009 内部使用 |
| `arch_validation_sessions` | DR-012 | DR-012 | — | 仅 DR-012 内部使用 |
| `rework_events` | DR-013 | DR-003/004/008 | DR-013/014 | 写方分散但逻辑一致，保持 DR-013 定义作为管理方 |
| `project_members` | DR-014 | DR-014 | — | MVP 仅 DR-014 使用，P1 多用户后再评估 |
| `operation_logs` | DR-014 | DR-014 | — | MVP 仅 DR-014 使用，P1 多用户后再评估 |
