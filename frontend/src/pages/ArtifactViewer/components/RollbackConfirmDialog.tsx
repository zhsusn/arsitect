import { useState } from 'react'

interface RollbackConfirmDialogProps {
  versionNumber: number
  versionInfo?: { created_at?: string; operation_type?: string }
  onConfirm: (backupCurrent: boolean) => void
  onCancel: () => void
}

export default function RollbackConfirmDialog({
  versionNumber,
  versionInfo,
  onConfirm,
  onCancel,
}: RollbackConfirmDialogProps) {
  const [backupCurrent, setBackupCurrent] = useState(true)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-2xl">⚠️</span>
          <h3 className="text-lg font-semibold text-gray-800">确认回滚</h3>
        </div>

        <p className="text-sm text-gray-600 mb-4">
          您即将将文件回滚到 <span className="font-medium text-orange-600">v{versionNumber}</span>。
          此操作将覆盖当前文件内容，且无法通过撤销按钮恢复。
        </p>

        {versionInfo?.created_at && (
          <div className="mb-4 text-xs text-gray-500 bg-gray-50 p-3 rounded">
            <div>目标版本: v{versionNumber}</div>
            <div>
              创建时间: {new Date(versionInfo.created_at).toLocaleString()}
            </div>
            <div>
              操作类型: {versionInfo.operation_type === 'rollback' ? '回滚' : '快照'}
            </div>
          </div>
        )}

        <div className="flex items-center gap-2 mb-6">
          <input
            type="checkbox"
            id="backup"
            checked={backupCurrent}
            onChange={(e) => setBackupCurrent(e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <label htmlFor="backup" className="text-sm text-gray-700">
            备份当前版本（创建快照）
          </label>
        </div>

        <div className="flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm rounded border border-gray-300 hover:bg-gray-50"
          >
            取消
          </button>
          <button
            onClick={() => onConfirm(backupCurrent)}
            className="px-4 py-2 text-sm rounded bg-orange-600 text-white hover:bg-orange-700"
          >
            确认回滚
          </button>
        </div>
      </div>
    </div>
  )
}
