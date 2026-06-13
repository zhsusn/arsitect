import { useEffect } from 'react'
import { Link } from 'react-router'
import { useGateCenterStore } from '@/stores/gateCenterStore'
import HistoryTable from './HistoryTable'

function convertToCSV(rows: Record<string, unknown>[]): string {
  if (rows.length === 0) return ''
  const headers = Object.keys(rows[0])
  const lines = [
    headers.join(','),
    ...rows.map((row) =>
      headers
        .map((h) => {
          const val = row[h]
          const str = val == null ? '' : String(val)
          if (str.includes(',') || str.includes('"') || str.includes('\n')) {
            return `"${str.replace(/"/g, '""')}"`
          }
          return str
        })
        .join(','),
    ),
  ]
  return lines.join('\n')
}

export default function GateHistoryPage() {
  const { history, historyLoading, historyError, historyFilters, fetchHistory, setHistoryFilter } =
    useGateCenterStore()

  useEffect(() => {
    fetchHistory()
  }, [fetchHistory, historyFilters])

  const handleExport = () => {
    const data = history.map((h) => ({
      gate_id: h.gate_id,
      gate_type: h.gate_type,
      project_id: h.project_id,
      status: h.status,
      decision_type: h.decision_type,
      decision_by: h.decision_by,
      decision_at: h.decision_at,
      reason: h.reason,
    }))
    const csv = convertToCSV(data)
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `gate-history-${new Date().toISOString().slice(0, 10)}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold">审批历史记录</h2>
        <Link
          to="/gates"
          className="px-3 py-1.5 rounded-md border border-gray-300 text-sm hover:bg-gray-50"
        >
          返回审批中心
        </Link>
      </div>

      <div className="flex flex-wrap gap-3 mb-4">
        <input
          type="text"
          placeholder="项目 ID"
          value={historyFilters.project_id ?? ''}
          onChange={(e) => setHistoryFilter('project_id', e.target.value || undefined)}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
        />
        <input
          type="text"
          placeholder="Gate 类型"
          value={historyFilters.gate_type ?? ''}
          onChange={(e) => setHistoryFilter('gate_type', e.target.value || undefined)}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
        />
        <input
          type="text"
          placeholder="结论类型"
          value={historyFilters.decision_type ?? ''}
          onChange={(e) => setHistoryFilter('decision_type', e.target.value || undefined)}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
        />
        <input
          type="date"
          value={historyFilters.start_date ?? ''}
          onChange={(e) => setHistoryFilter('start_date', e.target.value || undefined)}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
        />
        <input
          type="date"
          value={historyFilters.end_date ?? ''}
          onChange={(e) => setHistoryFilter('end_date', e.target.value || undefined)}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
        />
        <button
          onClick={handleExport}
          className="ml-auto px-4 py-1.5 rounded-md bg-gray-800 text-white text-sm hover:bg-gray-900"
        >
          导出 CSV
        </button>
      </div>

      {historyLoading && <div className="text-gray-600">加载中...</div>}
      {historyError && <div className="text-red-600 mb-2">{historyError}</div>}
      <HistoryTable records={history} />
    </div>
  )
}
