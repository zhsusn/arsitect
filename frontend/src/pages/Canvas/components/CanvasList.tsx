import { useMemo, useState, useCallback } from 'react'
import type { Node, Edge } from '@xyflow/react'
import { STATUS_COLORS, STATUS_LABELS, NODE_TYPE_LABELS } from '../constants'
import type { CanvasFilters } from '../constants'

interface CanvasListProps {
  nodes: Node[]
  edges: Edge[]
  filters: CanvasFilters
  onExecuteNode: (node: Node) => void
  onDetailNode: (node: Node) => void
  onMergeStage: (node: Node) => void
}

type SortKey = 'label' | 'type' | 'status' | 'stage' | 'progress'
type SortDir = 'asc' | 'desc'

export default function CanvasList({
  nodes,
  filters,
  onExecuteNode,
  onDetailNode,
  onMergeStage,
}: CanvasListProps) {
  const [sort, setSort] = useState<{ key: SortKey; dir: SortDir }>({
    key: 'label',
    dir: 'asc',
  })

  const handleSort = useCallback(
    (key: SortKey) => {
      setSort((prev) => ({
        key,
        dir: prev.key === key && prev.dir === 'asc' ? 'desc' : 'asc',
      }))
    },
    [],
  )

  const filteredNodes = useMemo(() => {
    let result = [...nodes]

    if (filters.onlyBlocked) {
      result = result.filter((n) => (n.data?.status as string) === 'Blocked')
    }

    if (filters.statuses.length > 0) {
      result = result.filter((n) => filters.statuses.includes((n.data?.status as never) || 'Pending'))
    }

    if (filters.types.length > 0) {
      result = result.filter((n) => filters.types.includes((n.type || 'stage') as never))
    }

    if (filters.stages.length > 0) {
      result = result.filter((n) => {
        const stageLabel =
          n.type === 'stage'
            ? (n.data?.label as string)
            : (n.data?.stageId as string)
        return filters.stages.includes(stageLabel || '')
      })
    }

    if (filters.keyword.trim()) {
      const kw = filters.keyword.trim().toLowerCase()
      result = result.filter((n) =>
        ((n.data?.label as string) || '').toLowerCase().includes(kw),
      )
    }

    result.sort((a, b) => {
      let av: string | number = ''
      let bv: string | number = ''

      switch (sort.key) {
        case 'label':
          av = (a.data?.label as string) || ''
          bv = (b.data?.label as string) || ''
          break
        case 'type':
          av = a.type || ''
          bv = b.type || ''
          break
        case 'status':
          av = (a.data?.status as string) || ''
          bv = (b.data?.status as string) || ''
          break
        case 'stage':
          av =
            a.type === 'stage'
              ? (a.data?.label as string) || ''
              : (a.data?.stageId as string) || ''
          bv =
            b.type === 'stage'
              ? (b.data?.label as string) || ''
              : (b.data?.stageId as string) || ''
          break
        case 'progress':
          av = (a.data?.progress as number) ?? 0
          bv = (b.data?.progress as number) ?? 0
          break
      }

      if (av < bv) return sort.dir === 'asc' ? -1 : 1
      if (av > bv) return sort.dir === 'asc' ? 1 : -1
      return 0
    })

    return result
  }, [nodes, filters, sort])

  const SortHeader = useCallback(
    ({ label, sortKey }: { label: string; sortKey: SortKey }) => {
      const active = sort.key === sortKey
      return (
        <th
          onClick={() => handleSort(sortKey)}
          className="px-4 py-2.5 text-left text-xs font-semibold text-gray-600 bg-gray-50 border-b border-gray-200 cursor-pointer select-none hover:bg-gray-100 transition-colors"
        >
          <span className="flex items-center gap-1">
            {label}
            {active && <span className="text-blue-500">{sort.dir === 'asc' ? '↑' : '↓'}</span>}
          </span>
        </th>
      )
    },
    [sort, handleSort],
  )

  return (
    <div className="h-full overflow-auto bg-white">
      <table className="w-full text-sm">
        <thead className="sticky top-0 z-10">
          <tr>
            <SortHeader label="节点名称" sortKey="label" />
            <SortHeader label="类型" sortKey="type" />
            <SortHeader label="状态" sortKey="status" />
            <SortHeader label="所属阶段" sortKey="stage" />
            <SortHeader label="进度" sortKey="progress" />
            <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-600 bg-gray-50 border-b border-gray-200">
              操作
            </th>
          </tr>
        </thead>
        <tbody>
          {filteredNodes.map((node) => {
            const status = (node.data?.status as string) || 'Pending'
            const colors = STATUS_COLORS[status] || STATUS_COLORS.Pending
            const label = (node.data?.label as string) || node.id
            const type = (node.type || 'stage') as string
            const progress = (node.data?.progress as number) ?? 0
            const stageLabel =
              type === 'stage'
                ? label
                : (node.data?.stageId as string) || '-'

            return (
              <tr
                key={node.id}
                className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
              >
                <td className="px-4 py-3 font-medium text-gray-800">{label}</td>
                <td className="px-4 py-3 text-gray-600">
                  {NODE_TYPE_LABELS[type] || type}
                </td>
                <td className="px-4 py-3">
                  <span
                    className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium"
                    style={{
                      backgroundColor: colors.bg,
                      color: colors.text,
                      border: `1px solid ${colors.border}`,
                    }}
                  >
                    <span
                      className="w-1.5 h-1.5 rounded-full"
                      style={{ backgroundColor: colors.dot }}
                    />
                    {STATUS_LABELS[status] || status}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-600">{stageLabel}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${Math.min(progress, 100)}%`,
                          backgroundColor: colors.border,
                        }}
                      />
                    </div>
                    <span className="text-xs text-gray-500 tabular-nums">{progress}%</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => onExecuteNode(node)}
                      className="px-2 py-1 text-xs text-blue-600 hover:bg-blue-50 rounded transition-colors"
                    >
                      执行
                    </button>
                    <button
                      onClick={() => onDetailNode(node)}
                      className="px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded transition-colors"
                    >
                      详情
                    </button>
                    {type === 'stage' && (
                      <button
                        onClick={() => onMergeStage(node)}
                        className="px-2 py-1 text-xs text-orange-600 hover:bg-orange-50 rounded transition-colors"
                      >
                        合并
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            )
          })}

          {filteredNodes.length === 0 && (
            <tr>
              <td colSpan={6} className="px-4 py-12 text-center text-gray-400 text-sm">
                无匹配节点
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
