import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router'
import { useStageDetailStore } from '../../../stores/stageDetailStore'
import { api } from '../../../services/api'
import {
  fetchStageExecutionStatus,
  stopExecution,
  type StageExecutionStatus,
} from '../../../services/stage'
import type { StageExecution } from '../../../types/stage-detail'

interface PhaseInfo {
  name: string
  key: string
  status: 'pending' | 'running' | 'completed' | 'failed'
}

function derivePhases(execution: StageExecution | null): PhaseInfo[] {
  const phases: PhaseInfo[] = [
    { name: 'Prep', key: 'PREP', status: 'pending' },
    { name: 'Exec', key: 'EXEC', status: 'pending' },
    { name: 'Post', key: 'POST', status: 'pending' },
  ]
  if (!execution) return phases

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

const STATUS_LABEL: Record<string, string> = {
  NOT_STARTED: '未开始',
  RUNNING: '运行中',
  SUCCESS: '成功',
  FAILED: '失败',
  STOPPED: '已停止',
  UNKNOWN: '未知',
}

export default function PocketFlowStatusTab() {
  const stageId = useStageDetailStore((s) => s.stageId)
  const projectId = useStageDetailStore((s) => s.projectId)
  const [executions, setExecutions] = useState<StageExecution[]>([])
  const [aggregate, setAggregate] = useState<StageExecutionStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [retryingId, setRetryingId] = useState<string | null>(null)
  const [stoppingId, setStoppingId] = useState<string | null>(null)

  const loadExecutions = useCallback(async () => {
    if (!stageId) return
    try {
      const res = await api.get<StageExecution[]>(`/v1/stages/${stageId}/executions`)
      setExecutions(res.data)
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        '加载执行记录失败'
      setError(msg)
    }
  }, [stageId])

  const loadAggregate = useCallback(async () => {
    if (!stageId) return
    try {
      const status = await fetchStageExecutionStatus(stageId)
      setAggregate(status)
      setError(null)
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        '加载执行状态失败'
      setError(msg)
    }
  }, [stageId])

  useEffect(() => {
    if (!stageId) return
    let cancelled = false
    setLoading(true)
    setError(null)

    Promise.all([loadExecutions(), loadAggregate()]).finally(() => {
      if (!cancelled) setLoading(false)
    })

    return () => {
      cancelled = true
    }
  }, [stageId, loadExecutions, loadAggregate])

  // Poll aggregate status while any execution is still running
  useEffect(() => {
    if (!stageId) return
    const shouldPoll =
      aggregate?.running_execution_ids.length ||
      executions.some((e) => e.overall_status === 'RUNNING' || e.overall_status === 'NOT_STARTED')
    if (!shouldPoll) return

    const timer = setInterval(() => {
      void loadAggregate()
      void loadExecutions()
    }, 3000)
    return () => clearInterval(timer)
  }, [stageId, aggregate?.running_execution_ids.length, executions, loadAggregate, loadExecutions])

  const handleRetry = async (executionId: string) => {
    setRetryingId(executionId)
    try {
      await api.post(`/v1/executions/${executionId}/retry`)
      await loadExecutions()
      await loadAggregate()
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '重试失败'
      setError(msg)
    } finally {
      setRetryingId(null)
    }
  }

  const handleStop = async (executionId: string) => {
    setStoppingId(executionId)
    try {
      await stopExecution(executionId)
      await loadExecutions()
      await loadAggregate()
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '停止失败'
      setError(msg)
    } finally {
      setStoppingId(null)
    }
  }

  const isRunning = (status: string) => status === 'RUNNING' || status === 'NOT_STARTED'

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

  return (
    <div className="space-y-4">
      {/* Aggregate status card */}
      {aggregate && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold text-blue-900">
              阶段状态: {STATUS_LABEL[aggregate.overall_status] || aggregate.overall_status}
            </div>
            <div className="text-xs text-blue-700">
              进度 {aggregate.progress_percent}%
            </div>
          </div>
          <div className="mt-2 h-2 w-full rounded-full bg-blue-100">
            <div
              className="h-2 rounded-full bg-blue-600 transition-all"
              style={{ width: `${aggregate.progress_percent}%` }}
            />
          </div>
          {aggregate.error_summary && (
            <div className="mt-3 rounded-md bg-red-100 p-2 text-xs text-red-700">
              <span className="font-semibold">错误摘要:</span> {aggregate.error_summary}
            </div>
          )}
          {aggregate.artifact_paths.length > 0 && (
            <div className="mt-3">
              <div className="text-xs font-medium text-blue-900 mb-1">产物路径</div>
              <div className="flex flex-wrap gap-1">
                {aggregate.artifact_paths.map((path, idx) => (
                  <span
                    key={idx}
                    className="max-w-[200px] truncate rounded bg-white px-2 py-0.5 text-[10px] text-blue-700 border border-blue-100"
                    title={path}
                  >
                    {path}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {executions.length === 0 && (
        <div className="flex h-32 items-center justify-center text-sm text-gray-400">
          暂无执行记录
        </div>
      )}

      {executions.map((exec) => {
        const phases = derivePhases(exec)
        const isFailed = exec.overall_status === 'FAILED'
        const running = isRunning(exec.overall_status)
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
              <span>状态: {STATUS_LABEL[exec.overall_status] || exec.overall_status}</span>
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

            <div className="mt-3 flex flex-wrap items-center gap-2">
              {isFailed && (
                <button
                  type="button"
                  onClick={() => handleRetry(exec.execution_id)}
                  disabled={retryingId === exec.execution_id}
                  className="inline-flex items-center rounded-md bg-red-600 px-3 py-1 text-xs font-medium text-white hover:bg-red-700 disabled:opacity-50"
                >
                  {retryingId === exec.execution_id ? '重试中...' : '重试'}
                </button>
              )}
              {running && (
                <button
                  type="button"
                  onClick={() => handleStop(exec.execution_id)}
                  disabled={stoppingId === exec.execution_id}
                  className="inline-flex items-center rounded-md bg-yellow-600 px-3 py-1 text-xs font-medium text-white hover:bg-yellow-700 disabled:opacity-50"
                >
                  {stoppingId === exec.execution_id ? '停止中...' : '停止执行'}
                </button>
              )}
              {projectId && (
                <Link
                  to={`/artifacts?project_id=${projectId}`}
                  className="inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50"
                >
                  查看产物
                </Link>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
