import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  ReactFlow,
  Background,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import {
  type ProjectStage,
  updateStageSkippable,
  reorderStages,
  mergeStages,
  splitStage,
} from '../../../services/template'

type ViewMode = 'sequence' | 'list' | 'dependency'

interface StageDefinitionPanelProps {
  projectId: string
  stages: ProjectStage[]
  skills: { skill_id: string; skill_name: string }[]
  readonly?: boolean
  onStagesChange?: (stages: ProjectStage[]) => void
}

export default function StageDefinitionPanel({
  projectId,
  stages: initialStages,
  skills,
  readonly = false,
  onStagesChange,
}: StageDefinitionPanelProps) {
  const [view, setView] = useState<ViewMode>('sequence')
  const [stages, setStages] = useState<ProjectStage[]>(initialStages)
  const [draggingId, setDraggingId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [mergeSource, setMergeSource] = useState<string | null>(null)

  useEffect(() => {
    setStages(initialStages)
  }, [initialStages])

  const skillMap = useMemo(() => {
    const map: Record<string, string> = {}
    for (const s of skills) map[s.skill_id] = s.skill_name
    return map
  }, [skills])

  const sortedStages = useMemo(
    () => [...stages].sort((a, b) => a.order_index - b.order_index),
    [stages],
  )

  const handleToggleSkippable = useCallback(
    async (stageId: string, value: boolean) => {
      if (readonly) return
      setLoading(true)
      try {
        const updated = await updateStageSkippable(projectId, stageId, value)
        setStages((prev) =>
          prev.map((s) => (s.project_stage_id === stageId ? updated : s)),
        )
        onStagesChange?.(
          stages.map((s) => (s.project_stage_id === stageId ? updated : s)),
        )
      } catch {
        // ignore
      } finally {
        setLoading(false)
      }
    },
    [projectId, readonly, stages, onStagesChange],
  )

  const handleDragStart = (stageId: string) => {
    if (readonly) return
    setDraggingId(stageId)
  }

  const handleDrop = async (targetId: string) => {
    if (!draggingId || draggingId === targetId || readonly) {
      setDraggingId(null)
      return
    }
    const fromIdx = sortedStages.findIndex((s) => s.project_stage_id === draggingId)
    const toIdx = sortedStages.findIndex((s) => s.project_stage_id === targetId)
    if (fromIdx < 0 || toIdx < 0) return

    const reordered = [...sortedStages]
    const [moved] = reordered.splice(fromIdx, 1)
    reordered.splice(toIdx, 0, moved)

    const orders: [string, number][] = reordered.map((s, i) => [s.project_stage_id, i + 1])
    setLoading(true)
    try {
      const updated = await reorderStages(projectId, orders)
      setStages(updated)
      onStagesChange?.(updated)
    } catch {
      // ignore
    } finally {
      setLoading(false)
      setDraggingId(null)
    }
  }

  const handleMerge = async (targetId: string) => {
    if (!mergeSource || mergeSource === targetId) {
      setMergeSource(null)
      return
    }
    setLoading(true)
    try {
      const updated = await mergeStages(projectId, mergeSource, targetId)
      setStages(updated)
      onStagesChange?.(updated)
    } catch {
      // ignore
    } finally {
      setLoading(false)
      setMergeSource(null)
    }
  }

  const handleSplit = async (stageId: string) => {
    setLoading(true)
    try {
      const updated = await splitStage(projectId, stageId)
      setStages(updated)
      onStagesChange?.(updated)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  // Dependency graph (React Flow)
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])

  useEffect(() => {
    if (view !== 'dependency') return
    const ns: Node[] = sortedStages.map((s, i) => ({
      id: s.project_stage_id,
      type: 'default',
      position: { x: i * 220 + 20, y: 100 },
      data: {
        label: (
          <div className="text-xs">
            <div className="font-semibold">{s.stage_id}</div>
            <div className="text-gray-500">{skillMap[s.primary_skill_id || ''] || '-'}</div>
            {s.skippable && <span className="text-[10px] text-amber-600">可跳过</span>}
          </div>
        ),
      },
      style: {
        width: 180,
        borderColor: s.is_frozen ? '#f59e0b' : s.skippable ? '#d97706' : '#3b82f6',
        background: s.is_frozen ? '#fef3c7' : '#fff',
      },
    }))
    const es: Edge[] = sortedStages.slice(0, -1).map((s, i) => ({
      id: `e-${s.project_stage_id}-${sortedStages[i + 1].project_stage_id}`,
      source: s.project_stage_id,
      target: sortedStages[i + 1].project_stage_id,
      type: 'smoothstep',
      animated: true,
    }))
    setNodes(ns)
    setEdges(es)
  }, [view, sortedStages, skillMap, setNodes, setEdges])

  return (
    <div className="bg-white border border-gray-200 rounded-xl flex flex-col h-full max-h-[80vh]">
      {/* Toolbar */}
      <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-0.5">
          {([
            { key: 'sequence', label: '序列视图' },
            { key: 'list', label: '列表视图' },
            { key: 'dependency', label: '依赖视图' },
          ] as const).map((v) => (
            <button
              key={v.key}
              onClick={() => setView(v.key)}
              className={[
                'px-3 py-1.5 text-sm rounded-md transition-colors',
                view === v.key
                  ? 'bg-white text-gray-900 shadow-sm font-medium'
                  : 'text-gray-600 hover:text-gray-900',
              ].join(' ')}
            >
              {v.label}
            </button>
          ))}
        </div>
        {readonly && (
          <span className="text-xs text-amber-700 bg-amber-50 border border-amber-200 px-2 py-1 rounded-md">
            只读（模板已冻结）
          </span>
        )}
        {loading && <span className="text-xs text-gray-500">处理中...</span>}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        {view === 'sequence' && (
          <div className="flex gap-3 overflow-x-auto pb-2">
            {sortedStages.map((stage, idx) => (
              <div key={stage.project_stage_id} className="flex items-center gap-3">
                <div
                  draggable={!readonly && !stage.is_frozen}
                  onDragStart={() => handleDragStart(stage.project_stage_id)}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={() => handleDrop(stage.project_stage_id)}
                  className={[
                    'relative w-48 border rounded-lg p-3 transition-shadow',
                    stage.is_frozen
                      ? 'border-amber-300 bg-amber-50'
                      : 'border-blue-200 bg-blue-50 hover:shadow-md',
                    draggingId === stage.project_stage_id ? 'opacity-50' : 'opacity-100',
                    !readonly && !stage.is_frozen ? 'cursor-move' : 'cursor-default',
                  ].join(' ')}
                >
                  <div className="text-xs font-semibold text-gray-900 mb-1">
                    #{stage.order_index} {stage.stage_id}
                  </div>
                  <div className="text-[11px] text-gray-500 mb-2">
                    主Skill: {skillMap[stage.primary_skill_id || ''] || '未分配'}
                  </div>
                  <div className="flex items-center justify-between">
                    <label className="flex items-center gap-1.5 text-xs text-gray-700 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={stage.skippable}
                        disabled={readonly || stage.is_frozen}
                        onChange={(e) =>
                          handleToggleSkippable(stage.project_stage_id, e.target.checked)
                        }
                        className="w-3.5 h-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      可跳过
                    </label>
                    {!readonly && !stage.is_frozen && (
                      <div className="flex gap-1">
                        <button
                          title="合并"
                          onClick={() =>
                            mergeSource
                              ? handleMerge(stage.project_stage_id)
                              : setMergeSource(stage.project_stage_id)
                          }
                          className={[
                            'text-[10px] px-1.5 py-0.5 rounded border',
                            mergeSource === stage.project_stage_id
                              ? 'bg-purple-100 border-purple-300 text-purple-700'
                              : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50',
                          ].join(' ')}
                        >
                          {mergeSource === stage.project_stage_id ? '取消' : '合并'}
                        </button>
                        <button
                          title="拆分"
                          onClick={() => handleSplit(stage.project_stage_id)}
                          className="text-[10px] px-1.5 py-0.5 rounded border bg-white border-gray-200 text-gray-600 hover:bg-gray-50"
                        >
                          拆分
                        </button>
                      </div>
                    )}
                  </div>
                  {stage.is_frozen && (
                    <div className="absolute -top-2 -right-2 bg-amber-500 text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full">
                      冻结
                    </div>
                  )}
                </div>
                {idx < sortedStages.length - 1 && (
                  <div className="text-gray-300 text-lg">→</div>
                )}
              </div>
            ))}
          </div>
        )}

        {view === 'list' && (
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 border-b border-gray-200">
                <th className="px-3 py-2">顺序</th>
                <th className="px-3 py-2">Stage</th>
                <th className="px-3 py-2">主Skill</th>
                <th className="px-3 py-2">辅助Skills</th>
                <th className="px-3 py-2">可跳过</th>
                <th className="px-3 py-2">状态</th>
                <th className="px-3 py-2">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sortedStages.map((stage) => (
                <tr
                  key={stage.project_stage_id}
                  draggable={!readonly && !stage.is_frozen}
                  onDragStart={() => handleDragStart(stage.project_stage_id)}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={() => handleDrop(stage.project_stage_id)}
                  className={[
                    'hover:bg-gray-50',
                    draggingId === stage.project_stage_id ? 'opacity-50' : 'opacity-100',
                    !readonly && !stage.is_frozen ? 'cursor-move' : 'cursor-default',
                  ].join(' ')}
                >
                  <td className="px-3 py-2 text-gray-500">{stage.order_index}</td>
                  <td className="px-3 py-2 font-medium text-gray-900">{stage.stage_id}</td>
                  <td className="px-3 py-2 text-gray-600">
                    {skillMap[stage.primary_skill_id || ''] || '-'}
                  </td>
                  <td className="px-3 py-2 text-gray-500">-</td>
                  <td className="px-3 py-2">
                    <input
                      type="checkbox"
                      checked={stage.skippable}
                      disabled={readonly || stage.is_frozen}
                      onChange={(e) =>
                        handleToggleSkippable(stage.project_stage_id, e.target.checked)
                      }
                      className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                  </td>
                  <td className="px-3 py-2">
                    {stage.is_frozen ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">
                        冻结
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                        {stage.status}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    {!readonly && !stage.is_frozen && (
                      <div className="flex gap-1">
                        <button
                          onClick={() =>
                            mergeSource
                              ? handleMerge(stage.project_stage_id)
                              : setMergeSource(stage.project_stage_id)
                          }
                          className={[
                            'text-xs px-2 py-1 rounded border',
                            mergeSource === stage.project_stage_id
                              ? 'bg-purple-100 border-purple-300 text-purple-700'
                              : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50',
                          ].join(' ')}
                        >
                          {mergeSource === stage.project_stage_id ? '取消合并' : '合并'}
                        </button>
                        <button
                          onClick={() => handleSplit(stage.project_stage_id)}
                          className="text-xs px-2 py-1 rounded border bg-white border-gray-200 text-gray-600 hover:bg-gray-50"
                        >
                          拆分
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {view === 'dependency' && (
          <div style={{ height: 400 }}>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              fitView
              nodesDraggable={!readonly}
              nodesConnectable={false}
            >
              <Background />
            </ReactFlow>
          </div>
        )}
      </div>
    </div>
  )
}
