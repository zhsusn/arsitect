interface ConflictConfirmDialogProps {
  onForceOverwrite: () => void
  onCancel: () => void
}

export default function ConflictConfirmDialog({
  onForceOverwrite,
  onCancel,
}: ConflictConfirmDialogProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-2xl">⚠️</span>
          <h3 className="text-lg font-semibold text-gray-800">保存冲突</h3>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          文件已被外部修改。如果继续保存，您的更改将覆盖外部修改。
        </p>
        <div className="flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm rounded border border-gray-300 hover:bg-gray-50"
          >
            取消保存并刷新
          </button>
          <button
            onClick={onForceOverwrite}
            className="px-4 py-2 text-sm rounded bg-red-600 text-white hover:bg-red-700"
          >
            强制覆盖
          </button>
        </div>
      </div>
    </div>
  )
}
