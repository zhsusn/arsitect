import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router'
import { useGateCenterStore } from '@/stores/gateCenterStore'
import SelfCheckPanel from './SelfCheckPanel'
import DecisionPanel from './DecisionPanel'
import BypassTrigger from './BypassTrigger'
import { useBypassCountdown } from '../hooks/useBypassCountdown'

function BypassCountdownDisplay({ deadlineAt }: { deadlineAt: string | null | undefined }) {
  const { text, urgency, isExpired } = useBypassCountdown(deadlineAt)

  const colorClass = {
    normal: 'text-blue-700 bg-blue-50 border-blue-200',
    warning: 'text-yellow-700 bg-yellow-50 border-yellow-200',
    danger: 'text-orange-700 bg-orange-50 border-orange-200',
    expired: 'text-red-700 bg-red-50 border-red-200',
  }[urgency]

  return (
    <div className={`inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm ${colorClass}`}>
      <span className="font-medium">旁路倒计时:</span>
      <span>{isExpired ? '已超时，需补审' : text}</span>
    </div>
  )
}

export default function GateDetailPage() {
  const { gateId } = useParams<{ gateId: string }>()
  const navigate = useNavigate()
  const {
    selectedGate,
    selectedGateBypass,
    selfCheckData,
    loading,
    error,
    fetchGateDetail,
    approveGate,
    rejectGate,
    retryGate,
  } = useGateCenterStore()

  useEffect(() => {
    if (gateId) {
      fetchGateDetail(gateId)
    }
  }, [gateId, fetchGateDetail])

  if (loading && !selectedGate) {
    return <div className="p-6 text-gray-600">加载中...</div>
  }

  if (error) {
    return <div className="p-6 text-red-600">加载失败: {error}</div>
  }

  if (!selectedGate) {
    return <div className="p-6 text-gray-600">未找到 Gate 信息</div>
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <button
        onClick={() => navigate('/gates')}
        className="mb-4 text-sm text-blue-600 hover:underline"
      >
        ← 返回列表
      </button>
      <h2 className="text-xl font-bold mb-4">Gate 详情</h2>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <div className="rounded-lg border border-gray-200 p-4 bg-white">
          <h3 className="text-lg font-semibold mb-2">基本信息</h3>
          <div className="space-y-1 text-sm text-gray-700">
            <div>Gate ID: {selectedGate.gate_id}</div>
            <div>类型: {selectedGate.gate_type}</div>
            <div>状态: {selectedGate.status}</div>
            <div>置信度: {selectedGate.confidence ?? '-'}</div>
            <div>审批人: {selectedGate.decision_by ?? '-'}</div>
            <div>
              审批时间:{' '}
              {selectedGate.decision_at ? new Date(selectedGate.decision_at).toLocaleString() : '-'}
            </div>
            <div>耗时: {selectedGate.duration_sec ? `${selectedGate.duration_sec}s` : '-'}</div>
            <div>解锁阶段: {selectedGate.unlocked_stages.join(', ') || '-'}</div>
          </div>
          {selectedGate.status === 'bypassed' && (
            <div className="mt-3">
              <BypassCountdownDisplay deadlineAt={selectedGateBypass?.deadline_at} />
            </div>
          )}
        </div>
        <SelfCheckPanel gate={selectedGate} data={selfCheckData} loading={loading} />
      </div>
      <div className="flex flex-wrap gap-3 items-start">
        <DecisionPanel
          gate={selectedGate}
          onApprove={() => gateId && approveGate(gateId)}
          onReject={(reason) => gateId && rejectGate(gateId, reason)}
          onRetry={() => gateId && retryGate(gateId)}
        />
        <BypassTrigger gateId={gateId} />
      </div>
    </div>
  )
}
