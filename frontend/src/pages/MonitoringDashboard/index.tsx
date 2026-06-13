import { useEffect, useState } from 'react'
import {
  fetchMonitoringOverview,
  fetchProjectStats,
  fetchOperationLogs,
  type MonitoringOverview,
  type ProjectStats,
  type OperationLog,
} from '../../services/monitoring'

export default function MonitoringDashboard() {
  const [overview, setOverview] = useState<MonitoringOverview | null>(null)
  const [projectId, setProjectId] = useState('')
  const [stats, setStats] = useState<ProjectStats | null>(null)
  const [logs, setLogs] = useState<OperationLog[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    fetchMonitoringOverview()
      .then(setOverview)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const loadProjectStats = async () => {
    if (!projectId.trim()) return
    setLoading(true)
    try {
      const [s, l] = await Promise.all([
        fetchProjectStats(projectId),
        fetchOperationLogs(projectId, 20),
      ])
      setStats(s)
      setLogs(l)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }

  if (loading && !overview) return <div style={{ padding: 24 }}>加载中...</div>
  if (error) return <div style={{ padding: 24, color: '#ef4444' }}>错误: {error}</div>

  return (
    <div style={{ maxWidth: 960 }}>
      <h1 style={{ marginBottom: 16 }}>监控看板</h1>

      {overview && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, marginBottom: 24 }}>
          <StatCard label="项目总数" value={overview.total_projects} />
          <StatCard label="活跃项目" value={overview.active_projects} />
          <StatCard label="风险项目" value={overview.risk_projects} />
          <StatCard label="待审批 Gate" value={overview.pending_gates} />
        </div>
      )}

      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        <input
          type="text"
          placeholder="输入项目ID查看详情..."
          value={projectId}
          onChange={(e) => setProjectId(e.target.value)}
          style={{ flex: 1, padding: 8 }}
        />
        <button onClick={loadProjectStats} disabled={!projectId.trim()}>
          查询
        </button>
      </div>

      {stats && (
        <div style={{ marginBottom: 24 }}>
          <h3>项目统计</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12 }}>
            <StatCard label="阶段数" value={stats.stage_count} />
            <StatCard label="执行数" value={stats.execution_count} />
            <StatCard label="Gate 数" value={stats.gate_count} />
          </div>
        </div>
      )}

      {logs.length > 0 && (
        <div>
          <h3>操作日志 (最近20条)</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
            <thead>
              <tr style={{ background: '#f3f4f6' }}>
                <th style={{ padding: 8, textAlign: 'left' }}>操作</th>
                <th style={{ padding: 8, textAlign: 'left' }}>目标</th>
                <th style={{ padding: 8, textAlign: 'left' }}>时间</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.log_id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                  <td style={{ padding: 8 }}>{log.action}</td>
                  <td style={{ padding: 8 }}>{log.target_type}:{log.target_id?.slice(0, 8) ?? '-'}</td>
                  <td style={{ padding: 8 }}>{log.created_at ? new Date(log.created_at).toLocaleString() : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ padding: 16, border: '1px solid #e5e7eb', borderRadius: 8, background: '#fff' }}>
      <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 700 }}>{value}</div>
    </div>
  )
}
