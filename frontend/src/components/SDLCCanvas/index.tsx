import { useCallback, useEffect, useRef, useState } from 'react'
import {
  ReactFlow,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type ReactFlowInstance,
  type Viewport as RFViewport,
  type NodeTypes,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import { useCanvasStore } from '../../stores/canvasStore'
import { useProjectSSE } from '../../services/sse'
import type { CanvasState } from '../../services/canvas'
import StageNode from './components/StageNode'
import GateNode from './components/GateNode'
import SkillNode from '../../pages/Canvas/components/SkillNode'
import ZoomControls from '../../pages/Canvas/components/ZoomControls'

const NODE_TYPES: NodeTypes = {
  stage: StageNode,
  gate: GateNode,
  skill: SkillNode,
}

interface SDLCCanvasProps {
  projectId: string
  onNodeContextMenu?: (event: React.MouseEvent, node: Node) => void
  onNodeClick?: (event: React.MouseEvent, node: Node) => void
  onStageExecute?: (stageId: string, stageLabel: string) => void
}

export default function SDLCCanvas({ projectId, onNodeContextMenu, onNodeClick, onStageExecute }: SDLCCanvasProps) {
  const { loadCanvas, saveCanvas, loading, saving } = useCanvasStore()
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const [viewport, setViewport] = useState<RFViewport>({ x: 0, y: 0, zoom: 1 })
  const flowRef = useRef<ReactFlowInstance<Node, Edge> | null>(null)
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const applyCanvasData = useCallback(
    (data: CanvasState) => {
      // Build gate status map: stageId -> gate decisionStatus
      const gateMap = new Map<string, string>()
      for (const edge of data.edges || []) {
        const src = data.nodes?.find((n) => n.id === edge.source)
        const tgt = data.nodes?.find((n) => n.id === edge.target)
        if (src?.type === 'gate' && tgt?.type === 'stage') {
          gateMap.set(tgt.id, (src.data?.decisionStatus as string) || 'pending')
        }
        if (tgt?.type === 'gate' && src?.type === 'stage') {
          gateMap.set(src.id, (tgt.data?.decisionStatus as string) || 'pending')
        }
      }

      const ns: Node[] = (data.nodes || []).map((n) => ({
        id: n.id,
        type: n.type || 'stage',
        position: n.position,
        data: {
          ...(n.data || {}),
          gateStatus: n.type === 'stage' ? gateMap.get(n.id) : (n.data?.gateStatus as string),
          onExecute:
            n.type === 'stage' && onStageExecute
              ? () => onStageExecute(n.id, (n.data?.label as string) || n.id)
              : undefined,
        },
        style: n.style,
        width: n.width,
        height: n.height,
      }))
      const es: Edge[] = (data.edges || []).map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        type: e.type,
        animated: e.animated,
        style: e.style,
        label: e.label,
      }))
      setNodes(ns)
      setEdges(es)
      if (data.viewport) {
        setViewport({
          x: data.viewport.x,
          y: data.viewport.y,
          zoom: data.viewport.zoom,
        })
        flowRef.current?.setViewport(data.viewport)
      }
    },
    [onStageExecute, setNodes, setEdges],
  )

  // Load canvas state on mount
  useEffect(() => {
    let mounted = true
    loadCanvas(projectId).then((data) => {
      if (!mounted || !data) return
      applyCanvasData(data)
    })
    return () => {
      mounted = false
    }
  }, [projectId, loadCanvas, applyCanvasData])

  // Real-time canvas updates via SSE
  useProjectSSE(projectId, {
    'stage.status_changed': () => loadCanvas(projectId).then((data) => data && applyCanvasData(data)),
    'stage.rollback_complete': () => loadCanvas(projectId).then((data) => data && applyCanvasData(data)),
    'skill.execution_updated': () => loadCanvas(projectId).then((data) => data && applyCanvasData(data)),
  })

  // Debounced save (3 seconds)
  const triggerSave = useCallback(() => {
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current)
    }
    saveTimerRef.current = setTimeout(() => {
      const cleanNodes = nodes.map((n) => ({
        id: n.id,
        type: n.type,
        position: n.position,
        data: n.data,
        style: n.style as Record<string, unknown> | undefined,
        width: n.width,
        height: n.height,
      }))
      const cleanEdges = edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        type: e.type,
        animated: e.animated,
        style: e.style as Record<string, unknown> | undefined,
        label: String(e.label ?? ''),
      }))
      saveCanvas(projectId, {
        nodes: cleanNodes,
        edges: cleanEdges,
        viewport: { x: viewport.x, y: viewport.y, zoom: viewport.zoom },
      })
    }, 3000)
  }, [nodes, edges, viewport, projectId, saveCanvas])

  const handleNodesChange = useCallback(
    (changes: Parameters<typeof onNodesChange>[0]) => {
      onNodesChange(changes)
      triggerSave()
    },
    [onNodesChange, triggerSave],
  )

  const handleEdgesChange = useCallback(
    (changes: Parameters<typeof onEdgesChange>[0]) => {
      onEdgesChange(changes)
      triggerSave()
    },
    [onEdgesChange, triggerSave],
  )

  const handleMoveEnd = useCallback(
    (_event: unknown, v: RFViewport) => {
      setViewport(v)
      triggerSave()
    },
    [triggerSave],
  )

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (saveTimerRef.current) {
        clearTimeout(saveTimerRef.current)
      }
    }
  }, [])

  return (
    <div style={{ height: '100%', minHeight: 600, position: 'relative' }}>
      {loading && (
        <div
          style={{
            position: 'absolute',
            top: 12,
            left: 12,
            zIndex: 10,
            padding: '4px 8px',
            backgroundColor: '#f3f4f6',
            borderRadius: 4,
            fontSize: 12,
            color: '#6b7280',
          }}
        >
          加载画布中...
        </div>
      )}
      {saving && (
        <div
          style={{
            position: 'absolute',
            top: 12,
            right: 12,
            zIndex: 10,
            padding: '4px 8px',
            backgroundColor: '#dbeafe',
            borderRadius: 4,
            fontSize: 12,
            color: '#1e40af',
          }}
        >
          保存中...
        </div>
      )}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={handleNodesChange}
        onEdgesChange={handleEdgesChange}
        onMoveEnd={handleMoveEnd}
        onNodeContextMenu={onNodeContextMenu}
        onNodeClick={onNodeClick}
        onInit={(instance: ReactFlowInstance<Node, Edge>) => {
          flowRef.current = instance
        }}
        nodeTypes={NODE_TYPES}
        fitView
      >
        <Background />
        <MiniMap
          nodeStrokeWidth={3}
          zoomable
          pannable
        />
        <div style={{ position: 'absolute', bottom: 16, left: 16, zIndex: 10 }}>
          <ZoomControls />
        </div>
      </ReactFlow>
    </div>
  )
}
