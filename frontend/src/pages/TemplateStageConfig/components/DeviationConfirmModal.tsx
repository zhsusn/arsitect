import { useMemo, useState } from 'react'
import { type DeviationItem, confirmDeviationWithReason } from '../../../services/template'

interface DeviationConfirmModalProps {
  projectId: string
  currentTemplateId: string
  targetTemplateId: string
  currentStages: {
    stage_id: string
    stage_name: string
    primary_skill_id: string | null
    auxiliary_skill_ids: string[] | null
    skippable: boolean
  }[]
  targetStages: {
    stage_id: string
    stage_name: string
    primary_skill_id: string | null
    auxiliary_skill_ids: string[] | null
    skippable: boolean
  }[]
  skillMap: Record<string, string>
  onClose: () => void
  onConfirmed: () => void
}

export default function DeviationConfirmModal({
  projectId,
  targetTemplateId,
  currentStages,
  targetStages,
  skillMap,
  onClose,
  onConfirmed,
}: DeviationConfirmModalProps) {
  const [reason, setReason] = useState('')
  const [riskAck, setRiskAck] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const deviationItems = useMemo<DeviationItem[]>(() => {
    const items: DeviationItem[] = []
    const currentMap = new Map(currentStages.map((s) => [s.stage_id, s]))
    const targetMap = new Map(targetStages.map((s) => [s.stage_id, s]))

    // Removed stages
    for (const s of currentStages) {
      if (!targetMap.has(s.stage_id)) {
        items.push({
          stage_id: s.stage_id,
          stage_name: s.stage_name,
          change_type: '删除',
          old_skill_id: s.primary_skill_id,
          old_auxiliary_skill_ids: s.auxiliary_skill_ids,
        })
      }
    }

    // Added stages
    for (const s of targetStages) {
      if (!currentMap.has(s.stage_id)) {
        items.push({
          stage_id: s.stage_id,
          stage_name: s.stage_name,
          change_type: '新增',
          new_skill_id: s.primary_skill_id,
          new_auxiliary_skill_ids: s.auxiliary_skill_ids,
        })
      }
    }

    // Modified stages
    for (const s of currentStages) {
      const t = targetMap.get(s.stage_id)
      if (!t) continue
      const skillChanged = s.primary_skill_id !== t.primary_skill_id
      const auxChanged =
        JSON.stringify((s.auxiliary_skill_ids || []).sort()) !==
        JSON.stringify((t.auxiliary_skill_ids || []).sort())
      if (skillChanged || auxChanged) {
        items.push({
          stage_id: s.stage_id,
          stage_name: s.stage_name,
          change_type: '修改',
          old_skill_id: s.primary_skill_id,
          new_skill_id: t.primary_skill_id,
          old_auxiliary_skill_ids: s.auxiliary_skill_ids,
          new_auxiliary_skill_ids: t.auxiliary_skill_ids,
        })
      }
    }

    return items
  }, [currentStages, targetStages])

  const skippedStages = useMemo(
    () => deviationItems.filter((i) => i.change_type === '删除').map((i) => i.stage_name),
    [deviationItems],
  )

  const canSubmit = reason.trim().length > 0 && (!skippedStages.length || riskAck)

  const handleConfirm = async () => {
    if (!canSubmit) return
    setSubmitting(true)
    setError(null)
    try {
      await confirmDeviationWithReason(projectId, {
        new_template_id: targetTemplateId,
        reason: reason.trim(),
        risk_acknowledged: riskAck,
        deviation_items: deviationItems,
      })
      onConfirmed()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '确认偏离失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">模板偏离确认</h2>
          <p className="text-sm text-gray-500 mt-1">
            当前项目模板与目标模板存在差异，请确认以下影响范围
          </p>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {error && (
            <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          {/* Impact preview */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-red-50 border border-red-100 rounded-lg p-3 text-center">
              <div className="text-xl font-bold text-red-700">
                {deviationItems.filter((i) => i.change_type === '删除').length}
              </div>
              <div className="text-xs text-red-600 mt-1">删除 Stage</div>
            </div>
            <div className="bg-green-50 border border-green-100 rounded-lg p-3 text-center">
              <div className="text-xl font-bold text-green-700">
                {deviationItems.filter((i) => i.change_type === '新增').length}
              </div>
              <div className="text-xs text-green-600 mt-1">新增 Stage</div>
            </div>
            <div className="bg-amber-50 border border-amber-100 rounded-lg p-3 text-center">
              <div className="text-xl font-bold text-amber-700">
                {deviationItems.filter((i) => i.change_type === '修改').length}
              </div>
              <div className="text-xs text-amber-600 mt-1">修改 Skill</div>
            </div>
          </div>

          {/* Deviation list */}
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <div className="bg-gray-50 px-4 py-2 text-sm font-medium text-gray-700 border-b border-gray-200">
              偏离项明细
            </div>
            <div className="max-h-48 overflow-y-auto">
              {deviationItems.length === 0 ? (
                <div className="px-4 py-6 text-sm text-gray-500 text-center">无偏离项</div>
              ) : (
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="text-left px-4 py-2 text-xs font-medium text-gray-500">Stage</th>
                      <th className="text-left px-4 py-2 text-xs font-medium text-gray-500">变更</th>
                      <th className="text-left px-4 py-2 text-xs font-medium text-gray-500">详情</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {deviationItems.map((item) => (
                      <tr key={`${item.stage_id}-${item.change_type}`}>
                        <td className="px-4 py-2 text-gray-900">{item.stage_name}</td>
                        <td className="px-4 py-2">
                          <span
                            className={[
                              'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                              item.change_type === '删除'
                                ? 'bg-red-100 text-red-800'
                                : item.change_type === '新增'
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-amber-100 text-amber-800',
                            ].join(' ')}
                          >
                            {item.change_type}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-gray-500 text-xs">
                          {item.change_type === '修改' ? (
                            <div>
                              {item.old_skill_id !== item.new_skill_id && (
                                <div>
                                  主Skill: {skillMap[item.old_skill_id || ''] || '-'} →{' '}
                                  {skillMap[item.new_skill_id || ''] || '-'}
                                </div>
                              )}
                            </div>
                          ) : (
                            '-'
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          {/* Reason input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              偏离原因 <span className="text-red-500">*</span>
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              placeholder="请详细说明偏离标准模板的原因..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-y"
            />
          </div>

          {/* Risk checkbox */}
          {skippedStages.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-3">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={riskAck}
                  onChange={(e) => setRiskAck(e.target.checked)}
                  className="mt-0.5 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <div className="text-sm text-yellow-800">
                  <span className="font-medium">我已了解跳过以下阶段的风险：</span>
                  <div className="mt-1 text-yellow-700">
                    {skippedStages.join('、')}
                  </div>
                </div>
              </label>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            返回标准模板
          </button>
          <button
            onClick={handleConfirm}
            disabled={!canSubmit || submitting}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? '确认中...' : '确认偏离'}
          </button>
        </div>
      </div>
    </div>
  )
}
