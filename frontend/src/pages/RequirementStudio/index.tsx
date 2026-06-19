import { useEffect, useMemo, useState, useCallback } from 'react'
import { useSearchParams, useLocation, useNavigate } from 'react-router'
import { useRequirementStudioStore } from '../../stores/requirementStudioStore'
import { fetchStudioStatus } from '../../services/requirementStudio'
import StageNavBar, { type StageInfo } from '../../components/StageNavBar'
import TaskTree, { type TaskItem } from '../../components/TaskTree'
import ArtifactRenderer from '../../components/ArtifactRenderer'
import ExecutionPanel from '../../components/ExecutionPanel'
import StatusBar from '../../components/StatusBar'
import ReviewPanel from '../../components/ReviewPanel'
import SizeEstimateCard, { type SizeEstimate } from '../../components/SizeEstimateCard'
import UserStoryTable, { type UserStory } from '../../components/UserStoryTable'
import AcceptanceCriteriaTable, { type AcceptanceCriterion } from '../../components/AcceptanceCriteriaTable'

const STAGES: StageInfo[] = [
  { id: 'requirement-outline', name: '概要需求', status: 'not_started' },
  { id: 'requirement-detailed', name: '详细需求', status: 'not_started' },
  { id: 'design-outline', name: '概要设计', status: 'not_started' },
  { id: 'design-detailed', name: '详细设计', status: 'not_started' },
  { id: 'artifacts', name: '设计产物', status: 'not_started' },
  { id: 'governance', name: '架构治理', status: 'not_started' },
]

// 通用产物 Tab（用于非概要需求阶段）
const GENERIC_TABS = [
  { id: 'markdown', label: 'Markdown' },
  { id: 'swagger', label: 'Swagger' },
  { id: 'svg', label: 'SVG' },
  { id: 'html', label: 'HTML' },
  { id: 'yaml', label: 'YAML' },
]

// 概要需求阶段专用 Tab
const OUTLINE_TABS = [
  { id: 'user-stories', label: '👤 用户故事' },
  { id: 'prd', label: '📝 PRD' },
  { id: 'sketch', label: '🎨 草图' },
  { id: 'acceptance', label: '✅ 验收标准' },
]

// 概要需求阶段专用任务
const OUTLINE_TASKS: TaskItem[] = [
  { taskId: 'brainstorm', name: '脑暴纪要', status: 'PASSED', type: 'inherit', module: '概要需求' },
  { taskId: 'user-stories', name: '用户故事', status: 'NOT_STARTED', type: 'skill', module: '概要需求' },
  { taskId: 'prd-outline', name: 'PRD（概要）', status: 'NOT_STARTED', type: 'skill', module: '概要需求' },
  { taskId: 'sketch', name: '草图', status: 'NOT_STARTED', type: 'skill', module: '概要需求' },
  { taskId: 'acceptance-criteria', name: '验收标准', status: 'NOT_STARTED', type: 'skill', module: '概要需求' },
]

// 演示数据：用户故事
const DEMO_USER_STORIES: UserStory[] = [
  {
    id: 'US-01',
    role: '订单管理员',
    description: '作为订单管理员，我需要创建新订单，以便记录客户购买信息',
    priority: 'P0',
    status: 'generated',
    acceptanceCriteria: [
      '成功创建订单后，系统返回唯一订单号',
      '库存不足时，返回明确错误信息并阻止创建',
      '订单创建时间记录在 200ms 内完成',
    ],
    createdAt: '2026-06-17',
    updatedAt: '2026-06-17',
  },
  {
    id: 'US-02',
    role: '订单管理员',
    description: '作为订单管理员，我需要查看订单列表，以便跟踪所有订单状态',
    priority: 'P0',
    status: 'generated',
    acceptanceCriteria: [
      '列表支持分页，默认 20 条/页',
      '支持按状态、时间范围筛选',
      '支持按订单号、客户名称搜索',
    ],
    createdAt: '2026-06-17',
    updatedAt: '2026-06-17',
  },
  {
    id: 'US-03',
    role: '仓库人员',
    description: '作为仓库人员，我需要更新订单发货状态，以便通知客户物流信息',
    priority: 'P1',
    status: 'generated',
    acceptanceCriteria: [
      '支持批量更新订单状态',
      '状态变更后自动触发通知',
      '记录状态变更历史',
    ],
    createdAt: '2026-06-17',
    updatedAt: '2026-06-17',
  },
  {
    id: 'US-04',
    role: '系统',
    description: '作为系统，我需要自动取消超期未支付订单，以便释放库存',
    priority: 'P2',
    status: 'generated',
    acceptanceCriteria: [
      '超期时间可配置，默认 24 小时',
      '取消前发送提醒通知',
      '取消后释放库存并记录日志',
    ],
    createdAt: '2026-06-17',
    updatedAt: '2026-06-17',
  },
]

// 演示数据：验收标准
const DEMO_ACCEPTANCE_CRITERIA: AcceptanceCriterion[] = [
  {
    id: 'AC-01',
    relatedStoryId: 'US-01',
    relatedStoryName: 'US-01 创建订单',
    description: '成功创建订单后，系统返回唯一订单号',
    priority: 'P0',
    status: 'generated',
    createdAt: '2026-06-17',
  },
  {
    id: 'AC-02',
    relatedStoryId: 'US-01',
    relatedStoryName: 'US-01 创建订单',
    description: '库存不足时，返回明确错误信息并阻止创建',
    priority: 'P0',
    status: 'generated',
    createdAt: '2026-06-17',
  },
  {
    id: 'AC-03',
    relatedStoryId: 'US-02',
    relatedStoryName: 'US-02 查看列表',
    description: '列表支持分页，默认 20 条/页',
    priority: 'P1',
    status: 'generated',
    createdAt: '2026-06-17',
  },
  {
    id: 'AC-04',
    relatedStoryId: 'US-02',
    relatedStoryName: 'US-02 查看列表',
    description: '支持按状态、时间范围筛选',
    priority: 'P1',
    status: 'generated',
    createdAt: '2026-06-17',
  },
]

// 演示数据：规模初估
const DEMO_SIZE_ESTIMATE: SizeEstimate = {
  moduleCount: 3,
  interfaceCount: 8,
  pageCount: 5,
  entityCount: 6,
  complexity: 'medium',
  riskLevel: 'low',
  recommendedPath: 'standard',
  estimatedWeeks: 3,
  estimatedPersonMonths: 1.5,
  breakdown: [
    { moduleName: '订单管理', estimatedHours: 40 },
    { moduleName: '库存联动', estimatedHours: 24 },
    { moduleName: '通知系统', estimatedHours: 16 },
  ],
}

// PRD 演示内容
const DEMO_PRD = `# 订单系统概要需求文档

## 1. 背景与目标

构建一个支持多渠道接入的订单管理系统，覆盖从订单创建到完成的全生命周期管理。

## 2. 功能范围

### 2.1 订单创建与管理
- 支持多渠道订单接入（Web、App、API）
- 订单信息包含：商品、数量、价格、客户、地址
- 实时库存校验

### 2.2 状态流转与通知
- 订单状态：待支付 → 已支付 → 处理中 → 已发货 → 已完成
- 状态变更自动触发通知（短信、邮件、站内信）

### 2.3 库存联动检查
- 创建订单时实时扣减库存
- 取消/超时订单自动释放库存
- 库存不足时阻止订单创建

## 3. 非功能需求

- 支持 1000 QPS
- 响应时间 < 200ms
- 数据一致性：库存扣减与订单创建必须原子性

## 4. 用户故事映射

| ID | 描述 | 优先级 |
|----|------|--------|
| US-01 | 创建新订单 | P0 |
| US-02 | 查看订单列表 | P0 |
| US-03 | 更新订单状态 | P1 |
| US-04 | 超期自动取消 | P2 |
`

// 草图演示内容（SVG）
const DEMO_SKETCH = '<svg viewBox="0 0 600 320" xmlns="http://www.w3.org/2000/svg">\n' +
  '  <!-- 订单列表页 -->\n' +
  '  <rect x="20" y="20" width="160" height="100" rx="6" fill="#f9fafb" stroke="#d1d5db" stroke-width="2"/>\n' +
  '  <text x="100" y="45" text-anchor="middle" font-size="13" font-weight="600" fill="#374151">订单列表页</text>\n' +
  '  <text x="30" y="65" font-size="11" fill="#6b7280">• 搜索栏</text>\n' +
  '  <text x="30" y="82" font-size="11" fill="#6b7280">• 筛选器</text>\n' +
  '  <text x="30" y="99" font-size="11" fill="#6b7280">• 数据表格</text>\n' +
  '\n' +
  '  <!-- 订单创建页 -->\n' +
  '  <rect x="230" y="20" width="160" height="100" rx="6" fill="#f9fafb" stroke="#d1d5db" stroke-width="2"/>\n' +
  '  <text x="310" y="45" text-anchor="middle" font-size="13" font-weight="600" fill="#374151">订单创建页</text>\n' +
  '  <text x="240" y="65" font-size="11" fill="#6b7280">• 商品选择</text>\n' +
  '  <text x="240" y="82" font-size="11" fill="#6b7280">• 数量输入</text>\n' +
  '  <text x="240" y="99" font-size="11" fill="#6b7280">• 提交按钮</text>\n' +
  '\n' +
  '  <!-- 订单详情页 -->\n' +
  '  <rect x="125" y="180" width="160" height="100" rx="6" fill="#f9fafb" stroke="#d1d5db" stroke-width="2"/>\n' +
  '  <text x="205" y="205" text-anchor="middle" font-size="13" font-weight="600" fill="#374151">订单详情页</text>\n' +
  '  <text x="135" y="225" font-size="11" fill="#6b7280">• 状态时间线</text>\n' +
  '  <text x="135" y="242" font-size="11" fill="#6b7280">• 操作按钮</text>\n' +
  '  <text x="135" y="259" font-size="11" fill="#6b7280">• 物流跟踪</text>\n' +
  '\n' +
  '  <!-- 连接线 -->\n' +
  '  <line x1="180" y1="70" x2="230" y2="70" stroke="#9ca3af" stroke-width="2" marker-end="url(#arrow)"/>\n' +
  '  <line x1="310" y1="120" x2="310" y2="150" stroke="#9ca3af" stroke-width="2" marker-end="url(#arrow)"/>\n' +
  '  <line x1="310" y1="150" x2="205" y2="180" stroke="#9ca3af" stroke-width="2" marker-end="url(#arrow)"/>\n' +
  '  <line x1="205" y1="150" x2="205" y2="180" stroke="#9ca3af" stroke-width="2" marker-end="url(#arrow)"/>\n' +
  '\n' +
  '  <!-- 箭头定义 -->\n' +
  '  <defs>\n' +
  '    <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">\n' +
  '      <path d="M0,0 L0,6 L9,3 z" fill="#9ca3af"/>\n' +
  '    </marker>\n' +
  '  </defs>\n' +
  '\n' +
  '  <!-- 图例 -->\n' +
  '  <text x="420" y="280" font-size="11" fill="#6b7280">—— 页面跳转</text>\n' +
  '  <text x="420" y="298" font-size="11" fill="#6b7280">→ 数据流</text>\n' +
  '</svg>'

export default function RequirementStudio() {
  const [searchParams] = useSearchParams()
  const location = useLocation()
  const navigate = useNavigate()
  const projectId = searchParams.get('projectId') || ''

  const {
    currentStage,
    setProjectId,
    setCurrentStage,
    stageStatus,
    setStageStatuses,
    selectedTaskId,
    selectTask,
    artifactContent,
    executionStatus,
    executionLogs,
    loading,
    error,
    setLoading,
    setError,
    annotations,
    setExecutionStatus,
    appendExecutionLog,
  } = useRequirementStudioStore()

  // 通用阶段使用 generic tab，概要需求阶段使用 outline tab
  const [activeTab, setActiveTab] = useState('markdown')

  useEffect(() => {
    setProjectId(projectId)
  }, [projectId, setProjectId])

  useEffect(() => {
    const pathParts = location.pathname.replace('/requirement-studio/', '').split('/')
    const pathStage = pathParts[0]
    if (pathStage && STAGES.some((s) => s.id === pathStage)) {
      setCurrentStage(pathStage)
    } else {
      setCurrentStage('requirement-outline')
    }
  }, [location.pathname, setCurrentStage])

  // 当阶段切换时，重置 activeTab
  useEffect(() => {
    if (currentStage === 'requirement-outline') {
      setActiveTab('user-stories')
    } else {
      setActiveTab('markdown')
    }
  }, [currentStage])

  useEffect(() => {
    if (!projectId) {
      setLoading(false)
      return
    }
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
        if (data.current_stage_id) {
          setCurrentStage(data.current_stage_id)
        }
        setError(null)
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : '加载阶段状态失败')
      })
      .finally(() => setLoading(false))
  }, [projectId, setLoading, setError, setCurrentStage, setStageStatuses])

  const handleStageChange = useCallback(
    (stageId: string) => {
      navigate(`/requirement-studio/${stageId}?projectId=${projectId}`)
    },
    [navigate, projectId]
  )

  const derivedStages = useMemo((): StageInfo[] => {
    return STAGES.map((s) => {
      const st = stageStatus[s.id]
      const status = st?.status || 'not_started'
      let derivedStatus: StageInfo['status'] = 'not_started'
      if (status === 'locked') derivedStatus = 'locked'
      else if (status === 'passed') derivedStatus = 'passed'
      else if (status === 'in_progress') derivedStatus = 'in_progress'
      else if (s.id === currentStage) derivedStatus = 'current'
      return {
        ...s,
        status: derivedStatus,
        progress: st?.progress || 0,
      }
    })
  }, [stageStatus, currentStage])

  // 非概要需求阶段的默认内容
  const defaultContent = useMemo(() => {
    const stageName = derivedStages.find((s) => s.id === currentStage)?.name || currentStage
    const guides: Record<string, string> = {
      'requirement-detailed': '## 📋 ' + stageName + '\n\n在此阶段，将概要需求拆分为详细的功能规格说明。\n\n**主要任务：**\n- 编写用户故事与验收标准\n- 定义接口契约与数据模型\n- 输出详细需求规格书\n\n**操作提示：**\n1. 导入概要需求作为输入产物\n2. 运行需求拆解 Skill 生成详细任务\n3. 在 Swagger/YAML 标签中查看接口定义',
      'design-outline': '## 🏗️ ' + stageName + '\n\n在此阶段，完成系统的高层架构设计。\n\n**主要任务：**\n- 定义 C4 模型 L1/L2 架构\n- 绘制系统上下文与容器图\n- 确定技术栈与部署拓扑\n\n**操作提示：**\n1. 在 SVG 标签中查看架构图\n2. 使用 C4 架构页面进行深度编辑（导航：架构设计 → C4 架构）\n3. 运行架构设计 Skill 生成容器图',
      'design-detailed': '## 🔧 ' + stageName + '\n\n在此阶段，完成组件级与代码级的详细设计。\n\n**主要任务：**\n- 定义 C4 L3 组件图\n- 设计数据库表结构与 API 详细规格\n- 输出 OpenUI 页面规格与数据绑定规则\n\n**操作提示：**\n1. 在 Swagger 标签中查看接口定义\n2. 使用 OpenUI 与数据绑定页面进行设计（导航：架构设计）\n3. 运行详细设计 Skill 生成组件图',
      'artifacts': '## 📦 ' + stageName + '\n\n在此阶段，汇总并管理所有设计产物。\n\n**主要任务：**\n- 汇总 Markdown / Swagger / SVG / YAML 产物\n- 进行版本管理与基线冻结\n- 执行产物一致性校验\n\n**操作提示：**\n1. 切换上方标签查看不同格式产物\n2. 点击编辑按钮修改产物内容\n3. 在治理面板中创建基线',
      'governance': '## 🛡️ ' + stageName + '\n\n在此阶段，对设计产物进行架构治理与合规审查。\n\n**主要任务：**\n- 执行架构一致性扫描\n- 检查 C4 模型与代码的映射关系\n- 创建基线并管理变更请求\n\n**操作提示：**\n1. 使用架构治理中心进行全面分析（导航：需求设计室 → 架构治理）\n2. 运行治理扫描 Skill 检测架构偏差\n3. 在治理面板中提交变更请求',
    }
    return guides[currentStage] || '## ' + stageName + '\n\n当前阶段工作区。请选择左侧任务或执行 Skill 生成产物。'
  }, [currentStage, derivedStages])

  // 任务树数据
  const stageTasks = useMemo((): TaskItem[] => {
    if (currentStage === 'requirement-outline') {
      return OUTLINE_TASKS
    }
    const stage = stageStatus[currentStage]
    if (!stage || !stage.tasks) return []
    return stage.tasks.map((t: any) => ({
      taskId: t.task_id || t.taskId,
      name: t.task_name || t.name,
      status: (t.status || 'NOT_STARTED').toUpperCase(),
      type: t.task_type || t.type || 'task',
      module: t.module || '默认模块',
    }))
  }, [stageStatus, currentStage])

  // 当用户点击左侧任务时，同步切换中间 Tab
  const handleTaskSelect = useCallback(
    (taskId: string) => {
      selectTask(taskId)
      if (currentStage === 'requirement-outline') {
        const tabMap: Record<string, string> = {
          'user-stories': 'user-stories',
          'prd-outline': 'prd',
          sketch: 'sketch',
          'acceptance-criteria': 'acceptance',
        }
        if (tabMap[taskId]) {
          setActiveTab(tabMap[taskId])
        }
      }
    },
    [currentStage, selectTask]
  )

  // 渲染概要需求阶段的中间内容区
  const renderOutlineContent = () => {
    switch (activeTab) {
      case 'user-stories':
        return (
          <UserStoryTable
            stories={DEMO_USER_STORIES}
            onAdd={() => console.log('add user story')}
            onDelete={(id) => console.log('delete', id)}
            onConfirm={(id) => console.log('confirm', id)}
          />
        )
      case 'prd':
        return (
          <ArtifactRenderer
            content={artifactContent || DEMO_PRD}
            type="markdown"
            onEdit={(content) => console.log('edit prd', content)}
          />
        )
      case 'sketch':
        return (
          <ArtifactRenderer
            content={artifactContent || DEMO_SKETCH}
            type="svg"
            onEdit={(content) => console.log('edit sketch', content)}
          />
        )
      case 'acceptance':
        return (
          <AcceptanceCriteriaTable
            criteria={DEMO_ACCEPTANCE_CRITERIA}
            onAdd={() => console.log('add criterion')}
            onDelete={(id) => console.log('delete', id)}
            onConfirm={(id) => console.log('confirm', id)}
          />
        )
      default:
        return null
    }
  }

  // 渲染非概要需求阶段的中间内容区
  const renderGenericContent = () => {
    return (
      <ArtifactRenderer
        content={artifactContent || defaultContent}
        type={activeTab as any}
        onEdit={(content) => console.log('edit artifact', content)}
      />
    )
  }

  const isOutlineStage = currentStage === 'requirement-outline'
  const tabs = isOutlineStage ? OUTLINE_TABS : GENERIC_TABS

  if (!projectId) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280' }}>
        请先在顶部选择项目
      </div>
    )
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280' }}>
        加载中...
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#dc2626' }}>
        错误: {error}
      </div>
    )
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: '#fff',
        borderRadius: 8,
        border: '1px solid #e5e7eb',
        overflow: 'hidden',
      }}
    >
      <StageNavBar stages={derivedStages} currentStage={currentStage} onStageChange={handleStageChange} />
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <TaskTree
          tasks={stageTasks}
          selectedTaskId={selectedTaskId}
          onTaskSelect={handleTaskSelect}
          onTaskExecute={(taskId) => {
            console.log('execute task', taskId)
          }}
        />
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', borderRight: '1px solid #e5e7eb' }}>
          <div style={{ display: 'flex', borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  padding: '8px 16px',
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
          <div style={{ flex: 1, overflow: 'auto' }}>
            {isOutlineStage ? renderOutlineContent() : renderGenericContent()}
          </div>
          {/* 概要需求阶段显示规模初估卡片 */}
          {isOutlineStage && <SizeEstimateCard estimate={DEMO_SIZE_ESTIMATE} />}
        </div>
        <div style={{ width: 300, minWidth: 300, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <ExecutionPanel
            status={executionStatus}
            logs={executionLogs}
            skillName={isOutlineStage ? 'requirement-extraction' : 'requirement-skill'}
            onExecute={() => {
              setExecutionStatus('prep')
              appendExecutionLog('> 开始执行...')
              setTimeout(() => setExecutionStatus('exec'), 1000)
              setTimeout(() => {
                setExecutionStatus('post')
                appendExecutionLog('> 执行完成')
                setExecutionStatus('success')
              }, 2000)
            }}
            onRetry={() => {
              setExecutionStatus('idle')
              console.log('retry')
            }}
            onAbort={() => {
              setExecutionStatus('idle')
              appendExecutionLog('> 已中断')
              console.log('abort')
            }}
          />
          <ReviewPanel
            annotations={annotations as any}
            onSubmit={(comment) => {
              console.log('submit review', comment)
            }}
          />
        </div>
      </div>
      <StatusBar
        projectName={projectId}
        stageName={derivedStages.find((s) => s.id === currentStage)?.name || ''}
        artifactName={isOutlineStage ? (activeTab === 'user-stories' ? '用户故事' : activeTab === 'prd' ? 'PRD' : activeTab === 'sketch' ? '草图' : '验收标准') : '-'}
        version="v1"
      />
    </div>
  )
}
