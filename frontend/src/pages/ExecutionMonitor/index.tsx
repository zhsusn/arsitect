import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router'
import { useExecutionMonitorStore } from '@/stores/executionMonitorStore'
import { useProjectSSE } from '@/hooks/useProjectSSE'
import { api } from '@/services/api'
import ExecutionLogStream from './components/ExecutionLogStream'
import RetryButton from './components/RetryButton'
import StopButton from './components/StopButton'
import type { SkillExecution } from '@/types/skill-execution'

const LS_PROJECT_KEY = 'arsitect:lastProjectId'

const statusTabs = [
  { key: 'ALL', label: '全部' },
  { key: 'RUNNING', label: '运行中' },
  { key: 'SUCCESS', label: '成功' },
  { key: 'FAILED', label: '失败' },
]

const statusColors: Record<string, { bg: string; color: string }> = {
  RUNNING: { bg: '#eff6ff', color: '#2563eb' },
  SUCCESS: { bg: '#ecfdf5', color: '#065f46' },
  FAILED: { bg: '#fef2f2', color: '#dc2626' },
  PENDING: { bg: '#f3f4f6', color: '#6b7280' },
  STOPPED: { bg: '#fef3c7', color: '#92400e' },
}

function getStatusStyle(status: string) {
  return statusColors[status] || statusColors.PENDING
}

function truncateId(id: string) {
  return id.length > 12 ? `${id.slice(0, 6)}...${id.slice(-4)}` : id
}

function getLastProjectId(): string | undefined {
  try {
    const value = localStorage.getItem(LS_PROJECT_KEY)
    return value || undefined
  } catch {
    return undefined
  }
}

export default function ExecutionMonitor() {
  const { executionId } = useParams<{ executionId: string }>()
  const {
    executions,
    isLoading,
    error,
    filterStatus,
    fetchExecutions,
    setFilterStatus,
    stopExecution,
  } = useExecutionMonitorStore()

  const [retryingId, setRetryingId] = useState<string | null>(null)
  const [projectId, setProjectId] = useState<string | undefined>(getLastProjectId)

  useEffect(() => {
    if (projectId) {
      fetchExecutions(projectId)
    } else {
      fetchExecutions()
    }
  }, [fetchExecutions, projectId])

  useProjectSSE(projectId, () => {
    if (projectId) {
      fetchExecutions(projectId)
    } else {
      fetchExecutions()
    }
  })

  useEffect(() => {
    const handleStorage = () => setProjectId(getLastProjectId())
    window.addEventListener('storage', handleStorage)
    return () => window.removeEventListener('storage', handleStorage)
  }, [])

  const filteredExecutions =
    filterStatus === 'ALL'
      ? executions
      : executions.filter((e) => e.overall_status === filterStatus)

  const handleRetry = async (exec: SkillExecution) => {
    setRetryingId(exec.execution_id)
    try {
      await api.post(`/v1/executions/${exec.execution_id}/retry`)
      if (projectId) {
        fetchExecutions(projectId)
      } else {
        fetchExecutions()
      }
    } catch (err: unknown) {
      console.error('重试失败', err instanceof Error ? err.message : err)
    } finally {
      setRetryingId(null)
    }
  }

  const handleStop = async (executionId: string) => {
    await stopExecution(executionId)
  }

  if (executionId) {
    // 详情模式：展示日志流
    return (
      <div style={{ padding: 24 }}>
        <div style={{ marginBottom: 16 }}>
          <Link to="/executions" style={{ textDecoration: 'none', color: '#2563eb', fontSize: 14 }}>
            ← 返回执行列表
          </Link>
        </div>
        <h2 style={{ margin: '0 0 16px' }}>执行详情: {truncateId(executionId)}</h2>
        <ExecutionLogStream executionId={executionId} />
      </div>
    )
  }

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ margin: '0 0 16px' }}>执行监控</h1>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        {statusTabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setFilterStatus(tab.key)}
            style={{
              padding: '6px 14px',
              fontSize: 13,
              borderRadius: 6,
              border: '1px solid #e5e7eb',
              background: filterStatus === tab.key ? '#1f2937' : '#fff',
              color: filterStatus === tab.key ? '#fff' : '#374151',
              cursor: 'pointer',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {isLoading && executions.length === 0 && (
        <div style={{ padding: 40, textAlign: 'center' }}>加载中...</div>
      )}

      {error && executions.length === 0 && (
        <div style={{ padding: 40, textAlign: 'center', color: '#ef4444' }}>错误: {error}</div>
      )}

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ background: '#f9fafb', textAlign: 'left' }}>
              <th style={{ padding: '10px 12px', borderBottom: '1px solid #e5e7eb' }}>执行 ID</th>
              <th style={{ padding: '10px 12px', borderBottom: '1px solid #e5e7eb' }}>Skill 名称</th>
              <th style={{ padding: '10px 12px', borderBottom: '1px solid #e5e7eb' }}>Stage</th>
              <th style={{ padding: '10px 12px', borderBottom: '1px solid #e5e7eb' }}>当前阶段</th>
              <th style={{ padding: '10px 12px', borderBottom: '1px solid #e5e7eb' }}>整体状态</th>
              <th style={{ padding: '10px 12px', borderBottom: '1px solid #e5e7eb' }}>重试次数</th>
              <th style={{ padding: '10px 12px', borderBottom: '1px solid #e5e7eb' }}>开始时间</th>
              <th style={{ padding: '10px 12px', borderBottom: '1px solid #e5e7eb' }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {filteredExecutions.length === 0 ? (
              <tr>
                <td
                  colSpan={8}
                  style={{
                    padding: 40,
                    textAlign: 'center',
                    color: '#6b7280',
                    borderBottom: '1px solid #e5e7eb',
                  }}
                >
                  暂无执行记录
                </td>
              </tr>
            ) : (
              filteredExecutions.map((exec) => {
                const style = getStatusStyle(exec.overall_status)
                return (
                  <tr key={exec.execution_id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                    <td style={{ padding: '10px 12px' }}>
                      <Link
                        to={`/executions/${exec.execution_id}`}
                        style={{ textDecoration: 'none', color: '#2563eb', fontFamily: 'monospace' }}
                      >
                        {truncateId(exec.execution_id)}
                      </Link>
                    </td>
                    <td style={{ padding: '10px 12px' }}>{exec.skill_name}</td>
                    <td style={{ padding: '10px 12px' }}>{exec.stage_id}</td>
                    <td style={{ padding: '10px 12px' }}>{exec.current_phase}</td>
                    <td style={{ padding: '10px 12px' }}>
                      <span
                        style={{
                          display: 'inline-block',
                          padding: '2px 8px',
                          borderRadius: 4,
                          fontSize: 12,
                          fontWeight: 600,
                          background: style.bg,
                          color: style.color,
                        }}
                      >
                        {exec.overall_status}
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                      {exec.retry_count}
                    </td>
                    <td style={{ padding: '10px 12px', whiteSpace: 'nowrap', color: '#6b7280' }}>
                      {exec.started_at ? new Date(exec.started_at).toLocaleString() : '-'}
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <Link
                          to={`/executions/${exec.execution_id}`}
                          style={{
                            fontSize: 12,
                            color: '#2563eb',
                            textDecoration: 'none',
                          }}
                        >
                          查看日志
                        </Link>
                        <RetryButton
                          executionId={exec.execution_id}
                          retryCount={exec.retry_count}
                          maxRetries={3}
                          status={exec.overall_status}
                          onRetry={() => handleRetry(exec)}
                        />
                        <StopButton
                          executionId={exec.execution_id}
                          status={exec.overall_status}
                          onStop={handleStop}
                        />
                        {retryingId === exec.execution_id && (
                          <span style={{ fontSize: 12, color: '#6b7280' }}>重试中...</span>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
