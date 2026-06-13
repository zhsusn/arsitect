import { useEffect } from 'react'
import type { PathDecision } from '../../../services/complexity'

interface DecisionPanelProps {
  decisions: PathDecision[]
  loading: boolean
  onRefresh: () => void
  onClose: () => void
}

export default function DecisionPanel({
  decisions,
  loading,
  onRefresh,
  onClose,
}: DecisionPanelProps) {
  useEffect(() => {
    onRefresh()
  }, [onRefresh])

  const typeLabel = (type: string) => {
    if (type === 'downgrade') return '路径降级'
    if (type === 'path_select') return '路径选择'
    return '规模评估'
  }

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-2xl z-40 flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <h3 className="font-semibold text-gray-800">决策日志</h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 text-xl leading-none"
        >
          ×
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        {loading && (
          <div className="text-sm text-gray-500 text-center py-8">加载中...</div>
        )}
        {!loading && decisions.length === 0 && (
          <div className="text-sm text-gray-400 text-center py-8">暂无决策记录</div>
        )}
        <div className="space-y-3">
          {decisions.map((d) => (
            <details key={d.decision_id} className="group border border-gray-200 rounded-md">
              <summary className="flex items-center justify-between cursor-pointer p-3 list-none">
                <div>
                  <div className="text-sm font-medium text-gray-800">
                    {typeLabel(d.decision_type)}
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    {d.created_at
                      ? new Date(d.created_at).toLocaleString('zh-CN')
                      : '-'}
                  </div>
                </div>
                <span className="text-xs text-gray-400 group-open:rotate-180 transition-transform">
                  ▼
                </span>
              </summary>
              <div className="px-3 pb-3 text-sm text-gray-600 space-y-1">
                {d.from_path && (
                  <div>
                    <span className="text-gray-400">原路径：</span>
                    {d.from_path}
                  </div>
                )}
                <div>
                  <span className="text-gray-400">目标路径：</span>
                  {d.to_path}
                </div>
                {d.reason && (
                  <div>
                    <span className="text-gray-400">原因：</span>
                    {d.reason}
                  </div>
                )}
              </div>
            </details>
          ))}
        </div>
      </div>
    </div>
  )
}
