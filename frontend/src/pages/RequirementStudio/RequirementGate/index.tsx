import { useEffect, useMemo, useState } from 'react'
import { useProjectContext } from '../../../App'
import { listUserStories, type UserStory } from '../../../services/userStory'
import { listSketches, type Sketch } from '../../../services/sketch'
import { listSizeEstimates, type SizeEstimate } from '../../../services/complexity'
import { fetchArtifacts, type ArtifactSummary } from '../../../services/requirementStudio'
import {
  listProjectReviews,
  createProjectReview,
  updateProjectReview,
} from '../../../services/projectReview'
import { fetchStageProgress, decideProjectStageGate } from '../../../services/stage'

interface ReviewItem {
  id: string
  category: 'user-story' | 'prd' | 'sketch' | 'size-estimate' | 'acceptance-criteria'
  title: string
  status: 'pending' | 'approved' | 'rejected'
  content?: string
  metadata?: Record<string, unknown>
}

const CATEGORIES = [
  { id: 'user-story', label: '用户故事', icon: '📝' },
  { id: 'prd', label: 'PRD 需求文档', icon: '📄' },
  { id: 'sketch', label: '需求草图', icon: '🎨' },
  { id: 'size-estimate', label: '规模初估', icon: '📊' },
  { id: 'acceptance-criteria', label: '验收标准', icon: '✅' },
]

export default function RequirementGatePage() {
  const { currentProjectId } = useProjectContext()
  const projectId = currentProjectId

  const [stories, setStories] = useState<UserStory[]>([])
  const [sketches, setSketches] = useState<Sketch[]>([])
  const [sizeEstimates, setSizeEstimates] = useState<SizeEstimate[]>([])
  const [artifacts, setArtifacts] = useState<ArtifactSummary[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [selectedCategory, setSelectedCategory] = useState<string>('user-story')
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null)
  const [reviewNotes, setReviewNotes] = useState<Record<string, string>>({})
  const [reviewStatus, setReviewStatus] = useState<Record<string, 'pending' | 'approved' | 'rejected'>>({})
  const [showGateModal, setShowGateModal] = useState(false)

  const [stageId, setStageId] = useState<string>('')

  useEffect(() => {
    if (!projectId) return
    setLoading(true)
    Promise.all([
      listUserStories(projectId),
      listSketches(projectId),
      listSizeEstimates(projectId),
      fetchArtifacts(projectId),
      listProjectReviews(projectId, 'gate1'),
      fetchStageProgress(projectId),
    ])
      .then(([s, sk, se, a, reviews, progress]) => {
        setStories(s)
        setSketches(sk)
        setSizeEstimates(se)
        setArtifacts(a)
        // Find requirement stage for Gate 1
        const reqStage = progress.stages.find(
          (st) => st.business_stage_key?.includes('requirement') || st.business_stage_key?.includes('brainstorm')
        )
        if (reqStage) setStageId(reqStage.project_stage_id)
        // 加载持久化的审查状态
        const statusMap: Record<string, 'pending' | 'approved' | 'rejected'> = {}
        const notesMap: Record<string, string> = {}
        reviews.forEach((r) => {
          if (['pending', 'approved', 'rejected'].includes(r.status)) {
            statusMap[r.item_id] = r.status as 'pending' | 'approved' | 'rejected'
          }
          if (r.notes) notesMap[r.item_id] = r.notes
        })
        setReviewStatus(statusMap)
        setReviewNotes(notesMap)
        setError(null)
      })
      .catch((err) => setError(err instanceof Error ? err.message : '加载失败'))
      .finally(() => setLoading(false))
  }, [projectId])

  const reviewItems = useMemo((): ReviewItem[] => {
    const items: ReviewItem[] = []

    // 用户故事
    stories.forEach((s) => {
      items.push({
        id: `story-${s.story_id}`,
        category: 'user-story',
        title: s.title,
        status: reviewStatus[`story-${s.story_id}`] || 'pending',
        content: s.description || '',
        metadata: { priority: s.priority, status: s.status },
      })
    })

    // PRD 产物
    artifacts.filter((a) => a.file_name.includes('prd') || a.file_name.includes('requirement')).forEach((a) => {
      items.push({
        id: `prd-${a.artifact_id}`,
        category: 'prd',
        title: a.file_name,
        status: reviewStatus[`prd-${a.artifact_id}`] || 'pending',
        metadata: { fileType: a.file_type, createdAt: a.created_at },
      })
    })

    // 草图
    sketches.forEach((s) => {
      items.push({
        id: `sketch-${s.sketch_id}`,
        category: 'sketch',
        title: s.name,
        status: reviewStatus[`sketch-${s.sketch_id}`] || 'pending',
        metadata: { pageCount: s.page_count, coverage: s.coverage_percent, status: s.status },
      })
    })

    // 规模初估
    sizeEstimates.forEach((se) => {
      items.push({
        id: `size-${se.estimate_id}`,
        category: 'size-estimate',
        title: `规模初估 (${se.complexity_level || '未评估'})`,
        status: reviewStatus[`size-${se.estimate_id}`] || 'pending',
        content: `模块: ${se.module_count}, 接口: ${se.interface_count}, 页面: ${se.page_count}, 复杂度: ${se.tech_complexity}, 风险: ${se.risk_level}`,
        metadata: { optimistic: se.optimistic_score, expected: se.expected_score, conservative: se.conservative_score },
      })
    })

    // 验收标准（从用户故事中提取）
    stories.filter((s) => s.acceptance_criteria).forEach((s) => {
      items.push({
        id: `ac-${s.story_id}`,
        category: 'acceptance-criteria',
        title: `验收: ${s.title}`,
        status: reviewStatus[`ac-${s.story_id}`] || 'pending',
        content: s.acceptance_criteria || '',
      })
    })

    return items
  }, [stories, sketches, sizeEstimates, artifacts, reviewStatus])

  const filteredItems = useMemo(() => {
    return reviewItems.filter((item) => item.category === selectedCategory)
  }, [reviewItems, selectedCategory])

  const selectedItem = useMemo(() => {
    return reviewItems.find((item) => item.id === selectedItemId) || null
  }, [reviewItems, selectedItemId])

  const stats = useMemo(() => {
    const total = reviewItems.length
    const approved = reviewItems.filter((i) => reviewStatus[i.id] === 'approved').length
    const rejected = reviewItems.filter((i) => reviewStatus[i.id] === 'rejected').length
    const pending = total - approved - rejected
    return { total, approved, rejected, pending, allApproved: approved === total && total > 0 }
  }, [reviewItems, reviewStatus])

  const handleApprove = async (itemId: string) => {
    setReviewStatus((prev) => ({ ...prev, [itemId]: 'approved' }))
    if (!projectId) return
    try {
      const reviews = await listProjectReviews(projectId, 'gate1')
      const existing = reviews.find((r) => r.item_id === itemId)
      const notes = reviewNotes[itemId] || undefined
      if (existing) {
        await updateProjectReview(projectId, existing.review_id, { status: 'approved', notes })
      } else {
        const item = reviewItems.find((i) => i.id === itemId)
        if (item) {
          await createProjectReview(projectId, {
            review_type: 'gate1',
            item_id: itemId,
            item_type: item.category,
            status: 'approved',
            notes,
          })
        }
      }
    } catch (err) {
      console.error('保存审查状态失败:', err)
    }
  }

  const handleReject = async (itemId: string) => {
    setReviewStatus((prev) => ({ ...prev, [itemId]: 'rejected' }))
    if (!projectId) return
    try {
      const reviews = await listProjectReviews(projectId, 'gate1')
      const existing = reviews.find((r) => r.item_id === itemId)
      const notes = reviewNotes[itemId] || undefined
      if (existing) {
        await updateProjectReview(projectId, existing.review_id, { status: 'rejected', notes })
      } else {
        const item = reviewItems.find((i) => i.id === itemId)
        if (item) {
          await createProjectReview(projectId, {
            review_type: 'gate1',
            item_id: itemId,
            item_type: item.category,
            status: 'rejected',
            notes,
          })
        }
      }
    } catch (err) {
      console.error('保存审查状态失败:', err)
    }
  }

  const handleNoteChange = (itemId: string, note: string) => {
    setReviewNotes((prev) => ({ ...prev, [itemId]: note }))
  }

  const handleNoteSave = async (itemId: string) => {
    if (!projectId) return
    const notes = reviewNotes[itemId]
    try {
      const reviews = await listProjectReviews(projectId, 'gate1')
      const existing = reviews.find((r) => r.item_id === itemId)
      if (existing) {
        await updateProjectReview(projectId, existing.review_id, { notes })
      } else {
        const item = reviewItems.find((i) => i.id === itemId)
        if (item) {
          await createProjectReview(projectId, {
            review_type: 'gate1',
            item_id: itemId,
            item_type: item.category,
            status: reviewStatus[itemId] || 'pending',
            notes,
          })
        }
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
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>需求确认 — Gate 1</h2>
          <div style={{ display: 'flex', gap: 6 }}>
            {CATEGORIES.map((cat) => {
              const count = reviewItems.filter((i) => i.category === cat.id).length
              const approvedCount = reviewItems.filter((i) => i.category === cat.id && reviewStatus[i.id] === 'approved').length
              return (
                <button
                  key={cat.id}
                  onClick={() => { setSelectedCategory(cat.id); setSelectedItemId(null) }}
                  style={{
                    padding: '4px 10px',
                    fontSize: 12,
                    borderRadius: 4,
                    border: '1px solid #e5e7eb',
                    background: selectedCategory === cat.id ? '#eff6ff' : '#fff',
                    color: selectedCategory === cat.id ? '#2563eb' : '#374151',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4,
                  }}
                >
                  <span>{cat.icon}</span>
                  <span>{cat.label}</span>
                  <span style={{ fontSize: 10, color: '#9ca3af' }}>({approvedCount}/{count})</span>
                </button>
              )
            })}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ fontSize: 13, color: '#6b7280' }}>
            审查: <span style={{ color: '#16a34a', fontWeight: 600 }}>{stats.approved}</span> / <span style={{ color: '#dc2626' }}>{stats.rejected}</span> / <span>{stats.pending}</span> (通过/驳回/待审)
          </div>
          <button
            onClick={() => setShowGateModal(true)}
            disabled={!stats.allApproved}
            style={{
              padding: '6px 16px',
              fontSize: 13,
              background: stats.allApproved ? '#16a34a' : '#e5e7eb',
              color: stats.allApproved ? '#fff' : '#9ca3af',
              border: 'none',
              borderRadius: 4,
              cursor: stats.allApproved ? 'pointer' : 'not-allowed',
              fontWeight: 600,
            }}
          >
            ✅ 通过 Gate 1
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '8px 16px', background: '#fef2f2', color: '#dc2626', fontSize: 13, borderBottom: '1px solid #e5e7eb' }}>
          {error}
        </div>
      )}

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* 左侧列表 */}
        <div style={{ width: 300, minWidth: 300, borderRight: '1px solid #e5e7eb', overflowY: 'auto', background: '#fff' }}>
          {loading && <div style={{ padding: 24, textAlign: 'center', color: '#9ca3af', fontSize: 13 }}>加载中...</div>}
          {filteredItems.length === 0 && !loading && (
            <div style={{ padding: 24, textAlign: 'center', color: '#9ca3af', fontSize: 13 }}>暂无{CATEGORIES.find(c => c.id === selectedCategory)?.label}记录</div>
          )}
          {filteredItems.map((item) => {
            const isSelected = selectedItemId === item.id
            const status = reviewStatus[item.id] || 'pending'
            return (
              <div
                key={item.id}
                onClick={() => setSelectedItemId(item.id)}
                style={{
                  padding: '10px 14px',
                  cursor: 'pointer',
                  borderLeft: isSelected ? '3px solid #2563eb' : '3px solid transparent',
                  background: isSelected ? '#eff6ff' : 'transparent',
                  borderBottom: '1px solid #f3f4f6',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: '#111827', wordBreak: 'break-all' }}>{item.title}</span>
                  <span style={{
                    fontSize: 10,
                    padding: '2px 6px',
                    borderRadius: 4,
                    background: status === 'approved' ? '#d1fae5' : status === 'rejected' ? '#fef2f2' : '#fef3c7',
                    color: status === 'approved' ? '#065f46' : status === 'rejected' ? '#dc2626' : '#92400e',
                  }}>
                    {status === 'approved' ? '已通过' : status === 'rejected' ? '已驳回' : '待审'}
                  </span>
                </div>
                {item.content && (
                  <div style={{ fontSize: 12, color: '#6b7280', lineHeight: 1.4, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {item.content.slice(0, 100)}
                  </div>
                )}
                {item.metadata && Object.keys(item.metadata).length > 0 && (
                  <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 4 }}>
                    {Object.entries(item.metadata).map(([k, v]) => `${k}: ${v}`).join(' | ')}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* 中间详情 */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 24, borderRight: '1px solid #e5e7eb' }}>
          {selectedItem ? (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h3 style={{ margin: 0, fontSize: 18 }}>{selectedItem.title}</h3>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    onClick={() => handleApprove(selectedItem.id)}
                    style={{
                      padding: '6px 14px',
                      fontSize: 13,
                      background: reviewStatus[selectedItem.id] === 'approved' ? '#16a34a' : '#fff',
                      color: reviewStatus[selectedItem.id] === 'approved' ? '#fff' : '#16a34a',
                      border: '1px solid #16a34a',
                      borderRadius: 4,
                      cursor: 'pointer',
                    }}
                  >
                    ✓ 通过
                  </button>
                  <button
                    onClick={() => handleReject(selectedItem.id)}
                    style={{
                      padding: '6px 14px',
                      fontSize: 13,
                      background: reviewStatus[selectedItem.id] === 'rejected' ? '#dc2626' : '#fff',
                      color: reviewStatus[selectedItem.id] === 'rejected' ? '#fff' : '#dc2626',
                      border: '1px solid #dc2626',
                      borderRadius: 4,
                      cursor: 'pointer',
                    }}
                  >
                    ✕ 驳回
                  </button>
                </div>
              </div>

              {selectedItem.content && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: '#374151' }}>内容</div>
                  <div style={{ padding: 16, background: '#f9fafb', borderRadius: 6, fontSize: 13, color: '#374151', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                    {selectedItem.content}
                  </div>
                </div>
              )}

              {selectedItem.metadata && Object.keys(selectedItem.metadata).length > 0 && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: '#374151' }}>元数据</div>
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    {Object.entries(selectedItem.metadata).map(([k, v]) => (
                      <span key={k} style={{ fontSize: 12, padding: '4px 10px', borderRadius: 4, background: '#f3f4f6', color: '#374151' }}>
                        {k}: {String(v)}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: '#374151' }}>审查备注</div>
                <textarea
                  value={reviewNotes[selectedItem.id] || ''}
                  onChange={(e) => handleNoteChange(selectedItem.id, e.target.value)}
                  onBlur={() => handleNoteSave(selectedItem.id)}
                  style={{ width: '100%', padding: 12, border: '1px solid #e5e7eb', borderRadius: 6, fontSize: 13, minHeight: 100, resize: 'vertical' }}
                  placeholder="输入审查意见..."
                />
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280', fontSize: 14 }}>
              请从左侧选择一项进行审查
            </div>
          )}
        </div>

        {/* 右侧审查面板 */}
        <div style={{ width: 280, minWidth: 280, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ borderTop: '1px solid #e5e7eb', padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#111827' }}>审查批注</div>
            <div style={{ maxHeight: 160, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 8 }}>
              {Object.keys(reviewNotes).length === 0 && <div style={{ fontSize: 12, color: '#9ca3af' }}>暂无批注</div>}
              {Object.entries(reviewNotes).map(([id, note]) => (
                <div key={id} style={{ padding: 8, background: '#f9fafb', borderRadius: 4, fontSize: 12, color: '#374151' }}>
                  <div style={{ fontWeight: 500, marginBottom: 2 }}>{reviewItems.find(i => i.id === id)?.title || id}</div>
                  <div>{note}</div>
                </div>
              ))}
            </div>
            <textarea
              value={selectedItem ? reviewNotes[selectedItem.id] || '' : ''}
              onChange={(e) => selectedItem && handleNoteChange(selectedItem.id, e.target.value)}
              onBlur={() => selectedItem && handleNoteSave(selectedItem.id)}
              placeholder={selectedItem ? '输入批注...' : '请先从左侧选择一项'}
              disabled={!selectedItem}
              style={{
                width: '100%', padding: 8, fontSize: 12, border: '1px solid #e5e7eb', borderRadius: 4, resize: 'none', minHeight: 60, fontFamily: 'inherit',
              }}
            />
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={() => selectedItem && handleApprove(selectedItem.id)}
                disabled={!selectedItem}
                style={{
                  flex: 1, padding: '6px 12px', fontSize: 12, background: selectedItem && reviewStatus[selectedItem.id] === 'approved' ? '#16a34a' : '#f3f4f6', color: selectedItem && reviewStatus[selectedItem.id] === 'approved' ? '#fff' : '#16a34a', border: '1px solid #16a34a', borderRadius: 4, cursor: selectedItem ? 'pointer' : 'not-allowed',
                }}
              >
                ✓ 通过
              </button>
              <button
                onClick={() => selectedItem && handleReject(selectedItem.id)}
                disabled={!selectedItem}
                style={{
                  flex: 1, padding: '6px 12px', fontSize: 12, background: selectedItem && reviewStatus[selectedItem.id] === 'rejected' ? '#dc2626' : '#f3f4f6', color: selectedItem && reviewStatus[selectedItem.id] === 'rejected' ? '#fff' : '#dc2626', border: '1px solid #dc2626', borderRadius: 4, cursor: selectedItem ? 'pointer' : 'not-allowed',
                }}
              >
                ✕ 驳回
              </button>
            </div>
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 12, color: '#374151' }}>审查进度</div>
            {CATEGORIES.map((cat) => {
              const catItems = reviewItems.filter((i) => i.category === cat.id)
              const catApproved = catItems.filter((i) => reviewStatus[i.id] === 'approved').length
              const catRejected = catItems.filter((i) => reviewStatus[i.id] === 'rejected').length
              const catTotal = catItems.length
              const progress = catTotal > 0 ? ((catApproved + catRejected) / catTotal) * 100 : 0
              return (
                <div key={cat.id} style={{ marginBottom: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                    <span>{cat.icon} {cat.label}</span>
                    <span style={{ color: '#6b7280' }}>{catApproved}/{catTotal}</span>
                  </div>
                  <div style={{ height: 6, background: '#f3f4f6', borderRadius: 3, overflow: 'hidden' }}>
                    <div style={{ width: `${progress}%`, height: '100%', background: catApproved === catTotal && catTotal > 0 ? '#16a34a' : '#2563eb', borderRadius: 3, transition: 'width 0.3s' }} />
                  </div>
                </div>
              )
            })}
            <div style={{ marginTop: 16, padding: 12, background: '#f9fafb', borderRadius: 6, fontSize: 12, color: '#374151' }}>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>Gate 1 检查清单</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                  <input type="checkbox" checked={stats.approved > 0} readOnly /> 用户故事已评审
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                  <input type="checkbox" checked={reviewItems.filter((i) => i.category === 'prd').some((i) => reviewStatus[i.id] === 'approved')} readOnly /> PRD 已确认
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                  <input type="checkbox" checked={reviewItems.filter((i) => i.category === 'sketch').some((i) => reviewStatus[i.id] === 'approved')} readOnly /> 草图已确认
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                  <input type="checkbox" checked={sizeEstimates.length > 0} readOnly /> 规模已初估
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                  <input type="checkbox" checked={reviewItems.filter((i) => i.category === 'acceptance-criteria').some((i) => reviewStatus[i.id] === 'approved')} readOnly /> 验收标准已审查
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Gate 1 通过确认弹窗 */}
      {showGateModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50 }}>
          <div style={{ background: '#fff', borderRadius: 8, padding: 24, width: 480, maxWidth: '90vw' }}>
            <h3 style={{ margin: '0 0 16px', fontSize: 18 }}>确认通过 Gate 1</h3>
            <div style={{ marginBottom: 16, fontSize: 13, color: '#374151', lineHeight: 1.6 }}>
              <p>通过 Gate 1 意味着：</p>
              <ul style={{ paddingLeft: 20, margin: '8px 0' }}>
                <li>需求基线已冻结</li>
                <li>用户故事已确认</li>
                <li>PRD 已通过审查</li>
                <li>草图已确认</li>
                <li>规模初估已完成</li>
                <li>验收标准已审查</li>
              </ul>
              <p style={{ color: '#dc2626' }}>通过后，需求阶段将被锁定，进入设计阶段前需通过变更请求修改。</p>
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button onClick={() => setShowGateModal(false)} style={{ padding: '8px 16px', fontSize: 13, border: '1px solid #e5e7eb', background: '#fff', borderRadius: 4, cursor: 'pointer' }}>取消</button>
              <button onClick={async () => {
                setShowGateModal(false)
                if (!projectId || !stageId) {
                  alert('无法锁定阶段：缺少项目或阶段ID')
                  return
                }
                try {
                  await decideProjectStageGate(projectId, stageId, 'pass', 'Gate 1 审批通过：需求基线冻结')
                  alert('Gate 1 已通过！需求基线已冻结，阶段已锁定。')
                } catch (err) {
                  alert(`Gate 1 锁定失败: ${err instanceof Error ? err.message : '未知错误'}`)
                }
              }} style={{ padding: '8px 16px', fontSize: 13, background: '#16a34a', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}>确认通过</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
