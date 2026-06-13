import { useState, useMemo } from 'react'
import type { GateDecision } from '@/services/gate'

const REASON_PRESETS = [
  { value: 'production_hotfix', label: '生产环境紧急修复' },
  { value: 'security_hotfix', label: '安全漏洞热修复' },
  { value: 'business_blocker', label: '关键业务阻塞' },
  { value: 'other', label: '其他' },
] as const

const GATE_TYPE_STAGE_MAP: Record<string, { stage_id: string; skill_id: string }> = {
  initiation: { stage_id: 'brainstorming', skill_id: 'brainstorming' },
  '1': { stage_id: 'detailed-requirements', skill_id: 'prd-generation' },
  '2': { stage_id: 'detailed-design', skill_id: 'high-level-design' },
  '2.5': { stage_id: 'detailed-design', skill_id: 'detailed-design' },
  '3': { stage_id: 'release-management', skill_id: 'release-management' },
}

interface BypassModalProps {
  gate: GateDecision
  onClose: () => void
  onSubmit: (payload: {
    stage_id: string
    skill_id: string
    triggered_by: string
    reason: string
    authorizer_token: string
    deadline_hours: number
  }) => void
}

export default function BypassModal({ gate, onClose, onSubmit }: BypassModalProps) {
  const [reasonPreset, setReasonPreset] = useState<string>(REASON_PRESETS[0].value)
  const [otherReason, setOtherReason] = useState('')
  const [authorizerToken, setAuthorizerToken] = useState('')
  const [deadlineHours, setDeadlineHours] = useState(24)
  const [detail, setDetail] = useState('')
  const [error, setError] = useState<string | null>(null)

  const applicant = useMemo(() => {
    if (typeof window === 'undefined') return 'current_user'
    return localStorage.getItem('X-User-Name')
      || localStorage.getItem('X-User-Role')
      || 'current_user'
  }, [])

  const mapped = GATE_TYPE_STAGE_MAP[gate.gate_type] || { stage_id: 'unknown', skill_id: 'unknown' }

  const handleSubmit = () => {
    setError(null)

    const presetLabel = REASON_PRESETS.find((r) => r.value === reasonPreset)?.label || ''
    const reasonText = reasonPreset === 'other' ? otherReason : presetLabel
    const fullReason = reasonPreset === 'other'
      ? `${reasonText}。${detail}`
      : `${reasonText}。${detail}`

    if (!fullReason || fullReason.length < 5 || fullReason.length > 500) {
      setError('申请理由（含详细描述）需在 5-500 字符之间')
      return
    }
    if (!authorizerToken || authorizerToken.length < 6) {
      setError('请输入有效的旁路授权 Token')
      return
    }

    onSubmit({
      stage_id: mapped.stage_id,
      skill_id: mapped.skill_id,
      triggered_by: applicant,
      reason: fullReason,
      authorizer_token: authorizerToken,
      deadline_hours: deadlineHours,
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-lg max-h-[90vh] overflow-y-auto">
        <h3 className="mb-4 text-lg font-semibold text-gray-800">申请旁路审批</h3>

        <div className="space-y-3 text-sm">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-gray-600 mb-1">Gate ID</label>
              <div className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-gray-700">
                {gate.gate_id}
              </div>
            </div>
            <div>
              <label className="block text-gray-600 mb-1">计划 ID</label>
              <div className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-gray-700">
                {gate.project_id}
              </div>
            </div>
            <div>
              <label className="block text-gray-600 mb-1">Stage ID</label>
              <div className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-gray-700">
                {mapped.stage_id}
              </div>
            </div>
            <div>
              <label className="block text-gray-600 mb-1">Skill ID</label>
              <div className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-gray-700">
                {mapped.skill_id}
              </div>
            </div>
          </div>

          <div>
            <label className="block text-gray-600 mb-1">申请人</label>
            <div className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-gray-700">
              {applicant}
            </div>
          </div>

          <div>
            <label className="block text-gray-600 mb-1">旁路原因</label>
            <div className="space-y-2">
              {REASON_PRESETS.map((r) => (
                <label key={r.value} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="reason_preset"
                    value={r.value}
                    checked={reasonPreset === r.value}
                    onChange={() => setReasonPreset(r.value)}
                    className="h-4 w-4 text-blue-600"
                  />
                  <span className="text-gray-700">{r.label}</span>
                </label>
              ))}
            </div>
            {reasonPreset === 'other' && (
              <input
                type="text"
                value={otherReason}
                onChange={(e) => setOtherReason(e.target.value)}
                placeholder="请输入其他原因"
                className="mt-2 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              />
            )}
          </div>

          <div>
            <label className="block text-gray-600 mb-1">授权 Token</label>
            <input
              type="password"
              value={authorizerToken}
              onChange={(e) => setAuthorizerToken(e.target.value)}
              placeholder="请输入旁路授权码"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-gray-600 mb-1">授权时长（小时）</label>
            <input
              type="number"
              min={1}
              max={72}
              value={deadlineHours}
              onChange={(e) => setDeadlineHours(Number(e.target.value))}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-gray-600 mb-1">详细描述（5-500 字符）</label>
            <textarea
              value={detail}
              onChange={(e) => setDetail(e.target.value)}
              rows={3}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              placeholder="请补充详细申请理由..."
            />
          </div>

          {error && <p className="text-xs text-red-600">{error}</p>}
        </div>

        <div className="mt-5 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-md border border-gray-300 text-sm hover:bg-gray-50"
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            className="px-4 py-2 rounded-md bg-orange-600 text-white text-sm hover:bg-orange-700"
          >
            提交申请
          </button>
        </div>
      </div>
    </div>
  )
}
