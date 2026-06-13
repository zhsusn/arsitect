import { useEffect, useState } from 'react'
import { fetchDeviationLogs, type DeviationLog } from '../../../services/template'

interface DeviationLogDrawerProps {
  projectId: string
  onClose: () => void
}

export default function DeviationLogDrawer({ projectId, onClose }: DeviationLogDrawerProps) {
  const [logs, setLogs] = useState<DeviationLog[]>([])
  const [loading, setLoading] = useState(false)
  const [expandedId, setExpandedId] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    fetchDeviationLogs(projectId)
      .then((data) => setLogs(data))
      .catch(() => setLogs([]))
      .finally(() => setLoading(false))
  }, [projectId])

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/20 z-40"
        onClick={onClose}
      />
      {/* Drawer */}
      <div className="fixed right-0 top-0 bottom-0 w-full max-w-md bg-white shadow-2xl z-50 flex flex-col">
        <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">决策日志</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          >
            ×
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <div className="text-sm text-gray-500 text-center py-8">加载中...</div>
          ) : logs.length === 0 ? (
            <div className="text-sm text-gray-500 text-center py-8">暂无决策记录</div>
          ) : (
            <div className="space-y-3">
              {logs.map((log) => {
                const isExpanded = expandedId === log.deviation_id
                let details: Record<string, unknown> | null = null
                try {
                  if (log.details_json) {
                    details = JSON.parse(log.details_json) as Record<string, unknown>
                  }
                } catch {
                  details = null
                }
                return (
                  <div
                    key={log.deviation_id}
                    className="border border-gray-200 rounded-lg overflow-hidden"
                  >
                    <button
                      onClick={() => setExpandedId(isExpanded ? null : log.deviation_id)}
                      className="w-full px-4 py-3 text-left bg-gray-50 hover:bg-gray-100 transition-colors flex items-start justify-between gap-3"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span
                            className={[
                              'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                              log.decision_type === 'deviation'
                                ? 'bg-red-100 text-red-800'
                                : log.decision_type === '回归标准'
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-gray-100 text-gray-800',
                            ].join(' ')}
                          >
                            {log.decision_type}
                          </span>
                          <span className="text-xs text-gray-400">
                            {log.created_at
                              ? new Date(log.created_at).toLocaleString('zh-CN')
                              : '-'}
                          </span>
                        </div>
                        <div className="text-sm text-gray-700 truncate">
                          {log.reason || '无原因说明'}
                        </div>
                      </div>
                      <span className="text-gray-400 text-lg leading-none mt-0.5">
                        {isExpanded ? '−' : '+'}
                      </span>
                    </button>

                    {isExpanded && details && (
                      <div className="px-4 py-3 bg-white text-sm border-t border-gray-100 space-y-2">
                        {'deviation_items' in details && Array.isArray(details.deviation_items) && (
                          <div>
                            <div className="text-xs font-medium text-gray-500 mb-1">偏离项</div>
                            <ul className="space-y-1">
                              {(details.deviation_items as Array<Record<string, unknown>>).map(
                                (item, idx) => (
                                  <li
                                    key={idx}
                                    className={[
                                      'text-xs px-2 py-1 rounded border',
                                      item.change_type === '删除'
                                        ? 'bg-red-50 border-red-100 text-red-700'
                                        : item.change_type === '新增'
                                          ? 'bg-green-50 border-green-100 text-green-700'
                                          : 'bg-amber-50 border-amber-100 text-amber-700',
                                    ].join(' ')}
                                  >
                                    [{String(item.change_type)}] {String(item.stage_name)}
                                  </li>
                                ),
                              )}
                            </ul>
                          </div>
                        )}
                        {'risk_acknowledged' in details && (
                          <div className="text-xs text-gray-500">
                            风险确认: {(details.risk_acknowledged as boolean) ? '是' : '否'}
                          </div>
                        )}
                        {log.operator_id && (
                          <div className="text-xs text-gray-500">
                            操作人: {log.operator_id}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </>
  )
}
