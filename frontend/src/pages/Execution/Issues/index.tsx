import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router'
import { useExecutionStore } from '../../../stores/executionStore'
import {
  fetchIssues,
  createIssue,
  feedbackIssue,
  type ExecutionIssue,
} from '../../../services/execution'

const ISSUE_TYPE_OPTIONS = [
  { value: 'compile_error', label: '编译错误' },
  { value: 'test_failure', label: '测试失败' },
  { value: 'arch_mismatch', label: '架构偏差' },
  { value: 'interface_mismatch', label: '接口不匹配' },
  { value: 'other', label: '其他' },
]

const STATUS_OPTIONS = [
  { value: 'open', label: '待处理' },
  { value: 'resolved', label: '已解决' },
  { value: 'closed', label: '已关闭' },
]

export default function ExecutionIssues() {
  const [searchParams] = useSearchParams()
  const projectId = searchParams.get('projectId') || ''

  const { issues, selectedIssueId, setIssues, selectIssue, setLoading, setError } = useExecutionStore()

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
  const [feedbackForm, setFeedbackForm] = useState({ targetArtifactId: '', changeDescription: '' })

  // 加载问题列表
  useEffect(() => {
    if (!projectId) return
    setLoading(true)
    fetchIssues(projectId)
      .then((data) => {
        setIssues(data)
        setError(null)
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : '加载问题失败')
      })
      .finally(() => setLoading(false))
  }, [projectId, setIssues, setLoading, setError])

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
    if (!projectId || !selectedIssueId || !feedbackForm.targetArtifactId) return
    try {
      setLoading(true)
      await feedbackIssue(projectId, selectedIssueId, {
        feedback_to_architecture: true,
        change_request_id: '',
      })
      const data = await fetchIssues(projectId)
      setIssues(data)
      setShowFeedbackModal(false)
      setFeedbackForm({ targetArtifactId: '', changeDescription: '' })
    } catch (err) {
      setError(err instanceof Error ? err.message : '反馈失败')
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
      {/* 顶部筛选栏 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px', borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          style={{ padding: '6px 10px', fontSize: 13, border: '1px solid #e5e7eb', borderRadius: 4, background: '#fff' }}
        >
          <option value="">全部类型</option>
          {ISSUE_TYPE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          style={{ padding: '6px 10px', fontSize: 13, border: '1px solid #e5e7eb', borderRadius: 4, background: '#fff' }}
        >
          <option value="">全部状态</option>
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <button
          onClick={() => setShowCreateForm(true)}
          style={{
            marginLeft: 'auto',
            padding: '6px 14px',
            fontSize: 13,
            background: '#2563eb',
            color: '#fff',
            border: 'none',
            borderRadius: 4,
            cursor: 'pointer',
          }}
        >
          + 新建问题
        </button>
      </div>

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* 左侧：问题列表 */}
        <div style={{ width: 320, minWidth: 320, borderRight: '1px solid #e5e7eb', overflowY: 'auto', background: '#fff' }}>
          {filteredIssues.length === 0 && (
            <div style={{ padding: 24, textAlign: 'center', color: '#9ca3af', fontSize: 13 }}>
              暂无问题记录
            </div>
          )}
          {filteredIssues.map((issue: any) => {
            const isSelected = issue.issue_id === selectedIssueId
            const typeLabel = ISSUE_TYPE_OPTIONS.find((o) => o.value === issue.issue_type)?.label || issue.issue_type
            const statusLabel = STATUS_OPTIONS.find((o) => o.value === issue.status)?.label || issue.status
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
        </div>

        {/* 右侧：问题详情 */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 24 }}>
          {selectedIssue ? (
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
                        background: '#dc2626',
                        color: '#fff',
                        border: 'none',
                        borderRadius: 4,
                        cursor: 'pointer',
                      }}
                    >
                      反馈回架构
                    </button>
                  )}
                </div>
              </div>

              <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 12, padding: '4px 10px', borderRadius: 4, background: '#f3f4f6', color: '#374151' }}>
                  类型: {ISSUE_TYPE_OPTIONS.find((o) => o.value === selectedIssue.issue_type)?.label || selectedIssue.issue_type}
                </span>
                <span style={{ fontSize: 12, padding: '4px 10px', borderRadius: 4, background: '#f3f4f6', color: '#374151' }}>
                  状态: {STATUS_OPTIONS.find((o) => o.value === selectedIssue.status)?.label || selectedIssue.status}
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
                  ⚠️ 已反馈回架构，关联变更请求: {selectedIssue.change_request_id || '处理中'}
                </div>
              )}
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280', fontSize: 14 }}>
              请从左侧选择一个问题
            </div>
          )}
        </div>
      </div>

      {/* 新建问题弹窗 */}
      {showCreateForm && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
        >
          <div
            style={{
              background: '#fff',
              borderRadius: 8,
              padding: 24,
              width: 480,
              maxWidth: '90vw',
              maxHeight: '90vh',
              overflow: 'auto',
            }}
          >
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
                  <option value="feedback">反馈回架构</option>
                  <option value="skip">跳过</option>
                </select>
              </div>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 8 }}>
                <button
                  onClick={() => setShowCreateForm(false)}
                  style={{ padding: '6px 12px', fontSize: 12, border: '1px solid #e5e7eb', borderRadius: 4, background: '#fff', cursor: 'pointer' }}
                >
                  取消
                </button>
                <button
                  onClick={handleCreateIssue}
                  disabled={!createForm.taskId}
                  style={{
                    padding: '6px 12px',
                    fontSize: 12,
                    background: createForm.taskId ? '#2563eb' : '#e5e7eb',
                    color: createForm.taskId ? '#fff' : '#9ca3af',
                    border: 'none',
                    borderRadius: 4,
                    cursor: createForm.taskId ? 'pointer' : 'not-allowed',
                  }}
                >
                  创建
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 反馈回架构弹窗 */}
      {showFeedbackModal && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
        >
          <div
            style={{
              background: '#fff',
              borderRadius: 8,
              padding: 24,
              width: 480,
              maxWidth: '90vw',
            }}
          >
            <h3 style={{ margin: '0 0 16px', fontSize: 16 }}>反馈回架构</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, display: 'block', marginBottom: 4 }}>关联设计产物</label>
                <input
                  value={feedbackForm.targetArtifactId}
                  onChange={(e) => setFeedbackForm((p) => ({ ...p, targetArtifactId: e.target.value }))}
                  style={{ width: '100%', padding: 8, border: '1px solid #e5e7eb', borderRadius: 4, fontSize: 13 }}
                  placeholder="例如: api-contract.yaml"
                />
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
                <button
                  onClick={() => setShowFeedbackModal(false)}
                  style={{ padding: '6px 12px', fontSize: 12, border: '1px solid #e5e7eb', borderRadius: 4, background: '#fff', cursor: 'pointer' }}
                >
                  取消
                </button>
                <button
                  onClick={handleFeedback}
                  disabled={!feedbackForm.targetArtifactId}
                  style={{
                    padding: '6px 12px',
                    fontSize: 12,
                    background: feedbackForm.targetArtifactId ? '#dc2626' : '#e5e7eb',
                    color: feedbackForm.targetArtifactId ? '#fff' : '#9ca3af',
                    border: 'none',
                    borderRadius: 4,
                    cursor: feedbackForm.targetArtifactId ? 'pointer' : 'not-allowed',
                  }}
                >
                  提交反馈
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
