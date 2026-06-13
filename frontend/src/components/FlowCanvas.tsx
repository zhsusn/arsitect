import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  ReactFlow,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  BackgroundVariant,
  type Node,
  type Edge,
  type Connection,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

export type ViewMode = 'topology' | 'swimlane' | 'list'

export interface DAGNodeDef {
  id: string
  label: string
  phase: string
  status: string
}

export interface DAGEdgeDef {
  source: string
  target: string
  label?: string
}

export interface FlowCanvasProps {
  projectId: string
  dag: { nodes: DAGNodeDef[]; edges: DAGEdgeDef[] }
  onNodeClick?: (node: DAGNodeDef) => void
}

const STATUS_COLORS: Record<string, string> = {
  pending: '#999',
  scheduled: '#4a90d9',
  executing: '#f5a623',
  completed: '#5cb85c',
  failed: '#d9534f',
  gate_waiting: '#9b59b6',
  skipped: '#94a3b8',
}

const normalizeStatus = (status: string): string =>
  status.toLowerCase().replace(/_/, '_')

export function FlowCanvas({
  projectId,
  dag,
  onNodeClick,
}: FlowCanvasProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('topology')
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])

  const initialNodes = useMemo(
    () =>
      dag.nodes.map((n, i) => ({
        id: n.id,
        type: 'default',
        position: { x: (i % 5) * 200, y: Math.floor(i / 5) * 100 },
        data: { label: n.label, status: n.status, phase: n.phase },
        style: {
          border: `2px solid ${STATUS_COLORS[normalizeStatus(n.status)] || '#999'}`,
          background: `${STATUS_COLORS[normalizeStatus(n.status)] || '#999'}22`,
        },
      })),
    [dag.nodes],
  )

  const initialEdges = useMemo(
    () =>
      dag.edges.map((e, i) => ({
        id: `e${i}`,
        source: e.source,
        target: e.target,
        label: e.label,
        animated: true,
      })),
    [dag.edges],
  )

  useEffect(() => {
    setNodes(initialNodes)
    setEdges(initialEdges)
  }, [initialNodes, initialEdges, setNodes, setEdges])

  // SSE real-time updates
  useEffect(() => {
    const source = new EventSource(`/api/v1/events/${projectId}`)
    source.onmessage = (event) => {
      const message = JSON.parse(event.data)
      if (message.type === 'skill_state_changed') {
        const { entity_id, to } = message.data
        setNodes((nds) =>
          nds.map((n) =>
            n.id === entity_id
              ? {
                  ...n,
                  data: { ...n.data, status: to },
                  style: {
                    border: `2px solid ${STATUS_COLORS[normalizeStatus(to)] || '#999'}`,
                    background: `${STATUS_COLORS[normalizeStatus(to)] || '#999'}22`,
                  },
                }
              : n,
          ),
        )
      }
    }
    source.onerror = (err) => {
      console.error('SSE error:', err)
    }
    return () => source.close()
  }, [projectId, setNodes])

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  )

  const handleNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      const def = dag.nodes.find((n) => n.id === node.id)
      if (def && onNodeClick) {
        onNodeClick(def)
      }
    },
    [dag.nodes, onNodeClick],
  )

  return (
    <div className="flow-canvas" style={{ width: '100%', height: '600px' }}>
      <div className="view-toggle" style={{ marginBottom: 8 }}>
        {(['topology', 'swimlane', 'list'] as const).map((mode) => (
          <button
            key={mode}
            className={viewMode === mode ? 'active' : ''}
            onClick={() => setViewMode(mode)}
            style={{
              marginRight: 8,
              padding: '4px 12px',
              borderRadius: 4,
              border: '1px solid #d1d5db',
              background: viewMode === mode ? '#eff6ff' : '#fff',
              color: viewMode === mode ? '#3b82f6' : '#374151',
              cursor: 'pointer',
            }}
          >
            {mode === 'topology' && 'Topology'}
            {mode === 'swimlane' && 'Swimlane'}
            {mode === 'list' && 'List'}
          </button>
        ))}
      </div>

      <div className="legend" style={{ marginBottom: 8 }}>
        {Object.entries(STATUS_COLORS).map(([status, color]) => (
          <span key={status} className="legend-item" style={{ marginRight: 12 }}>
            <span
              className="dot"
              style={{
                display: 'inline-block',
                width: 10,
                height: 10,
                borderRadius: '50%',
                background: color,
                marginRight: 4,
              }}
            />
            {status}
          </span>
        ))}
      </div>

      {viewMode === 'topology' && (
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={handleNodeClick}
          fitView
        >
          <Controls />
          <MiniMap />
          <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
        </ReactFlow>
      )}

      {viewMode === 'list' && (
        <div className="node-list" style={{ overflow: 'auto', height: '100%' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left', padding: 8 }}>ID</th>
                <th style={{ textAlign: 'left', padding: 8 }}>Name</th>
                <th style={{ textAlign: 'left', padding: 8 }}>Phase</th>
                <th style={{ textAlign: 'left', padding: 8 }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {nodes.map((n) => (
                <tr key={n.id}>
                  <td style={{ padding: 8 }}>{n.id}</td>
                  <td style={{ padding: 8 }}>{(n.data?.label as string) ?? ''}</td>
                  <td style={{ padding: 8 }}>{(n.data?.phase as string) ?? ''}</td>
                  <td style={{ padding: 8, color: STATUS_COLORS[normalizeStatus(n.data?.status as string)] }}>
                    {(n.data?.status as string) ?? ''}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {viewMode === 'swimlane' && (
        <div style={{ padding: 24, color: '#6b7280' }}>
          Swimlane view placeholder — implement per-phase swimlane layout here.
        </div>
      )}
    </div>
  )
}
