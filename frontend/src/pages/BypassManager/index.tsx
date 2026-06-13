import { useCallback, useEffect, useState } from 'react'
import {
  applyBypass,
  listBypassApplications,
  approveBypass,
  type BypassRecord,
} from '../../services/bypass'
import ProjectSelector from '../../components/ProjectSelector'

const LS_PROJECT_KEY = 'arsitect:lastProjectId'

export default function BypassManager() {
  const [projectId, setProjectId] = useState(() => {
    try {
      return localStorage.getItem(LS_PROJECT_KEY) || ''
    } catch {
      return ''
    }
  })
  const [records, setRecords] = useState<BypassRecord[]>([])
  const [showApply, setShowApply] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [viewingRecord, setViewingRecord] = useState<BypassRecord | null>(null)

  const loadRecords = useCallback(async () => {
    if (!projectId.trim()) return
    setLoading(true)
    setError(null)
    try {
      const data = await listBypassApplications(projectId)
      setRecords(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    loadRecords()
  }, [loadRecords])

  useEffect(() => {
    try {
      if (projectId.trim()) {
        localStorage.setItem(LS_PROJECT_KEY, projectId)
      }
    } catch {
      // ignore
    }
  }, [projectId])

  const handleApprove = async (recordId: string) => {
    setError(null)
    try {
      await approveBypass(recordId, { approved_by: 'admin' })
      await loadRecords()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '审批失败')
    }
  }

  const openDetail = (record: BypassRecord) => {
    setViewingRecord(record)
  }

  const closeDetail = () => {
    setViewingRecord(null)
  }

  const isPending = (status: string) => status === 'PENDING_POST_APPROVAL'

  return (
    <div style={{ maxWidth: 960 }}>
      <h1 style={{ marginBottom: 16 }}>旁路审批管理</h1>

      <div style={{ display: 'flex', gap: 8, marginBottom: 24, alignItems: 'center' }}>
        <ProjectSelector value={projectId} onChange={setProjectId} />
        <button onClick={() => setShowApply(true)} disabled={!projectId.trim()}>
          + 申请旁路
        </button>
      </div>

      {error && <div style={{ color: '#ef4444', marginBottom: 16 }}>错误: {error}</div>}

      {showApply && (
        <ApplyBypassModal
          onClose={() => setShowApply(false)}
          onApplied={loadRecords}
        />
      )}

      <h3>审批记录</h3>

      {loading && (
        <div style={{ color: '#6b7280', padding: 24, textAlign: 'center' }}>加载中...</div>
      )}

      {!loading && records.length === 0 && (
        <div style={{ color: '#6b7280', padding: 24, textAlign: 'center' }}>暂无记录</div>
      )}

      {!loading && records.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {records.map((r) => (
            <div
              key={r.record_id}
              style={{
                padding: 12,
                border: '1px solid #e5e7eb',
                borderRadius: 6,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: 14 }}>
                  {r.status} · {r.reason ?? '无原因'}
                </div>
                <div style={{ fontSize: 12, color: '#6b7280' }}>
                  Stage: {r.stage_id.slice(0, 8)} · Skill: {r.skill_id.slice(0, 8)}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <button onClick={() => openDetail(r)}>查看详情</button>
                {isPending(r.status) ? (
                  <button onClick={() => handleApprove(r.record_id)} disabled={loading}>
                    审批通过
                  </button>
                ) : (
                  <span
                    style={{
                      fontSize: 12,
                      color: '#6b7280',
                      background: '#f3f4f6',
                      padding: '4px 8px',
                      borderRadius: 4,
                    }}
                  >
                    已{r.status === 'APPROVED' ? '通过' : r.status === 'REJECTED' ? '驳回' : '处理'}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {viewingRecord && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 50,
          }}
          onClick={closeDetail}
        >
          <div
            style={{ background: '#fff', padding: 24, borderRadius: 8, width: 480, maxWidth: '90vw' }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ marginTop: 0 }}>旁路审批详情</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: 14 }}>
              <div><strong>记录ID:</strong> {viewingRecord.record_id}</div>
              <div><strong>计划ID:</strong> {viewingRecord.plan_id}</div>
              <div><strong>阶段ID:</strong> {viewingRecord.stage_id}</div>
              <div><strong>技能ID:</strong> {viewingRecord.skill_id}</div>
              <div><strong>触发人:</strong> {viewingRecord.triggered_by}</div>
              <div><strong>原因:</strong> {viewingRecord.reason ?? '无'}</div>
              <div><strong>状态:</strong> {viewingRecord.status}</div>
              <div><strong>截止时间:</strong> {viewingRecord.deadline_at ?? '无'}</div>
              <div><strong>关闭时间:</strong> {viewingRecord.closed_at ?? '无'}</div>
              <div><strong>创建时间:</strong> {viewingRecord.created_at ?? '无'}</div>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 8 }}>
                <button type="button" onClick={closeDetail}>关闭</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function ApplyBypassModal({
  onClose,
  onApplied,
}: {
  onClose: () => void
  onApplied: () => void
}) {
  const [gateId, setGateId] = useState('')
  const [planId, setPlanId] = useState('')
  const [stageId, setStageId] = useState('')
  const [skillId, setSkillId] = useState('')
  const [reason, setReason] = useState('')
  const [triggeredBy, setTriggeredBy] = useState('')
  const [token, setToken] = useState('')
  const [deadlineHours, setDeadlineHours] = useState<number>(24)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    setSubmitting(true)
    try {
      await applyBypass(gateId, {
        plan_id: planId,
        stage_id: stageId,
        skill_id: skillId,
        triggered_by: triggeredBy,
        reason,
        authorizer_token: token,
        deadline_hours: deadlineHours,
      })
      onApplied()
      onClose()
    } catch (e: unknown) {
      setFormError(e instanceof Error ? e.message : '申请失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.4)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 50,
      }}
      onClick={onClose}
    >
      <div
        style={{ background: '#fff', padding: 24, borderRadius: 8, width: 480, maxWidth: '90vw' }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 style={{ marginTop: 0 }}>申请旁路审批</h3>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <input placeholder="Gate ID" value={gateId} onChange={(e) => setGateId(e.target.value)} required style={{ padding: 8, border: '1px solid #e5e7eb' }} />
          <input placeholder="Plan ID" value={planId} onChange={(e) => setPlanId(e.target.value)} required style={{ padding: 8, border: '1px solid #e5e7eb' }} />
          <input placeholder="Stage ID" value={stageId} onChange={(e) => setStageId(e.target.value)} required style={{ padding: 8, border: '1px solid #e5e7eb' }} />
          <input placeholder="Skill ID" value={skillId} onChange={(e) => setSkillId(e.target.value)} required style={{ padding: 8, border: '1px solid #e5e7eb' }} />
          <input placeholder="申请人ID" value={triggeredBy} onChange={(e) => setTriggeredBy(e.target.value)} required style={{ padding: 8, border: '1px solid #e5e7eb' }} />
          <input
            type="text"
            placeholder="授权Token（32字节）"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            required
            style={{ padding: 8, border: '1px solid #e5e7eb' }}
          />
          <input
            type="number"
            placeholder="有效时长（小时）"
            value={deadlineHours}
            onChange={(e) => setDeadlineHours(Number(e.target.value))}
            min={1}
            required
            style={{ padding: 8, border: '1px solid #e5e7eb' }}
          />
          <textarea placeholder="原因（5-500字）" value={reason} onChange={(e) => setReason(e.target.value)} required minLength={5} maxLength={500} rows={3} style={{ padding: 8, border: '1px solid #e5e7eb' }} />
          {formError && <div style={{ color: '#ef4444' }}>错误: {formError}</div>}
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
            <button type="button" onClick={onClose}>取消</button>
            <button type="submit" disabled={submitting}>提交</button>
          </div>
        </form>
      </div>
    </div>
  )
}
