import { useEffect, useMemo, useState, useCallback } from 'react'
import { useProjectContext } from '../../../App'
import { useRequirementStudioStore } from '../../../stores/requirementStudioStore'
import { useExecutionStore } from '../../../stores/executionStore'
import { fetchStudioStatus, executeStage, fetchArtifacts } from '../../../services/requirementStudio'
import { getArtifactContent, saveArtifactContent } from '../../../services/artifact'
import { createProjectReview } from '../../../services/projectReview'
import { listUserStories, createUserStory, importUserStoriesFromRequirements } from '../../../services/userStory'
import { fetchProjectOverview } from '../../../services/project'
import TaskTree, { type TaskItem } from '../../../components/TaskTree'
import ArtifactRenderer from '../../../components/ArtifactRenderer'
import ExecutionPanel from '../../../components/ExecutionPanel'
import StatusBar from '../../../components/StatusBar'
import ReviewPanel from '../../../components/ReviewPanel'
import SizeEstimateCard, { type SizeEstimate } from '../../../components/SizeEstimateCard'
import UserStoryTable, { type UserStory } from '../../../components/UserStoryTable'
import AcceptanceCriteriaTable, { type AcceptanceCriterion } from '../../../components/AcceptanceCriteriaTable'

const VIEW_TABS = [
  { id: 'outline', label: '概要视图' },
  { id: 'detailed', label: '详细视图' },
  { id: 'history', label: '版本历史' },
]

const OUTLINE_CONTENT_TABS = [
  { id: 'user-stories', label: '👤 用户故事' },
  { id: 'prd', label: '📝 概要 PRD' },
  { id: 'sketch', label: '🎨 草图' },
  { id: 'acceptance', label: '✅ 验收标准' },
]

const DETAILED_CONTENT_TABS = [
  { id: 'markdown', label: 'Markdown' },
  { id: 'swagger', label: 'Swagger' },
  { id: 'yaml', label: 'YAML' },
  { id: 'html', label: 'HTML' },
]

const OUTLINE_TASKS: TaskItem[] = [
  { taskId: 'brainstorm', name: '脑暴纪要', status: 'INHERITED', type: 'inherit', module: '概要需求', description: '继承自脑暴室阶段', isReadOnly: true },
  { taskId: 'user-stories', name: '用户故事', status: 'NOT_STARTED', type: 'skill', module: '概要需求', description: '基于脑暴纪要提取用户故事' },
  { taskId: 'prd-outline', name: 'PRD（概要）', status: 'NOT_STARTED', type: 'skill', module: '概要需求', description: '生成概要 PRD 文档' },
  { taskId: 'sketch', name: '草图', status: 'NOT_STARTED', type: 'skill', module: '概要需求', description: '生成低保真页面草图' },
  { taskId: 'acceptance-criteria', name: '验收标准', status: 'NOT_STARTED', type: 'skill', module: '概要需求', description: '生成验收标准清单' },
]

const DETAILED_TASKS: TaskItem[] = [
  { taskId: 'import-outline', name: '导入概要需求', status: 'INHERITED', type: 'inherit', module: '详细需求', description: '自动继承概要需求产物', isReadOnly: true },
  { taskId: 'spec-detailed', name: '详细规格', status: 'NOT_STARTED', type: 'skill', module: '详细需求', description: '编写详细需求规格书' },
  { taskId: 'interface-draft', name: '接口契约初稿', status: 'NOT_STARTED', type: 'skill', module: '详细需求', description: '定义接口契约初稿' },
  { taskId: 'data-model', name: '数据模型', status: 'NOT_STARTED', type: 'skill', module: '详细需求', description: '定义数据模型' },
  { taskId: 'review', name: '审查迭代', status: 'NOT_STARTED', type: 'skill', module: '详细需求', description: '审查并迭代详细需求' },
]

const DEMO_PRD = `# 订单系统概要需求文档

## 1. 背景与目标

构建一个支持多渠道接入的订单管理系统...

## 2. 功能范围

- 订单创建与管理
- 状态流转与通知
- 库存联动检查

## 3. 非功能需求

- 支持 1000 QPS
- 响应时间 < 200ms

## 4. 用户故事映射

| ID | 描述 | 优先级 |
|----|------|--------|
| US-01 | 创建新订单 | P0 |
| US-02 | 查看订单列表 | P0 |
`

const DEMO_SKETCH = '<svg viewBox="0 0 600 320" xmlns="http://www.w3.org/2000/svg">\n' +
  '  <rect x="20" y="20" width="160" height="100" rx="6" fill="#f9fafb" stroke="#d1d5db" stroke-width="2"/>\n' +
  '  <text x="100" y="45" text-anchor="middle" font-size="13" font-weight="600" fill="#374151">订单列表页</text>\n' +
  '  <text x="30" y="65" font-size="11" fill="#6b7280">• 搜索栏</text>\n' +
  '  <text x="30" y="82" font-size="11" fill="#6b7280">• 筛选器</text>\n' +
  '  <text x="30" y="99" font-size="11" fill="#6b7280">• 数据表格</text>\n' +
  '  <rect x="230" y="20" width="160" height="100" rx="6" fill="#f9fafb" stroke="#d1d5db" stroke-width="2"/>\n' +
  '  <text x="310" y="45" text-anchor="middle" font-size="13" font-weight="600" fill="#374151">订单创建页</text>\n' +
  '  <text x="240" y="65" font-size="11" fill="#6b7280">• 商品选择</text>\n' +
  '  <text x="240" y="82" font-size="11" fill="#6b7280">• 数量输入</text>\n' +
  '  <text x="240" y="99" font-size="11" fill="#6b7280">• 提交按钮</text>\n' +
  '  <rect x="125" y="180" width="160" height="100" rx="6" fill="#f9fafb" stroke="#d1d5db" stroke-width="2"/>\n' +
  '  <text x="205" y="205" text-anchor="middle" font-size="13" font-weight="600" fill="#374151">订单详情页</text>\n' +
  '  <text x="135" y="225" font-size="11" fill="#6b7280">• 状态时间线</text>\n' +
  '  <text x="135" y="242" font-size="11" fill="#6b7280">• 操作按钮</text>\n' +
  '  <text x="135" y="259" font-size="11" fill="#6b7280">• 物流跟踪</text>\n' +
  '  <line x1="180" y1="70" x2="230" y2="70" stroke="#9ca3af" stroke-width="2" marker-end="url(#arrow)"/>\n' +
  '  <line x1="310" y1="120" x2="310" y2="150" stroke="#9ca3af" stroke-width="2" marker-end="url(#arrow)"/>\n' +
  '  <line x1="310" y1="150" x2="205" y2="180" stroke="#9ca3af" stroke-width="2" marker-end="url(#arrow)"/>\n' +
  '  <defs>\n' +
  '    <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">\n' +
  '      <path d="M0,0 L0,6 L9,3 z" fill="#9ca3af"/>\n' +
  '    </marker>\n' +
  '  </defs>\n' +
  '</svg>'

const DETAILED_GUIDE = `## 📋 详细需求

在此阶段，将概要需求拆分为详细的功能规格说明。

**主要任务：**
- 编写用户故事与验收标准
- 定义接口契约与数据模型
- 输出详细需求规格书

**操作提示：**
1. 导入概要需求作为输入产物
2. 运行需求拆解 Skill 生成详细任务
3. 在 Swagger/YAML 标签中查看接口定义`

// 验收标准校验规则
function validateAcceptanceCriteria(criteria: AcceptanceCriterion[]): Array<{ id: string; issue: string; suggestion: string }> {
  const issues: Array<{ id: string; issue: string; suggestion: string }> = []
  for (const c of criteria) {
    const text = c.description.toLowerCase()
    if (text.includes('快') || text.includes('大量') || text.includes('安全') || text.includes('高') || text.includes('低')) {
      if (!/\d+/.test(c.description)) {
        issues.push({ id: c.id, issue: `"${c.description}" 无量化指标`, suggestion: '添加具体的数值或边界' })
      }
    }
    if (text.includes('支持') && !text.includes('通过')) {
      issues.push({ id: c.id, issue: `"${c.description}" 验收方法不明确`, suggestion: '明确验收方法或测试步骤' })
    }
  }
  return issues
}

export default function RequirementPlanPage() {
  const { currentProjectId } = useProjectContext()
  const projectId = currentProjectId

  const [viewTab, setViewTab] = useState('outline')
  const [contentTab, setContentTab] = useState('user-stories')
  const [userStories, setUserStories] = useState<UserStory[]>([])
  const [acceptanceCriteria, setAcceptanceCriteria] = useState<AcceptanceCriterion[]>([])
  const [sizeEstimate, setSizeEstimate] = useState<SizeEstimate | null>(null)
  const [prdContent, setPrdContent] = useState(DEMO_PRD)
  const [prdArtifactId, setPrdArtifactId] = useState<string | null>(null)
  const [loadingStories, setLoadingStories] = useState(false)
  const [validationIssues, setValidationIssues] = useState<Array<{ id: string; issue: string; suggestion: string }>>([])
  const [showValidationModal, setShowValidationModal] = useState(false)
  const [showStoryModal, setShowStoryModal] = useState(false)
  const [newStoryForm, setNewStoryForm] = useState({ title: '', description: '', pageDesc: '', priority: 'P1', status: 'DRAFT' })

  const {
    selectedTaskId,
    selectTask,
    artifactContent,
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

  // Load PRD artifact content when projectId changes
  useEffect(() => {
    if (!projectId) return
    fetchArtifacts(projectId)
      .then((artifacts) => {
        // Find PRD artifact by file_name or file_type
        const prdArtifact = artifacts.find(
          (a) => a.file_name.toLowerCase().includes('prd') || a.file_type === 'markdown',
        )
        if (prdArtifact) {
          setPrdArtifactId(prdArtifact.artifact_id)
          return getArtifactContent(prdArtifact.artifact_id)
        }
        return null
      })
      .then((content) => {
        if (content) {
          setPrdContent(content)
          useRequirementStudioStore.getState().setArtifactContent(content)
        }
      })
      .catch((err) => {
        console.warn('加载PRD产物失败:', err)
      })
  }, [projectId])
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
        setError(null)
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : '加载阶段状态失败')
      })
      .finally(() => setLoading(false))
  }, [projectId, setLoading, setError, setStageStatuses])

  // Load user stories from API
  useEffect(() => {
    if (!projectId) return
    setLoadingStories(true)
    listUserStories(projectId)
      .then((stories) => {
        const mapped: UserStory[] = stories.map((s) => ({
          id: s.story_id,
          role: s.title?.split(' ')[0] || '用户',
          description: s.description || '',
          priority: (s.priority?.toUpperCase() as any) || 'P2',
          status: s.status === 'CONFIRMED' ? 'confirmed' : s.status === 'MODIFIED' ? 'modified' : 'generated',
          acceptanceCriteria: s.acceptance_criteria ? JSON.parse(s.acceptance_criteria) : [],
          createdAt: s.created_at || '',
          updatedAt: s.updated_at || '',
        }))
        setUserStories(mapped)
        // Derive acceptance criteria from user stories
        const ac: AcceptanceCriterion[] = []
        mapped.forEach((us) => {
          us.acceptanceCriteria.forEach((desc, idx) => {
            ac.push({
              id: `AC-${us.id}-${idx}`,
              relatedStoryId: us.id,
              relatedStoryName: `${us.id} ${us.role}`,
              description: desc,
              priority: us.priority,
              status: 'generated',
              createdAt: us.createdAt,
            })
          })
        })
        setAcceptanceCriteria(ac)
      })
      .catch(() => {
        // Fallback to empty if API fails (project may not have stories yet)
        setUserStories([])
        setAcceptanceCriteria([])
      })
      .finally(() => setLoadingStories(false))
  }, [projectId])

  // Load size estimate from project overview
  useEffect(() => {
    if (!projectId) return
    fetchProjectOverview(projectId)
      .then((overview) => {
        const est = overview.size_estimate
        if (est) {
          setSizeEstimate({
            moduleCount: est.module_count || 0,
            interfaceCount: est.interface_count || 0,
            pageCount: est.page_count || 0,
            entityCount: 0,
            complexity: (est.tech_complexity as 'medium' | 'low' | 'high') || 'medium',
            riskLevel: (est.risk_level as 'low' | 'medium' | 'high') || 'low',
            recommendedPath: 'standard',
            estimatedWeeks: 3,
            estimatedPersonMonths: 1.5,
          })
        }
      })
      .catch(() => setSizeEstimate(null))
  }, [projectId])

  const stageTasks = useMemo((): TaskItem[] => {
    if (viewTab === 'outline') return OUTLINE_TASKS
    if (viewTab === 'detailed') return DETAILED_TASKS
    return []
  }, [viewTab])

  const handleTaskSelect = useCallback(
    (taskId: string) => {
      selectTask(taskId)
      if (viewTab === 'outline') {
        const tabMap: Record<string, string> = {
          'user-stories': 'user-stories',
          'prd-outline': 'prd',
          sketch: 'sketch',
          'acceptance-criteria': 'acceptance',
        }
        if (tabMap[taskId]) setContentTab(tabMap[taskId])
      }
    },
    [viewTab, selectTask]
  )

  const handleTaskExecute = useCallback(async (_taskId: string) => {
    if (!projectId) return
    const stageId = viewTab === 'outline' ? 'requirement-outline' : 'requirement-detailed'
    setExecutionStatus('prep')
    appendExecutionLog('> 初始化上下文...')
    try {
      connectSSE(projectId)
      await executeStage(projectId, stageId)
      setExecutionStatus('exec')
      appendExecutionLog('> 执行中...')
      // Simulate completion after 2s for demo (real would use SSE)
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
  }, [projectId, viewTab, setExecutionStatus, appendExecutionLog, connectSSE, disconnectSSE])

  const handleTaskView = useCallback((_taskId: string) => {
    // For inherited tasks, just switch to the corresponding content tab
    if (_taskId === 'brainstorm') {
      setContentTab('prd')
      selectTask(_taskId)
    } else if (_taskId === 'import-outline') {
      setContentTab('markdown')
      selectTask(_taskId)
    }
  }, [selectTask])

  const handleEditSave = useCallback(async (content: string) => {
    setPrdContent(content)
    if (!prdArtifactId) {
      appendExecutionLog('> 警告: 未找到PRD产物，无法保存到后端')
      return
    }
    try {
      await saveArtifactContent(prdArtifactId, content)
      appendExecutionLog('> PRD内容已保存')
    } catch (err) {
      appendExecutionLog(`> 保存PRD失败: ${err instanceof Error ? err.message : '未知错误'}`)
    }
  }, [prdArtifactId, appendExecutionLog])

  const handleAddStory = useCallback(async () => {
    if (!projectId) return
    try {
      const story = await createUserStory(projectId, {
        title: newStoryForm.title,
        description: newStoryForm.description,
        page_desc: newStoryForm.pageDesc,
        priority: newStoryForm.priority,
        status: newStoryForm.status,
      })
      const mapped: UserStory = {
        id: story.story_id,
        role: story.title?.split(' ')[0] || '用户',
        description: story.description || '',
        priority: (story.priority?.toUpperCase() as any) || 'P2',
        status: 'generated',
        acceptanceCriteria: story.acceptance_criteria ? JSON.parse(story.acceptance_criteria) : [],
        createdAt: story.created_at || '',
        updatedAt: story.updated_at || '',
      }
      setUserStories((prev) => [...prev, mapped])
      setShowStoryModal(false)
      setNewStoryForm({ title: '', description: '', pageDesc: '', priority: 'P1', status: 'DRAFT' })
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建用户故事失败')
    }
  }, [projectId, newStoryForm, setError])

  const handleImportStories = useCallback(async () => {
    if (!projectId) return
    try {
      const result = await importUserStoriesFromRequirements(projectId)
      // Reload stories
      const stories = await listUserStories(projectId)
      const mapped: UserStory[] = stories.map((s) => ({
        id: s.story_id,
        role: s.title?.split(' ')[0] || '用户',
        description: s.description || '',
        priority: (s.priority?.toUpperCase() as any) || 'P2',
        status: 'generated',
        acceptanceCriteria: s.acceptance_criteria ? JSON.parse(s.acceptance_criteria) : [],
        createdAt: s.created_at || '',
        updatedAt: s.updated_at || '',
      }))
      setUserStories(mapped)
      appendExecutionLog(`> 导入完成: ${result.imported_count} 条用户故事`)
    } catch (err) {
      setError(err instanceof Error ? err.message : '导入用户故事失败')
    }
  }, [projectId, appendExecutionLog, setError])

  const handleValidateCriteria = useCallback(() => {
    const issues = validateAcceptanceCriteria(acceptanceCriteria)
    setValidationIssues(issues)
    setShowValidationModal(true)
  }, [acceptanceCriteria])

  const renderOutlineContent = () => {
    switch (contentTab) {
      case 'user-stories':
        return (
          <UserStoryTable
            stories={userStories}
            onAdd={() => setShowStoryModal(true)}
            onDelete={(id) => setUserStories((prev) => prev.filter((s) => s.id !== id))}
            onConfirm={(id) => setUserStories((prev) => prev.map((s) => s.id === id ? { ...s, status: 'confirmed' as const } : s))}
            onImport={handleImportStories}
            loading={loadingStories}
          />
        )
      case 'prd':
        return <ArtifactRenderer content={artifactContent || prdContent} type="markdown" onEdit={handleEditSave} />
      case 'sketch':
        return <ArtifactRenderer content={artifactContent || DEMO_SKETCH} type="svg" />
      case 'acceptance':
        return (
          <AcceptanceCriteriaTable
            criteria={acceptanceCriteria}
            onAdd={() => {}}
            onDelete={() => {}}
            onConfirm={() => {}}
            onValidate={handleValidateCriteria}
          />
        )
      default:
        return null
    }
  }

  const renderDetailedContent = () => {
    return <ArtifactRenderer content={artifactContent || DETAILED_GUIDE} type={contentTab as any} onEdit={handleEditSave} />
  }

  const contentTabs = viewTab === 'outline' ? OUTLINE_CONTENT_TABS : DETAILED_CONTENT_TABS

  if (!projectId) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280' }}>
        请先在顶部选择项目
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#fff', borderRadius: 8, border: '1px solid #e5e7eb', overflow: 'hidden' }}>
      {/* 顶部视图切换 */}
      <div style={{ display: 'flex', borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
        {VIEW_TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              setViewTab(tab.id)
              if (tab.id === 'outline') setContentTab('user-stories')
              else if (tab.id === 'detailed') setContentTab('markdown')
            }}
            style={{
              padding: '10px 20px',
              fontSize: 13,
              border: 'none',
              background: viewTab === tab.id ? '#fff' : 'transparent',
              color: viewTab === tab.id ? '#2563eb' : '#6b7280',
              borderBottom: viewTab === tab.id ? '2px solid #2563eb' : '2px solid transparent',
              cursor: 'pointer',
              fontWeight: viewTab === tab.id ? 600 : 400,
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
          onTaskSelect={handleTaskSelect}
          onTaskExecute={handleTaskExecute}
          onTaskView={handleTaskView}
        />

        {/* 中间：内容区 */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', borderRight: '1px solid #e5e7eb' }}>
          <div style={{ display: 'flex', borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
            {contentTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setContentTab(tab.id)}
                style={{
                  padding: '8px 16px',
                  fontSize: 13,
                  border: 'none',
                  background: contentTab === tab.id ? '#fff' : 'transparent',
                  color: contentTab === tab.id ? '#2563eb' : '#6b7280',
                  borderBottom: contentTab === tab.id ? '2px solid #2563eb' : '2px solid transparent',
                  cursor: 'pointer',
                  fontWeight: contentTab === tab.id ? 600 : 400,
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <div style={{ flex: 1, overflow: 'auto' }}>
            {viewTab === 'outline' ? renderOutlineContent() : viewTab === 'detailed' ? renderDetailedContent() : (
              <div style={{ padding: 24, color: '#6b7280' }}>版本历史视图开发中...</div>
            )}
          </div>
          {viewTab === 'outline' && sizeEstimate && <SizeEstimateCard estimate={sizeEstimate} />}
        </div>

        {/* 右侧：执行与审查面板 */}
        <div style={{ width: 300, minWidth: 300, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <ExecutionPanel
            status={executionStatus}
            logs={executionLogs}
            skillName={viewTab === 'outline' ? 'requirement-extraction' : 'detailed-requirement'}
            onExecute={() => {
              const currentTask = stageTasks.find(t => t.taskId === selectedTaskId)
              if (currentTask && !currentTask.isReadOnly) {
                handleTaskExecute(currentTask.taskId)
              } else {
                setExecutionStatus('failed')
                appendExecutionLog('> 请先选择一个可执行的任务')
              }
            }}
            onRetry={() => {
              setExecutionStatus('idle')
            }}
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
                  item_id: `reqplan-${viewTab}-${Date.now()}`,
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
        stageName="需求方案"
        artifactName={viewTab === 'outline' ? '概要视图' : viewTab === 'detailed' ? '详细视图' : '版本历史'}
        version="v1"
      />

      {/* 新建用户故事弹窗 */}
      {showStoryModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50
        }}>
          <div style={{ background: '#fff', borderRadius: 8, padding: 24, width: 480, maxHeight: '80vh', overflow: 'auto' }}>
            <h3 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 600 }}>新建用户故事</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: 13, color: '#374151', fontWeight: 500 }}>标题</label>
                <input
                  value={newStoryForm.title}
                  onChange={(e) => setNewStoryForm((p) => ({ ...p, title: e.target.value }))}
                  placeholder="如：订单管理员创建新订单"
                  style={{ width: '100%', padding: 8, border: '1px solid #e5e7eb', borderRadius: 4, fontSize: 13, marginTop: 4 }}
                />
              </div>
              <div>
                <label style={{ fontSize: 13, color: '#374151', fontWeight: 500 }}>描述</label>
                <textarea
                  value={newStoryForm.description}
                  onChange={(e) => setNewStoryForm((p) => ({ ...p, description: e.target.value }))}
                  placeholder="作为...我需要...以便..."
                  rows={3}
                  style={{ width: '100%', padding: 8, border: '1px solid #e5e7eb', borderRadius: 4, fontSize: 13, marginTop: 4, resize: 'vertical' }}
                />
              </div>
              <div>
                <label style={{ fontSize: 13, color: '#374151', fontWeight: 500 }}>页面描述（用于草图生成）</label>
                <textarea
                  value={newStoryForm.pageDesc}
                  onChange={(e) => setNewStoryForm((p) => ({ ...p, pageDesc: e.target.value }))}
                  placeholder="描述该用户故事涉及的页面元素..."
                  rows={2}
                  style={{ width: '100%', padding: 8, border: '1px solid #e5e7eb', borderRadius: 4, fontSize: 13, marginTop: 4, resize: 'vertical' }}
                />
              </div>
              <div style={{ display: 'flex', gap: 12 }}>
                <div style={{ flex: 1 }}>
                  <label style={{ fontSize: 13, color: '#374151', fontWeight: 500 }}>优先级</label>
                  <select
                    value={newStoryForm.priority}
                    onChange={(e) => setNewStoryForm((p) => ({ ...p, priority: e.target.value }))}
                    style={{ width: '100%', padding: 8, border: '1px solid #e5e7eb', borderRadius: 4, fontSize: 13, marginTop: 4 }}
                  >
                    <option value="P0">P0</option>
                    <option value="P1">P1</option>
                    <option value="P2">P2</option>
                    <option value="P3">P3</option>
                  </select>
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ fontSize: 13, color: '#374151', fontWeight: 500 }}>状态</label>
                  <select
                    value={newStoryForm.status}
                    onChange={(e) => setNewStoryForm((p) => ({ ...p, status: e.target.value }))}
                    style={{ width: '100%', padding: 8, border: '1px solid #e5e7eb', borderRadius: 4, fontSize: 13, marginTop: 4 }}
                  >
                    <option value="DRAFT">草稿</option>
                    <option value="CONFIRMED">已确认</option>
                  </select>
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 20 }}>
              <button
                onClick={() => setShowStoryModal(false)}
                style={{ padding: '8px 16px', fontSize: 13, border: '1px solid #e5e7eb', background: '#fff', borderRadius: 4, cursor: 'pointer' }}
              >
                取消
              </button>
              <button
                onClick={handleAddStory}
                disabled={!newStoryForm.title}
                style={{
                  padding: '8px 16px', fontSize: 13, background: '#2563eb', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer',
                  opacity: !newStoryForm.title ? 0.6 : 1,
                }}
              >
                创建
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 验收标准校验弹窗 */}
      {showValidationModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50
        }}>
          <div style={{ background: '#fff', borderRadius: 8, padding: 24, width: 560, maxHeight: '70vh', overflow: 'auto' }}>
            <h3 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 600 }}>
              验收标准校验结果
            </h3>
            {validationIssues.length === 0 ? (
              <div style={{ color: '#16a34a', fontSize: 14, padding: '16px 0' }}>
                ✅ 所有验收标准通过校验！
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div style={{ fontSize: 13, color: '#374151', marginBottom: 4 }}>
                  ⚠️ 发现 {validationIssues.length} 项需要修改：
                </div>
                {validationIssues.map((issue) => (
                  <div key={issue.id} style={{ padding: 10, background: '#fffbeb', borderRadius: 4, border: '1px solid #fde68a' }}>
                    <div style={{ fontSize: 13, fontWeight: 500, color: '#92400e' }}>{issue.issue}</div>
                    <div style={{ fontSize: 12, color: '#78350f', marginTop: 4 }}>建议: {issue.suggestion}</div>
                  </div>
                ))}
              </div>
            )}
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 20 }}>
              <button
                onClick={() => setShowValidationModal(false)}
                style={{ padding: '8px 16px', fontSize: 13, background: '#2563eb', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
