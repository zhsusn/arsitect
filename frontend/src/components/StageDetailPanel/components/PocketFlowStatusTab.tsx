import { useEffect, useState } from 'react'
import { useStageDetailStore } from '../../../stores/stageDetailStore'
import { api } from '../../../services/api'
import type { StageExecution } from '../../../types/stage-detail'

interface PhaseInfo {
  name: string
  key: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  durationSec: number | null
  artifactCount: number
}

function derivePhases(execution: StageExecution | null): PhaseInfo[] {
  if (!execution) {
    return [
      { name: 'Prep', key: 'PREP', status: 'pending', durationSec: null, artifactCount: 0 },
      { name: 'Exec', key: 'EXEC', status: 'pending', durationSec: null, artifactCount: 0 },
      { name: 'Post', key: 'POST', status: 'pending', durationSec: null, artifactCount: 0 },
    ]
  }
  const phases: PhaseInfo[] = [
    { name: 'Prep', key: 'PREP', status: 'pending', durationSec: null, artifactCount: 0 },
    { name: 'Exec', key: 'EXEC', status: 'pending', durationSec: null, artifactCount: 0 },
    { name: 'Post', key: 'POST', status: 'pending', durationSec: null, artifactCount: 0 },
  ]

  const current = execution.current_phase
  const overall = execution.overall_status

  for (let i = 0; i < phases.length; i++) {
    const p = phases[i]
    if (current === p.key) {
      p.status = overall === 'FAILED' ? 'failed' : 'running'
    } else if (
      (current === 'EXEC' && p.key === 'PREP') ||
      (current === 'POST' && (p.key === 'PREP' || p.key === 'EXEC')) ||
      (overall === 'SUCCESS' && p.key !== 'NONE')
    ) {
      p.status = 'completed'
    }
  }

  if (overall === 'FAILED' && current === 'NONE') {
    // Failure before any phase started
    phases[0].status = 'failed'
  }

  return phases
}

const PHASE_STATUS_STYLES: Record<string, { dot: string; text: string; label: string }> = {
  pending: { dot: 'bg-gray-300', text: 'text-gray-500', label: '待执行' },
  running: { dot: 'bg-amber-400', text: 'text-amber-600', label: '执行中' },
  completed: { dot: 'bg-green-500', text: 'text-green-600', label: '完成' },
  failed: { dot: 'bg-red-500', text: 'text-red-600', label: '失败' },
}

export default function PocketFlowStatusTab() {
  const stageId = useStageDetailStore((s) => s.stageId)
  const [executions, setExecutions] = useState<StageExecution[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [retryingId, setRetryingId] = useState<string | null>(null)

  useEffect(() => {
    if (!stageId) return
    let cancelled = false
    setLoading(true)
    setError(null)

    api
      .get<StageExecution[]>(`/v1/stages/${stageId}/executions`)
      .then((res) => {
        if (!cancelled) setExecutions(res.data)
      })
      .catch((err) => {
        if (!cancelled) setError(err?.response?.data?.detail || '加载执行记录失败')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [stageId])

  const handleRetry = async (executionId: string) => {
    setRetryingId(executionId)
    try {
      await api.post(`/v1/executions/${executionId}/retry`)
      // Refresh executions
      const res = await api.get<StageExecution[]>(`/v1/stages/${stageId}/executions`)
      setExecutions(res.data)
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '重试失败'
      setError(msg)
    } finally {
      setRetryingId(null)
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 2 }).map((_, i) => (
          <div key={i} className="animate-pulse rounded-lg border border-gray-200 p-4">
            <div className="mb-3 h-4 w-1/4 rounded bg-gray-200" />
            <div className="space-y-2">
              <div className="h-3 w-full rounded bg-gray-200" />
              <div className="h-3 w-2/3 rounded bg-gray-200" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        {error}
      </div>
    )
  }

  if (executions.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-gray-400">
        暂无执行记录
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {executions.map((exec) => {
        const phases = derivePhases(exec)
        const isFailed = exec.overall_status === 'FAILED'
        return (
          <div key={exec.execution_id} className="rounded-lg border border-gray-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium text-gray-800">{exec.skill_name}</div>
              <div className="text-xs text-gray-400">
                {new Date(exec.created_at).toLocaleString()}
              </div>
            </div>

            <div className="mt-3 flex items-center gap-2">
              {phases.map((phase, idx) => {
                const style = PHASE_STATUS_STYLES[phase.status]
                return (
                  <div key={phase.key} className="flex flex-1 items-center gap-2">
                    <div className="flex flex-1 flex-col items-center">
                      <div className="flex items-center gap-1.5">
                        <span className={`inline-block h-2.5 w-2.5 rounded-full ${style.dot}`} />
                        <span className={`text-xs font-medium ${style.text}`}>{phase.name}</span>
                      </div>
                      <span className={`mt-0.5 text-[10px] ${style.text}`}>{style.label}</span>
                    </div>
                    {idx < phases.length - 1 && (
                      <div className="h-px flex-1 bg-gray-200" />
                    )}
                  </div>
                )
              })}
            </div>

            <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
              <span>重试: {exec.retry_count}/3</span>
              <span>状态: {exec.overall_status}</span>
              {exec.completed_at && exec.started_at && (
                <span>
                  耗时:{' '}
                  {Math.round(
                    (new Date(exec.completed_at).getTime() -
                      new Date(exec.started_at).getTime()) /
                      1000
                  )}
                  s
                </span>
              )}
            </div>

            {isFailed && (
              <div className="mt-3 rounded-md bg-red-50 p-3">
                <div className="text-xs font-medium text-red-700">执行失败</div>
                <div className="mt-1 text-xs text-red-600">
                  阶段 {exec.current_phase} 执行异常，请检查日志后重试。
                </div>
                <button
                  type="button"
                  onClick={() => handleRetry(exec.execution_id)}
                  disabled={retryingId === exec.execution_id}
                  className="mt-2 inline-flex items-center rounded-md bg-red-600 px-3 py-1 text-xs font-medium text-white hover:bg-red-700 disabled:opacity-50"
                >
                  {retryingId === exec.execution_id ? '重试中...' : '重试'}
                </button>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
