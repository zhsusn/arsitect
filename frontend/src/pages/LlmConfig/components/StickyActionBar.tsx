interface StickyActionBarProps {
  onCancel: () => void
  saving?: boolean
}

export default function StickyActionBar({ onCancel, saving = false }: StickyActionBarProps) {
  return (
    <div className="sticky bottom-0 -mx-6 -mb-6 px-6 py-4 bg-white/95 backdrop-blur border-t border-gray-200 shadow-[0_-2px_8px_rgba(0,0,0,0.04)] flex items-center justify-end gap-3 mt-6">
      <button
        type="button"
        onClick={onCancel}
        disabled={saving}
        className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg disabled:opacity-50"
      >
        取消
      </button>
      <button
        type="submit"
        disabled={saving}
        className="px-4 py-2 text-sm bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 flex items-center gap-2"
      >
        {saving && (
          <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
        )}
        {saving ? '保存中...' : '保存'}
      </button>
    </div>
  )
}
