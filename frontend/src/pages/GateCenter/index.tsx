import { useEffect } from 'react'
import { Link } from 'react-router'
import { useGateCenterStore } from '@/stores/gateCenterStore'
import StatCards from './components/StatCards'
import GateCardList from './components/GateCardList'
import BypassTrigger from './components/BypassTrigger'

export default function GateCenter() {
  const { gates, stats, filters, loading, error, bypassMap, fetchGates, setFilter } = useGateCenterStore()

  useEffect(() => {
    fetchGates()
  }, [fetchGates, filters.project_id, filters.gate_type, filters.status])

  const handleStatusFilter = (status: string) => {
    setFilter('status', status || undefined)
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold">审批中心</h2>
        <div className="flex gap-2 items-center">
          <BypassTrigger />
          <Link
            to="/gates/history"
            className="px-3 py-1.5 rounded-md border border-gray-300 text-sm hover:bg-gray-50"
          >
            历史记录
          </Link>
        </div>
      </div>

      <StatCards stats={stats} activeFilter={filters.status} onFilter={handleStatusFilter} />

      <div className="flex flex-wrap gap-3 mb-4">
        <select
          value={filters.gate_type ?? ''}
          onChange={(e) => setFilter('gate_type', e.target.value || undefined)}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value="">全部类型</option>
          <option value="1">Gate 1</option>
          <option value="2">Gate 2</option>
          <option value="2.5">Gate 2.5</option>
          <option value="3">Gate 3</option>
          <option value="initiation">立项</option>
        </select>
        <select
          value={filters.status ?? ''}
          onChange={(e) => setFilter('status', e.target.value || undefined)}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value="">全部状态</option>
          <option value="pending">待审</option>
          <option value="passed">已通过</option>
          <option value="rejected">已驳回</option>
          <option value="bypassed">已旁路</option>
        </select>
      </div>

      {loading && <div className="text-gray-600">加载中...</div>}
      {error && <div className="text-red-600 mb-2">{error}</div>}
      <GateCardList gates={gates} bypassMap={bypassMap} />
    </div>
  )
}
