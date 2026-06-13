import { useSkillRegistryStore } from '../../../stores/skillRegistryStore'

interface ChangeLogBarProps {
  expanded: boolean
  onToggle: () => void
}

const OPERATION_LABELS: Record<string, string> = {
  ADD_NODE: '添加节点',
  DELETE_NODE: '删除节点',
  ADD_EDGE: '添加连线',
  DELETE_EDGE: '删除连线',
}

export function ChangeLogBar({ expanded, onToggle }: ChangeLogBarProps) {
  const { changeLogs, undoDAG, redoDAG, fetchChangeLogs } = useSkillRegistryStore()

  return (
    <div
      className={`
        bg-white border-t border-gray-200 transition-all duration-300 flex flex-col
        ${expanded ? 'h-[200px]' : 'h-10'}
      `}
    >
      {/* Header bar */}
      <div className="flex items-center justify-between px-4 h-10 shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={onToggle}
            className="flex items-center gap-1.5 text-sm font-medium text-gray-700 hover:text-gray-900"
          >
            <svg
              className={`w-4 h-4 text-gray-400 transition-transform ${expanded ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
            变更日志
            <span className="text-xs text-gray-400 font-normal">({changeLogs.length})</span>
          </button>

          <div className="flex gap-1 ml-2">
            <button
              onClick={() => {
                undoDAG()
                fetchChangeLogs()
              }}
              title="撤销 (Ctrl+Z)"
              className="p-1 rounded hover:bg-gray-100 text-gray-500 hover:text-gray-700 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
              </svg>
            </button>
            <button
              onClick={() => {
                redoDAG()
                fetchChangeLogs()
              }}
              title="重做 (Ctrl+Y)"
              className="p-1 rounded hover:bg-gray-100 text-gray-500 hover:text-gray-700 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 10h-10a8 8 0 00-8 8v2M21 10l-6 6m6-6l-6-6" />
              </svg>
            </button>
          </div>
        </div>

        <button
          onClick={fetchChangeLogs}
          className="p-1 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600"
          title="刷新"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="flex-1 overflow-auto px-4 pb-2">
          {changeLogs.length === 0 ? (
            <div className="text-center text-sm text-gray-400 py-6">暂无操作记录</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-500 border-b border-gray-100">
                  <th className="py-2 pr-4 font-medium">操作类型</th>
                  <th className="py-2 pr-4 font-medium">目标对象</th>
                  <th className="py-2 pr-4 font-medium">时间</th>
                </tr>
              </thead>
              <tbody>
                {changeLogs.map((log) => (
                  <tr key={log.log_id} className="border-b border-gray-50 hover:bg-gray-50/50">
                    <td className="py-2 pr-4">
                      <span
                        className={`
                          inline-block px-2 py-0.5 rounded text-xs font-medium
                          ${log.operation_type.includes('ADD')
                            ? 'bg-green-50 text-green-700'
                            : 'bg-red-50 text-red-700'
                          }
                        `}
                      >
                        {OPERATION_LABELS[log.operation_type] || log.operation_type}
                      </span>
                    </td>
                    <td className="py-2 pr-4 text-gray-700 font-mono text-xs">
                      {log.target_id.slice(0, 12)}...
                    </td>
                    <td className="py-2 pr-4 text-gray-500 text-xs">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}
