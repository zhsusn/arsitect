import { useEffect, useState, useCallback, useMemo } from 'react'
import { useParams } from 'react-router'
import {
  type Node,
  type Edge,
  useNodesState,
  useEdgesState,
} from '@xyflow/react'

import SDLCCanvas from '../../components/SDLCCanvas'
import StageDetailPanel from '../../components/StageDetailPanel'
import { FlowCanvas } from '../../components/FlowCanvas'
import { useExecutionPlanStore } from '../../stores/executionPlanStore'
import { useStageDetailStore } from '../../stores/stageDetailStore'
import { api } from '../../services/api'
import type { ProjectStage } from '../../types/stage-detail'
import type { ExecutionPlanItem, ExecutionPlanDetail } from '../../types/execution-plan'
import { fetchCanvasState, mergeCanvasStages } from '../../services/canvas'
import type { CanvasNode, CanvasEdge } from '../../services/canvas'

import FilterPanel from './components/FilterPanel'
import CanvasSwimlane from './components/CanvasSwimlane'
import CanvasList from './components/CanvasList'
import NodeContextMenu from './components/NodeContextMenu'
import StageMergeModal from './components/StageMergeModal'
import BatchExecutionPanel from './components/BatchExecutionPanel'
import ReleaseConfirmModal from './components/ReleaseConfirmModal'

import {
  type ViewMode,
  type CanvasFilters,
  DEFAULT_FILTERS,
  VIEW_MODE_LABELS,
} from './constants'
import type { ContextMenuAction } from './components/NodeContextMenu'

export default function CanvasPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const [viewMode, setViewMode] = useState<ViewMode>('stage')
  const [projectStages, setProjectStages] = useState<ProjectStage[]>([])
  const openPanel = useStageDetailStore((s) => s.openPanel)

  const [filters, setFilters] = useState<CanvasFilters>(DEFAULT_FILTERS)
  const [showFilters, setShowFilters] = useState(false)

  // Canvas state for swimlane / list / merge (shared)
  const [canvasNodes, setCanvasNodes] = useState<CanvasNode[]>([])
  const [canvasEdges, setCanvasEdges] = useState<CanvasEdge[]>([])
  const [canvasLoading, setCanvasLoading] = useState(false)

  // Context menu
  const [contextMenu, setContextMenu] = useState<{
    node: Node
    x: number
    y: number
  } | null>(null)

  // Merge modal
  const [mergeOpen, setMergeOpen] = useState(false)

  // Load project stages for node-click mapping
  useEffect(() => {
    if (!projectId) return
    let cancelled = false
    api
      .get<ProjectStage[]>(`/v1/templates/projects/${projectId}/stage-sequence`)
      .then((res) => {
        if (!cancelled) setProjectStages(res.data)
      })
      .catch((err) => {
        console.error('Failed to load project stages:', err)
      })
    return () => {
      cancelled = true
    }
  }, [projectId])

  // Load canvas state for non-stage views
  useEffect(() => {
    if (!projectId) return
    if (viewMode === 'stage' || viewMode === 'execution') return

    let cancelled = false
    setCanvasLoading(true)
    fetchCanvasState(projectId)
      .then((data) => {
        if (cancelled) return
        setCanvasNodes(data.nodes)
        setCanvasEdges(data.edges)
      })
      .catch((err) => console.error('Failed to load canvas state:', err))
      .finally(() => {
        if (!cancelled) setCanvasLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [projectId, viewMode])

  // Execution view state
  const {
    plan,
    isLoading: planLoading,
    error: planError,
    fetchPlan,
    executePlan,
    freezePlan,
  } = useExecutionPlanStore()

  const [, setRfNodes] = useNodesState<Node>([])
  const [rfEdges, setRfEdges] = useEdgesState<Edge>([])
  const [execLoading, setExecLoading] = useState(false)

  // Batch execution & release confirmation state
  const [batchPanelOpen, setBatchPanelOpen] = useState(false)
  const [releaseModalOpen, setReleaseModalOpen] = useState(false)
  const [releaseModalData, setReleaseModalData] = useState<{
    stageId: string
    stageName: string
    skills: Array<{ skill_name: string; skill_id: string }>
  } | null>(null)
  const [, setExecutingStages] = useState<Set<string>>(new Set())

  // Auto-load or create execution plan when switching to execution view
  useEffect(() => {
    if (viewMode !== 'execution' || !projectId) return

    let cancelled = false
    setExecLoading(true)

    const loadOrCreate = async () => {
      try {
        const listRes = await api.get<ExecutionPlanItem[]>(
          `/v1/projects/${projectId}/execution-plans`,
        )
        const plans = listRes.data

        if (plans.length > 0 && !cancelled) {
          await fetchPlan(plans[0].plan_id)
          setExecLoading(false)
          return
        }

        const createRes = await api.post<ExecutionPlanDetail>(
          `/v1/projects/${projectId}/execution-plans`,
          { template_level: null, skill_nodes: [] },
        )
        if (!cancelled) {
          await fetchPlan(createRes.data.plan_id)
        }
      } catch (err) {
        console.error('Failed to load/create execution plan:', err)
      } finally {
        if (!cancelled) setExecLoading(false)
      }
    }

    loadOrCreate()
    return () => {
      cancelled = true
    }
  }, [viewMode, projectId, fetchPlan])

  // Build React Flow nodes/edges from execution plan data
  const planNodes = useMemo(() => plan?.nodes ?? [], [plan])
  useEffect(() => {
    if (viewMode !== 'execution' || planNodes.length === 0) {
      setRfNodes((prev) => (prev.length === 0 ? prev : []))
      setRfEdges((prev) => (prev.length === 0 ? prev : []))
      return
    }

    const stageIds = Array.from(new Set(planNodes.map((n) => n.stage_id)))
    const stageIndexMap = new Map(stageIds.map((id, idx) => [id, idx]))

    const ns: Node[] = planNodes.map((node) => ({
      id: node.node_id,
      type: 'planNode',
      position: {
        x: node.order_index * 200,
        y:
          (stageIndexMap.get(node.stage_id) ?? 0) * 150 +
          (node.node_type === 'auxiliary' ? 80 : 0),
      },
      data: {
        label: node.skill_id,
        status: node.status,
        nodeType: node.node_type,
      },
    }))

    const es: Edge[] = []

    const sortedNodes = [...planNodes].sort((a, b) => a.order_index - b.order_index)
    for (let i = 0; i < sortedNodes.length - 1; i++) {
      es.push({
        id: `e-${sortedNodes[i].node_id}-${sortedNodes[i + 1].node_id}`,
        source: sortedNodes[i].node_id,
        target: sortedNodes[i + 1].node_id,
      })
    }

    const nodesByStage = new Map<string, typeof planNodes>()
    for (const node of planNodes) {
      const list = nodesByStage.get(node.stage_id) || []
      list.push(node)
      nodesByStage.set(node.stage_id, list)
    }

    for (const [, stageNodes] of nodesByStage) {
      const primaryNodes = stageNodes.filter((n) => n.node_type === 'primary')
      const auxiliaryNodes = stageNodes.filter((n) => n.node_type === 'auxiliary')

      for (const primary of primaryNodes) {
        for (const aux of auxiliaryNodes) {
          es.push({
            id: `e-pa-${primary.node_id}-${aux.node_id}`,
            source: primary.node_id,
            target: aux.node_id,
            animated: true,
          })
        }
      }
    }

    setRfNodes(ns)
    setRfEdges(es)
  }, [planNodes, viewMode, setRfNodes, setRfEdges])

  const handleExecute = useCallback(async () => {
    if (!plan) return
    await executePlan(plan.plan_id)
  }, [plan, executePlan])

  const handleFreeze = useCallback(async () => {
    if (!plan) return
    await freezePlan(plan.plan_id)
  }, [plan, freezePlan])

  const handleStageNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      if (node.type !== 'stage' || !projectId) return
      const orderIndex = parseInt(node.id.replace('stage-', ''), 10)
      if (Number.isNaN(orderIndex)) return
      const matched = projectStages.find((s) => s.order_index === orderIndex)
      if (matched) {
        openPanel(projectId, matched.project_stage_id)
      }
    },
    [projectId, projectStages, openPanel],
  )

  // Stage execution with release confirmation for高危 skills
  const handleStageExecute = useCallback(
    (stageId: string, stageLabel: string) => {
      const isReleaseStage = stageLabel.toLowerCase().includes('release') || stageLabel.toLowerCase().includes('finish')
      if (isReleaseStage) {
        setReleaseModalData({ stageId, stageName: stageLabel, skills: [{ skill_name: stageLabel, skill_id: stageId }] })
        setReleaseModalOpen(true)
        return
      }
      setExecutingStages((prev) => new Set(prev).add(stageId))
      // Trigger execution via API
      if (plan) {
        executePlan(plan.plan_id).catch(console.error)
      }
    },
    [plan, executePlan],
  )

  const handleReleaseConfirm = useCallback(() => {
    if (releaseModalData) {
      setExecutingStages((prev) => new Set(prev).add(releaseModalData.stageId))
      if (plan) {
        executePlan(plan.plan_id).catch(console.error)
      }
    }
    setReleaseModalOpen(false)
    setReleaseModalData(null)
  }, [plan, executePlan, releaseModalData])

  // Context menu
  const handleNodeContextMenu = useCallback((event: React.MouseEvent, node: Node) => {
    event.preventDefault()
    setContextMenu({
      node,
      x: event.clientX,
      y: event.clientY,
    })
  }, [])

  const closeContextMenu = useCallback(() => {
    setContextMenu(null)
  }, [])

  const handleContextAction = useCallback(
    (node: Node, action: ContextMenuAction) => {
      const nodeType = node.type || 'stage'
      switch (action) {
        case 'execute':
          if (nodeType === 'stage') {
            handleStageExecute(node.id, (node.data?.label as string) || node.id)
          } else {
            handleStageExecute(node.id, (node.data?.label as string) || node.id)
          }
          break
        case 'detail':
          if (nodeType === 'stage' && projectId) {
            const orderIndex = parseInt(node.id.replace('stage-', ''), 10)
            const matched = projectStages.find((s) => s.order_index === orderIndex)
            if (matched) openPanel(projectId, matched.project_stage_id)
          } else {
            window.open(`/artifacts?node=${node.id}`, '_blank')
          }
          break
        case 'merge':
          if (nodeType === 'stage') setMergeOpen(true)
          break
        case 'retry':
          if (plan) {
            executePlan(plan.plan_id).catch(console.error)
          }
          break
        case 'logs':
          window.open(`/executions?node=${node.id}`, '_blank')
          break
        case 'artifacts':
          window.open(`/artifacts?node=${node.id}`, '_blank')
          break
        case 'approve':
          window.open(`/gates?stage=${node.id}`, '_blank')
          break
      }
    },
    [projectId, projectStages, openPanel, plan, executePlan, handleStageExecute],
  )

  // Stage options for filter panel
  const stageOptions = useMemo(() => {
    const stages = canvasNodes
      .filter((n) => n.type === 'stage')
      .map((n) => n.data?.label || n.id)
    return stages
  }, [canvasNodes])

  // Merge handlers
  const handleMergeConfirm = useCallback(
    async (sourceId: string, targetId: string) => {
      if (!projectId) return
      try {
        const result = await mergeCanvasStages(projectId, {
          source_stage_id: sourceId,
          target_stage_id: targetId,
        })
        setCanvasNodes(result.nodes)
        setCanvasEdges(result.edges)
        setMergeOpen(false)
        alert(result.message)
      } catch (err) {
        console.error('Merge failed:', err)
        alert('合并失败: ' + (err instanceof Error ? err.message : '未知错误'))
      }
    },
    [projectId],
  )

  // List view handlers
  const handleListExecute = useCallback((node: Node) => {
    alert(`执行节点: ${node.data?.label || node.id}`)
  }, [])

  const handleListDetail = useCallback(
    (node: Node) => {
      if (node.type === 'stage' && projectId) {
        const orderIndex = parseInt(node.id.replace('stage-', ''), 10)
        const matched = projectStages.find((s) => s.order_index === orderIndex)
        if (matched) openPanel(projectId, matched.project_stage_id)
      } else {
        alert(`查看详情: ${node.data?.label || node.id}`)
      }
    },
    [projectId, projectStages, openPanel],
  )

  const handleListMerge = useCallback(() => {
    setMergeOpen(true)
  }, [])

  if (!projectId) {
    return (
      <div style={{ padding: 24 }}>
        <h2>SDLC 画布</h2>
        <p style={{ color: '#6b7280' }}>请选择一个项目以查看画布。</p>
      </div>
    )
  }

  return (
    <div style={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      {/* Header bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '12px 16px',
          borderBottom: '1px solid #e5e7eb',
          background: '#f9fafb',
          borderRadius: '8px 8px 0 0',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <h2 style={{ margin: 0, fontSize: 16 }}>项目画布 — {projectId}</h2>

          {/* View mode switcher */}
          <div
            style={{
              display: 'flex',
              background: '#e5e7eb',
              borderRadius: 6,
              padding: 2,
            }}
          >
            {(['stage', 'execution', 'swimlane', 'list'] as ViewMode[]).map((mode) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                style={{
                  padding: '4px 12px',
                  borderRadius: 4,
                  border: 'none',
                  background: viewMode === mode ? '#fff' : 'transparent',
                  color: viewMode === mode ? '#3b82f6' : '#6b7280',
                  fontSize: 13,
                  fontWeight: 500,
                  cursor: 'pointer',
                  boxShadow: viewMode === mode ? '0 1px 2px rgba(0,0,0,0.1)' : 'none',
                }}
              >
                {VIEW_MODE_LABELS[mode]}
              </button>
            ))}
          </div>

          {viewMode === 'execution' && plan && (
            <span
              style={{
                padding: '2px 8px',
                borderRadius: 4,
                fontSize: 12,
                background: plan.is_frozen ? '#fee2e2' : '#ecfdf5',
                color: plan.is_frozen ? '#991b1b' : '#065f46',
              }}
            >
              {plan.is_frozen ? '已冻结' : '未冻结'}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {/* Filter toggle */}
          <button
            onClick={() => setShowFilters((s) => !s)}
            style={{
              padding: '4px 12px',
              borderRadius: 4,
              border: '1px solid #d1d5db',
              background: showFilters ? '#eff6ff' : '#fff',
              color: showFilters ? '#3b82f6' : '#374151',
              fontSize: 13,
              cursor: 'pointer',
            }}
          >
            筛选
            {showFilters && ' ✓'}
          </button>

          <button
            onClick={() => setBatchPanelOpen(true)}
            style={{
              padding: '4px 12px',
              borderRadius: 4,
              border: '1px solid #d1d5db',
              background: '#fff',
              color: '#374151',
              fontSize: 13,
              cursor: 'pointer',
            }}
          >
            批量执行
          </button>

          {viewMode === 'execution' && (
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={handleExecute}
                disabled={!plan || planLoading || plan?.is_frozen}
                style={{
                  padding: '4px 12px',
                  borderRadius: 4,
                  border: '1px solid #d1d5db',
                  background: !plan || planLoading || plan?.is_frozen ? '#f3f4f6' : '#fff',
                  color: !plan || planLoading || plan?.is_frozen ? '#9ca3af' : '#374151',
                  fontSize: 13,
                  cursor: !plan || planLoading || plan?.is_frozen ? 'not-allowed' : 'pointer',
                }}
              >
                执行
              </button>
              <button
                onClick={handleFreeze}
                disabled={!plan || planLoading || plan?.is_frozen}
                style={{
                  padding: '4px 12px',
                  borderRadius: 4,
                  border: '1px solid #d1d5db',
                  background: !plan || planLoading || plan?.is_frozen ? '#f3f4f6' : '#fff',
                  color: !plan || planLoading || plan?.is_frozen ? '#9ca3af' : '#374151',
                  fontSize: 13,
                  cursor: !plan || planLoading || plan?.is_frozen ? 'not-allowed' : 'pointer',
                }}
              >
                冻结
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main content area */}
      <div
        style={{
          flex: 1,
          border: '1px solid #e5e7eb',
          borderTop: 'none',
          borderRadius: '0 0 8px 8px',
          overflow: 'hidden',
          display: 'flex',
        }}
      >
        {/* Filter panel */}
        {showFilters && (
          <FilterPanel
            filters={filters}
            onChange={setFilters}
            stageOptions={stageOptions}
            onClose={() => setShowFilters(false)}
          />
        )}

        {/* View rendering */}
        <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
          {viewMode === 'stage' && (
            <SDLCCanvas
              projectId={projectId}
              onNodeClick={handleStageNodeClick}
              onNodeContextMenu={handleNodeContextMenu}
              onStageExecute={handleStageExecute}
            />
          )}

          {viewMode === 'execution' && (
            <>
              {execLoading ? (
                <div style={{ padding: 40, textAlign: 'center', color: '#6b7280' }}>
                  加载执行计划中...
                </div>
              ) : planError ? (
                <div style={{ padding: 40, textAlign: 'center', color: '#ef4444' }}>
                  错误: {planError}
                </div>
              ) : plan ? (
                <FlowCanvas
                  projectId={projectId}
                  dag={{
                    nodes: plan.nodes.map((n) => ({
                      id: n.node_id,
                      label: n.skill_id,
                      phase: n.stage_id,
                      status: n.status,
                    })),
                    edges: rfEdges.map((e) => ({
                      source: e.source,
                      target: e.target,
                      label: typeof e.label === 'string' ? e.label : undefined,
                    })),
                  }}
                />
              ) : (
                <div style={{ padding: 40, textAlign: 'center', color: '#6b7280' }}>
                  暂无执行计划
                </div>
              )}
            </>
          )}

          {viewMode === 'swimlane' && (
            <>
              {canvasLoading ? (
                <div style={{ padding: 40, textAlign: 'center', color: '#6b7280' }}>
                  加载画布中...
                </div>
              ) : (
                <CanvasSwimlane
                  allNodes={canvasNodes as unknown as Node[]}
                  allEdges={canvasEdges as unknown as Edge[]}
                  filters={filters}
                  onNodeContextMenu={handleNodeContextMenu}
                />
              )}
            </>
          )}

          {viewMode === 'list' && (
            <>
              {canvasLoading ? (
                <div style={{ padding: 40, textAlign: 'center', color: '#6b7280' }}>
                  加载画布中...
                </div>
              ) : (
                <CanvasList
                  nodes={canvasNodes as unknown as Node[]}
                  edges={canvasEdges as unknown as Edge[]}
                  filters={filters}
                  onExecuteNode={handleListExecute}
                  onDetailNode={handleListDetail}
                  onMergeStage={handleListMerge}
                />
              )}
            </>
          )}
        </div>
      </div>

      {/* Context menu */}
      {contextMenu && (
        <NodeContextMenu
          node={contextMenu.node}
          x={contextMenu.x}
          y={contextMenu.y}
          onAction={handleContextAction}
          onClose={closeContextMenu}
        />
      )}

      {/* Merge modal */}
      {mergeOpen && (
        <StageMergeModal
          nodes={canvasNodes as unknown as Node[]}
          edges={canvasEdges as unknown as Edge[]}
          onConfirm={handleMergeConfirm}
          onCancel={() => setMergeOpen(false)}
        />
      )}

      {/* Batch Execution Panel */}
      <BatchExecutionPanel
        open={batchPanelOpen}
        onClose={() => setBatchPanelOpen(false)}
        stages={plan?.nodes
          ? Array.from(new Set(plan.nodes.map((n) => n.stage_id))).map((stageId) => {
              const stageNodes = plan.nodes.filter((n) => n.stage_id === stageId)
              const completed = stageNodes.filter((n) => n.status === 'Success' || n.status === 'Executed').length
              return {
                stageId,
                stageName: stageId,
                status: stageNodes.every((n) => n.status === 'Success') ? 'Success' : stageNodes.some((n) => n.status === 'Executing') ? 'Executing' : 'Pending',
                progress: stageNodes.length > 0 ? (completed / stageNodes.length) * 100 : 0,
                skills: stageNodes.map((n) => ({
                  skillId: n.node_id,
                  skillName: n.skill_id,
                  status: n.status,
                })),
              }
            })
          : []}
        onStartAll={() => {
          if (plan) executePlan(plan.plan_id).catch(console.error)
        }}
        onStopAll={() => {
          setExecutingStages(new Set())
        }}
      />

      {/* Release Confirm Modal */}
      {releaseModalOpen && releaseModalData && (
        <ReleaseConfirmModal
          open={releaseModalOpen}
          skillName={releaseModalData.stageName}
          skillType="发布类Skill"
          onCancel={() => {
            setReleaseModalOpen(false)
            setReleaseModalData(null)
          }}
          onConfirm={handleReleaseConfirm}
        />
      )}

      <StageDetailPanel />
    </div>
  )
}
