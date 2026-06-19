import { useEffect, useMemo, useState } from 'react'
import { useProjectContext } from '../../../App'
import { useExecutionStore } from '../../../stores/executionStore'
import {
  fetchTasks,
  createTask,
  executeTask,
  fetchIssues,
  createIssue,
  feedbackIssue,
  type ExecutionTask,
  type ExecutionIssue,
} from '../../../services/execution'
import { createChangeRequest } from '../../../services/requirementStudio'

const ISSUE_TYPE_OPTIONS = [
  { value: 'compile_error', label: '编译错误' },
  { value: 'test_failure', label: '测试失败' },
  { value: 'arch_mismatch', label: '架构偏差' },
  { value: 'interface_mismatch', label: '接口不匹配' },
  { value: 'other', label: '其他' },
]

const ISSUE_STATUS_OPTIONS = [
  { value: 'open', label: '待处理' },
  { value: 'resolved', label: '已解决' },
  { value: 'closed', label: '已关闭' },
]

const TEST_STATUS_LABELS: Record<string, string> = {
  not_started: '未执行',
  in_progress: '执行中',
  passed: '通过',
  failed: '失败',
  blocked: '阻塞',
}

const TEST_STATUS_COLORS: Record<string, { bg: string; color: string }> = {
  not_started: { bg: '#f3f4f6', color: '#6b7280' },
  in_progress: { bg: '#dbeafe', color: '#2563eb' },
  passed: { bg: '#d1fae5', color: '#065f46' },
  failed: { bg: '#fef2f2', color: '#dc2626' },
  blocked: { bg: '#fef3c7', color: '#92400e' },
}

export default function TestingPage() {
  const { currentProjectId } = useProjectContext()
  const projectId = currentProjectId

  const { issues, selectedIssueId, setIssues, selectIssue, setLoading, setError } = useExecutionStore()

  const [tasks, setTasks] = useState<ExecutionTask[]>([])
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)

  const [filterType, setFilterType] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [createForm, setCreateForm] = useState({
    taskId: '',
    issueType: 'other' as 'compile_error' | 'test_failure' | 'arch_mismatch' | 'interface_mismatch' | 'other',
    errorLog: '',
    suggestedAction: 'retry' as 'retry' | 'feedback' | 'skip',
  })
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)
  const [feedbackForm, setFeedbackForm] = useState({
    targetArtifact: 'dd',
    changeDescription: '',
  })
  const [showTestReport, setShowTestReport] = useState(false)
  const [activeTab, setActiveTab] = useState('issues')

  // 测试用例创建
  const [showTestCaseForm, setShowTestCaseForm] = useState(false)
  const [testCaseForm, setTestCaseForm] = useState({
    name: '',
    parentModule: '',
    assignedSkill: '',
  })

  const ARTIFACT_OPTIONS = [
    { value: 'api-contract', label: '接口契约 (api-contract.yaml)' },
    { value: 'dd', label: '详细设计 (dd.md)' },
    { value: 'c4-l2', label: '系统结构 (c4-l2.dsl.yml)' },
  ]

  useEffect(() => {
    if (!projectId) return
    setLoading(true)
    Promise.all([
      fetchIssues(projectId),
      fetchTasks(projectId),
    ])
      .then(([issueData, taskData]) => {
        setIssues(issueData)
        setTasks(taskData)
        setError(null)
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : '加载失败')
      })
      .finally(() => setLoading(false))
  }, [projectId, setIssues, setLoading, setError])

  const testCases = useMemo(() => tasks.filter((t: any) => t.type === 'test'), [tasks])
  const filteredIssues = useMemo(() => {
    return issues.filter((issue: any) => {
      const matchType = !filterType || issue.issue_type === filterType
      const matchStatus = !filterStatus || issue.status === filterStatus
      return matchType && matchStatus
    })
  }, [issues, filterType, filterStatus])

  const selectedIssue = useMemo(() => {
    return issues.find((issue: any) => issue.issue_id === selectedIssueId) as ExecutionIssue | undefined
  }, [issues, selectedIssueId])

  const selectedTestCase = useMemo(() => {
    return tasks.find((t: any) => t.task_id === selectedTaskId) as ExecutionTask | undefined
  }, [tasks, selectedTaskId])

  const testStats = useMemo(() => {
    const total = testCases.length
    const passed = testCases.filter((t) => t.status === 'passed').length
    const failed = testCases.filter((t) => t.status === 'failed').length
    const inProgress = testCases.filter((t) => t.status === 'in_progress').length
    const notStarted = testCases.filter((t) => t.status === 'not_started').length
    return { total, passed, failed, inProgress, notStarted }
  }, [testCases])

  const handleCreateIssue = async () => {
    if (!projectId || !createForm.taskId) return
    try {
      setLoading(true)
      await createIssue(projectId, {
        task_id: createForm.taskId,
        issue_type: createForm.issueType,
        error_log: createForm.errorLog,
        suggested_action: createForm.suggestedAction,
      })
      const data = await fetchIssues(projectId)
      setIssues(data)
      setShowCreateForm(false)
      setCreateForm({ taskId: '', issueType: 'other', errorLog: '', suggestedAction: 'retry' })
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建问题失败')
    } finally {
      setLoading(false)
    }
  }

  const handleFeedback = async () => {
    if (!projectId || !selectedIssueId || !feedbackForm.targetArtifact) return
    try {
      setLoading(true)
      await feedbackIssue(projectId, selectedIssueId, {
        feedback_to_architecture: true,
        change_request_id: '',
      })
      await createChangeRequest(projectId, {
        title: `Bug 反馈: ${selectedIssue?.issue_type || '问题'}`,
        description: feedbackForm.changeDescription || `测试发现 ${selectedIssue?.issue_type}，需修改设计产物`,
        affected_artifacts: [feedbackForm.targetArtifact],
        target_stage_id: 'design-finalization',
      })
      const data = await fetchIssues(projectId)
      setIssues(data)
      setShowFeedbackModal(false)
      setFeedbackForm({ targetArtifact: 'dd', changeDescription: '' })
    } catch (err) {
      setError(err instanceof Error ? err.message : '反馈失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateTestCase = async () => {
    if (!projectId || !testCaseForm.name) return
    try {
      setLoading(true)
      await createTask(projectId, {
        name: testCaseForm.name,
        type: 'test',
        parent_module: testCaseForm.parentModule,
        assigned_skill_id: testCaseForm.assignedSkill,
      })
      const data = await fetchTasks(projectId)
      setTasks(data)
      setShowTestCaseForm(false)
      setTestCaseForm({ name: '', parentModule: '', assignedSkill: '' })
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建测试用例失败')
    } finally {
      setLoading(false)
    }
  }

  const handleExecuteTest = async (taskId: string) => {
    if (!projectId) return
    try {
      setLoading(true)
      await executeTask(projectId, taskId)
      const data = await fetchTasks(projectId)
      setTasks(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '执行失败')
    } finally {
      setLoading(false)
    }
  }

  if (!projectId) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280' }}>
        请先在顶部选择项目
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
      {/* 顶部 Tab 切换 */}
      <div style={{ display: 'flex', borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
        {['test-cases', 'issues', 'reports'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '10px 20px',
              fontSize: 13,
              border: 'none',
              background: activeTab === tab ? '#fff' : 'transparent',
              color: activeTab === tab ? '#2563eb' : '#6b7280',
              borderBottom: activeTab === tab ? '2px solid #2563eb' : '2px solid transparent',
              cursor: 'pointer',
              fontWeight: activeTab === tab ? 600 : 400,
            }}
          >
            {tab === 'test-cases' ? `测试用例 (${testStats.total})` : tab === 'issues' ? '问题追踪' : '测试报告'}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* 左侧：列表 */}
        <div style={{ width: 320, minWidth: 320, borderRight: '1px solid #e5e7eb', overflowY: 'auto', background: '#fff' }}>

          {/* 测试用例列表 */}
          {activeTab === 'test-cases' && (
            <>
              <div style={{ padding: '10px 12px', borderBottom: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>测试用例</div>
                  <div style={{ fontSize: 11, color: '#6b7280', marginTop: 2 }}>
                    <span style={{ color: '#16a34a' }}>{testStats.passed}</span> 通过 / <span style={{ color: '#dc2626' }}>{testStats.failed}</span> 失败 / <span>{testStats.notStarted}</span> 未执行
                  </div>
                </div>
                <button onClick={() => setShowTestCaseForm(true)} style={{ fontSize: 11, padding: '4px 10px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}>+ 新建</button>
              </div>
              {testCases.length === 0 && (
                <div style={{ padding: 24, textAlign: 'center', color: '#9ca3af', fontSize: 13 }}>
                  暂无测试用例，请创建
                </div>
              )}
              {testCases.map((tc) => {
                const isSelected = tc.task_id === selectedTaskId
                const status = tc.status
                const colors = TEST_STATUS_COLORS[status] || TEST_STATUS_COLORS.not_started
                return (
                  <div
                    key={tc.task_id}
                    onClick={() => setSelectedTaskId(tc.task_id)}
                    style={{
                      padding: '12px 16px',
                      cursor: 'pointer',
                      borderLeft: isSelected ? '3px solid #2563eb' : '3px solid transparent',
                      background: isSelected ? '#eff6ff' : 'transparent',
                      borderBottom: '1px solid #f3f4f6',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                      <span style={{ fontSize: 13, fontWeight: 600, color: '#111827' }}>{tc.name}</span>
                      <span style={{ fontSize: 11, padding: '2px 6px', borderRadius: 4, background: colors.bg, color: colors.color }}>
                        {TEST_STATUS_LABELS[status] || status}
                      </span>
                    </div>
                    <div style={{ fontSize: 12, color: '#6b7280' }}>
                      模块: {tc.parent_module || '默认模块'} | 重试: {tc.retry_count}/3
                    </div>
                    {tc.assigned_skill_id && (
                      <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>
                        Skill: {tc.assigned_skill_id}
                      </div>
                    )}
                  </div>
                )
              })}
            </>
          )}

          {/* 问题筛选栏 */}
          {activeTab === 'issues' && (
            <div style={{ padding: '10px 12px', borderBottom: '1px solid #e5e7eb', display: 'flex', gap: 8 }}>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                style={{ padding: '6px 10px', fontSize: 12, border: '1px solid #e5e7eb', borderRadius: 4, background: '#fff', flex: 1 }}
              >
                <option value="">全部类型</option>
                {ISSUE_TYPE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                style={{ padding: '6px 10px', fontSize: 12, border: '1px solid #e5e7eb', borderRadius: 4, background: '#fff', flex: 1 }}
              >
                <option value="">全部状态</option>
                {ISSUE_STATUS_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
          )}

          {/* 问题列表 */}
          {activeTab === 'issues' && (
            <>
              <div style={{ padding: '8px 12px', borderBottom: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 12, color: '#6b7280' }}>共 {filteredIssues.length} 个问题</span>
                <button onClick={() => setShowCreateForm(true)} style={{ fontSize: 11, padding: '3px 8px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}>+ 新建</button>
              </div>
              {filteredIssues.length === 0 && (
                <div style={{ padding: 24, textAlign: 'center', color: '#9ca3af', fontSize: 13 }}>
                  暂无问题记录
                </div>
              )}
              {filteredIssues.map((issue: any) => {
                const isSelected = issue.issue_id === selectedIssueId
                const typeLabel = ISSUE_TYPE_OPTIONS.find((o) => o.value === issue.issue_type)?.label || issue.issue_type
                const statusLabel = ISSUE_STATUS_OPTIONS.find((o) => o.value === issue.status)?.label || issue.status
                return (
                  <div
                    key={issue.issue_id}
                    onClick={() => selectIssue(issue.issue_id)}
                    style={{
                      padding: '12px 16px',
                      cursor: 'pointer',
                      borderLeft: isSelected ? '3px solid #2563eb' : '3px solid transparent',
                      background: isSelected ? '#eff6ff' : 'transparent',
                      borderBottom: '1px solid #f3f4f6',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                      <span style={{ fontSize: 13, fontWeight: 600, color: '#111827' }}>
                        #{issue.issue_id.slice(-4)} {typeLabel}
                      </span>
                      <span
                        style={{
                          fontSize: 11,
                          padding: '2px 6px',
                          borderRadius: 4,
                          background: issue.status === 'open' ? '#fef3c7' : issue.status === 'resolved' ? '#d1fae5' : '#f3f4f6',
                          color: issue.status === 'open' ? '#92400e' : issue.status === 'resolved' ? '#065f46' : '#6b7280',
                        }}
                      >
                        {statusLabel}
                      </span>
                    </div>
                    <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 2 }}>
                      关联任务: {issue.task_id?.slice(-4) || '无'}
                    </div>
                    <div style={{ fontSize: 11, color: '#9ca3af' }}>
                      {issue.created_at?.slice(0, 10) || ''}
                    </div>
                  </div>
                )
              })}
            </>
          )}

          {/* 测试报告 */}
          {activeTab === 'reports' && (
            <>
              {showTestReport && (
                <div style={{ padding: 16, borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>测试报告摘要</div>
                  <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                    <div style={{ flex: 1, textAlign: 'center', padding: 8, background: '#d1fae5', borderRadius: 4 }}>
                      <div style={{ fontSize: 18, fontWeight: 700, color: '#065f46' }}>{testStats.passed}</div>
                      <div style={{ fontSize: 11, color: '#065f46' }}>通过</div>
                    </div>
                    <div style={{ flex: 1, textAlign: 'center', padding: 8, background: '#fef2f2', borderRadius: 4 }}>
                      <div style={{ fontSize: 18, fontWeight: 700, color: '#dc2626' }}>{testStats.failed}</div>
                      <div style={{ fontSize: 11, color: '#dc2626' }}>失败</div>
                    </div>
                    <div style={{ flex: 1, textAlign: 'center', padding: 8, background: '#fef3c7', borderRadius: 4 }}>
                      <div style={{ fontSize: 18, fontWeight: 700, color: '#92400e' }}>{testStats.notStarted}</div>
                      <div style={{ fontSize: 11, color: '#92400e' }}>未执行</div>
                    </div>
                  </div>
                  <div style={{ fontSize: 11, color: '#6b7280' }}>覆盖率: 72% | 耗时: 12s</div>
                </div>
              )}
              <div style={{ padding: 24, textAlign: 'center', color: '#9ca3af', fontSize: 13 }}>
                点击运行测试生成报告
              </div>
            </>
          )}
        </div>

        {/* 右侧：详情 */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 24 }}>
          {activeTab === 'test-cases' && selectedTestCase ? (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h3 style={{ margin: 0, fontSize: 18 }}>{selectedTestCase.name}</h3>
                <div style={{ display: 'flex', gap: 8 }}>
                  {selectedTestCase.status === 'not_started' && (
                    <button onClick={() => handleExecuteTest(selectedTestCase.task_id)} style={{ padding: '6px 14px', fontSize: 13, background: '#2563eb', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}>
                      ▶ 执行测试
                    </button>
                  )}
                  {selectedTestCase.status === 'failed' && (
                    <button onClick={() => handleExecuteTest(selectedTestCase.task_id)} style={{ padding: '6px 14px', fontSize: 13, background: '#f59e0b', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}>
                      🔄 重试
                    </button>
                  )}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 12, padding: '4px 10px', borderRadius: 4, background: '#f3f4f6', color: '#374151' }}>
                  类型: 测试
                </span>
                <span style={{ fontSize: 12, padding: '4px 10px', borderRadius: 4, background: '#f3f4f6', color: '#374151' }}>
                  状态: {TEST_STATUS_LABELS[selectedTestCase.status] || selectedTestCase.status}
                </span>
                <span style={{ fontSize: 12, padding: '4px 10px', borderRadius: 4, background: '#f3f4f6', color: '#374151' }}>
                  重试: {selectedTestCase.retry_count}/3
                </span>
              </div>
              <div style={{ marginBottom: 12, fontSize: 13, color: '#374151' }}>
                <strong>所属模块:</strong> {selectedTestCase.parent_module || '默认模块'}
              </div>
              <div style={{ marginBottom: 12, fontSize: 13, color: '#374151' }}>
                <strong>分配 Skill:</strong> {selectedTestCase.assigned_skill_id || '未分配'}
              </div>
              <div style={{ marginBottom: 12, fontSize: 13, color: '#374151' }}>
                <strong>输入产物:</strong> {selectedTestCase.input_artifacts || '无'}
              </div>
              <div style={{ marginBottom: 12, fontSize: 13, color: '#374151' }}>
                <strong>输出产物:</strong> {selectedTestCase.output_artifact_path || '无'}
              </div>
            </div>
          ) : activeTab === 'test-cases' ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280', fontSize: 14 }}>
              请从左侧选择一个测试用例
            </div>
          ) : activeTab === 'issues' && selectedIssue ? (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h3 style={{ margin: 0, fontSize: 18 }}>
                  问题 #{selectedIssue.issue_id.slice(-4)}
                </h3>
                <div style={{ display: 'flex', gap: 8 }}>
                  {selectedIssue.status === 'open' && (
                    <button
                      onClick={() => setShowFeedbackModal(true)}
                      style={{
                        padding: '6px 12px',
                        fontSize: 12,
                        background: '#f59e0b',
                        color: '#fff',
                        border: 'none',
                        borderRadius: 4,
                        cursor: 'pointer',
                      }}
                    >
                      🔄 反馈回方案设计室
                    </button>
                  )}
                </div>
              </div>

              <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 12, padding: '4px 10px', borderRadius: 4, background: '#f3f4f6', color: '#374151' }}>
                  类型: {ISSUE_TYPE_OPTIONS.find((o) => o.value === selectedIssue.issue_type)?.label || selectedIssue.issue_type}
                </span>
                <span style={{ fontSize: 12, padding: '4px 10px', borderRadius: 4, background: '#f3f4f6', color: '#374151' }}>
                  状态: {ISSUE_STATUS_OPTIONS.find((o) => o.value === selectedIssue.status)?.label || selectedIssue.status}
                </span>
                <span style={{ fontSize: 12, padding: '4px 10px', borderRadius: 4, background: '#f3f4f6', color: '#374151' }}>
                  关联任务: {selectedIssue.task_id?.slice(-4) || '无'}
                </span>
              </div>

              {selectedIssue.error_log && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: '#111827' }}>错误日志</div>
                  <pre
                    style={{
                      background: '#1f2937',
                      color: '#e5e7eb',
                      padding: 16,
                      borderRadius: 4,
                      overflow: 'auto',
                      fontSize: 12,
                      fontFamily: 'monospace',
                      lineHeight: 1.5,
                      maxHeight: 300,
                    }}
                  >
                    {selectedIssue.error_log}
                  </pre>
                </div>
              )}

              {Array.isArray(selectedIssue.related_artifacts) && selectedIssue.related_artifacts.length > 0 && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: '#111827' }}>关联产物</div>
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    {selectedIssue.related_artifacts.map((artifact: string, i: number) => (
                      <span
                        key={i}
                        style={{
                          fontSize: 12,
                          padding: '4px 10px',
                          borderRadius: 4,
                          background: '#eff6ff',
                          color: '#2563eb',
                        }}
                      >
                        {artifact}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {selectedIssue.feedback_to_architecture && (
                <div
                  style={{
                    padding: 12,
                    background: '#fef3c7',
                    borderRadius: 4,
                    border: '1px solid #f59e0b',
                    fontSize: 13,
                    color: '#92400e',
                  }}
                >
                  ⚠️ 已反馈回方案设计室，关联变更请求: {selectedIssue.change_request_id || '处理中'}
                </div>
              )}
            </div>
          ) : activeTab === 'issues' ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280', fontSize: 14 }}>
              请从左侧选择一个问题或运行测试
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280', fontSize: 14 }}>
              <div style={{ marginBottom: 16 }}>点击运行测试生成报告</div>
              <button
                onClick={() => setShowTestReport(true)}
                style={{
                  padding: '8px 20px',
                  fontSize: 13,
                  background: '#2563eb',
                  color: '#fff',
                  border: 'none',
                  borderRadius: 4,
                  cursor: 'pointer',
                }}
              >
                ▶ 运行测试
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 新建测试用例弹窗 */}
      {showTestCaseForm && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ background: '#fff', borderRadius: 8, padding: 24, width: 480, maxWidth: '90vw' }}>
            <h3 style={{ margin: '0 0 16px', fontSize: 16 }}>新建测试用例</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, display: 'block', marginBottom: 4 }}>用例名称</label>
                <input
                  value={testCaseForm.name}
                  onChange={(e) => setTestCaseForm((p) => ({ ...p, name: e.target.value }))}
                  style={{ width: '100%', padding: 8, border: '1px solid #e5e7eb', borderRadius: 4, fontSize: 13 }}
                  placeholder="例如: 订单创建接口单元测试"
                />
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, display: 'block', marginBottom: 4 }}>所属模块</label>
                <input
                  value={testCaseForm.parentModule}
                  onChange={(e) => setTestCaseForm((p) => ({ ...p, parentModule: e.target.value }))}
                  style={{ width: '100%', padding: 8, border: '1px solid #e5e7eb', borderRadius: 4, fontSize: 13 }}
                  placeholder="例如: 订单模块"
                />
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, display: 'block', marginBottom: 4 }}>分配 Skill</label>
                <input
                  value={testCaseForm.assignedSkill}
                  onChange={(e) => setTestCaseForm((p) => ({ ...p, assignedSkill: e.target.value }))}
                  style={{ width: '100%', padding: 8, border: '1px solid #e5e7eb', borderRadius: 4, fontSize: 13 }}
                  placeholder="例如: skill-unit-test"
                />
              </div>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 8 }}>
                <button onClick={() => setShowTestCaseForm(false)} style={{ padding: '6px 12px', fontSize: 12, border: '1px solid #e5e7eb', borderRadius: 4, background: '#fff', cursor: 'pointer' }}>取消</button>
                <button onClick={handleCreateTestCase} disabled={!testCaseForm.name} style={{ padding: '6px 12px', fontSize: 12, background: testCaseForm.name ? '#2563eb' : '#e5e7eb', color: testCaseForm.name ? '#fff' : '#9ca3af', border: 'none', borderRadius: 4, cursor: testCaseForm.name ? 'pointer' : 'not-allowed' }}>创建</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 新建问题弹窗 */}
      {showCreateForm && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ background: '#fff', borderRadius: 8, padding: 24, width: 480, maxWidth: '90vw', maxHeight: '90vh', overflow: 'auto' }}>
            <h3 style={{ margin: '0 0 16px', fontSize: 16 }}>新建执行问题</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, display: 'block', marginBottom: 4 }}>关联任务 ID</label>
                <input
                  value={createForm.taskId}
                  onChange={(e) => setCreateForm((p) => ({ ...p, taskId: e.target.value }))}
                  style={{ width: '100%', padding: 8, border: '1px solid #e5e7eb', borderRadius: 4, fontSize: 13 }}
                  placeholder="任务 ID"
                />
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, display: 'block', marginBottom: 4 }}>问题类型</label>
                <select
                  value={createForm.issueType}
                  onChange={(e) => setCreateForm((p) => ({ ...p, issueType: e.target.value as any }))}
                  style={{ width: '100%', padding: 8, border: '1px solid #e5e7eb', borderRadius: 4, fontSize: 13 }}
                >
                  {ISSUE_TYPE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, display: 'block', marginBottom: 4 }}>错误日志</label>
                <textarea
                  value={createForm.errorLog}
                  onChange={(e) => setCreateForm((p) => ({ ...p, errorLog: e.target.value }))}
                  style={{ width: '100%', padding: 8, border: '1px solid #e5e7eb', borderRadius: 4, fontSize: 13, minHeight: 80, resize: 'vertical' }}
                  placeholder="粘贴错误日志..."
                />
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, display: 'block', marginBottom: 4 }}>建议操作</label>
                <select
                  value={createForm.suggestedAction}
                  onChange={(e) => setCreateForm((p) => ({ ...p, suggestedAction: e.target.value as any }))}
                  style={{ width: '100%', padding: 8, border: '1px solid #e5e7eb', borderRadius: 4, fontSize: 13 }}
                >
                  <option value="retry">重试</option>
                  <option value="feedback">反馈回方案设计室</option>
                  <option value="skip">跳过</option>
                </select>
              </div>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 8 }}>
                <button onClick={() => setShowCreateForm(false)} style={{ padding: '6px 12px', fontSize: 12, border: '1px solid #e5e7eb', borderRadius: 4, background: '#fff', cursor: 'pointer' }}>取消</button>
                <button onClick={handleCreateIssue} disabled={!createForm.taskId} style={{ padding: '6px 12px', fontSize: 12, background: createForm.taskId ? '#2563eb' : '#e5e7eb', color: createForm.taskId ? '#fff' : '#9ca3af', border: 'none', borderRadius: 4, cursor: createForm.taskId ? 'pointer' : 'not-allowed' }}>创建</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 反馈回方案设计室弹窗 */}
      {showFeedbackModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ background: '#fff', borderRadius: 8, padding: 24, width: 480, maxWidth: '90vw' }}>
            <h3 style={{ margin: '0 0 16px', fontSize: 16 }}>🔄 反馈回方案设计室</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ padding: 12, background: '#f9fafb', borderRadius: 4, fontSize: 13, color: '#374151' }}>
                <strong>问题描述:</strong> {selectedIssue?.error_log?.slice(0, 100) || '无'}...
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, display: 'block', marginBottom: 4 }}>关联设计产物</label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {ARTIFACT_OPTIONS.map((opt) => (
                    <label key={opt.value} style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13 }}>
                      <input
                        type="radio"
                        name="targetArtifact"
                        value={opt.value}
                        checked={feedbackForm.targetArtifact === opt.value}
                        onChange={(e) => setFeedbackForm((p) => ({ ...p, targetArtifact: e.target.value }))}
                      />
                      {opt.label}
                    </label>
                  ))}
                </div>
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, display: 'block', marginBottom: 4 }}>变更描述</label>
                <textarea
                  value={feedbackForm.changeDescription}
                  onChange={(e) => setFeedbackForm((p) => ({ ...p, changeDescription: e.target.value }))}
                  style={{ width: '100%', padding: 8, border: '1px solid #e5e7eb', borderRadius: 4, fontSize: 13, minHeight: 60 }}
                  placeholder="描述问题及建议的变更..."
                />
              </div>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 8 }}>
                <button onClick={() => setShowFeedbackModal(false)} style={{ padding: '6px 12px', fontSize: 12, border: '1px solid #e5e7eb', borderRadius: 4, background: '#fff', cursor: 'pointer' }}>取消</button>
                <button onClick={handleFeedback} disabled={!feedbackForm.targetArtifact} style={{ padding: '6px 12px', fontSize: 12, background: feedbackForm.targetArtifact ? '#f59e0b' : '#e5e7eb', color: feedbackForm.targetArtifact ? '#fff' : '#9ca3af', border: 'none', borderRadius: 4, cursor: feedbackForm.targetArtifact ? 'pointer' : 'not-allowed' }}>创建变更请求并跳转</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
