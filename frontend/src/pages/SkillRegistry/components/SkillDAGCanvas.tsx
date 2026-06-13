import { useEffect, useState, useCallback, useRef } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type ReactFlowInstance,
  type Connection,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useSkillRegistryStore } from '../../../stores/skillRegistryStore'
import { DAGContextMenu } from './DAGContextMenu'
import { SkillNodeLibraryPanel } from './SkillNodeLibraryPanel'
import { ChangeLogBar } from './ChangeLogBar'
import type { Skill } from '../../../stores/skillRegistryStore'

function detectCycle(nodes: Node[], edges: Edge[]): { hasCycle: boolean; cycleNodes: Set<string>; cycleEdges: Set<string> } {
  const adj: Record<string, string[]> = {}
  const edgeMap: Record<string, string> = {}

  nodes.forEach((n) => {
    adj[n.id] = []
  })
  edges.forEach((e) => {
    if (adj[e.source]) {
      adj[e.source].push(e.target)
    }
    edgeMap[`${e.source}->${e.target}`] = e.id
  })

  const WHITE = 0, GRAY = 1, BLACK = 2
  const color: Record<string, number> = {}
  nodes.forEach((n) => { color[n.id] = WHITE })

  const cycleNodes = new Set<string>()
  const cycleEdges = new Set<string>()
  let hasCycle = false

  function dfs(u: string, path: string[]): boolean {
    color[u] = GRAY
    path.push(u)

    for (const v of adj[u]) {
      if (color[v] === GRAY) {
        // Found cycle — mark nodes and edges from v to end of path
        const idx = path.indexOf(v)
        for (let i = idx; i < path.length; i++) {
          cycleNodes.add(path[i])
          const next = path[i + 1] || v
          const edgeId = edgeMap[`${path[i]}->${next}`]
          if (edgeId) cycleEdges.add(edgeId)
        }
        const closingEdge = edgeMap[`${path[path.length - 1]}->${v}`]
        if (closingEdge) cycleEdges.add(closingEdge)
        hasCycle = true
        return true
      }
      if (color[v] === WHITE) {
        if (dfs(v, path)) return true
      }
    }

    path.pop()
    color[u] = BLACK
    return false
  }

  for (const n of nodes) {
    if (color[n.id] === WHITE) {
      dfs(n.id, [])
    }
  }

  return { hasCycle, cycleNodes, cycleEdges }
}

export function SkillDAGCanvas() {
  const {
    dag,
    skills,
    fetchDAG,
    addDAGNode,
    addDAGEdge,
    undoDAG,
    redoDAG,
    saveDAG,
    fetchChangeLogs,
  } = useSkillRegistryStore()

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const [contextMenu, setContextMenu] = useState<{
    x: number
    y: number
    nodeId: string | null
  } | null>(null)
  const [libraryCollapsed, setLibraryCollapsed] = useState(false)
  const [logExpanded, setLogExpanded] = useState(false)
  const [cycleError, setCycleError] = useState<string | null>(null)
  const [flashingNodes, setFlashingNodes] = useState<Set<string>>(new Set())
  const [flashingEdges, setFlashingEdges] = useState<Set<string>>(new Set())
  const flowRef = useRef<ReactFlowInstance<Node, Edge> | null>(null)
  const flashTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    fetchDAG()
    fetchChangeLogs()
  }, [fetchDAG, fetchChangeLogs])

  useEffect(() => {
    const ns: Node[] = dag.nodes.map((n) => {
      const skill = skills.find((s) => s.skill_id === n.skill_id)
      return {
        id: n.node_id,
        position: { x: n.position_x, y: n.position_y },
        data: { label: skill?.skill_name || n.skill_id, skillId: n.skill_id },
        type: 'default',
      }
    })
    const es: Edge[] = dag.edges.map((e) => ({
      id: e.edge_id,
      source: e.source_node_id,
      target: e.target_node_id,
      label: `${e.confidence}%`,
      animated: !e.is_auto_parsed,
    }))
    setNodes(ns)
    setEdges(es)
  }, [dag, skills, setNodes, setEdges])

  const onNodeContextMenu = useCallback(
    (event: React.MouseEvent, node: Node) => {
      event.preventDefault()
      setContextMenu({
        x: event.clientX,
        y: event.clientY,
        nodeId: node.id,
      })
    },
    [],
  )

  const onPaneClick = useCallback(() => {
    setContextMenu(null)
  }, [])

  const onConnect = useCallback(
    async (connection: Connection) => {
      if (!connection.source || !connection.target) return
      const edgeId = `e-${connection.source}-${connection.target}`
      try {
        await addDAGEdge({
          edge_id: edgeId,
          source_node_id: connection.source,
          target_node_id: connection.target,
          confidence: 100,
          is_auto_parsed: false,
        })
      } catch (err: unknown) {
        alert(err instanceof Error ? err.message : '添加连线失败')
      }
    },
    [addDAGEdge],
  )

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'copy'
  }, [])

  const onDrop = useCallback(
    async (event: React.DragEvent) => {
      event.preventDefault()
      const data = event.dataTransfer.getData('application/skill')
      if (!data || !flowRef.current) return

      const skill: Skill = JSON.parse(data)
      const position = flowRef.current.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      })

      try {
        await addDAGNode({
          node_id: `node-${Date.now()}`,
          skill_id: skill.skill_id,
          position_x: position.x,
          position_y: position.y,
        })
      } catch (err: unknown) {
        alert(err instanceof Error ? err.message : '添加节点失败')
      }
    },
    [addDAGNode],
  )

  const handleSave = useCallback(async () => {
    const { hasCycle, cycleNodes, cycleEdges } = detectCycle(nodes, edges)
    if (hasCycle) {
      setCycleError('检测到循环依赖，无法保存')
      setFlashingNodes(cycleNodes)
      setFlashingEdges(cycleEdges)

      if (flashTimer.current) clearTimeout(flashTimer.current)
      flashTimer.current = setTimeout(() => {
        setFlashingNodes(new Set())
        setFlashingEdges(new Set())
        setCycleError(null)
      }, 3000)
      return
    }

    setCycleError(null)
    try {
      await saveDAG()
      alert('DAG 保存成功')
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : '保存失败')
    }
  }, [nodes, edges, saveDAG])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.ctrlKey && (e.key === 'z' || e.key === 'Z')) {
        e.preventDefault()
        undoDAG()
      }
      if (e.ctrlKey && (e.key === 'y' || e.key === 'Y')) {
        e.preventDefault()
        redoDAG()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [undoDAG, redoDAG])

  // Apply flashing styles
  const styledNodes = nodes.map((n) => ({
    ...n,
    style: flashingNodes.has(n.id)
      ? { ...n.style, animation: 'pulse-red 1s infinite', borderColor: '#ef4444', borderWidth: 2 }
      : n.style,
    className: flashingNodes.has(n.id) ? 'ring-2 ring-red-500 animate-pulse' : '',
  }))

  const styledEdges = edges.map((e) => ({
    ...e,
    style: flashingEdges.has(e.id)
      ? { ...e.style, stroke: '#ef4444', strokeWidth: 3 }
      : e.style,
    animated: flashingEdges.has(e.id) ? true : e.animated,
  }))

  return (
    <div className="flex flex-col h-[600px] border border-gray-200 rounded-lg overflow-hidden">
      <style>{`
        @keyframes pulse-red {
          0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
          50% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
        }
      `}</style>

      <div className="flex flex-1 overflow-hidden">
        <SkillNodeLibraryPanel
          collapsed={libraryCollapsed}
          onToggle={() => setLibraryCollapsed((c) => !c)}
        />

        <div className="flex-1 relative">
          {/* Toolbar */}
          <div className="absolute top-3 left-3 z-10 flex gap-2">
            <button
              onClick={handleSave}
              className="px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 shadow-sm"
            >
              保存 DAG
            </button>
            <button
              onClick={() => { undoDAG(); fetchChangeLogs() }}
              className="px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 shadow-sm"
              title="撤销"
            >
              ↩ 撤销
            </button>
            <button
              onClick={() => { redoDAG(); fetchChangeLogs() }}
              className="px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 shadow-sm"
              title="重做"
            >
              ↪ 重做
            </button>
          </div>

          {/* Cycle Error */}
          {cycleError && (
            <div className="absolute top-3 right-3 z-10 px-4 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 shadow-sm">
              {cycleError}
            </div>
          )}

          <ReactFlow
            nodes={styledNodes}
            edges={styledEdges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeContextMenu={onNodeContextMenu}
            onPaneClick={onPaneClick}
            onConnect={onConnect}
            onDragOver={onDragOver}
            onDrop={onDrop}
            onInit={(instance) => {
              flowRef.current = instance as ReactFlowInstance<Node, Edge>
            }}
            fitView
          >
            <Background />
            <Controls />
            <MiniMap />
          </ReactFlow>

          {contextMenu && (
            <DAGContextMenu
              x={contextMenu.x}
              y={contextMenu.y}
              nodeId={contextMenu.nodeId}
              onClose={() => setContextMenu(null)}
            />
          )}
        </div>
      </div>

      <ChangeLogBar
        expanded={logExpanded}
        onToggle={() => setLogExpanded((e) => !e)}
      />
    </div>
  )
}
