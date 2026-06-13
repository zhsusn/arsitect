import { useEffect, useState } from 'react'
import { fetchTemplateDetail, type TemplateStage } from '../../../services/template'

interface TemplatePreviewModalProps {
  templateId: string
  templateName: string
  skillMap: Record<string, string>
  onClose: () => void
  onUse: () => void
}

export default function TemplatePreviewModal({
  templateId,
  templateName,
  skillMap,
  onClose,
  onUse,
}: TemplatePreviewModalProps) {
  const [stages, setStages] = useState<TemplateStage[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    fetchTemplateDetail(templateId)
      .then((detail) => {
        const seen = new Set<string>()
        const unique = detail.stages.filter((s) => {
          const key = `${s.order_index}|${s.stage_name}`
          if (seen.has(key)) return false
          seen.add(key)
          return true
        })
        setStages(unique)
      })
      .catch(() => setStages([]))
      .finally(() => setLoading(false))
  }, [templateId])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[85vh] flex flex-col">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">模板预览</h2>
            <p className="text-sm text-gray-500 mt-0.5">{templateName}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          {loading ? (
            <div className="text-sm text-gray-500 text-center py-8">加载中...</div>
          ) : stages.length === 0 ? (
            <div className="text-sm text-gray-500 text-center py-8">暂无阶段数据</div>
          ) : (
            <div className="space-y-3">
              {stages.map((stage) => (
                <div
                  key={stage.stage_id}
                  className="border border-gray-200 rounded-lg p-3 flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-7 h-7 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold">
                      {stage.order_index}
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {stage.stage_name}
                      </div>
                      <div className="text-xs text-gray-500 mt-0.5">
                        主Skill: {skillMap[stage.primary_skill_id || ''] || '未分配'}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {stage.skippable && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 border border-gray-200">
                        可跳过
                      </span>
                    )}
                    <span className="text-xs text-gray-400">
                      {(stage.auxiliary_skill_ids || []).length} 辅助
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            关闭
          </button>
          <button
            onClick={onUse}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
          >
            使用此模板
          </button>
        </div>
      </div>
    </div>
  )
}
