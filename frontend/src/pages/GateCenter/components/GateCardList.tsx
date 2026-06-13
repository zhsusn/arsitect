import { useNavigate } from 'react-router'
import type { GateDecision } from '@/services/gate'
import type { BypassRecord } from '@/services/bypass'
import { useBypassCountdown } from '../hooks/useBypassCountdown'

interface GateCardListProps {
  gates: GateDecision[]
  bypassMap?: Record<string, BypassRecord | null>
}

function BypassBadge({ deadlineAt }: { deadlineAt: string | null | undefined }) {
  const { text, urgency, isExpired } = useBypassCountdown(deadlineAt)

  const colorClass = {
    normal: 'bg-blue-100 text-blue-700 border-blue-300',
    warning: 'bg-yellow-100 text-yellow-700 border-yellow-300',
    danger: 'bg-orange-100 text-orange-700 border-orange-300',
    expired: 'bg-red-100 text-red-700 border-red-300',
  }[urgency]

  return (
    <span
      className={[
        'text-xs px-2 py-0.5 rounded-full border font-medium',
        colorClass,
      ].join(' ')}
    >
      {isExpired ? '已超时，需补审' : text}
    </span>
  )
}

export default function GateCardList({ gates, bypassMap }: GateCardListProps) {
  const navigate = useNavigate()

  const statusClass = (status: GateDecision['status']) => {
    const map: Record<GateDecision['status'], string> = {
      pending: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      passed: 'bg-green-100 text-green-800 border-green-300',
      rejected: 'bg-red-100 text-red-800 border-red-300',
      bypassed: 'bg-gray-100 text-gray-800 border-gray-300',
    }
    return map[status]
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {gates.map((g) => {
        const isInitiation = g.gate_type === 'initiation'
        const bypass = bypassMap?.[g.gate_id]
        return (
          <div
            key={g.gate_id}
            onClick={() => navigate(`/gates/${g.gate_id}`)}
            className={[
              'rounded-lg border p-4 cursor-pointer transition hover:shadow-md',
              isInitiation ? 'border-orange-400 ring-1 ring-orange-200' : 'border-gray-200',
            ].join(' ')}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-gray-700">
                {g.gate_type}{' '}
                <span className="text-xs text-gray-400">#{g.gate_id.slice(0, 8)}</span>
              </span>
              <div className="flex items-center gap-2">
                {g.status === 'bypassed' && (
                  <BypassBadge deadlineAt={bypass?.deadline_at} />
                )}
                <span
                  className={['text-xs px-2 py-0.5 rounded-full border', statusClass(g.status)].join(
                    ' ',
                  )}
                >
                  {g.status}
                </span>
              </div>
            </div>
            <div className="text-sm text-gray-600">
              <div>审批人: {g.decision_by ?? '-'}</div>
              <div>更新时间: {g.updated_at ? new Date(g.updated_at).toLocaleString() : '-'}</div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
