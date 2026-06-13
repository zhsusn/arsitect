import { useCallback, useState } from 'react'
import type { CanvasFilters, StatusFilter, NodeTypeFilter } from '../constants'
import { STATUS_LABELS, DEFAULT_FILTERS } from '../constants'

interface FilterPanelProps {
  filters: CanvasFilters
  onChange: (filters: CanvasFilters) => void
  stageOptions: string[]
  onClose: () => void
}

const STATUS_OPTIONS: StatusFilter[] = [
  'Pending',
  'Executing',
  'Success',
  'Failed',
  'Blocked',
  'Skipped',
  'Bypass',
  'Warning',
  'Frozen',
  'Draft',
]

const TYPE_OPTIONS: { value: NodeTypeFilter; label: string }[] = [
  { value: 'stage', label: '阶段' },
  { value: 'gate', label: '闸门' },
  { value: 'skill', label: '技能' },
]

export default function FilterPanel({ filters, onChange, stageOptions, onClose }: FilterPanelProps) {
  const [local, setLocal] = useState<CanvasFilters>(filters)

  const toggleStatus = useCallback((status: StatusFilter) => {
    setLocal((prev) => {
      const set = new Set(prev.statuses)
      if (set.has(status)) set.delete(status)
      else set.add(status)
      return { ...prev, statuses: Array.from(set) }
    })
  }, [])

  const toggleStage = useCallback((stage: string) => {
    setLocal((prev) => {
      const set = new Set(prev.stages)
      if (set.has(stage)) set.delete(stage)
      else set.add(stage)
      return { ...prev, stages: Array.from(set) }
    })
  }, [])

  const toggleType = useCallback((type: NodeTypeFilter) => {
    setLocal((prev) => {
      const set = new Set(prev.types)
      if (set.has(type)) set.delete(type)
      else set.add(type)
      return { ...prev, types: Array.from(set) }
    })
  }, [])

  const apply = useCallback(() => {
    onChange(local)
  }, [local, onChange])

  const clearAll = useCallback(() => {
    setLocal(DEFAULT_FILTERS)
    onChange(DEFAULT_FILTERS)
  }, [onChange])

  const toggleOnlyBlocked = useCallback(() => {
    setLocal((prev) => {
      const next = { ...prev, onlyBlocked: !prev.onlyBlocked }
      return next
    })
  }, [])

  return (
    <div className="w-72 bg-white border-r border-gray-200 h-full flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <h3 className="text-sm font-semibold text-gray-800">筛选与搜索</h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 text-lg leading-none"
          title="关闭"
        >
          ×
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-5">
        {/* Keyword search */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1.5">关键词搜索</label>
          <input
            type="text"
            value={local.keyword}
            onChange={(e) => setLocal((prev) => ({ ...prev, keyword: e.target.value }))}
            placeholder="节点名称..."
            className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Quick blocked filter */}
        <div>
          <button
            onClick={toggleOnlyBlocked}
            className={`w-full px-3 py-2 text-sm rounded-md border transition-colors ${
              local.onlyBlocked
                ? 'bg-orange-50 border-orange-300 text-orange-700'
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            {local.onlyBlocked ? '✓ ' : ''}仅看阻塞节点
          </button>
        </div>

        {/* Status filter */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1.5">状态</label>
          <div className="flex flex-wrap gap-2">
            {STATUS_OPTIONS.map((status) => {
              const active = local.statuses.includes(status)
              return (
                <button
                  key={status}
                  onClick={() => toggleStatus(status)}
                  className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
                    active
                      ? 'bg-blue-50 border-blue-300 text-blue-700'
                      : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {active ? '✓ ' : ''}
                  {STATUS_LABELS[status]}
                </button>
              )
            })}
          </div>
        </div>

        {/* Stage filter */}
        {stageOptions.length > 0 && (
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1.5">阶段</label>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {stageOptions.map((stage) => {
                const active = local.stages.includes(stage)
                return (
                  <button
                    key={stage}
                    onClick={() => toggleStage(stage)}
                    className={`w-full text-left px-2.5 py-1.5 text-xs rounded-md border transition-colors ${
                      active
                        ? 'bg-blue-50 border-blue-300 text-blue-700'
                        : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    {active ? '✓ ' : ''}
                    {stage}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {/* Type filter */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1.5">类型</label>
          <div className="flex flex-wrap gap-2">
            {TYPE_OPTIONS.map((t) => {
              const active = local.types.includes(t.value)
              return (
                <button
                  key={t.value}
                  onClick={() => toggleType(t.value)}
                  className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
                    active
                      ? 'bg-blue-50 border-blue-300 text-blue-700'
                      : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {active ? '✓ ' : ''}
                  {t.label}
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {/* Footer actions */}
      <div className="px-4 py-3 border-t border-gray-200 flex gap-2">
        <button
          onClick={apply}
          className="flex-1 px-3 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
        >
          应用筛选
        </button>
        <button
          onClick={clearAll}
          className="flex-1 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
        >
          清除全部
        </button>
      </div>
    </div>
  )
}
