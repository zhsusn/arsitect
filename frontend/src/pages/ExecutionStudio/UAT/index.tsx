import { useEffect, useMemo, useState } from 'react'
import { useProjectContext } from '../../../App'
import { listUserStories, type UserStory } from '../../../services/userStory'
import { fetchTasks, type ExecutionTask } from '../../../services/execution'
import { fetchIssues, type ExecutionIssue } from '../../../services/execution'
import {
  listProjectReviews,
  createProjectReview,
  updateProjectReview,
} from '../../../services/projectReview'
import { fetchStageProgress, decideProjectStageGate } from '../../../services/stage'

interface UATItem {
  storyId: string
  title: string
  criteria: string
  status: 'pending' | 'passed' | 'failed' | 'skipped'
  testResult?: string
  notes?: string
}

const STATUS_LABELS: Record<string, string> = {
  pending: '待验收',
  passed: '通过',
  failed: '失败',
  skipped: '跳过',
}

const STATUS_COLORS: Record<string, { bg: string; color: string }> = {
  pending: { bg: '#fef3c7', color: '#92400e' },
  passed: { bg: '#d1fae5', color: '#065f46' },
  failed: { bg: '#fef2f2', color: '#dc2626' },
  skipped: { bg: '#f3f4f6', color: '#6b7280' },
}

export default function UATPage() {
  const { currentProjectId } = useProjectContext()
  const projectId = currentProjectId

  const [stories, setStories] = useState<UserStory[]>([])
  const [tasks, setTasks] = useState<ExecutionTask[]>([])
  const [issues, setIssues] = useState<ExecutionIssue[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [selectedStoryId, setSelectedStoryId] = useState<string | null>(null)
  const [uatStatus, setUatStatus] = useState<Record<string, 'pending' | 'passed' | 'failed' | 'skipped'>>({})
  const [uatNotes, setUatNotes] = useState<Record<string, string>>({})
  const [showGate3Modal, setShowGate3Modal] = useState(false)
  const [stageId, setStageId] = useState<string>('')

  useEffect(() => {
    if (!projectId) return
    setLoading(true)
    Promise.all([
      listUserStories(projectId),
      fetchTasks(projectId),
      fetchIssues(projectId),
      listProjectReviews(projectId, 'uat'),
      fetchStageProgress(projectId),
    ])
      .then(([s, t, i, reviews, progress]) => {
        setStories(s)
        setTasks(t)
        setIssues(i)
        // Find UAT stage for Gate 3 (typically verification/uat stage)
        const uatStage = progress.stages.find(
          (st) => st.business_stage_key?.includes('uat') || st.business_stage_key?.includes('verify') || st.business_stage_key?.includes('release')
        )
        if (uatStage) setStageId(uatStage.project_stage_id)
        // 加载持久化的 UAT 状态
        const statusMap: Record<string, 'pending' | 'passed' | 'failed' | 'skipped'> = {}
        const notesMap: Record<string, string> = {}
        reviews.forEach((r) => {
          if (['pending', 'passed', 'failed', 'skipped'].includes(r.status)) {
            statusMap[r.item_id] = r.status as 'pending' | 'passed' | 'failed' | 'skipped'
          }
          if (r.notes) notesMap[r.item_id] = r.notes
        })
        setUatStatus(statusMap)
        setUatNotes(notesMap)
        setError(null)
        if (s.length > 0 && !selectedStoryId) setSelectedStoryId(s[0].story_id)
      })
      .catch((err) => setError(err instanceof Error ? err.message : '加载失败'))
      .finally(() => setLoading(false))
  }, [projectId, selectedStoryId])

  const uatItems = useMemo((): UATItem[] => {
    return stories
      .filter((s) => s.acceptance_criteria)
      .map((s) => ({
        storyId: s.story_id,
        title: s.title,
        criteria: s.acceptance_criteria || '',
        status: uatStatus[s.story_id] || 'pending',
        notes: uatNotes[s.story_id] || '',
      }))
  }, [stories, uatStatus, uatNotes])

  const selectedStory = useMemo(() => {
    return stories.find((s) => s.story_id === selectedStoryId) || null
  }, [stories, selectedStoryId])

  const storyTests = useMemo(() => {
    if (!selectedStoryId) return []
    return tasks.filter((t) => t.type === 'test')
  }, [tasks, selectedStoryId])

  const storyIssues = useMemo(() => {
    if (!selectedStoryId) return []
    return issues.filter((i) => i.task_id?.includes(selectedStoryId))
  }, [issues, selectedStoryId])

  const stats = useMemo(() => {
    const total = uatItems.length
    const passed = uatItems.filter((u) => uatStatus[u.storyId] === 'passed').length
    const failed = uatItems.filter((u) => uatStatus[u.storyId] === 'failed').length
    const skipped = uatItems.filter((u) => uatStatus[u.storyId] === 'skipped').length
    const pending = total - passed - failed - skipped
    const allPassed = passed === total && total > 0
    return { total, passed, failed, skipped, pending, allPassed }
  }, [uatItems, uatStatus])

  const testTaskStats = useMemo(() => {
    const testTasks = tasks.filter((t) => t.type === 'test')
    const total = testTasks.length
    const passed = testTasks.filter((t) => t.status === 'passed').length
    const failed = testTasks.filter((t) => t.status === 'failed').length
    return { total, passed, failed }
  }, [tasks])

  const handleStatusChange = async (storyId: string, status: 'pending' | 'passed' | 'failed' | 'skipped') => {
    setUatStatus((prev) => ({ ...prev, [storyId]: status }))
    if (!projectId) return
    try {
      const reviews = await listProjectReviews(projectId, 'uat')
      const existing = reviews.find((r) => r.item_id === storyId)
      const notes = uatNotes[storyId] || undefined
      if (existing) {
        await updateProjectReview(projectId, existing.review_id, { status, notes })
      } else {
        await createProjectReview(projectId, {
          review_type: 'uat',
          item_id: storyId,
          item_type: 'acceptance-criteria',
          status,
          notes,
        })
      }
    } catch (err) {
      console.error('保存 UAT 状态失败:', err)
    }
  }

  const handleNoteChange = (storyId: string, note: string) => {
    setUatNotes((prev) => ({ ...prev, [storyId]: note }))
  }

  const handleNoteSave = async (storyId: string) => {
    if (!projectId) return
    const notes = uatNotes[storyId]
    try {
      const reviews = await listProjectReviews(projectId, 'uat')
      const existing = reviews.find((r) => r.item_id === storyId)
      if (existing) {
        await updateProjectReview(projectId, existing.review_id, { notes })
      } else {
        await createProjectReview(projectId, {
          review_type: 'uat',
          item_id: storyId,
          item_type: 'acceptance-criteria',
          status: uatStatus[storyId] || 'pending',
          notes,
        })
      }
    } catch (err) {
      console.error('保存备注失败:', err)
    }
  }

  if (!projectId) {
    return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280' }}>请先在顶部选择项目</div>
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#fff', borderRadius: 8, border: '1px solid #e5e7eb', overflow: 'hidden' }}>
      {/* 顶部 */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>UAT 验收 — Gate 3</h2>
          <div style={{ display: 'flex', gap: 12, fontSize: 13 }}>
            <span>用户故事: <strong>{stories.length}</strong></span>
            <span>验收项: <strong>{stats.total}</strong></span>
            <span style={{ color: '#16a34a' }}>通过: <strong>{stats.passed}</strong></span>
            <span style={{ color: '#dc2626' }}>失败: <strong>{stats.failed}</strong></span>
            <span>待审: <strong>{stats.pending}</strong></span>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ fontSize: 13, color: '#6b7280' }}>
            测试: <span style={{ color: '#16a34a' }}>{testTaskStats.passed}</span> / <span style={{ color: '#dc2626' }}>{testTaskStats.failed}</span> / {testTaskStats.total}
          </div>
          <button
            onClick={() => setShowGate3Modal(true)}
            disabled={!stats.allPassed}
            style={{
              padding: '6px 16px',
              fontSize: 13,
              background: stats.allPassed ? '#16a34a' : '#e5e7eb',
              color: stats.allPassed ? '#fff' : '#9ca3af',
              border: 'none',
              borderRadius: 4,
              cursor: stats.allPassed ? 'pointer' : 'not-allowed',
              fontWeight: 600,
            }}
          >
            ✅ 通过 Gate 3
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '8px 16px', background: '#fef2f2', color: '#dc2626', fontSize: 13, borderBottom: '1px solid #e5e7eb' }}>
          {error}
        </div>
      )}

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* 左侧：用户故事列表 */}
        <div style={{ width: 300, minWidth: 300, borderRight: '1px solid #e5e7eb', overflowY: 'auto', background: '#fff' }}>
          <div style={{ padding: '10px 12px', borderBottom: '1px solid #e5e7eb', fontSize: 13, fontWeight: 600, color: '#374151' }}>
            用户故事 ({stories.length})
          </div>
          {loading && <div style={{ padding: 24, textAlign: 'center', color: '#9ca3af', fontSize: 13 }}>加载中...</div>}
          {stories.map((story) => {
            const isSelected = selectedStoryId === story.story_id
            const hasCriteria = !!story.acceptance_criteria
            const status = uatStatus[story.story_id] || 'pending'
            const colors = STATUS_COLORS[status]
            return (
              <div
                key={story.story_id}
                onClick={() => setSelectedStoryId(story.story_id)}
                style={{
                  padding: '10px 14px',
                  cursor: 'pointer',
                  borderLeft: isSelected ? '3px solid #2563eb' : '3px solid transparent',
                  background: isSelected ? '#eff6ff' : 'transparent',
                  borderBottom: '1px solid #f3f4f6',
                  opacity: hasCriteria ? 1 : 0.6,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: '#111827', wordBreak: 'break-all' }}>{story.title}</span>
                  {hasCriteria && (
                    <span style={{ fontSize: 10, padding: '2px 6px', borderRadius: 4, background: colors.bg, color: colors.color, whiteSpace: 'nowrap' }}>
                      {STATUS_LABELS[status]}
                    </span>
                  )}
                </div>
                <div style={{ fontSize: 12, color: '#6b7280' }}>
                  优先级: {story.priority} | {!hasCriteria ? '无验收标准' : '有验收标准'}
                </div>
              </div>
            )
          })}
        </div>

        {/* 中间：验收详情 */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 24, borderRight: '1px solid #e5e7eb' }}>
          {selectedStory ? (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h3 style={{ margin: 0, fontSize: 18 }}>{selectedStory.title}</h3>
                <span style={{ fontSize: 12, padding: '4px 10px', borderRadius: 4, background: '#f3f4f6', color: '#374151' }}>
                  优先级: {selectedStory.priority}
                </span>
              </div>

              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: '#374151' }}>用户故事描述</div>
                <div style={{ padding: 16, background: '#f9fafb', borderRadius: 6, fontSize: 13, color: '#374151', lineHeight: 1.6 }}>
                  {selectedStory.description || '无描述'}
                </div>
              </div>

              {selectedStory.acceptance_criteria ? (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: '#374151' }}>验收标准</div>
                  <div style={{ padding: 16, background: '#f0fdf4', borderRadius: 6, fontSize: 13, color: '#374151', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                    {selectedStory.acceptance_criteria}
                  </div>
                </div>
              ) : (
                <div style={{ marginBottom: 16, padding: 16, background: '#fef2f2', borderRadius: 6, fontSize: 13, color: '#dc2626' }}>
                  ⚠️ 该用户故事没有验收标准，无法执行 UAT 验收
                </div>
              )}

              {selectedStory.acceptance_criteria && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: '#374151' }}>UAT 执行结果</div>
                  <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                    {(['passed', 'failed', 'skipped', 'pending'] as const).map((status) => (
                      <button
                        key={status}
                        onClick={() => handleStatusChange(selectedStory.story_id, status)}
                        style={{
                          padding: '6px 14px',
                          fontSize: 13,
                          background: uatStatus[selectedStory.story_id] === status ? STATUS_COLORS[status].bg : '#fff',
                          color: uatStatus[selectedStory.story_id] === status ? STATUS_COLORS[status].color : '#374151',
                          border: `1px solid ${uatStatus[selectedStory.story_id] === status ? STATUS_COLORS[status].color : '#e5e7eb'}`,
                          borderRadius: 4,
                          cursor: 'pointer',
                          fontWeight: uatStatus[selectedStory.story_id] === status ? 600 : 400,
                        }}
                      >
                        {status === 'passed' ? '✓ 通过' : status === 'failed' ? '✕ 失败' : status === 'skipped' ? '⊘ 跳过' : '○ 待验收'}
                      </button>
                    ))}
                  </div>
                  <textarea
                    value={uatNotes[selectedStory.story_id] || ''}
                    onChange={(e) => handleNoteChange(selectedStory.story_id, e.target.value)}
                    onBlur={() => handleNoteSave(selectedStory.story_id)}
                    style={{ width: '100%', padding: 12, border: '1px solid #e5e7eb', borderRadius: 6, fontSize: 13, minHeight: 80, resize: 'vertical' }}
                    placeholder="输入 UAT 验收备注..."
                  />
                </div>
              )}

              {/* 关联测试 */}
              {storyTests.length > 0 && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: '#374151' }}>关联测试 ({storyTests.length})</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {storyTests.map((t) => (
                      <div key={t.task_id} style={{ padding: 10, background: '#f9fafb', borderRadius: 6, fontSize: 13, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span>{t.name}</span>
                        <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 4, background: t.status === 'passed' ? '#d1fae5' : t.status === 'failed' ? '#fef2f2' : '#fef3c7', color: t.status === 'passed' ? '#065f46' : t.status === 'failed' ? '#dc2626' : '#92400e' }}>
                          {t.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 关联问题 */}
              {storyIssues.length > 0 && (
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: '#374151' }}>关联问题 ({storyIssues.length})</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {storyIssues.map((i) => (
                      <div key={i.issue_id} style={{ padding: 10, background: '#fef2f2', borderRadius: 6, fontSize: 12, color: '#dc2626' }}>
                        #{i.issue_id.slice(-4)} {i.issue_type} — {i.status}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280', fontSize: 14 }}>
              请从左侧选择一个用户故事
            </div>
          )}
        </div>

        {/* 右侧：UAT 报告 + Gate 3 */}
        <div style={{ width: 300, minWidth: 300, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ padding: 16, borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12, color: '#374151' }}>UAT 验收报告</div>

            <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
              <div style={{ flex: 1, textAlign: 'center', padding: 10, background: '#d1fae5', borderRadius: 6 }}>
                <div style={{ fontSize: 20, fontWeight: 700, color: '#065f46' }}>{stats.passed}</div>
                <div style={{ fontSize: 11, color: '#065f46' }}>通过</div>
              </div>
              <div style={{ flex: 1, textAlign: 'center', padding: 10, background: '#fef2f2', borderRadius: 6 }}>
                <div style={{ fontSize: 20, fontWeight: 700, color: '#dc2626' }}>{stats.failed}</div>
                <div style={{ fontSize: 11, color: '#dc2626' }}>失败</div>
              </div>
              <div style={{ flex: 1, textAlign: 'center', padding: 10, background: '#fef3c7', borderRadius: 6 }}>
                <div style={{ fontSize: 20, fontWeight: 700, color: '#92400e' }}>{stats.pending}</div>
                <div style={{ fontSize: 11, color: '#92400e' }}>待审</div>
              </div>
            </div>

            <div style={{ marginBottom: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                <span>验收进度</span>
                <span style={{ color: '#6b7280' }}>{stats.total > 0 ? Math.round(((stats.passed + stats.failed + stats.skipped) / stats.total) * 100) : 0}%</span>
              </div>
              <div style={{ height: 8, background: '#f3f4f6', borderRadius: 4, overflow: 'hidden' }}>
                <div style={{ width: `${stats.total > 0 ? ((stats.passed + stats.failed + stats.skipped) / stats.total) * 100 : 0}%`, height: '100%', background: stats.allPassed ? '#16a34a' : '#2563eb', borderRadius: 4, transition: 'width 0.3s' }} />
              </div>
            </div>

            <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 4 }}>
              测试覆盖: {testTaskStats.total} 个用例 / {stories.length} 个故事
            </div>
            <div style={{ fontSize: 12, color: '#6b7280' }}>
              问题数: {issues.length} 个
            </div>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 12, color: '#374151' }}>Gate 3 检查清单</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, cursor: 'pointer' }}>
                <input type="checkbox" checked={stats.total > 0} readOnly /> 所有用户故事有验收标准
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, cursor: 'pointer' }}>
                <input type="checkbox" checked={testTaskStats.total > 0} readOnly /> 测试用例已执行
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, cursor: 'pointer' }}>
                <input type="checkbox" checked={testTaskStats.failed === 0 && testTaskStats.total > 0} readOnly /> 无失败的测试用例
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, cursor: 'pointer' }}>
                <input type="checkbox" checked={issues.filter((i) => i.status === 'open').length === 0} readOnly /> 无未解决问题
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, cursor: 'pointer' }}>
                <input type="checkbox" checked={stats.allPassed} readOnly /> 所有验收项已通过
              </label>
            </div>

            {stats.allPassed && (
              <div style={{ marginTop: 16, padding: 12, background: '#d1fae5', borderRadius: 6, fontSize: 13, color: '#065f46' }}>
                ✅ 所有验收项已通过，可以提交 Gate 3 审批
              </div>
            )}

            {stats.failed > 0 && (
              <div style={{ marginTop: 16, padding: 12, background: '#fef2f2', borderRadius: 6, fontSize: 13, color: '#dc2626' }}>
                ⚠️ 有 {stats.failed} 个验收项失败，请修复后重新验收
              </div>
            )}

            {stats.pending > 0 && (
              <div style={{ marginTop: 16, padding: 12, background: '#fef3c7', borderRadius: 6, fontSize: 13, color: '#92400e' }}>
                ⏳ 还有 {stats.pending} 个验收项待执行
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Gate 3 通过确认弹窗 */}
      {showGate3Modal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50 }}>
          <div style={{ background: '#fff', borderRadius: 8, padding: 24, width: 480, maxWidth: '90vw' }}>
            <h3 style={{ margin: '0 0 16px', fontSize: 18 }}>确认通过 Gate 3</h3>
            <div style={{ marginBottom: 16, fontSize: 13, color: '#374151', lineHeight: 1.6 }}>
              <p>通过 Gate 3 意味着 UAT 验收已完成，业务流程验收通过：</p>
              <ul style={{ paddingLeft: 20, margin: '8px 0' }}>
                <li>所有用户故事的验收标准已确认通过</li>
                <li>测试用例全部通过</li>
                <li>无未解决问题</li>
                <li>可进入发布阶段</li>
              </ul>
              <p style={{ color: '#dc2626' }}>通过后，设计/开发阶段将被锁定，发布前需通过变更请求修改。</p>
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button onClick={() => setShowGate3Modal(false)} style={{ padding: '8px 16px', fontSize: 13, border: '1px solid #e5e7eb', background: '#fff', borderRadius: 4, cursor: 'pointer' }}>取消</button>
              <button onClick={async () => {
                setShowGate3Modal(false)
                if (!projectId || !stageId) {
                  alert('无法锁定阶段：缺少项目或阶段ID')
                  return
                }
                try {
                  await decideProjectStageGate(projectId, stageId, 'pass', 'Gate 3 审批通过：UAT 验收完成')
                  alert('Gate 3 已通过！UAT 验收完成，阶段已锁定。')
                } catch (err) {
                  alert(`Gate 3 锁定失败: ${err instanceof Error ? err.message : '未知错误'}`)
                }
              }} style={{ padding: '8px 16px', fontSize: 13, background: '#16a34a', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}>确认通过</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
