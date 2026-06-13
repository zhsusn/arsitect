import type { GateDecision } from '@/services/gate'

interface HistoryTableProps {
  records: GateDecision[]
}

export default function HistoryTable({ records }: HistoryTableProps) {
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full text-sm text-left">
        <thead className="bg-gray-50 text-gray-700 font-medium">
          <tr>
            <th className="px-4 py-2">Gate ID</th>
            <th className="px-4 py-2">类型</th>
            <th className="px-4 py-2">项目 ID</th>
            <th className="px-4 py-2">状态</th>
            <th className="px-4 py-2">结论</th>
            <th className="px-4 py-2">审批人</th>
            <th className="px-4 py-2">审批时间</th>
            <th className="px-4 py-2">原因</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {records.map((r) => (
            <tr key={r.decision_id} className="hover:bg-gray-50">
              <td className="px-4 py-2">{r.gate_id}</td>
              <td className="px-4 py-2">{r.gate_type}</td>
              <td className="px-4 py-2">{r.project_id}</td>
              <td className="px-4 py-2">{r.status}</td>
              <td className="px-4 py-2">{r.decision_type ?? '-'}</td>
              <td className="px-4 py-2">{r.decision_by ?? '-'}</td>
              <td className="px-4 py-2">
                {r.decision_at ? new Date(r.decision_at).toLocaleString() : '-'}
              </td>
              <td className="px-4 py-2 max-w-xs truncate" title={r.reason ?? ''}>
                {r.reason ?? '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {records.length === 0 && (
        <div className="px-4 py-6 text-center text-gray-500">暂无记录</div>
      )}
    </div>
  )
}
