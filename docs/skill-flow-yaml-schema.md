# Skill Flow YAML Schema 规格书

> 本文档定义 skill-arsenal 多 Agent 编排引擎的声明式工作流 Schema、执行语义与运行时行为。
>
> 版本：V1.0 | 2026-05-13
> 对标参考：GitHub Actions Workflow、Argo Workflows、AWS Step Functions、LangGraph

---

## 一、设计目标

Skill Flow 旨在解决当前 "用户手动按顺序触发 Skill" 的痛点，通过声明式 YAML 定义 Skill 之间的依赖关系、数据流转、审批节点与错误处理策略，实现 **SDLC 全生命周期的自动化编排**。

| 需求 | 解法 |
|------|------|
| 顺序执行 | 默认按 `stages` 数组顺序串行执行 |
| 并行加速 | `parallel` 关键字支持无依赖 Skill 并行触发 |
| 人工审批 | `gate` / `human_approval` 节点阻塞执行，等待外部信号 |
| 条件分支 | `condition` / `when` 表达式基于前置输出动态路由 |
| 失败重试 | `retry` / `on_error` 策略支持自动回退与重试 |
| 数据传递 | `input` / `output` / `artifacts` 声明实现 Skill 间数据流转 |
| 状态持久化 | 执行状态自动保存，支持断点续跑与故障恢复 |

---

## 二、Schema 定义

### 2.1 顶层结构

```yaml
# skill-flow.schema.json 核心字段
apiVersion: skill-arsenal.dev/v1       # 必填。Schema 版本
kind: SkillFlow                        # 必填。固定值
metadata:                              # 必填。工作流元数据
  name: string                         # 必填。工作流标识符，kebab-case
  version: semver                      # 可选。默认 1.0.0
  description: string                  # 可选。工作流用途说明
  labels:                              # 可选。用于检索与分类
    string: string
  annotations:                         # 可选。附加元数据
    string: string
spec:                                  # 必填。工作流规格
  global:                              # 可选。全局配置
    timeout: duration                  # 可选。默认 30m
    retries: integer                   # 可选。默认 0
    concurrency: integer               # 可选。并行度限制，默认 4
    env:                               # 可选。全局环境变量
      string: string
    artifacts:                         # 可选。全局制品仓库配置
      basePath: string                 # 默认 openspec/changes/{change-id}/
      storage: local | s3 | minio      # 默认 local
  stages:                              # 必填。阶段列表
    - StageDefinition
  hooks:                               # 可选。生命周期钩子
    onStart: HookDefinition
    onSuccess: HookDefinition
    onFailure: HookDefinition
    onGatePending: HookDefinition
```

### 2.2 Stage 定义（核心）

```yaml
# StageDefinition 联合类型
# 以下 5 种类型可混排在 stages 数组中

# --- 类型 A: Skill 调用节点（最常用） ---
skill: string                          # 必填。Skill 名称（对应目录名）
id: string                             # 可选。阶段唯一标识，默认 skill-{index}
displayName: string                    # 可选。UI 展示名称
input:                                 # 可选。输入映射
  artifacts:                           # 制品输入（文件/目录）
    - name: string                     # 制品别名
      from: string                     # 来源阶段 ID + 输出名
      path: string                     # 映射到 Skill 工作目录的路径
  params:                              # 参数输入（KV 对）
    string: string | number | boolean
output:                                # 可选。输出声明
  artifacts:                           # 制品输出
    - name: string                     # 输出别名
      path: string                     # Skill 工作目录中的相对路径
  results:                             # 结构化结果字段
    - name: string                     # 结果字段名
      description: string
      type: string | number | boolean | object
gate: string                           # 可选。关联的审批闸门（gate-1 / gate-2 / gate-3）
condition: expression                  # 可选。执行条件表达式（见 3.4 节）
when: expression                       # 可选。同 condition，更易读别名
timeout: duration                      # 可选。覆盖全局 timeout
retries:                               # 可选。覆盖全局 retries
  count: integer                       # 重试次数
  delay: duration                      # 首次重试延迟
  backoff: linear | exponential        # 退避策略
  maxDelay: duration                   # 最大延迟
parallel:                              # 可选。仅当值为 StageDefinition[] 时有效
  - StageDefinition                    # 并行子阶段列表
onError:                               # 可选。错误处理策略
  strategy: retry | rollback | skip | notify
  retry: RetryDefinition               # strategy=retry 时必填
  rollbackTo: string                   # strategy=rollback 时必填，回退到指定 stage ID
  notify:                              # strategy=notify 时必填
    channels: [webhook | email | slack]
    message: string
```

### 2.3 完整示例：SDLC 交付流水线

```yaml
apiVersion: skill-arsenal.dev/v1
kind: SkillFlow
metadata:
  name: openspec-delivery-pipeline
  version: 1.2.0
  description: OpenSpec 规格驱动的完整软件交付流水线，含四道人工闸门
  labels:
    domain: sdlc
    complexity: high
    team: backend
  annotations:
    author: zhsusn
    changelog: "v1.2.0: 增加 monitoring-setup 并行执行"

spec:
  global:
    timeout: 2h
    retries: 1
    concurrency: 4
    env:
      PROJECT_NAME: "my-service"
      OPENAI_MODEL: "gpt-5"
    artifacts:
      basePath: "openspec/changes/{metadata.changeId}"
      storage: local

  stages:
    # ========== 阶段 0: 项目初始化 ==========
    - skill: progress-tracker
      id: init
      displayName: "项目初始化"
      output:
        artifacts:
          - name: tracker-state
            path: "progress-tracker.yaml"

    # ========== 阶段 1: 需求探索 ==========
    - skill: brainstorming
      id: brainstorm
      displayName: "需求脑暴"
      input:
        artifacts:
          - name: tracker
            from: "init.tracker-state"
            path: "progress-tracker.yaml"
      output:
        artifacts:
          - name: ideas
            path: "ideas.md"

    - skill: competitive-analysis
      id: competitive
      displayName: "竞品分析"
      input:
        params:
          mode: positioning
      output:
        artifacts:
          - name: competitive-report
            path: "competitive-analysis.md"

    # ========== 阶段 2: 概要需求（Gate 1） ==========
    - skill: prd-generation
      id: prd
      displayName: "概要需求生成"
      input:
        artifacts:
          - name: ideas
            from: "brainstorm.ideas"
            path: "ideas.md"
          - name: competitive-report
            from: "competitive.competitive-report"
            path: "competitive-analysis.md"
      output:
        artifacts:
          - name: prd-bundle
            path: "prd/"
        results:
          - name: gate1-status
            description: "Gate 1 状态"
            type: string
      gate: gate-1
      onError:
        strategy: rollback
        rollbackTo: brainstorm

    - skill: human
      id: gate-1-approval
      displayName: "Gate 1 审批"
      input:
        params:
          gate: gate-1
          action: await-sign-off
      condition: "prd.gate1-status != 'auto-approved'"

    # ========== 阶段 2.5: 详细需求（Gate 2.5） ==========
    - skill: detailed-requirements
      id: detailed-req
      displayName: "详细需求拆解"
      input:
        artifacts:
          - name: prd-bundle
            from: "prd.prd-bundle"
            path: "prd/"
      output:
        artifacts:
          - name: detailed-specs
            path: "detailed-requirements/"

    - skill: human
      id: gate-2-5-approval
      displayName: "Gate 2.5 审批"
      input:
        params:
          gate: gate-2.5
          action: await-sign-off

    # ========== 阶段 3: 概要设计（Gate 2） ==========
    - skill: high-level-design
      id: hld
      displayName: "概要设计"
      input:
        artifacts:
          - name: detailed-specs
            from: "detailed-req.detailed-specs"
            path: "detailed-requirements/"
      output:
        artifacts:
          - name: hld-bundle
            path: "design/"
          - name: rollback-plan
            path: "ops/rollback-plan.md"
          - name: monitoring-rules
            path: "ops/monitoring-rules.yaml"
      gate: gate-2

    - skill: human
      id: gate-2-approval
      displayName: "Gate 2 审批"
      input:
        params:
          gate: gate-2
          action: await-sign-off

    # ========== 阶段 3.5: 接口契约 + 监控配置（并行） ==========
    - parallel:
        - skill: interface-first-dev
          id: interface-dev
          displayName: "接口契约生成"
          input:
            artifacts:
              - name: hld-bundle
                from: "hld.hld-bundle"
                path: "design/"
          output:
            artifacts:
              - name: api-contract
                path: "api-contract/"

        - skill: monitoring-setup
          id: monitoring-setup
          displayName: "监控规则初始化"
          input:
            artifacts:
              - name: monitoring-rules
                from: "hld.monitoring-rules"
                path: "ops/monitoring-rules.yaml"
          output:
            artifacts:
              - name: monitoring-config
                path: "ops/monitoring-rules.yaml"

    # ========== 阶段 4: 详细设计 ==========
    - skill: detailed-design
      id: detailed-design
      displayName: "详细设计"
      input:
        artifacts:
          - name: hld-bundle
            from: "hld.hld-bundle"
            path: "design/"
          - name: api-contract
            from: "interface-dev.api-contract"
            path: "api-contract/"
      output:
        artifacts:
          - name: detailed-design-bundle
            path: "detailed-design/"

    # ========== 阶段 5: 计划与拆解 ==========
    - skill: writing-plans
      id: write-plan
      displayName: "实现计划"
      input:
        artifacts:
          - name: detailed-design-bundle
            from: "detailed-design.detailed-design-bundle"
            path: "detailed-design/"
      output:
        artifacts:
          - name: plan
            path: "plan.md"

    - skill: task-breakdown
      id: breakdown
      displayName: "任务拆解"
      input:
        artifacts:
          - name: plan
            from: "write-plan.plan"
            path: "plan.md"
      output:
        artifacts:
          - name: tasks
            path: "tasks.md"

    # ========== 阶段 6-7: 编码执行 ==========
    - skill: executing-plans
      id: execute
      displayName: "编码实现"
      input:
        artifacts:
          - name: tasks
            from: "breakdown.tasks"
            path: "tasks.md"
          - name: api-contract
            from: "interface-dev.api-contract"
            path: "api-contract/"
      output:
        artifacts:
          - name: src
            path: "src/"
        results:
          - name: completed-tasks
            type: number
          - name: failed-tasks
            type: number
      timeout: 4h
      retries:
        count: 2
        delay: 30s
        backoff: exponential
        maxDelay: 10m
      onError:
        strategy: retry

    # ========== 阶段 8: 单元测试 ==========
    - skill: unit-test
      id: unit-test
      displayName: "单元测试"
      input:
        artifacts:
          - name: src
            from: "execute.src"
            path: "src/"
      output:
        results:
          - name: coverage
            type: number
          - name: passed
            type: number
          - name: failed
            type: number
      # 覆盖率不足时，自动回退到编码阶段补充测试
      onError:
        strategy: rollback
        rollbackTo: execute

    # ========== 阶段 9: 集成测试 ==========
    - skill: integration-test
      id: integration-test
      displayName: "集成测试"
      input:
        artifacts:
          - name: src
            from: "execute.src"
            path: "src/"
          - name: api-contract
            from: "interface-dev.api-contract"
            path: "api-contract/"
      output:
        artifacts:
          - name: e2e-report
            path: "tests/e2e-report.md"
          - name: uat-checklist
            path: "tests/uat-checklist.md"
        results:
          - name: p0-passed
            type: boolean

    # ========== 阶段 9.5: UAT（Gate 3） ==========
    - skill: uat-verification
      id: uat
      displayName: "UAT 验证"
      input:
        artifacts:
          - name: uat-checklist
            from: "integration-test.uat-checklist"
            path: "tests/uat-checklist.md"
      output:
        artifacts:
          - name: uat-report
            path: "tests/uat-report.md"
      gate: gate-3
      condition: "integration-test.p0-passed == true"

    - skill: human
      id: gate-3-approval
      displayName: "Gate 3 审批"
      input:
        params:
          gate: gate-3
          action: await-sign-off

    # ========== 阶段 10.5: 发布管理 ==========
    - skill: release-management
      id: release
      displayName: "发布准备"
      input:
        artifacts:
          - name: uat-report
            from: "uat.uat-report"
            path: "tests/uat-report.md"
          - name: rollback-plan
            from: "hld.rollback-plan"
            path: "ops/rollback-plan.md"
      output:
        artifacts:
          - name: release-notes
            path: "RELEASE.md"
          - name: release-checklist
            path: "ops/release-checklist.md"
      human_approval: true

    # ========== 阶段 11: 归档 ==========
    - skill: finish
      id: finish
      displayName: "归档收尾"
      input:
        artifacts:
          - name: src
            from: "execute.src"
            path: "src/"
          - name: release-notes
            from: "release.release-notes"
            path: "RELEASE.md"
      output:
        artifacts:
          - name: archive
            path: "archive/"

    # ========== 阶段 12: 监控分析（周期性） ==========
    - skill: monitoring-analysis
      id: monitoring
      displayName: "监控分析"
      input:
        artifacts:
          - name: monitoring-config
            from: "monitoring-setup.monitoring-config"
            path: "ops/monitoring-rules.yaml"
      output:
        artifacts:
          - name: health-report
            path: "ops/health-report.md"
          - name: feedback-loop
            path: "ops/feedback-loop.md"
      # 周期性执行，非阻塞主线
      when: "metadata.schedule == 'weekly'"

  hooks:
    onStart:
      action: notify
      params:
        message: "流水线 {metadata.name} 已启动"
        channel: webhook
        url: "${env.WEBHOOK_URL}"

    onSuccess:
      action: notify
      params:
        message: "流水线 {metadata.name} 执行成功，共 {stats.duration}"
        channel: webhook

    onFailure:
      action: notify
      params:
        message: "流水线 {metadata.name} 在阶段 {failedStage.id} 失败: {failedStage.error}"
        channel: webhook

    onGatePending:
      action: notify
      params:
        message: "阶段 {pendingStage.displayName} 等待人工审批"
        channel: slack
        mention: "${env.TECH_LEAD_SLACK_ID}"
```

---

## 三、执行语义详解

### 3.1 DAG 构建与调度

Skill Flow 引擎将 `stages` 数组解析为 **DAG（有向无环图）**，节点是 Stage，边是 `input` 中的 `from` 依赖。

```
原始 stages 数组:
  [A] → [B] → [C]
   ↓     ↓
  [D] → [E]

解析为 DAG:
    A
   / \
  B   D
  |   |
  C   E

拓扑排序执行顺序: A → (B, D 并行) → (C, E 并行)
```

**约束**：
- 如果检测到循环依赖（如 A 依赖 B，B 依赖 A），启动时立即报错
- `parallel` 块内部也遵循 DAG 规则，块内子阶段可互相依赖
- 全局 `concurrency` 限制同时运行的 Skill 数量，超出时排队等待

### 3.2 数据流与 Artifacts

Skill 之间通过 **Artifacts（制品）** 传递数据，遵循 "写时复制、读时引用" 原则：

```
Stage A 输出: artifacts/basePath/A/output/
Stage B 输入: 将 A/output/ 挂载到 B 工作目录的 input/ 下
```

**路径解析规则**：

| 写法 | 含义 |
|------|------|
| `from: "prd.prd-bundle"` | 引用阶段 `prd` 的 artifacts 中名为 `prd-bundle` 的输出 |
| `path: "prd/"` | 在目标 Skill 工作目录中映射为 `prd/` |
| `basePath: "openspec/changes/{metadata.changeId}"` | 支持模板变量替换 |

**变量作用域**：

| 变量来源 | 访问方式 | 示例 |
|----------|----------|------|
| 工作流 metadata | `metadata.name`, `metadata.labels.key` | `{metadata.changeId}` |
| 全局 env | `env.VAR_NAME` | `${env.PROJECT_NAME}` |
| 阶段结果 | `stageId.resultName` | `unit-test.coverage` |
| 系统变量 | `system.timestamp`, `system.uuid` | `{system.timestamp}` |

### 3.3 Gate 与人工审批

Gate 是 Skill Flow 的核心差异化能力，将 `skill` 的 "四道人工闸门" 从文档规范落地为运行时机制。

#### 3.3.1 Gate 节点行为

```
执行到 Gate 节点:
  1. 引擎暂停当前分支执行
  2. 持久化当前状态到数据库
  3. 触发 onGatePending hook（发送通知）
  4. 等待外部审批信号

审批信号格式:
  {
    "gateId": "gate-2",
    "decision": "sign-off" | "conditional" | "reject",
    "comment": "架构合理，同意通过",
    "signer": "zhangsan@company.com",
    "timestamp": "2026-05-13T10:00:00Z"
  }

决策处理:
  - sign-off   → 继续执行下游阶段
  - conditional → 继续执行，但标记为 "带条件通过"，写入 human-decisions.md
  - reject     → 触发 onError 策略（默认 rollback 到上一非 Gate 阶段）
```

#### 3.3.2 审批方式

| 方式 | 触发条件 | 适用场景 |
|------|----------|----------|
| `gate: gate-x` | Skill 节点标记 gate | 正式阶段门控（Gate 1/2.5/2/3） |
| `human_approval: true` | 布尔标记 | 高风险操作（如 release-management） |
| `condition` + human skill | 条件执行 human skill | 条件性审批（如自动审批通过时跳过） |

### 3.4 条件表达式（Expression）

条件表达式用于 `condition` / `when` 字段，支持简单的逻辑运算：

```yaml
# 比较运算
condition: "unit-test.coverage >= 0.70"
condition: "execute.failed-tasks == 0"
condition: "metadata.environment != 'production'"

# 逻辑组合
condition: "unit-test.coverage >= 0.70 and integration-test.p0-passed == true"
condition: "metadata.environment == 'production' or gate-3.decision == 'sign-off'"

# 存在性检查
condition: "has(artifacts['api-contract'])"
condition: "env.SKIP_UAT != ''"

# 正则匹配（用于文本结果判断）
condition: "match(uat.status, 'PASS|APPROVED')"
```

**支持的运算符**：`==`, `!=`, `<`, `<=`, `>`, `>=`, `and`, `or`, `not`, `has()`, `match()`, `in()`

### 3.5 错误处理策略

| 策略 | 行为 | 适用场景 |
|------|------|----------|
| `retry` | 按重试配置重新执行本阶段 | 瞬时故障（网络超时、API 限流） |
| `rollback` | 回退到指定阶段重新执行 | 逻辑错误（设计缺陷、需求变更） |
| `skip` | 跳过本阶段，继续下游 | 可选步骤失败不影响主线 |
| `notify` | 发送通知，终止流水线 | 需要人工介入的致命错误 |

**回滚语义**：
- `rollbackTo` 指定阶段 ID，引擎将：
  1. 取消当前阶段及所有已执行的下游阶段
  2. 恢复到目标阶段的输出状态
  3. 从目标阶段的下一个阶段重新开始
- 支持多级回滚（如从 `unit-test` 回滚到 `execute`，再回滚到 `breakdown`）

### 3.6 状态机

每个 Stage 在执行过程中处于以下状态之一：

```
          ┌─────────────┐
          │   Pending   │ ← 初始状态，等待依赖满足
          └──────┬──────┘
                 │ 依赖全部完成
                 ▼
          ┌─────────────┐
          │   Running   │ ← 正在执行 Skill
          └──────┬──────┘
                 │
       ┌─────────┼─────────┬─────────┐
       ▼         ▼         ▼         ▼
  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
  │Success │ │ Failed │ │Skipped │ │Waiting │
  │(成功)  │ │(失败)  │ │(跳过)  │ │(Gate)  │
  └────┬───┘ └───┬────┘ └────────┘ └───┬────┘
       │         │                     │
       │         │ onError=retry       │ 收到审批
       │         └────────────────────▶│
       │                               ▼
       │                         ┌────────┐
       └────────────────────────▶│Resume  │
                                 └────────┘
```

**流水线级状态**：

| 状态 | 含义 |
|------|------|
| `Pending` | 已创建，未开始执行 |
| `Running` | 至少一个 Stage 正在执行 |
| `Paused` | 等待 Gate 审批 |
| `Succeeded` | 所有 Stage 成功完成 |
| `Failed` | 至少一个 Stage 失败且未恢复 |
| `Cancelled` | 被用户手动取消 |

---

## 四、运行时架构

### 4.1 组件划分

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Skill Flow Runtime                             │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐│
│  │  Scheduler  │  │   Executor  │  │      State Manager          ││
│  │  (DAG 调度)  │  │ (Skill 执行) │  │  (SQLite / PostgreSQL)      ││
│  │             │  │             │  │                             ││
│  │ • 拓扑排序   │  │ • 加载 Skill│  │ • 阶段状态持久化             ││
│  │ • 并行控制   │  │ • 注入输入  │  │ • 断点续跑支持               ││
│  │ • 条件评估   │  │ • 捕获输出  │  │ • 历史查询                   ││
│  │ • 超时监控   │  │ • 日志收集  │  │ • 审计日志                   ││
│  └──────┬──────┘  └──────┬──────┘  └─────────────┬───────────────┘│
│         │                │                       │               │
│         └────────────────┼───────────────────────┘               │
│                          │                                       │
│                   ┌──────▼──────┐                                │
│                   │   Engine    │                                │
│                   │   Core      │                                │
│                   └──────┬──────┘                                │
│                          │                                       │
│  ┌───────────────────────┼───────────────────────────────────┐  │
│  │                       │                                   │  │
│  ▼                       ▼                                   ▼  │
│ ┌─────────┐        ┌─────────┐                        ┌────────┐│
│ │  Skill  │        │  Gate   │                        │  Hook  ││
│ │ Adapter │        │ Adapter │                        │Adapter ││
│ │         │        │         │                        │        ││
│ │Kimi CLI │        │ Web UI  │                        │Webhook ││
│ │Claude CLI│       │ CLI     │                        │ Slack  ││
│ │MCP Client│       │ Email   │                        │ Email  ││
│ └─────────┘        └─────────┘                        └────────┘│
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 Skill Adapter 抽象

运行时通过 **Adapter 模式** 屏蔽不同平台的差异：

```python
# 伪代码
class SkillAdapter(ABC):
    @abstractmethod
    def load_skill(self, name: str) -> SkillManifest: ...
    
    @abstractmethod
    def execute(self, manifest: SkillManifest, context: ExecutionContext) -> ExecutionResult: ...

class KimiCodeAdapter(SkillAdapter):
    def execute(self, manifest, context):
        # 调用 kimi-cli skill run {name} --input {context.artifacts}
        pass

class ClaudeCodeAdapter(SkillAdapter):
    def execute(self, manifest, context):
        # 调用 claude skill run {name} --input {context.artifacts}
        pass

class MCPAdapter(SkillAdapter):
    def execute(self, manifest, context):
        # 启动 MCP Server，通过 JSON-RPC 调用 tool
        pass
```

### 4.3 状态持久化 Schema

```sql
-- 核心表结构（SQLite / PostgreSQL）
CREATE TABLE flows (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    spec JSON NOT NULL,
    status TEXT CHECK(status IN ('Pending','Running','Paused','Succeeded','Failed','Cancelled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE flow_stages (
    id TEXT PRIMARY KEY,
    flow_id TEXT REFERENCES flows(id),
    stage_id TEXT NOT NULL,
    skill_name TEXT,
    status TEXT CHECK(status IN ('Pending','Running','Success','Failed','Skipped','Waiting')),
    input_artifacts JSON,
    output_artifacts JSON,
    results JSON,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    retry_count INTEGER DEFAULT 0
);

CREATE TABLE gate_decisions (
    id TEXT PRIMARY KEY,
    flow_id TEXT REFERENCES flows(id),
    stage_id TEXT NOT NULL,
    gate_name TEXT NOT NULL,
    decision TEXT CHECK(decision IN ('sign-off','conditional','reject')),
    comment TEXT,
    signer TEXT,
    decided_at TIMESTAMP
);
```

---

## 五、CLI 与 API 接口

### 5.1 CLI 命令

```bash
# 运行工作流
skill-arsenal flow run openspec-delivery-pipeline.yaml --change-id=feat-login

# 查看运行状态
skill-arsenal flow status <flow-id>

# 列出历史运行
skill-arsenal flow list --status=Running --limit=10

# 审批 Gate
skill-arsenal flow approve <flow-id> --gate=gate-2 --decision=sign-off --comment="架构合理"

# 取消运行
skill-arsenal flow cancel <flow-id>

# 重试失败阶段
skill-arsenal flow retry <flow-id> --stage=execute

# 验证 YAML 语法
skill-arsenal flow validate ./my-pipeline.yaml

# 导出运行报告
skill-arsenal flow export <flow-id> --format=html --output=report.html
```

### 5.2 REST API

```yaml
# 核心端点
POST   /api/v1/flows                    # 创建工作流实例
GET    /api/v1/flows/{id}               # 查询工作流状态
POST   /api/v1/flows/{id}/approve       # Gate 审批
POST   /api/v1/flows/{id}/cancel        # 取消工作流
POST   /api/v1/flows/{id}/retry         # 重试阶段
GET    /api/v1/flows/{id}/logs          # 获取阶段日志
GET    /api/v1/flows/{id}/artifacts     # 列出品制品
GET    /api/v1/flows/{id}/artifacts/{name}  # 下载制品
POST   /api/v1/flows/validate           # 验证 YAML
GET    /api/v1/templates                # 获取内置模板列表
```

---

## 六、与现有生态的集成

| 集成点 | 方式 |
|--------|------|
| **SDLC 可视化平台** | Flow YAML 驱动画布渲染，以 `skills/sdlc` 下 25 个 Skill 为节点展示拓扑图与泳道视图，支持节点状态实时同步 |
| **validate.py** | 新增 `scripts/validate-flow.py` 校验 YAML Schema、DAG 无环性、Stage 存在性 |
| **convert.py** | 支持将 Flow 导出为 GitHub Actions Workflow（用于 CI/CD 触发） |
| **progress-tracker** | Flow 运行时自动向 progress-tracker 上报阶段进度 |
| **human skill** | Gate 审批节点底层调用 `human` Skill 记录审计日志 |
| **MCP Server** | Flow 引擎自身可暴露为 MCP Server，供外部 Agent 调用 |

---

## 七、演进路线

| 版本 | 目标 | 关键特性 |
|------|------|----------|
| **v0.1** | MVP | 串行 Stage 执行、input/output 传递、本地文件系统存储 |
| **v0.2** | 并行 | `parallel` 支持、全局 concurrency 控制、基础条件表达式 |
| **v0.3** | 门控 | Gate 审批节点、状态持久化、CLI 审批命令 |
| **v0.4** | 弹性 | 重试策略、rollback、超时控制、Hook 通知 |
| **v0.5** | 可视化 | 与 SDLC 全过程可视化平台集成，以 `skills/sdlc` Skill 为节点渲染实时状态看板与交互式流程画布 |
| **v1.0** | 生产 | 分布式执行（多机）、PostgreSQL 后端、RBAC 权限、REST API |

---

## 附录 A：JSON Schema（机器校验用）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SkillFlow",
  "type": "object",
  "required": ["apiVersion", "kind", "metadata", "spec"],
  "properties": {
    "apiVersion": { "type": "string", "enum": ["skill-arsenal.dev/v1"] },
    "kind": { "type": "string", "enum": ["SkillFlow"] },
    "metadata": {
      "type": "object",
      "required": ["name"],
      "properties": {
        "name": { "type": "string", "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$" },
        "version": { "type": "string" },
        "description": { "type": "string" },
        "labels": { "type": "object", "additionalProperties": { "type": "string" } },
        "annotations": { "type": "object", "additionalProperties": { "type": "string" } }
      }
    },
    "spec": {
      "type": "object",
      "required": ["stages"],
      "properties": {
        "global": {
          "type": "object",
          "properties": {
            "timeout": { "type": "string" },
            "retries": { "type": "integer", "minimum": 0 },
            "concurrency": { "type": "integer", "minimum": 1 },
            "env": { "type": "object" },
            "artifacts": {
              "type": "object",
              "properties": {
                "basePath": { "type": "string" },
                "storage": { "type": "string", "enum": ["local", "s3", "minio"] }
              }
            }
          }
        },
        "stages": {
          "type": "array",
          "items": { "$ref": "#/definitions/stage" }
        },
        "hooks": {
          "type": "object",
          "properties": {
            "onStart": { "$ref": "#/definitions/hook" },
            "onSuccess": { "$ref": "#/definitions/hook" },
            "onFailure": { "$ref": "#/definitions/hook" },
            "onGatePending": { "$ref": "#/definitions/hook" }
          }
        }
      }
    }
  },
  "definitions": {
    "stage": {
      "type": "object",
      "properties": {
        "skill": { "type": "string" },
        "id": { "type": "string" },
        "displayName": { "type": "string" },
        "input": { "type": "object" },
        "output": { "type": "object" },
        "gate": { "type": "string" },
        "condition": { "type": "string" },
        "when": { "type": "string" },
        "timeout": { "type": "string" },
        "retries": { "type": "object" },
        "parallel": { "type": "array", "items": { "$ref": "#/definitions/stage" } },
        "onError": { "type": "object" }
      }
    },
    "hook": {
      "type": "object",
      "required": ["action"],
      "properties": {
        "action": { "type": "string", "enum": ["notify", "webhook", "script"] },
        "params": { "type": "object" }
      }
    }
  }
}
```
