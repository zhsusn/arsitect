import { useMemo, useState, useCallback } from 'react'
import {
  ReactFlow,
  Background,
  type Node,
  type Edge,
  type NodeTypes,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import StageNode from '../../../components/SDLCCanvas/components/StageNode'
import GateNode from '../../../components/SDLCCanvas/components/GateNode'
import SkillNode from './SkillNode'
import ZoomControls from './ZoomControls'
import type { CanvasFilters } from '../constants'

const NODE_TYPES: NodeTypes = {
  stage: StageNode,
  gate: GateNode,
  skill: SkillNode,
}

interface CanvasSwimlaneProps {
  allNodes: Node[]
  allEdges: Edge[]
  filters: CanvasFilters
  onNodeContextMenu: (event: React.MouseEvent, node: Node) => void
  onStageExecute?: (stageId: string, stageLabel: string) => void
}

interface SwimlaneDef {
  stageId: string
  label: string
  status: string
  skills: Node[]
  x: number
  width: number
  collapsed: boolean
}

const SWIMLANE_HEADER_HEIGHT = 60
const SWIMLANE_COL_WIDTH = 220
const SKILL_HEIGHT = 80
const SKILL_GAP = 20
const SWIMLANE_PADDING = 16

export default function CanvasSwimlane({
  allNodes,
  allEdges,
  filters,
  onNodeContextMenu,
  onStageExecute,
}: CanvasSwimlaneProps) {
  const [collapsedLanes, setCollapsedLanes] = useState<Set<string>>(new Set())

  const toggleLane = useCallback((stageId: string) => {
    setCollapsedLanes((prev) => {
      const next = new Set(prev)
      if (next.has(stageId)) next.delete(stageId)
      else next.add(stageId)
      return next
    })
  }, [])

  const { swimlanes, nodes, edges } = useMemo(() => {
    // Filter source nodes
    let sourceNodes = [...allNodes]

    if (filters.onlyBlocked) {
      sourceNodes = sourceNodes.filter(
        (n) =>
          (n.data?.status as string) === 'Blocked' ||
          n.type === 'stage' ||
          n.type === 'gate',
      )
    }

    if (filters.statuses.length > 0) {
      sourceNodes = sourceNodes.filter(
        (n) =>
          filters.statuses.includes((n.data?.status as never) || 'Pending') ||
          n.type === 'stage' ||
          n.type === 'gate',
      )
    }

    if (filters.types.length > 0) {
      sourceNodes = sourceNodes.filter((n) =>
        filters.types.includes((n.type || 'stage') as never),
      )
    }

    if (filters.keyword.trim()) {
      const kw = filters.keyword.trim().toLowerCase()
      sourceNodes = sourceNodes.filter(
        (n) =>
          ((n.data?.label as string) || '').toLowerCase().includes(kw) ||
          n.type === 'stage' ||
          n.type === 'gate',
      )
    }

    const stageNodes = sourceNodes
      .filter((n) => n.type === 'stage')
      .sort((a, b) => (a.position.x ?? 0) - (b.position.x ?? 0))

    // Build gate status map
    const gateMap = new Map<string, string>()
    for (const edge of allEdges) {
      const src = allNodes.find((n) => n.id === edge.source)
      const tgt = allNodes.find((n) => n.id === edge.target)
      if (src?.type === 'gate' && tgt?.type === 'stage') {
        gateMap.set(tgt.id, (src.data?.decisionStatus as string) || 'pending')
      }
      if (tgt?.type === 'gate' && src?.type === 'stage') {
        gateMap.set(src.id, (tgt.data?.decisionStatus as string) || 'pending')
      }
    }

    // Build swimlanes
    const lanes: SwimlaneDef[] = stageNodes.map((stage, idx) => {
      const stageId = stage.id
      const stageLabel = (stage.data?.label as string) || stageId
      const stageStatus = (stage.data?.status as string) || 'Pending'

      // Find skills belonging to this stage via stageId in data or edges
      let skills = sourceNodes.filter((n) => {
        if (n.type !== 'skill') return false
        const skillStageId = n.data?.stageId as string | undefined
        if (skillStageId) return skillStageId === stageId
        // Fallback: infer from edges (skill connected to stage)
        return allEdges.some(
          (e) =>
            (e.source === stageId && e.target === n.id) ||
            (e.target === stageId && e.source === n.id),
        )
      })

      if (filters.stages.length > 0 && !filters.stages.includes(stageLabel)) {
        skills = []
      }

      return {
        stageId,
        label: stageLabel,
        status: stageStatus,
        skills,
        x: idx * SWIMLANE_COL_WIDTH,
        width: SWIMLANE_COL_WIDTH,
        collapsed: collapsedLanes.has(stageId),
      }
    })

    // Build positioned nodes
    const positionedNodes: Node[] = []
    const positionedEdges: Edge[] = []

    lanes.forEach((lane) => {
      // Swimlane header node (acts as the stage node)
      positionedNodes.push({
        id: lane.stageId,
        type: 'stage',
        position: { x: lane.x + SWIMLANE_PADDING, y: 20 },
        data: {
          label: lane.label,
          status: lane.status,
          progress: (stageNodes.find((s) => s.id === lane.stageId)?.data?.progress as number) ?? 0,
          gateStatus: gateMap.get(lane.stageId),
          onExecute: onStageExecute ? () => onStageExecute(lane.stageId, lane.label) : undefined,
        },
        style: {
          width: lane.width - SWIMLANE_PADDING * 2,
          zIndex: 2,
        } as Record<string, unknown>,
        width: lane.width - SWIMLANE_PADDING * 2,
        height: SWIMLANE_HEADER_HEIGHT,
      })

      // Skills inside swimlane
      if (!lane.collapsed) {
        lane.skills.forEach((skill, sIdx) => {
          const y = SWIMLANE_HEADER_HEIGHT + 40 + sIdx * (SKILL_HEIGHT + SKILL_GAP)
          positionedNodes.push({
            id: skill.id,
            type: 'skill',
            position: { x: lane.x + SWIMLANE_PADDING, y },
            data: skill.data,
            style: { zIndex: 2 },
            width: lane.width - SWIMLANE_PADDING * 2,
            height: SKILL_HEIGHT,
          })
        })
      }

      // Dashed separator edge to next lane (visual)
      if (lanes.length > 1) {
        const nextLane = lanes.find((l) => l.x > lane.x)
        if (nextLane) {
          positionedEdges.push({
            id: `sep-${lane.stageId}-${nextLane.stageId}`,
            source: lane.stageId,
            target: nextLane.stageId,
            type: 'step',
            style: { stroke: '#e5e7eb', strokeDasharray: '5 5', strokeWidth: 1 },
            animated: false,
            label: '',
            hidden: true, // Use as anchor, not visible
          })
        }
      }
    })

    // Copy gate nodes and position them between lanes
    const gateNodes = sourceNodes.filter((n) => n.type === 'gate')
    gateNodes.forEach((gate) => {
      // Find connected stages
      const connectedStages = lanes.filter((lane) =>
        allEdges.some(
          (e) =>
            (e.source === lane.stageId && e.target === gate.id) ||
            (e.target === lane.stageId && e.source === gate.id),
        ),
      )

      if (connectedStages.length >= 2) {
        const left = connectedStages[0]
        const right = connectedStages[1]
        const x = left.x + left.width + (right.x - (left.x + left.width)) / 2 - 60
        const y = 30
        positionedNodes.push({
          id: gate.id,
          type: 'gate',
          position: { x, y },
          data: gate.data,
          style: { zIndex: 3 },
          width: 120,
          height: 50,
        })

        positionedEdges.push({
          id: `g-${left.stageId}-${gate.id}`,
          source: left.stageId,
          target: gate.id,
          type: 'default',
          animated: false,
        })
        positionedEdges.push({
          id: `g-${gate.id}-${right.stageId}`,
          source: gate.id,
          target: right.stageId,
          type: 'default',
          animated: false,
        })
      }
    })

    // Keep original skill-skill edges within the same lane
    allEdges.forEach((e) => {
      const sourceInPositioned = positionedNodes.find((n) => n.id === e.source)
      const targetInPositioned = positionedNodes.find((n) => n.id === e.target)
      if (
        sourceInPositioned &&
        targetInPositioned &&
        !positionedEdges.find((pe) => pe.id === e.id)
      ) {
        positionedEdges.push({
          ...e,
          type: e.type || 'default',
        })
      }
    })

    return { swimlanes: lanes, nodes: positionedNodes, edges: positionedEdges }
  }, [allNodes, allEdges, filters, collapsedLanes, onStageExecute])

  const handleNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      if (node.type === 'stage') {
        toggleLane(node.id)
      }
    },
    [toggleLane],
  )

  return (
    <div className="h-full w-full relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={NODE_TYPES}
        onNodeClick={handleNodeClick}
        onNodeContextMenu={onNodeContextMenu}
        fitView
        fitViewOptions={{ padding: 0.1 }}
        minZoom={0.2}
        maxZoom={2}
      >
        <Background gap={20} size={1} color="#f3f4f6" />
        {/* Swimlane separators rendered as background pattern would be ideal,
            but we use dashed edges between stages as separators */}
        <div className="absolute bottom-4 left-4 z-10">
          <ZoomControls />
        </div>
      </ReactFlow>

      {/* Swimlane separator lines overlay */}
      <svg
        className="absolute inset-0 pointer-events-none"
        style={{ width: '100%', height: '100%' }}
      >
        {swimlanes.slice(0, -1).map((lane) => (
          <line
            key={`line-${lane.stageId}`}
            x1={(lane.x + lane.width).toString()}
            y1="0"
            x2={(lane.x + lane.width).toString()}
            y2="100%"
            stroke="#e5e7eb"
            strokeWidth="1"
            strokeDasharray="6 4"
          />
        ))}
      </svg>

      {/* Collapse indicators */}
      <div className="absolute top-4 right-4 z-10 bg-white/90 backdrop-blur rounded-lg border border-gray-200 shadow-sm px-3 py-2">
        <div className="text-xs text-gray-500">
          点击 Stage 标签可折叠/展开泳道
        </div>
      </div>
    </div>
  )
}
