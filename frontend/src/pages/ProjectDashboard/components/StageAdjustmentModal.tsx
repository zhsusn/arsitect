import { useEffect, useState } from 'react'
import {
  fetchStageProgress,
  rollbackProjectStage,
  fetchPreviousStage,
  type StageProgressItem,
} from '../../../services/stage'
import { updateProjectExecutionStrategy } from '../../../services/project'

interface StageAdjustmentModalProps {
  open: boolean
  projectId: string
  currentStageId?: string
  onClose: () => void
  onAction?: () => void
}

const STRATEGIES = [
  { value: 'full_auto', label: '全自动' },
  { value: 'semi_auto', label: '半自动' },
  { value: 'full_manual', label: '全人工' },
]

export default function StageAdjustmentModal({
  open,
  projectId,
  currentStageId,
  onClose,
  onAction,
}: StageAdjustmentModalProps) {
  const [currentStage, setCurrentStage] = useState<StageProgressItem | null>(null)
  const [previousStage, setPreviousStage] = useState<StageProgressItem | null>(null)
  const [strategy, setStrategy] = useState<string>('semi_auto')
  const [reason, setReason] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [confirmRollback, setConfirmRollback] = useState(false)

  useEffect(() => {
    if (!open) {
      setConfirmRollback(false)
      return
    }
    let cancelled = false
    setLoading(true)
    setError(null)
    setConfirmRollback(false)
    fetchStageProgress(projectId)
      .then((progress) => {
        if (cancelled) return
        setStrategy(progress.execution_strategy || 'semi_auto')
        const current = progress.stages.find(
          (s) => s.project_stage_id === (currentStageId || progress.current_stage_id),
        )
        setCurrentStage(current || null)
        if (current) {
          return fetchPreviousStage(projectId, current.project_stage_id)
        }
        return null
      })
      .then((prev) => {
        if (!cancelled) setPreviousStage(prev || null)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : '加载失败')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [open, projectId, currentStageId])

  const handleRollback = async () => {
    if (!currentStage || !previousStage) return
    setLoading(true)
    setError(null)
    try {
      await rollbackProjectStage(
        projectId,
        currentStage.project_stage_id,
        previousStage.project_stage_id,
        reason || undefined,
      )
      onAction?.()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : '回退失败')
    } finally {
      setLoading(false)
    }
  }

  const handleStrategyChange = async () => {
    setLoading(true)
    setError(null)
    try {
      await updateProjectExecutionStrategy(projectId, strategy, reason || undefined)
      onAction?.()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : '修改策略失败')
    } finally {
      setLoading(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h3 className="mb-4 text-lg font-semibold text-gray-800">调整阶段</h3>
        {loading && <div className="mb-2 text-sm text-gray-500">处理中...</div>}
        {error && <div className="mb-2 text-sm text-red-600">{error}</div>}

        <div className="mb-4">
          <label className="mb-1 block text-sm text-gray-600">当前阶段</label>
          <div className="rounded border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-800">
            {currentStage
              ? currentStage.business_stage_key || currentStage.project_stage_id
              : '-'}
          </div>
        </div>

        <div className="mb-4">
          <label className="mb-1 block text-sm text-gray-600">调整原因（可选）</label>
          <input
            type="text"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="输入调整原因"
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>

        <div className="mb-4">
          <label className="mb-1 block text-sm text-gray-600">执行策略</label>
          <select
            value={strategy}
            onChange={(e) => setStrategy(e.target.value)}
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          >
            {STRATEGIES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={handleStrategyChange}
            disabled={loading}
            className="mt-2 w-full rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:bg-gray-300"
          >
            修改执行策略
          </button>
        </div>

        <div className="mb-4 border-t border-gray-200 pt-4">
          <button
            type="button"
            onClick={() => setConfirmRollback(true)}
            disabled={loading || !previousStage}
            className="w-full rounded bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:bg-gray-300"
          >
            {previousStage
              ? `回退到上一阶段 (${previousStage.business_stage_key || previousStage.project_stage_id})`
              : '无上一阶段'}
          </button>
        </div>

        <div className="flex justify-end">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="rounded border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            关闭
          </button>
        </div>

        {confirmRollback && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl">
              <h4 className="mb-2 text-base font-semibold text-gray-800">确认回退</h4>
              <p className="mb-4 text-sm text-gray-600">
                确定要回退到阶段「
                {previousStage?.business_stage_key || previousStage?.project_stage_id}
                」吗？
              </p>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setConfirmRollback(false)}
                  className="rounded border border-gray-300 bg-white px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  type="button"
                  onClick={handleRollback}
                  disabled={loading}
                  className="rounded bg-red-600 px-4 py-2 text-sm text-white hover:bg-red-700 disabled:bg-gray-300"
                >
                  确认回退
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
