import { useMemo, useState, useCallback } from 'react'
import type { Node, Edge } from '@xyflow/react'
import { STATUS_COLORS } from '../constants'

interface StageMergeModalProps {
  nodes: Node[]
  edges: Edge[]
  onConfirm: (sourceStageId: string, targetStageId: string) => void
  onCancel: () => void
}

export default function StageMergeModal({ nodes, edges, onConfirm, onCancel }: StageMergeModalProps) {
  const stageNodes = useMemo(
    () =>
      nodes
        .filter((n) => n.type === 'stage')
        .sort((a, b) => (a.position.x ?? 0) - (b.position.x ?? 0)),
    [nodes],
  )

  const [selectedIds, setSelectedIds] = useState<[string | null, string | null]>([null, null])

  const sourceId = selectedIds[0]
  const targetId = selectedIds[1]

  const handleSelect = useCallback(
    (id: string) => {
      setSelectedIds((prev) => {
        if (prev[0] === null) return [id, null]
        if (prev[0] === id) return [null, null]
        if (prev[1] === null) {
          // Ensure adjacency: target must be immediately after source in the sorted list
          const sourceIdx = stageNodes.findIndex((s) => s.id === prev[0])
          const targetIdx = stageNodes.findIndex((s) => s.id === id)
          if (Math.abs(sourceIdx - targetIdx) === 1) {
            return sourceIdx < targetIdx ? [prev[0], id] : [id, prev[0]]
          }
          // Not adjacent, replace source
          return [id, null]
        }
        if (prev[1] === id) return [prev[0], null]
        return [id, null]
      })
    },
    [stageNodes],
  )

  const previewNodes = useMemo(() => {
    if (!sourceId || !targetId) return null
    const source = stageNodes.find((s) => s.id === sourceId)
    const target = stageNodes.find((s) => s.id === targetId)
    if (!source || !target) return null

    const sourceLabel = (source.data?.label as string) || source.id
    const targetLabel = (target.data?.label as string) || target.id
    const mergedLabel = `${sourceLabel} + ${targetLabel}`

    // Find skills belonging to both stages
    const sourceSkills = nodes.filter(
      (n) => n.type === 'skill' && (n.data?.stageId === sourceId || n.data?.stageId === source.id),
    )
    const targetSkills = nodes.filter(
      (n) => n.type === 'skill' && (n.data?.stageId === targetId || n.data?.stageId === target.id),
    )

    // Find shared gate: edges between source and target stages, or gates connected to both
    const connectingEdges = edges.filter(
      (e) =>
        (e.source === sourceId && e.target === targetId) ||
        (e.source === targetId && e.target === sourceId) ||
        (e.source === sourceId && nodes.find((n) => n.id === e.target && n.type === 'gate')) ||
        (e.target === targetId && nodes.find((n) => n.id === e.source && n.type === 'gate')),
    )

    const gateNodes = connectingEdges
      .map((e) => nodes.find((n) => n.id === e.target || n.id === e.source))
      .filter((n): n is Node => !!n && n.type === 'gate')

    return {
      mergedLabel,
      sourceSkills,
      targetSkills,
      gateNodes,
      totalSkills: sourceSkills.length + targetSkills.length,
    }
  }, [sourceId, targetId, stageNodes, nodes, edges])

  const canConfirm = !!sourceId && !!targetId

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-xl w-[560px] max-w-[90vw] max-h-[80vh] flex flex-col">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-base font-semibold text-gray-900">合并 Stage</h3>
          <p className="text-xs text-gray-500 mt-1">选择两个相邻的 Stage 进行合并</p>
        </div>

        <div className="px-6 py-4 overflow-y-auto">
          {/* Stage selector */}
          <div className="mb-4">
            <label className="block text-xs font-medium text-gray-600 mb-2">选择 Stage（按顺序选择两个相邻阶段）</label>
            <div className="flex flex-wrap gap-2">
              {stageNodes.map((stage, idx) => {
                const label = (stage.data?.label as string) || stage.id
                const status = (stage.data?.status as string) || 'Pending'
                const colors = STATUS_COLORS[status] || STATUS_COLORS.Pending
                const isSelected = selectedIds.includes(stage.id)
                const isSource = sourceId === stage.id
                const isTarget = targetId === stage.id

                return (
                  <button
                    key={stage.id}
                    onClick={() => handleSelect(stage.id)}
                    className={`px-3 py-2 text-xs rounded-lg border transition-all ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50 text-blue-700 ring-1 ring-blue-300'
                        : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
                    }`}
                    title={`#${idx + 1}`}
                  >
                    <span
                      className="inline-block w-2 h-2 rounded-full mr-1.5"
                      style={{ backgroundColor: colors.dot }}
                    />
                    {isSource && <span className="mr-1">①</span>}
                    {isTarget && <span className="mr-1">②</span>}
                    {label}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Preview */}
          {previewNodes && (
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <h4 className="text-xs font-semibold text-gray-700 mb-3">合并预览</h4>

              <div className="mb-3">
                <span className="text-xs text-gray-500">合并后名称：</span>
                <span className="text-sm font-medium text-gray-900 ml-1">{previewNodes.mergedLabel}</span>
              </div>

              <div className="mb-3">
                <span className="text-xs text-gray-500">保留技能数：</span>
                <span className="text-sm font-medium text-gray-900 ml-1">
                  {previewNodes.totalSkills} 个
                </span>
                <div className="mt-1.5 flex flex-wrap gap-1">
                  {previewNodes.sourceSkills.map((s) => (
                    <span
                      key={s.id}
                      className="px-2 py-0.5 text-[10px] bg-white border border-gray-200 rounded text-gray-600"
                    >
                      {(s.data?.label as string) || s.id}
                    </span>
                  ))}
                  {previewNodes.targetSkills.map((s) => (
                    <span
                      key={s.id}
                      className="px-2 py-0.5 text-[10px] bg-white border border-gray-200 rounded text-gray-600"
                    >
                      {(s.data?.label as string) || s.id}
                    </span>
                  ))}
                </div>
              </div>

              {previewNodes.gateNodes.length > 0 && (
                <div>
                  <span className="text-xs text-gray-500">共享 Gate：</span>
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {previewNodes.gateNodes.map((g) => (
                      <span
                        key={g.id}
                        className="px-2 py-0.5 text-[10px] bg-white border border-gray-200 rounded-full text-gray-600"
                      >
                        {(g.data?.label as string) || g.id}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            取消
          </button>
          <button
            onClick={() => {
              if (sourceId && targetId) onConfirm(sourceId, targetId)
            }}
            disabled={!canConfirm}
            className={`px-4 py-2 text-sm rounded-lg transition-colors ${
              canConfirm
                ? 'text-white bg-blue-600 hover:bg-blue-700'
                : 'text-gray-400 bg-gray-100 cursor-not-allowed'
            }`}
          >
            确认合并
          </button>
        </div>
      </div>
    </div>
  )
}
