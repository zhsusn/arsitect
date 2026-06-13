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
  pollInterval?: number
}

export default function SDLCCanvas({ projectId, onNodeContextMenu, onNodeClick, onStageExecute, pollInterval = 3000 }: SDLCCanvasProps) {
  const { loadCanvas, saveCanvas, loading, saving } = useCanvasStore()
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const [viewport, setViewport] = useState<RFViewport>({ x: 0, y: 0, zoom: 1 })
  const flowRef = useRef<ReactFlowInstance<Node, Edge> | null>(null)
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const serverDataRef = useRef<Map<string, Record<string, unknown>>>(new Map())

  // Load canvas state on mount
  useEffect(() => {
    let mounted = true
    loadCanvas(projectId).then((data) => {
      if (!mounted || !data) return

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
      serverDataRef.current = new Map((data.nodes || []).map((n) => [n.id, { ...(n.data || {}) }]))
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
    })
    return () => {
      mounted = false
    }
  }, [projectId, loadCanvas, setNodes, setEdges])

  // Inject onStageExecute into stage nodes
  useEffect(() => {
    if (!onStageExecute) return
    setNodes((prev) =>
      prev.map((n) => {
        if (n.type !== 'stage') return n
        return {
          ...n,
          data: {
            ...n.data,
            onExecute: () => onStageExecute(n.id, (n.data?.label as string) || n.id),
          },
        }
      }),
    )
  }, [onStageExecute, setNodes])

  // Poll canvas state for real-time status updates
  useEffect(() => {
    if (!pollInterval || !projectId) return
    const timer = setInterval(() => {
      loadCanvas(projectId).then((data) => {
        if (!data) return
        const newMap = new Map((data.nodes || []).map((n) => [n.id, { ...(n.data || {}) }]))
        setNodes((prev) =>
          prev.map((n) => {
            const newData = newMap.get(n.id)
            const oldData = serverDataRef.current.get(n.id)
            if (
              newData &&
              (newData.status !== oldData?.status || newData.progress !== oldData?.progress || newData.gateStatus !== oldData?.gateStatus)
            ) {
              serverDataRef.current.set(n.id, newData)
              return {
                ...n,
                data: {
                  ...n.data,
                  status: newData.status,
                  progress: newData.progress,
                  gateStatus: newData.gateStatus,
                },
              }
            }
            return n
          }),
        )
      })
    }, pollInterval)
    return () => clearInterval(timer)
  }, [projectId, loadCanvas, pollInterval, setNodes])

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
