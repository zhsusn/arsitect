import { useEffect, useState } from 'react'
import { useStageDetailStore } from '../../../stores/stageDetailStore'
import { api } from '../../../services/api'
import type { StageGate } from '../../../types/stage-detail'

const STATUS_STYLES: Record<string, { bg: string; text: string; label: string; dot: string }> = {
  pending: {
    bg: 'bg-yellow-50 border-yellow-200',
    text: 'text-yellow-700',
    label: '待审',
    dot: 'bg-yellow-400',
  },
  passed: {
    bg: 'bg-green-50 border-green-200',
    text: 'text-green-700',
    label: '已通过',
    dot: 'bg-green-500',
  },
  rejected: {
    bg: 'bg-red-50 border-red-200',
    text: 'text-red-700',
    label: '已驳回',
    dot: 'bg-red-500',
  },
  bypassed: {
    bg: 'bg-orange-50 border-orange-200',
    text: 'text-orange-700',
    label: '已旁路',
    dot: 'bg-orange-500',
  },
}

export default function GateLinkTab() {
  const projectId = useStageDetailStore((s) => s.projectId)
  const [gates, setGates] = useState<StageGate[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!projectId) return
    let cancelled = false
    setLoading(true)
    setError(null)

    api
      .get<{ data: StageGate[] }>(`/v1/gates?project_id=${projectId}`)
      .then((res) => {
        if (!cancelled) setGates(res.data.data)
      })
      .catch((err) => {
        if (!cancelled) setError(err?.response?.data?.detail || '加载 Gate 列表失败')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [projectId])

  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 2 }).map((_, i) => (
          <div key={i} className="animate-pulse rounded-lg border border-gray-200 p-4">
            <div className="mb-2 h-4 w-1/4 rounded bg-gray-200" />
            <div className="h-3 w-1/2 rounded bg-gray-200" />
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

  if (gates.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-gray-400">
        暂无 Gate 记录
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {gates.map((gate) => {
        const style = STATUS_STYLES[gate.status] || STATUS_STYLES.pending
        const isPending = gate.status === 'pending'
        return (
          <div
            key={gate.decision_id}
            className={`rounded-lg border p-4 ${style.bg}`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className={`inline-block h-2.5 w-2.5 rounded-full ${style.dot}`} />
                <span className="text-sm font-semibold text-gray-800">
                  Gate {gate.gate_type}
                </span>
              </div>
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${style.text}`}>
                {style.label}
              </span>
            </div>

            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-600">
              {gate.confidence && (
                <span>置信度: {gate.confidence}</span>
              )}
              {gate.decision_by && (
                <span>审批人: {gate.decision_by}</span>
              )}
              {gate.decision_at && (
                <span>
                  审批时间: {new Date(gate.decision_at).toLocaleString()}
                </span>
              )}
              {gate.duration_sec !== null && (
                <span>耗时: {gate.duration_sec}s</span>
              )}
            </div>

            {gate.reason && (
              <div className="mt-2 text-xs text-gray-600">
                原因: {gate.reason}
              </div>
            )}

            {isPending && (
              <div className="mt-3">
                <a
                  href={`/gates/${gate.decision_id}`}
                  className="inline-flex items-center rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700"
                >
                  前往审批
                </a>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
