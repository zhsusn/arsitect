import { useState } from 'react'
import type { GateDecision } from '@/services/gate'

interface DecisionPanelProps {
  gate: GateDecision
  onApprove: () => void
  onReject: (reason: string) => void
  onRetry: () => void
}

export default function DecisionPanel({ gate, onApprove, onReject, onRetry }: DecisionPanelProps) {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [reason, setReason] = useState('')
  const [error, setError] = useState<string | null>(null)

  const handleOpenReject = () => {
    setReason('')
    setError(null)
    setIsModalOpen(true)
  }

  const handleConfirmReject = () => {
    if (reason.length < 5 || reason.length > 500) {
      setError('原因长度需在 5-500 字符之间')
      return
    }
    setIsModalOpen(false)
    onReject(reason)
  }

  const canDecide = gate.status === 'pending'
  const isLowConfidence = gate.confidence === 'low'

  return (
    <div className="rounded-lg border border-gray-200 p-4 bg-white">
      <h3 className="text-lg font-semibold mb-3">审批操作</h3>
      <div className="flex gap-3">
        <div className="relative group">
          <button
            onClick={onApprove}
            disabled={!canDecide || isLowConfidence}
            className="px-4 py-2 rounded-md bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            通过
          </button>
          {isLowConfidence && (
            <div className="absolute bottom-full left-1/2 mb-2 hidden w-max -translate-x-1/2 rounded-md bg-gray-800 px-3 py-1.5 text-xs text-white group-hover:block z-10">
              置信度低，请先提升质量或申请旁路
              <div className="absolute left-1/2 top-full -translate-x-1/2 border-4 border-transparent border-t-gray-800" />
            </div>
          )}
        </div>
        <button
          onClick={handleOpenReject}
          disabled={!canDecide}
          className="px-4 py-2 rounded-md bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          驳回
        </button>
        <button
          onClick={onRetry}
          disabled={!canDecide}
          className="px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          重试
        </button>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
            <h4 className="mb-2 text-base font-semibold">驳回原因</h4>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={4}
              className="w-full rounded-md border border-gray-300 p-2 text-sm focus:border-blue-500 focus:outline-none"
              placeholder="请输入驳回原因（5-500 字符）"
            />
            {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => setIsModalOpen(false)}
                className="px-3 py-1.5 rounded-md border border-gray-300 text-sm hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={handleConfirmReject}
                className="px-3 py-1.5 rounded-md bg-red-600 text-white text-sm hover:bg-red-700"
              >
                确认驳回
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
