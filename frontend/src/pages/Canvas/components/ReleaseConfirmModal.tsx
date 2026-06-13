import { useState } from 'react'

interface ReleaseConfirmModalProps {
  open: boolean
  skillName: string
  skillType?: string
  impactSummary?: string
  onCancel: () => void
  onConfirm: () => void
}

export default function ReleaseConfirmModal({
  open,
  skillName,
  skillType,
  impactSummary,
  onCancel,
  onConfirm,
}: ReleaseConfirmModalProps) {
  const [checked, setChecked] = useState(false)

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ backgroundColor: 'rgba(0,0,0,0.45)' }}
      onClick={onCancel}
    >
      <div
        className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-5 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-red-50 flex items-center justify-center text-red-600 text-xl">
              ⚠
            </div>
            <h3 className="text-lg font-bold text-red-700">高危操作确认</h3>
          </div>
        </div>

        <div className="px-6 py-5 space-y-4">
          <div className="bg-gray-50 rounded-lg p-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Skill 名称</span>
              <span className="font-medium text-gray-900">{skillName}</span>
            </div>
            {skillType && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">类型</span>
                <span className="font-medium text-gray-900">{skillType}</span>
              </div>
            )}
          </div>

          <div>
            <p className="text-sm font-medium text-gray-700 mb-1">影响范围摘要</p>
            <p className="text-sm text-gray-600 leading-relaxed">
              {impactSummary ||
                `执行 ${skillName} 将会触发生产环境相关的变更流程，可能涉及分支合并、产物归档、CHANGELOG 生成等不可逆操作。请确保已完成功能验证和代码审查。`}
            </p>
          </div>

          <label className="flex items-start gap-3 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={checked}
              onChange={(e) => setChecked(e.target.checked)}
              className="mt-0.5 w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">
              我已了解此操作的影响，确认继续执行
            </span>
          </label>
        </div>

        <div className="px-6 py-4 bg-gray-50 flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            取消
          </button>
          <button
            onClick={() => {
              setChecked(false)
              onConfirm()
            }}
            disabled={!checked}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            确认执行
          </button>
        </div>
      </div>
    </div>
  )
}
