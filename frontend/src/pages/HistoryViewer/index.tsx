import { useState } from 'react'
import {
  fetchTimeline,
  fetchReworkAnalysis,
  type TimelineEvent,
  type ReworkAnalysisItem,
} from '../../services/history'

export default function HistoryViewer() {
  const [projectId, setProjectId] = useState('')
  const [timeline, setTimeline] = useState<TimelineEvent[]>([])
  const [rework, setRework] = useState<ReworkAnalysisItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadHistory = async () => {
    if (!projectId.trim()) return
    setLoading(true)
    setError(null)
    try {
      const [t, r] = await Promise.all([
        fetchTimeline(projectId),
        fetchReworkAnalysis(projectId),
      ])
      setTimeline(t)
      setRework(r)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 960 }}>
      <h1 style={{ marginBottom: 16 }}>历史回溯</h1>

      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        <input
          type="text"
          placeholder="输入项目ID..."
          value={projectId}
          onChange={(e) => setProjectId(e.target.value)}
          style={{ flex: 1, padding: 8 }}
        />
        <button onClick={loadHistory} disabled={!projectId.trim() || loading}>
          {loading ? '加载中...' : '查询'}
        </button>
      </div>

      {error && <div style={{ color: '#ef4444', marginBottom: 16 }}>错误: {error}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24 }}>
        <div>
          <h3>时间线</h3>
          {timeline.length === 0 ? (
            <div style={{ color: '#6b7280', padding: 24, textAlign: 'center' }}>暂无数据</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {timeline.map((event) => (
                <div
                  key={event.event_id}
                  style={{
                    padding: 12,
                    borderLeft: '3px solid #3b82f6',
                    background: '#f9fafb',
                    borderRadius: 4,
                  }}
                >
                  <div style={{ fontWeight: 600, marginBottom: 4 }}>{event.event_type}</div>
                  <div style={{ fontSize: 13, color: '#4b5563' }}>{event.description}</div>
                  <div style={{ fontSize: 12, color: '#9ca3af', marginTop: 4 }}>
                    {new Date(event.created_at).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <h3>返工分析</h3>
          {rework.length === 0 ? (
            <div style={{ color: '#6b7280', padding: 24, textAlign: 'center' }}>暂无返工记录</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {rework.map((item, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: 12,
                    background: '#fef2f2',
                    borderRadius: 4,
                    display: 'flex',
                    justifyContent: 'space-between',
                  }}
                >
                  <span style={{ fontSize: 13 }}>{item.reason ?? '未知原因'}</span>
                  <span style={{ fontWeight: 700, color: '#dc2626' }}>{item.count}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
