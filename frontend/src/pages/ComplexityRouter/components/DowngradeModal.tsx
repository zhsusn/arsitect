import { useState } from 'react'

interface DowngradeModalProps {
  fromPath: string
  toPath: string
  skippedStages: string[]
  onConfirm: (reason: string) => void
  onCancel: () => void
}

export default function DowngradeModal({
  fromPath,
  toPath,
  skippedStages,
  onConfirm,
  onCancel,
}: DowngradeModalProps) {
  const [reason, setReason] = useState('')

  return (
    <div
      className="fixed inset-0 bg-black/40 flex items-center justify-center z-50"
      onClick={(e) => {
        if (e.target === e.currentTarget) onCancel()
      }}
    >
      <div className="bg-white rounded-lg shadow-xl min-w-[420px] max-w-[560px] p-6">
        <h2 className="text-lg font-semibold mb-2">路径降级确认</h2>
        <p className="text-sm text-gray-500 mb-4">
          即将从 <strong>{fromPath}</strong> 降级至 <strong>{toPath}</strong>
          ，以下阶段将被跳过：
        </p>

        <div className="bg-gray-50 rounded-md p-3 mb-4 max-h-40 overflow-y-auto">
          {skippedStages.length === 0 ? (
            <span className="text-sm text-gray-400">无额外跳过阶段</span>
          ) : (
            <ul className="space-y-1">
              {skippedStages.map((stage) => (
                <li key={stage} className="text-sm text-gray-600 line-through">
                  {stage}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="mb-5">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            降级原因 <span className="text-red-500">*</span>
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            placeholder="请说明降级原因（必填）"
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm border border-gray-300 rounded-md bg-white hover:bg-gray-50"
          >
            返回重选
          </button>
          <button
            disabled={!reason.trim()}
            onClick={() => onConfirm(reason.trim())}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            确认降级
          </button>
        </div>
      </div>
    </div>
  )
}
