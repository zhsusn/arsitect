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
import type { CanvasFilters, StatusFilter } from '../constants'
import type { StageProgressItem } from '../../../services/stage'

const NODE_TYPES: NodeTypes = {
  stage: StageNode,
  gate: GateNode,
  skill: SkillNode,
}

interface MergeGroupDef {
  group_id?: string
  label: string
  business_stage_keys: string[]
}

interface CanvasSwimlaneProps {
  allNodes: Node[]
  allEdges: Edge[]
  filters: CanvasFilters
  onNodeContextMenu: (event: React.MouseEvent, node: Node) => void
  onStageExecute?: (stageId: string, stageLabel: string) => void
  stages?: StageProgressItem[]
  mergeGroups?: MergeGroupDef[]
  skillNameMap?: Record<string, string>
}

interface SwimlaneDef {
  stageId: string
  label: string
  status: string
  skills: Node[]
  x: number
  width: number
  collapsed: boolean
  mergeGroupLabel?: string | null
}

const SWIMLANE_HEADER_HEIGHT = 60
const SWIMLANE_COL_WIDTH = 220
const SKILL_HEIGHT = 80
const SKILL_GAP = 20
const SWIMLANE_PADDING = 16

const BUSINESS_STAGE_LABELS: Record<string, string> = {
  brainstorm: '头脑风暴',
  charter: '项目立项',
  clarify: '概要需求',
  align: '详细需求',
  'contract-hld': '概要设计',
  'contract-dd': '详细设计',
  build: '编码实现',
  verify: '测试验证',
  release: '发布上线',
}

function runtimeStatusToFilterStatus(status: string): StatusFilter {
  switch (status) {
    case 'in_progress':
      return 'Executing'
    case 'passed':
    case 'completed':
      return 'Success'
    case 'failed':
    case 'error':
      return 'Failed'
    case 'blocked':
      return 'Blocked'
    case 'skipped':
      return 'Skipped'
    case 'executing':
      return 'Executing'
    default:
      return 'Pending'
  }
}

function resolveMergeGroupLabel(
  stage: StageProgressItem,
  mergeGroups?: MergeGroupDef[],
): string | null {
  if (stage.merge_group_label) return stage.merge_group_label
  const key = stage.business_stage_key
  if (!key || !mergeGroups) return null
  const group = mergeGroups.find((g) => g.business_stage_keys.includes(key))
  return group ? group.label : null
}

function stageLabelFromProgress(stage: StageProgressItem): string {
  if (stage.business_stage_key) {
    return BUSINESS_STAGE_LABELS[stage.business_stage_key] || stage.business_stage_key
  }
  return stage.stage_id
}

export default function CanvasSwimlane({
  allNodes,
  allEdges,
  filters,
  onNodeContextMenu,
  onStageExecute,
  stages,
  mergeGroups,
  skillNameMap,
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
    const useStageSource = stages && stages.length > 0

    let lanes: SwimlaneDef[] = []

    if (useStageSource) {
      const sorted = [...stages].sort((a, b) => a.order_index - b.order_index)

      lanes = sorted.map((stage, idx) => {
        const stageId = stage.project_stage_id
        const label = stageLabelFromProgress(stage)
        const mergeGroupLabel = resolveMergeGroupLabel(stage, mergeGroups)
        const displayStatus = stage.runtime_status || 'not_started'
        const filterStatus = runtimeStatusToFilterStatus(displayStatus)

        const isVisibleByStatus =
          filters.statuses.length === 0 || filters.statuses.includes(filterStatus)
        const isVisibleByKeyword =
          !filters.keyword.trim() ||
          label.toLowerCase().includes(filters.keyword.trim().toLowerCase())
        const isVisibleByStageFilter =
          filters.stages.length === 0 || filters.stages.includes(label)

        let skills: Node[] = []

        if (isVisibleByStatus && isVisibleByKeyword && isVisibleByStageFilter) {
          const primaryId = stage.primary_skill_id
          const primaryLabel = primaryId
            ? skillNameMap?.[primaryId] || primaryId
            : '未绑定主 Skill'

          skills = [
            {
              id: `${stageId}-primary`,
              type: 'skill',
              position: { x: 0, y: 0 },
              data: {
                label: primaryLabel,
                status: filterStatus,
                skillType: 'primary',
                stageId,
                progress: stage.progress_percent,
              },
            },
            {
              id: `${stageId}-aux-placeholder`,
              type: 'skill',
              position: { x: 0, y: 0 },
              data: {
                label: '辅助 Skill',
                status: 'Pending',
                skillType: 'auxiliary',
                stageId,
              },
            },
          ]

          if (filters.statuses.length > 0) {
            skills = skills.filter((s) =>
              filters.statuses.includes((s.data?.status as StatusFilter) || 'Pending'),
            )
          }
        }

        if (filters.onlyBlocked && filterStatus !== 'Blocked') {
          skills = []
        }

        return {
          stageId,
          label,
          status: displayStatus,
          skills,
          x: idx * SWIMLANE_COL_WIDTH,
          width: SWIMLANE_COL_WIDTH,
          collapsed: collapsedLanes.has(stageId),
          mergeGroupLabel,
        }
      })
    } else {
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
      lanes = stageNodes.map((stage, idx) => {
        const stageId = stage.id
        const stageLabel = (stage.data?.label as string) || stageId
        const stageStatus = (stage.data?.status as string) || 'Pending'
        const mergeGroupLabel = (stage.data?.mergeGroupLabel as string) || null

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
          mergeGroupLabel,
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
            progress:
              (stageNodes.find((s) => s.id === lane.stageId)?.data?.progress as number) ?? 0,
            gateStatus: gateMap.get(lane.stageId),
            onExecute: onStageExecute
              ? () => onStageExecute(lane.stageId, lane.label)
              : undefined,
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
    }

    // Stage-source positioning (reached only when useStageSource is true)
    const positionedNodes: Node[] = []

    lanes.forEach((lane) => {
      positionedNodes.push({
        id: lane.stageId,
        type: 'stage',
        position: { x: lane.x + SWIMLANE_PADDING, y: 20 },
        data: {
          label: lane.label,
          status: lane.status,
          progress: 0,
          onExecute: onStageExecute
            ? () => onStageExecute(lane.stageId, lane.label)
            : undefined,
        },
        style: {
          width: lane.width - SWIMLANE_PADDING * 2,
          zIndex: 2,
        } as Record<string, unknown>,
        width: lane.width - SWIMLANE_PADDING * 2,
        height: SWIMLANE_HEADER_HEIGHT,
      })

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
    })

    return { swimlanes: lanes, nodes: positionedNodes, edges: [] as Edge[] }
  }, [
    allNodes,
    allEdges,
    filters,
    collapsedLanes,
    onStageExecute,
    stages,
    mergeGroups,
    skillNameMap,
  ])

  const handleNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      if (node.type === 'stage') {
        toggleLane(node.id)
      }
    },
    [toggleLane],
  )

  // Compute merge group overlays and inter-group separators from lanes
  const groupOverlays = useMemo(() => {
    const groups: {
      label: string
      startIdx: number
      endIdx: number
      x: number
      width: number
    }[] = []
    let currentLabel: string | null = null
    let startIdx = 0

    swimlanes.forEach((lane, idx) => {
      const label = lane.mergeGroupLabel
      if (label && label !== currentLabel) {
        if (currentLabel) {
          const startLane = swimlanes[startIdx]
          const endLane = swimlanes[idx - 1]
          groups.push({
            label: currentLabel,
            startIdx,
            endIdx: idx - 1,
            x: startLane.x,
            width: endLane.x + endLane.width - startLane.x,
          })
        }
        currentLabel = label
        startIdx = idx
      } else if (!label && currentLabel) {
        const startLane = swimlanes[startIdx]
        const endLane = swimlanes[idx - 1]
        groups.push({
          label: currentLabel,
          startIdx,
          endIdx: idx - 1,
          x: startLane.x,
          width: endLane.x + endLane.width - startLane.x,
        })
        currentLabel = null
      }
    })

    if (currentLabel) {
      const startLane = swimlanes[startIdx]
      const endLane = swimlanes[swimlanes.length - 1]
      groups.push({
        label: currentLabel,
        startIdx,
        endIdx: swimlanes.length - 1,
        x: startLane.x,
        width: endLane.x + endLane.width - startLane.x,
      })
    }

    return groups
  }, [swimlanes])

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
        <div className="absolute bottom-4 left-4 z-10">
          <ZoomControls />
        </div>
      </ReactFlow>

      {/* Swimlane separator lines & merge group overlays */}
      <svg
        className="absolute inset-0 pointer-events-none"
        style={{ width: '100%', height: '100%' }}
      >
        {groupOverlays.map((group) => (
          <g key={`group-${group.label}-${group.startIdx}`}>
            <rect
              x={group.x + 4}
              y="4"
              width={group.width - 8}
              height="100%"
              rx="8"
              fill="none"
              stroke="#a855f7"
              strokeWidth="1.5"
              strokeDasharray="8 4"
            />
            <text
              x={group.x + group.width / 2}
              y="20"
              textAnchor="middle"
              fill="#7e22ce"
              fontSize="12"
              fontWeight="600"
            >
              {group.label}
            </text>
          </g>
        ))}
        {swimlanes.slice(0, -1).map((lane, idx) => {
          const nextLane = swimlanes[idx + 1]
          const showSeparator = lane.mergeGroupLabel !== nextLane.mergeGroupLabel
          if (!showSeparator) return null
          return (
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
          )
        })}
      </svg>

      {/* Collapse indicators */}
      <div className="absolute top-4 right-4 z-10 bg-white/90 backdrop-blur rounded-lg border border-gray-200 shadow-sm px-3 py-2">
        <div className="text-xs text-gray-500">点击 Stage 标签可折叠/展开泳道</div>
      </div>
    </div>
  )
}
