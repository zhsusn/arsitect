import { useEffect, useMemo, useState } from 'react'
import { useProjectContext } from '../../../App'
import { fetchTasks, fetchIssues, type ExecutionTask, type ExecutionIssue } from '../../../services/execution'
import {
  listProjectReviews,
  createProjectReview,
  updateProjectReview,
} from '../../../services/projectReview'

interface ReviewItem {
  id: string
  stage: 'file-scan' | 'static-analysis' | 'manual-review' | 'regression'
  axis: 'code-style' | 'security' | 'performance' | 'maintainability' | 'architecture'
  title: string
  severity: 'critical' | 'warning' | 'info'
  status: 'open' | 'fixed' | 'waived'
  description: string
  suggestion?: string
  filePath?: string
  lineNumber?: number
}

const STAGES = [
  { id: 'file-scan', label: '文件扫描', icon: '🔍' },
  { id: 'static-analysis', label: '静态分析', icon: '📊' },
  { id: 'manual-review', label: '人工审查', icon: '👤' },
  { id: 'regression', label: '回归验证', icon: '♻️' },
]

const AXES = [
  { id: 'code-style', label: '代码规范', color: '#2563eb' },
  { id: 'security', label: '安全', color: '#dc2626' },
  { id: 'performance', label: '性能', color: '#f59e0b' },
  { id: 'maintainability', label: '可维护性', color: '#16a34a' },
  { id: 'architecture', label: '架构一致性', color: '#8b5cf6' },
]

const SEVERITY_COLORS: Record<string, { bg: string; color: string }> = {
  critical: { bg: '#fef2f2', color: '#dc2626' },
  warning: { bg: '#fef3c7', color: '#92400e' },
  info: { bg: '#f3f4f6', color: '#6b7280' },
}

export default function CodeReviewPage() {
  const { currentProjectId } = useProjectContext()
  const projectId = currentProjectId

  const [_tasks, setTasks] = useState<ExecutionTask[]>([])
  const [_issues, setIssues] = useState<ExecutionIssue[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [selectedStage, setSelectedStage] = useState<string>('file-scan')
  const [selectedAxis, setSelectedAxis] = useState<string>('')
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null)

  // 模拟审查数据
  const [reviewItems, setReviewItems] = useState<ReviewItem[]>([])

  useEffect(() => {
    if (!projectId) return
    setLoading(true)
    Promise.all([fetchTasks(projectId), fetchIssues(projectId), listProjectReviews(projectId, 'code_review')])
      .then(([t, i, reviews]) => {
        setTasks(t)
        setIssues(i)
        // 从任务和issue生成审查项
        const items: ReviewItem[] = []
        t.filter((task) => task.type === 'coding').forEach((task) => {
          if (task.status === 'failed') {
            items.push({
              id: `review-${task.task_id}-style`,
              stage: 'static-analysis',
              axis: 'code-style',
              title: `${task.name} — 代码规范问题`,
              severity: 'warning',
              status: 'open',
              description: `任务 ${task.name} 执行失败，可能存在代码规范问题`,
              suggestion: '检查代码格式和命名规范',
              filePath: task.output_artifact_path || undefined,
            })
          }
        })
        i.forEach((issue) => {
          const axis = issue.issue_type === 'arch_mismatch' ? 'architecture' : issue.issue_type === 'interface_mismatch' ? 'architecture' : 'security'
          const stage = issue.issue_type === 'compile_error' ? 'file-scan' : 'static-analysis'
          items.push({
            id: `review-issue-${issue.issue_id}`,
            stage: stage as any,
            axis: axis as any,
            title: `Issue #${issue.issue_id.slice(-4)} — ${issue.issue_type}`,
            severity: issue.issue_type === 'compile_error' ? 'critical' : 'warning',
            status: issue.status === 'resolved' ? 'fixed' : 'open',
            description: issue.error_log || '无描述',
            suggestion: issue.suggested_action || '请修复',
          })
        })
        // 如果没有数据，添加一些默认示例
        if (items.length === 0) {
          items.push(
            { id: 'demo-1', stage: 'file-scan', axis: 'code-style', title: '未使用变量', severity: 'warning', status: 'open', description: '检测到未使用的导入', suggestion: '删除未使用的导入', filePath: 'src/components/Header.tsx', lineNumber: 3 },
            { id: 'demo-2', stage: 'static-analysis', axis: 'security', title: '硬编码密钥', severity: 'critical', status: 'open', description: '发现硬编码的 API 密钥', suggestion: '使用环境变量存储密钥', filePath: 'src/config.ts', lineNumber: 15 },
            { id: 'demo-3', stage: 'manual-review', axis: 'architecture', title: '循环依赖', severity: 'warning', status: 'waived', description: '模块 A 和模块 B 存在循环依赖', suggestion: '引入抽象层解耦', filePath: 'src/modules/A.ts' },
            { id: 'demo-4', stage: 'static-analysis', axis: 'performance', title: 'N+1 查询', severity: 'warning', status: 'fixed', description: '数据库查询存在 N+1 问题', suggestion: '使用 JOIN 或批量查询', filePath: 'src/services/user.ts' },
          )
        }
        // 应用持久化的审查状态
        const statusMap = new Map(reviews.map((r) => [r.item_id, r.status]))
        items.forEach((item) => {
          const saved = statusMap.get(item.id)
          if (saved && ['open', 'fixed', 'waived'].includes(saved)) {
            item.status = saved as 'open' | 'fixed' | 'waived'
          }
        })
        setReviewItems(items)
        setError(null)
      })
      .catch((err) => setError(err instanceof Error ? err.message : '加载失败'))
      .finally(() => setLoading(false))
  }, [projectId])

  const filteredItems = useMemo(() => {
    return reviewItems.filter((item) => {
      const matchStage = item.stage === selectedStage
      const matchAxis = !selectedAxis || item.axis === selectedAxis
      return matchStage && matchAxis
    })
  }, [reviewItems, selectedStage, selectedAxis])

  const selectedItem = useMemo(() => {
    return reviewItems.find((item) => item.id === selectedItemId) || null
  }, [reviewItems, selectedItemId])

  const stats = useMemo(() => {
    const total = reviewItems.length
    const open = reviewItems.filter((i) => i.status === 'open').length
    const fixed = reviewItems.filter((i) => i.status === 'fixed').length
    const waived = reviewItems.filter((i) => i.status === 'waived').length
    const critical = reviewItems.filter((i) => i.severity === 'critical').length
    return { total, open, fixed, waived, critical, allClear: open === 0 && total > 0 }
  }, [reviewItems])

  const axisStats = useMemo(() => {
    return AXES.map((axis) => {
      const axisItems = reviewItems.filter((i) => i.axis === axis.id)
      const open = axisItems.filter((i) => i.status === 'open').length
      return { ...axis, total: axisItems.length, open }
    })
  }, [reviewItems])

  const handleStatusChange = async (itemId: string, status: 'open' | 'fixed' | 'waived') => {
    setReviewItems((prev) => prev.map((item) => (item.id === itemId ? { ...item, status } : item)))
    if (!projectId) return
    try {
      const reviews = await listProjectReviews(projectId, 'code_review')
      const existing = reviews.find((r) => r.item_id === itemId)
      const item = reviewItems.find((i) => i.id === itemId)
      if (existing) {
        await updateProjectReview(projectId, existing.review_id, { status })
      } else if (item) {
        await createProjectReview(projectId, {
          review_type: 'code_review',
          item_id: itemId,
          item_type: item.axis,
          status,
        })
      }
    } catch (err) {
      console.error('保存代码审查状态失败:', err)
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
          <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>代码审查</h2>
          <div style={{ display: 'flex', gap: 8 }}>
            {STAGES.map((stage) => (
              <button
                key={stage.id}
                onClick={() => { setSelectedStage(stage.id); setSelectedItemId(null) }}
                style={{
                  padding: '4px 10px',
                  fontSize: 12,
                  borderRadius: 4,
                  border: '1px solid #e5e7eb',
                  background: selectedStage === stage.id ? '#eff6ff' : '#fff',
                  color: selectedStage === stage.id ? '#2563eb' : '#374151',
                  cursor: 'pointer',
                }}
              >
                {stage.icon} {stage.label}
              </button>
            ))}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ fontSize: 13, color: '#6b7280' }}>
            <span style={{ color: '#dc2626' }}>{stats.critical}</span> 严重 / <span>{stats.open}</span> 待修复 / <span style={{ color: '#16a34a' }}>{stats.fixed}</span> 已修复
          </div>
          <button
            disabled={!stats.allClear}
            style={{
              padding: '6px 16px',
              fontSize: 13,
              background: stats.allClear ? '#16a34a' : '#e5e7eb',
              color: stats.allClear ? '#fff' : '#9ca3af',
              border: 'none',
              borderRadius: 4,
              cursor: stats.allClear ? 'pointer' : 'not-allowed',
              fontWeight: 600,
            }}
          >
            ✅ 审查通过
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '8px 16px', background: '#fef2f2', color: '#dc2626', fontSize: 13, borderBottom: '1px solid #e5e7eb' }}>
          {error}
        </div>
      )}

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* 左侧：审查项列表 */}
        <div style={{ width: 320, minWidth: 320, borderRight: '1px solid #e5e7eb', overflowY: 'auto', background: '#fff' }}>
          {/* 五轴筛选 */}
          <div style={{ padding: '10px 12px', borderBottom: '1px solid #e5e7eb', display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            <button
              onClick={() => setSelectedAxis('')}
              style={{ padding: '3px 8px', fontSize: 11, borderRadius: 4, border: '1px solid #e5e7eb', background: selectedAxis === '' ? '#374151' : '#fff', color: selectedAxis === '' ? '#fff' : '#374151', cursor: 'pointer' }}
            >
              全部
            </button>
            {AXES.map((axis) => (
              <button
                key={axis.id}
                onClick={() => setSelectedAxis(axis.id === selectedAxis ? '' : axis.id)}
                style={{
                  padding: '3px 8px',
                  fontSize: 11,
                  borderRadius: 4,
                  border: `1px solid ${axis.color}`,
                  background: selectedAxis === axis.id ? axis.color : '#fff',
                  color: selectedAxis === axis.id ? '#fff' : axis.color,
                  cursor: 'pointer',
                }}
              >
                {axis.label}
              </button>
            ))}
          </div>

          {loading && <div style={{ padding: 24, textAlign: 'center', color: '#9ca3af', fontSize: 13 }}>加载中...</div>}
          {filteredItems.length === 0 && !loading && (
            <div style={{ padding: 24, textAlign: 'center', color: '#9ca3af', fontSize: 13 }}>该阶段暂无审查项</div>
          )}
          {filteredItems.map((item) => {
            const isSelected = selectedItemId === item.id
            const colors = SEVERITY_COLORS[item.severity]
            return (
              <div
                key={item.id}
                onClick={() => setSelectedItemId(item.id)}
                style={{
                  padding: '10px 14px',
                  cursor: 'pointer',
                  borderLeft: isSelected ? '3px solid #2563eb' : '3px solid transparent',
                  background: isSelected ? '#eff6ff' : item.status === 'fixed' ? '#f0fdf4' : item.status === 'waived' ? '#f9fafb' : 'transparent',
                  borderBottom: '1px solid #f3f4f6',
                  opacity: item.status === 'fixed' ? 0.7 : 1,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: '#111827', wordBreak: 'break-all' }}>{item.title}</span>
                  <span style={{ fontSize: 10, padding: '2px 6px', borderRadius: 4, background: colors.bg, color: colors.color, whiteSpace: 'nowrap' }}>
                    {item.severity === 'critical' ? '严重' : item.severity === 'warning' ? '警告' : '信息'}
                  </span>
                </div>
                <div style={{ fontSize: 12, color: '#6b7280' }}>
                  {AXES.find((a) => a.id === item.axis)?.label} | {item.filePath || '无文件'}
                </div>
                <div style={{ fontSize: 11, color: item.status === 'fixed' ? '#16a34a' : item.status === 'waived' ? '#6b7280' : '#92400e', marginTop: 2 }}>
                  {item.status === 'fixed' ? '✓ 已修复' : item.status === 'waived' ? '⊘ 已豁免' : '○ 待修复'}
                </div>
              </div>
            )
          })}
        </div>

        {/* 中间：审查详情 */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 24, borderRight: '1px solid #e5e7eb' }}>
          {selectedItem ? (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h3 style={{ margin: 0, fontSize: 18 }}>{selectedItem.title}</h3>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    onClick={() => handleStatusChange(selectedItem.id, 'fixed')}
                    style={{
                      padding: '6px 14px',
                      fontSize: 13,
                      background: selectedItem.status === 'fixed' ? '#16a34a' : '#fff',
                      color: selectedItem.status === 'fixed' ? '#fff' : '#16a34a',
                      border: '1px solid #16a34a',
                      borderRadius: 4,
                      cursor: 'pointer',
                    }}
                  >
                    ✓ 标记已修复
                  </button>
                  <button
                    onClick={() => handleStatusChange(selectedItem.id, 'waived')}
                    style={{
                      padding: '6px 14px',
                      fontSize: 13,
                      background: selectedItem.status === 'waived' ? '#6b7280' : '#fff',
                      color: selectedItem.status === 'waived' ? '#fff' : '#6b7280',
                      border: '1px solid #6b7280',
                      borderRadius: 4,
                      cursor: 'pointer',
                    }}
                  >
                    ⊘ 豁免
                  </button>
                  <button
                    onClick={() => handleStatusChange(selectedItem.id, 'open')}
                    style={{
                      padding: '6px 14px',
                      fontSize: 13,
                      background: selectedItem.status === 'open' ? '#f59e0b' : '#fff',
                      color: selectedItem.status === 'open' ? '#fff' : '#f59e0b',
                      border: '1px solid #f59e0b',
                      borderRadius: 4,
                      cursor: 'pointer',
                    }}
                  >
                    ○ 待修复
                  </button>
                </div>
              </div>

              <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 12, padding: '4px 10px', borderRadius: 4, background: '#f3f4f6', color: '#374151' }}>
                  阶段: {STAGES.find((s) => s.id === selectedItem.stage)?.label}
                </span>
                <span style={{ fontSize: 12, padding: '4px 10px', borderRadius: 4, background: AXES.find((a) => a.id === selectedItem.axis)?.color + '15', color: AXES.find((a) => a.id === selectedItem.axis)?.color }}>
                  五轴: {AXES.find((a) => a.id === selectedItem.axis)?.label}
                </span>
                <span style={{ fontSize: 12, padding: '4px 10px', borderRadius: 4, background: SEVERITY_COLORS[selectedItem.severity].bg, color: SEVERITY_COLORS[selectedItem.severity].color }}>
                  严重: {selectedItem.severity === 'critical' ? '严重' : selectedItem.severity === 'warning' ? '警告' : '信息'}
                </span>
                {selectedItem.filePath && (
                  <span style={{ fontSize: 12, padding: '4px 10px', borderRadius: 4, background: '#eff6ff', color: '#2563eb' }}>
                    📄 {selectedItem.filePath}{selectedItem.lineNumber ? `:${selectedItem.lineNumber}` : ''}
                  </span>
                )}
              </div>

              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: '#374151' }}>问题描述</div>
                <div style={{ padding: 16, background: '#fef2f2', borderRadius: 6, fontSize: 13, color: '#374151', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                  {selectedItem.description}
                </div>
              </div>

              {selectedItem.suggestion && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: '#374151' }}>修复建议</div>
                  <div style={{ padding: 16, background: '#f0fdf4', borderRadius: 6, fontSize: 13, color: '#374151', lineHeight: 1.6 }}>
                    {selectedItem.suggestion}
                  </div>
                </div>
              )}

              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: '#374151' }}>审查备注</div>
                <textarea
                  style={{ width: '100%', padding: 12, border: '1px solid #e5e7eb', borderRadius: 6, fontSize: 13, minHeight: 80, resize: 'vertical' }}
                  placeholder="输入审查意见..."
                />
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280', fontSize: 14 }}>
              请从左侧选择一个审查项
            </div>
          )}
        </div>

        {/* 右侧：审查统计 */}
        <div style={{ width: 280, minWidth: 280, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ padding: 16, borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12, color: '#374151' }}>审查统计</div>
            <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
              <div style={{ flex: 1, textAlign: 'center', padding: 10, background: '#fef2f2', borderRadius: 6 }}>
                <div style={{ fontSize: 20, fontWeight: 700, color: '#dc2626' }}>{stats.open}</div>
                <div style={{ fontSize: 11, color: '#dc2626' }}>待修复</div>
              </div>
              <div style={{ flex: 1, textAlign: 'center', padding: 10, background: '#d1fae5', borderRadius: 6 }}>
                <div style={{ fontSize: 20, fontWeight: 700, color: '#065f46' }}>{stats.fixed}</div>
                <div style={{ fontSize: 11, color: '#065f46' }}>已修复</div>
              </div>
              <div style={{ flex: 1, textAlign: 'center', padding: 10, background: '#f3f4f6', borderRadius: 6 }}>
                <div style={{ fontSize: 20, fontWeight: 700, color: '#6b7280' }}>{stats.waived}</div>
                <div style={{ fontSize: 11, color: '#6b7280' }}>已豁免</div>
              </div>
            </div>
            <div style={{ fontSize: 12, color: '#6b7280' }}>
              总审查项: {stats.total} | 严重: {stats.critical}
            </div>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 12, color: '#374151' }}>五轴审查</div>
            {axisStats.map((axis) => (
              <div key={axis.id} style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                  <span style={{ color: axis.color }}>{axis.label}</span>
                  <span style={{ color: '#6b7280' }}>{axis.total - axis.open}/{axis.total}</span>
                </div>
                <div style={{ height: 6, background: '#f3f4f6', borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{ width: `${axis.total > 0 ? ((axis.total - axis.open) / axis.total) * 100 : 0}%`, height: '100%', background: axis.color, borderRadius: 3, transition: 'width 0.3s' }} />
                </div>
              </div>
            ))}

            <div style={{ marginTop: 16, padding: 12, background: '#f9fafb', borderRadius: 6, fontSize: 12, color: '#374151' }}>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>审查检查清单</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                  <input type="checkbox" checked={reviewItems.filter((i) => i.stage === 'file-scan').every((i) => i.status !== 'open')} readOnly /> 文件扫描无问题
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                  <input type="checkbox" checked={reviewItems.filter((i) => i.stage === 'static-analysis').every((i) => i.status !== 'open')} readOnly /> 静态分析通过
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                  <input type="checkbox" checked={reviewItems.filter((i) => i.stage === 'manual-review').every((i) => i.status !== 'open')} readOnly /> 人工审查完成
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                  <input type="checkbox" checked={reviewItems.filter((i) => i.stage === 'regression').every((i) => i.status !== 'open')} readOnly /> 回归验证通过
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                  <input type="checkbox" checked={stats.critical === 0} readOnly /> 无严重问题
                </label>
              </div>
            </div>

            {stats.allClear && (
              <div style={{ marginTop: 16, padding: 12, background: '#d1fae5', borderRadius: 6, fontSize: 13, color: '#065f46' }}>
                ✅ 所有审查项已处理，可以提交审查通过
              </div>
            )}

            {stats.critical > 0 && (
              <div style={{ marginTop: 16, padding: 12, background: '#fef2f2', borderRadius: 6, fontSize: 13, color: '#dc2626' }}>
                ⚠️ 还有 {stats.critical} 个严重问题待修复
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
