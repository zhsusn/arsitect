import { useEffect, useState, useCallback } from 'react'
import {
  triggerValidation,
  fetchSessions,
  updateBaseline,
  type ArchValidationSession,
} from '../../services/archValidation'

const LS_PROJECT_KEY = 'arsitect:lastProjectId'

const LEVEL_LABELS: Record<string, string> = {
  L1: 'L1 - 系统上下文',
  L2: 'L2 - 容器',
  L3: 'L3 - 组件',
  L4: 'L4 - 代码',
}

const STATUS_COLORS: Record<string, string> = {
  NO_DRIFT: '#16a34a',
  DRIFT_DETECTED: '#ea580c',
  BASELINE_UPDATED: '#2563eb',
  PENDING: '#6b7280',
}

function EmptyState({ onTrigger }: { onTrigger: () => void }) {
  return (
    <div
      style={{
        padding: 48,
        textAlign: 'center',
        border: '1px dashed #d1d5db',
        borderRadius: 12,
        background: '#fff',
      }}
    >
      <div style={{ fontSize: 48, marginBottom: 16 }}>🔍</div>
      <h3 style={{ margin: '0 0 8px', fontSize: 16, color: '#111827' }}>
        暂无验证记录
      </h3>
      <p style={{ margin: '0 0 20px', fontSize: 14, color: '#6b7280' }}>
        该项目尚未触发过架构验证。点击下方按钮开始第一次检测。
      </p>
      <button
        onClick={onTrigger}
        style={{
          padding: '8px 20px',
          background: '#2563eb',
          color: '#fff',
          border: 'none',
          borderRadius: 6,
          cursor: 'pointer',
          fontSize: 14,
          fontWeight: 500,
        }}
      >
        立即验证
      </button>
    </div>
  )
}

function DiffPanel({
  session,
  onClose,
  onBaseline,
}: {
  session: ArchValidationSession
  onClose: () => void
  onBaseline: () => void
}) {
  const hasDrift = session.status === 'DRIFT_DETECTED'
  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.4)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 100,
        padding: 24,
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        style={{
          background: '#fff',
          borderRadius: 12,
          width: '100%',
          maxWidth: 960,
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid #e5e7eb',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div style={{ fontWeight: 600, fontSize: 16 }}>
              差异对比 — {LEVEL_LABELS[session.level] || session.level}
            </div>
            <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>
              {session.diff_summary || '无差异'} ·{' '}
              <span
                style={{
                  color: STATUS_COLORS[session.status] || '#6b7280',
                  fontWeight: 600,
                }}
              >
                {session.status}
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: 20,
              cursor: 'pointer',
              color: '#6b7280',
            }}
          >
            ✕
          </button>
        </div>

        <div
          style={{
            flex: 1,
            overflow: 'auto',
            padding: 16,
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 16,
          }}
        >
          <div
            style={{
              background: '#f9fafb',
              borderRadius: 8,
              padding: 12,
              border: '1px solid #e5e7eb',
            }}
          >
            <div
              style={{
                fontSize: 12,
                color: '#6b7280',
                marginBottom: 8,
                fontWeight: 600,
              }}
            >
              基线 DSL
            </div>
            <pre
              style={{
                fontSize: 12,
                overflow: 'auto',
                maxHeight: 400,
                margin: 0,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-all',
              }}
            >
              {session.baseline_dsl || '(空)'}
            </pre>
          </div>
          <div
            style={{
              background: '#f9fafb',
              borderRadius: 8,
              padding: 12,
              border: '1px solid #e5e7eb',
            }}
          >
            <div
              style={{
                fontSize: 12,
                color: '#6b7280',
                marginBottom: 8,
                fontWeight: 600,
              }}
            >
              当前 DSL
            </div>
            <pre
              style={{
                fontSize: 12,
                overflow: 'auto',
                maxHeight: 400,
                margin: 0,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-all',
              }}
            >
              {session.current_dsl || '(空)'}
            </pre>
          </div>
        </div>

        {hasDrift && (
          <div
            style={{
              padding: '12px 20px',
              borderTop: '1px solid #e5e7eb',
              display: 'flex',
              justifyContent: 'flex-end',
              gap: 8,
            }}
          >
            <button
              onClick={onClose}
              style={{
                padding: '6px 14px',
                border: '1px solid #d1d5db',
                background: '#fff',
                borderRadius: 6,
                cursor: 'pointer',
                fontSize: 13,
              }}
            >
              关闭
            </button>
            <button
              onClick={onBaseline}
              style={{
                padding: '6px 14px',
                background: '#2563eb',
                color: '#fff',
                border: 'none',
                borderRadius: 6,
                cursor: 'pointer',
                fontSize: 13,
                fontWeight: 500,
              }}
            >
              将当前设为基线
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default function ArchValidation() {
  const [projectId, setProjectId] = useState(() => {
    try {
      return localStorage.getItem(LS_PROJECT_KEY) || ''
    } catch {
      return ''
    }
  })
  const [level, setLevel] = useState('L2')
  const [sessions, setSessions] = useState<ArchValidationSession[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedSession, setSelectedSession] =
    useState<ArchValidationSession | null>(null)

  const loadHistory = useCallback(async () => {
    if (!projectId.trim()) {
      setSessions([])
      return
    }
    setLoading(true)
    setError(null)
    try {
      const list = await fetchSessions(projectId)
      setSessions(list)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '加载历史失败'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    loadHistory()
  }, [loadHistory])

  const handleTrigger = async () => {
    if (!projectId.trim()) {
      setError('请先选择项目')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const s = await triggerValidation(projectId, level)
      setSessions((prev) => [s, ...prev])
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '触发验证失败'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleBaseline = async () => {
    if (!selectedSession) return
    setLoading(true)
    setError(null)
    try {
      const s = await updateBaseline(projectId, selectedSession.level)
      setSessions((prev) => [s, ...prev])
      setSelectedSession(null)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '更新基线失败'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const latestSession = sessions[0] ?? null

  return (
    <div style={{ maxWidth: 960 }}>
      <h1 style={{ marginBottom: 16 }}>架构验证中心</h1>

      <div
        style={{
          display: 'flex',
          gap: 8,
          marginBottom: 24,
          flexWrap: 'wrap',
          alignItems: 'center',
        }}
      >
        <input
          type="text"
          placeholder="项目ID"
          value={projectId}
          onChange={(e) => setProjectId(e.target.value)}
          style={{ flex: 1, minWidth: 200, padding: 8, borderRadius: 4, border: '1px solid #d1d5db' }}
        />
        <select
          value={level}
          onChange={(e) => setLevel(e.target.value)}
          style={{ padding: 8, borderRadius: 4, border: '1px solid #d1d5db' }}
        >
          <option value="L1">L1 - 系统上下文</option>
          <option value="L2">L2 - 容器</option>
          <option value="L3">L3 - 组件</option>
          <option value="L4">L4 - 代码</option>
        </select>
        <button
          onClick={handleTrigger}
          disabled={loading || !projectId.trim()}
          style={{
            padding: '8px 16px',
            background: loading ? '#9ca3af' : '#2563eb',
            color: '#fff',
            border: 'none',
            borderRadius: 6,
            cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: 14,
            fontWeight: 500,
          }}
        >
          {loading ? '验证中…' : '触发验证'}
        </button>
      </div>

      {error && (
        <div
          style={{
            color: '#b91c1c',
            marginBottom: 16,
            padding: '10px 14px',
            background: '#fef2f2',
            borderRadius: 6,
            fontSize: 14,
          }}
        >
          {error}
        </div>
      )}

      {/* Latest result banner */}
      {latestSession && (
        <div
          style={{
            marginBottom: 24,
            padding: '14px 18px',
            borderRadius: 8,
            background: '#fff',
            border: '1px solid #e5e7eb',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 8,
          }}
        >
          <div>
            <div style={{ fontSize: 13, color: '#374151', fontWeight: 600 }}>
              最新验证结果
            </div>
            <div style={{ fontSize: 13, color: '#6b7280', marginTop: 4 }}>
              {LEVEL_LABELS[latestSession.level]} ·{' '}
              <span
                style={{
                  color:
                    STATUS_COLORS[latestSession.status] || '#6b7280',
                  fontWeight: 600,
                }}
              >
                {latestSession.status}
              </span>{' '}
              · {latestSession.diff_summary || '无差异'} ·{' '}
              {new Date(latestSession.created_at).toLocaleString()}
            </div>
          </div>
          <button
            onClick={() => setSelectedSession(latestSession)}
            style={{
              padding: '6px 14px',
              background: '#eff6ff',
              color: '#2563eb',
              border: '1px solid #bfdbfe',
              borderRadius: 6,
              cursor: 'pointer',
              fontSize: 13,
              fontWeight: 500,
            }}
          >
            查看 DSL
          </button>
        </div>
      )}

      {/* History list */}
      {sessions.length === 0 && !loading && (
        <EmptyState onTrigger={handleTrigger} />
      )}

      {sessions.length > 0 && (
        <div
          style={{
            background: '#fff',
            borderRadius: 8,
            border: '1px solid #e5e7eb',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              padding: '12px 16px',
              borderBottom: '1px solid #e5e7eb',
              fontWeight: 600,
              fontSize: 14,
              color: '#111827',
            }}
          >
            验证历史 ({sessions.length})
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: '#f9fafb' }}>
                <th style={{ textAlign: 'left', padding: '10px 16px', fontWeight: 600, color: '#374151' }}>
                  时间
                </th>
                <th style={{ textAlign: 'left', padding: '10px 16px', fontWeight: 600, color: '#374151' }}>
                  层级
                </th>
                <th style={{ textAlign: 'left', padding: '10px 16px', fontWeight: 600, color: '#374151' }}>
                  状态
                </th>
                <th style={{ textAlign: 'left', padding: '10px 16px', fontWeight: 600, color: '#374151' }}>
                  漂移摘要
                </th>
                <th style={{ textAlign: 'right', padding: '10px 16px', fontWeight: 600, color: '#374151' }}>
                  操作
                </th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((s) => (
                <tr
                  key={s.session_id}
                  style={{ borderTop: '1px solid #f3f4f6' }}
                >
                  <td style={{ padding: '10px 16px', color: '#4b5563' }}>
                    {new Date(s.created_at).toLocaleString()}
                  </td>
                  <td style={{ padding: '10px 16px', color: '#4b5563' }}>
                    {LEVEL_LABELS[s.level] || s.level}
                  </td>
                  <td style={{ padding: '10px 16px' }}>
                    <span
                      style={{
                        display: 'inline-block',
                        padding: '2px 8px',
                        borderRadius: 12,
                        fontSize: 12,
                        fontWeight: 600,
                        color: '#fff',
                        background:
                          STATUS_COLORS[s.status] || '#6b7280',
                      }}
                    >
                      {s.status}
                    </span>
                  </td>
                  <td style={{ padding: '10px 16px', color: '#4b5563' }}>
                    {s.diff_summary || '—'}
                  </td>
                  <td style={{ padding: '10px 16px', textAlign: 'right' }}>
                    <button
                      onClick={() => setSelectedSession(s)}
                      style={{
                        padding: '4px 10px',
                        background: '#eff6ff',
                        color: '#2563eb',
                        border: '1px solid #bfdbfe',
                        borderRadius: 4,
                        cursor: 'pointer',
                        fontSize: 12,
                      }}
                    >
                      查看 DSL
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selectedSession && (
        <DiffPanel
          session={selectedSession}
          onClose={() => setSelectedSession(null)}
          onBaseline={handleBaseline}
        />
      )}
    </div>
  )
}
