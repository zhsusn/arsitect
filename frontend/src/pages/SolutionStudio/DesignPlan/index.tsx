import { useState, useMemo, useEffect, useCallback } from 'react'
import { useProjectContext } from '../../../App'
import { useRequirementStudioStore } from '../../../stores/requirementStudioStore'
import { useExecutionStore } from '../../../stores/executionStore'
import { fetchStudioStatus, executeStage } from '../../../services/requirementStudio'
import { createProjectReview } from '../../../services/projectReview'
import TaskTree, { type TaskItem } from '../../../components/TaskTree'
import ArtifactRenderer from '../../../components/ArtifactRenderer'
import ExecutionPanel from '../../../components/ExecutionPanel'
import StatusBar from '../../../components/StatusBar'
import ReviewPanel from '../../../components/ReviewPanel'

const TABS = [
  { id: 'outline', label: '概要设计' },
  { id: 'detailed', label: '详细设计' },
  { id: 'db', label: 'DB 设计' },
  { id: 'contract', label: '接口契约' },
  { id: 'history', label: '版本历史' },
]

const OUTLINE_TASKS: TaskItem[] = [
  { taskId: 'hld', name: 'HLD 生成', status: 'NOT_STARTED', type: 'skill', module: '概要设计', description: '生成概要设计文档' },
  { taskId: 'c4-l1', name: 'C4 Context', status: 'NOT_STARTED', type: 'skill', module: '概要设计', description: '绘制系统上下文图' },
  { taskId: 'c4-l2', name: 'C4 Container', status: 'NOT_STARTED', type: 'skill', module: '概要设计', description: '绘制容器图' },
  { taskId: 'tech-stack', name: '技术栈选型', status: 'NOT_STARTED', type: 'skill', module: '概要设计', description: '确定技术栈与部署拓扑' },
]

const DETAILED_TASKS: TaskItem[] = [
  { taskId: 'dd', name: 'DD 生成', status: 'NOT_STARTED', type: 'skill', module: '详细设计', description: '生成详细设计文档' },
  { taskId: 'c4-l3', name: 'C4 Component', status: 'NOT_STARTED', type: 'skill', module: '详细设计', description: '绘制组件图' },
  { taskId: 'db-schema', name: '数据库表结构', status: 'NOT_STARTED', type: 'skill', module: '详细设计', description: '设计数据库表结构' },
  { taskId: 'api-spec', name: 'API 详细规格', status: 'NOT_STARTED', type: 'skill', module: '详细设计', description: '定义 API 详细规格' },
  { taskId: 'openui', name: 'OpenUI 规格', status: 'NOT_STARTED', type: 'skill', module: '详细设计', description: '输出 OpenUI 页面规格' },
]

const DB_TASKS: TaskItem[] = [
  { taskId: 'er-diagram', name: 'ER 图生成', status: 'NOT_STARTED', type: 'skill', module: 'DB 设计', description: '生成 ER 关系图' },
  { taskId: 'ddl', name: 'DDL 定义', status: 'NOT_STARTED', type: 'skill', module: 'DB 设计', description: '定义 DDL 语句' },
  { taskId: 'index', name: '索引设计', status: 'NOT_STARTED', type: 'skill', module: 'DB 设计', description: '设计索引策略' },
]

const CONTRACT_TASKS: TaskItem[] = [
  { taskId: 'openapi', name: 'OpenAPI 3.0', status: 'NOT_STARTED', type: 'skill', module: '接口契约', description: '编写 OpenAPI 3.0 YAML' },
  { taskId: 'swagger', name: 'Swagger UI', status: 'NOT_STARTED', type: 'skill', module: '接口契约', description: 'Swagger UI 预览' },
  { taskId: 'validation', name: '接口校验', status: 'NOT_STARTED', type: 'skill', module: '接口契约', description: '校验接口一致性' },
]

const DEMO_HLD = `# 订单系统概要设计文档

## 1. 系统上下文（C4 L1）


text
[用户] → 使用 → [订单系统]
[管理员] → 管理 → [订单系统]
[订单系统] → 调用 → [库存系统]
[订单系统] → 调用 → [通知系统]


## 2. 容器图（C4 L2）

| 容器 | 技术 | 职责 |
|------|------|------|
| Web App | React 19 + Vite 6 | 前端单页应用 |
| API | FastAPI + SQLAlchemy | 后端 API 服务 |
| Database | SQLite → PostgreSQL | 数据持久化 |
| Message Queue | Redis | 异步通知队列 |

## 3. 技术栈选型

- **前端**: React 19 + Vite 6 + TypeScript 5.6
- **后端**: FastAPI + SQLAlchemy + Pydantic
- **数据库**: SQLite (MVP) → PostgreSQL 15+ (P1)
- **缓存**: Redis
- **消息队列**: Redis Streams
- **部署**: Docker + Docker Compose
`

const DEMO_DDL = `tables:
  - name: orders
    columns:
      - name: order_id
        type: UUID
        pk: true
      - name: user_id
        type: UUID
        fk: users.id
      - name: status
        type: VARCHAR(20)
      - name: total_amount
        type: DECIMAL(10, 2)
      - name: created_at
        type: TIMESTAMP
        default: now()
    indexes:
      - columns: [user_id, created_at]
      - columns: [status]

  - name: order_items
    columns:
      - name: item_id
        type: UUID
        pk: true
      - name: order_id
        type: UUID
        fk: orders.order_id
      - name: product_id
        type: UUID
        fk: products.product_id
      - name: quantity
        type: INTEGER
      - name: unit_price
        type: DECIMAL(10, 2)
`

const DEMO_OPENAPI = `openapi: 3.0.0
info:
  title: 订单系统 API
  version: 1.0.0
paths:
  /api/v1/orders:
    get:
      summary: 获取订单列表
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: page_size
          in: query
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OrderListResponse'
    post:
      summary: 创建订单
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateOrderRequest'
      responses:
        '201':
          description: 创建成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OrderResponse'
        '422':
          description: 库存不足

components:
  schemas:
    OrderListResponse:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/Order'
        total:
          type: integer
    Order:
      type: object
      properties:
        order_id:
          type: string
        status:
          type: string
          enum: [pending, paid, shipped, completed, cancelled]
    CreateOrderRequest:
      type: object
      properties:
        items:
          type: array
          items:
            type: object
            properties:
              product_id:
                type: string
              quantity:
                type: integer
    OrderResponse:
      type: object
      properties:
        order_id:
          type: string
        status:
          type: string
`

export default function DesignPlanPage() {
  const { currentProjectId } = useProjectContext()
  const projectId = currentProjectId
  const [activeTab, setActiveTab] = useState('outline')
  const [artifactContent, setArtifactContent] = useState('')

  const {
    selectedTaskId,
    selectTask,
    executionStatus,
    executionLogs,
    annotations,
    setExecutionStatus,
    appendExecutionLog,
    setStageStatuses,
    setLoading,
    setError,
  } = useRequirementStudioStore()

  const { connectSSE, disconnectSSE } = useExecutionStore()

  useEffect(() => {
    if (!projectId) return
    setLoading(true)
    fetchStudioStatus(projectId)
      .then((data) => {
        const newStatus: Record<string, any> = {}
        data.stages.forEach((stage) => {
          newStatus[stage.stage_id] = {
            status: stage.status,
            progress: stage.progress_percent,
            tasks: [],
          }
        })
        setStageStatuses(newStatus)
      })
      .catch((err) => setError(err instanceof Error ? err.message : '加载失败'))
      .finally(() => setLoading(false))
  }, [projectId, setLoading, setError, setStageStatuses])

  const stageTasks = useMemo((): TaskItem[] => {
    switch (activeTab) {
      case 'outline': return OUTLINE_TASKS
      case 'detailed': return DETAILED_TASKS
      case 'db': return DB_TASKS
      case 'contract': return CONTRACT_TASKS
      default: return []
    }
  }, [activeTab])

  const getArtifactType = (): 'markdown' | 'swagger' | 'yaml' | 'html' => {
    switch (activeTab) {
      case 'outline': return 'markdown'
      case 'detailed': return 'markdown'
      case 'db': return 'yaml'
      case 'contract': return selectedTaskId === 'swagger' ? 'swagger' : 'yaml'
      default: return 'markdown'
    }
  }

  const getDefaultContent = () => {
    switch (activeTab) {
      case 'outline': return DEMO_HLD
      case 'detailed': return DEMO_HLD
      case 'db': return DEMO_DDL
      case 'contract': return DEMO_OPENAPI
      default: return '## 设计方案\n\n请选择上方 Tab 查看不同阶段的设计产物。'
    }
  }

  const handleExecute = useCallback(async () => {
    if (!projectId) return
    const stageMap: Record<string, string> = {
      outline: 'design-outline',
      detailed: 'design-detailed',
      db: 'db-design',
      contract: 'interface-contract',
    }
    const stageId = stageMap[activeTab] || 'design-outline'
    setExecutionStatus('prep')
    appendExecutionLog('> 开始执行...')
    try {
      connectSSE(projectId)
      await executeStage(projectId, stageId)
      setExecutionStatus('exec')
      appendExecutionLog('> 执行中...')
      setTimeout(() => {
        setExecutionStatus('post')
        appendExecutionLog('> 执行完成')
        setExecutionStatus('success')
        disconnectSSE()
      }, 2000)
    } catch (err) {
      setExecutionStatus('failed')
      appendExecutionLog(`> 执行失败: ${err instanceof Error ? err.message : '未知错误'}`)
      disconnectSSE()
    }
  }, [projectId, activeTab, setExecutionStatus, appendExecutionLog, connectSSE, disconnectSSE])

  if (!projectId) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280' }}>
        请先在顶部选择项目
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#fff', borderRadius: 8, border: '1px solid #e5e7eb', overflow: 'hidden' }}>
      {/* 顶部 Tab 切换 */}
      <div style={{ display: 'flex', borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '10px 20px',
              fontSize: 13,
              border: 'none',
              background: activeTab === tab.id ? '#fff' : 'transparent',
              color: activeTab === tab.id ? '#2563eb' : '#6b7280',
              borderBottom: activeTab === tab.id ? '2px solid #2563eb' : '2px solid transparent',
              cursor: 'pointer',
              fontWeight: activeTab === tab.id ? 600 : 400,
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* 左侧：任务树 */}
        <TaskTree
          tasks={stageTasks}
          selectedTaskId={selectedTaskId}
          onTaskSelect={selectTask}
          onTaskExecute={(taskId) => {
            selectTask(taskId)
            handleExecute()
          }}
        />

        {/* 中间：产物渲染区 */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', borderRight: '1px solid #e5e7eb' }}>
          <div style={{ flex: 1, overflow: 'auto' }}>
            {activeTab === 'history' ? (
              <div style={{ padding: 24, color: '#6b7280' }}>版本历史视图开发中...</div>
            ) : (
              <ArtifactRenderer
                content={artifactContent || getDefaultContent()}
                type={getArtifactType()}
                onEdit={(content) => setArtifactContent(content)}
              />
            )}
          </div>
        </div>

        {/* 右侧：执行与审查面板 */}
        <div style={{ width: 300, minWidth: 300, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <ExecutionPanel
            status={executionStatus}
            logs={executionLogs}
            skillName={activeTab === 'outline' ? 'high-level-design' : activeTab === 'detailed' ? 'detailed-design' : activeTab === 'db' ? 'db-design' : 'interface-contract'}
            onExecute={handleExecute}
            onRetry={() => setExecutionStatus('idle')}
            onAbort={() => {
              setExecutionStatus('idle')
              appendExecutionLog('> 已中断')
              disconnectSSE()
            }}
          />
          <ReviewPanel
            annotations={annotations as any}
            onSubmit={async (comment) => {
              if (!projectId) return
              try {
                await createProjectReview(projectId, {
                  review_type: 'code_review',
                  item_id: `design-${activeTab}-${Date.now()}`,
                  item_type: 'annotation',
                  status: 'pending',
                  notes: comment,
                })
                appendExecutionLog('> 审查批注已保存')
              } catch (err) {
                appendExecutionLog(`> 保存批注失败: ${err instanceof Error ? err.message : '未知错误'}`)
              }
            }}
          />
        </div>
      </div>

      <StatusBar
        projectName={projectId}
        stageName="设计方案"
        artifactName={TABS.find((t) => t.id === activeTab)?.label || '-'}
        version="v1"
      />
    </div>
  )
}
