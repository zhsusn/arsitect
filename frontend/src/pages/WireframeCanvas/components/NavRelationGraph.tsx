import { useMemo, useState } from 'react'
import type { WireframePage, WireframeNavLink } from '../../../services/wireframe'

interface NavRelationGraphProps {
  pages: WireframePage[]
  links: WireframeNavLink[]
}

type LayoutMode = 'force' | 'hierarchy' | 'circle'

export default function NavRelationGraph({ pages, links }: NavRelationGraphProps) {
  const [layoutMode, setLayoutMode] = useState<LayoutMode>('force')
  const [selectedNode, setSelectedNode] = useState<string | null>(null)

  const { nodes, edges } = useMemo(() => {
    const width = 800
    const height = 500
    const centerX = width / 2
    const centerY = height / 2

    const nodeMap = new Map<string, { x: number; y: number; label: string; type: string }>()

    if (layoutMode === 'circle') {
      const radius = Math.min(width, height) * 0.35
      pages.forEach((p, idx) => {
        const angle = (idx / pages.length) * 2 * Math.PI - Math.PI / 2
        nodeMap.set(p.page_id, {
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle),
          label: p.page_name,
          type: p.page_type,
        })
      })
    } else if (layoutMode === 'hierarchy') {
      const levels: WireframePage[][] = []
      const visited = new Set<string>()
      let current = pages.filter((p) => !links.some((l) => l.target_page_id === p.page_id))
      if (current.length === 0) current = [pages[0]]
      while (current.length > 0 && visited.size < pages.length * 2) {
        levels.push(current)
        current.forEach((p) => visited.add(p.page_id))
        const nextIds = new Set(
          links.filter((l) => current.some((p) => p.page_id === l.source_page_id)).map((l) => l.target_page_id),
        )
        current = pages.filter((p) => nextIds.has(p.page_id) && !visited.has(p.page_id))
      }
      levels.forEach((level, li) => {
        level.forEach((p, pi) => {
          nodeMap.set(p.page_id, {
            x: 80 + (pi + 0.5) * ((width - 160) / Math.max(level.length, 1)),
            y: 60 + li * ((height - 120) / Math.max(levels.length, 1)),
            label: p.page_name,
            type: p.page_type,
          })
        })
      })
    } else {
      pages.forEach((p) => {
        const seed = p.page_id.charCodeAt(0) + p.page_id.charCodeAt(p.page_id.length - 1)
        nodeMap.set(p.page_id, {
          x: 100 + (seed * 137.5) % (width - 200),
          y: 80 + (seed * 89) % (height - 160),
          label: p.page_name,
          type: p.page_type,
        })
      })
    }

    return {
      nodes: Array.from(nodeMap.entries()).map(([id, n]) => ({ id, ...n })),
      edges: links.map((l) => ({
        id: `${l.source_page_id}-${l.target_page_id}`,
        source: l.source_page_id,
        target: l.target_page_id,
        label: l.relation_strength,
      })),
    }
  }, [pages, links, layoutMode])

  const getEdgePath = (sourceId: string, targetId: string) => {
    const s = nodes.find((n) => n.id === sourceId)
    const t = nodes.find((n) => n.id === targetId)
    if (!s || !t) return ''
    const dx = t.x - s.x
    const dy = t.y - s.y
    const len = Math.sqrt(dx * dx + dy * dy)
    if (len === 0) return ''
    const ndx = dx / len
    const ndy = dy / len
    const r = 24
    const sx = s.x + ndx * r
    const sy = s.y + ndy * r
    const tx = t.x - ndx * r
    const ty = t.y - ndy * r
    return `M ${sx} ${sy} L ${tx} ${ty}`
  }

  return (
    <div className="h-full flex flex-col bg-white">
      <div className="px-4 py-2 border-b flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700">页面跳转关系图</h3>
        <div className="flex gap-1">
          {([
            { key: 'force', label: '力导向' },
            { key: 'hierarchy', label: '层次' },
            { key: 'circle', label: '环形' },
          ] as { key: LayoutMode; label: string }[]).map((m) => (
            <button
              key={m.key}
              onClick={() => setLayoutMode(m.key)}
              className={`px-2 py-1 text-xs rounded border ${
                layoutMode === m.key ? 'bg-blue-50 border-blue-300 text-blue-700' : 'border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-auto p-4">
        <svg viewBox="0 0 800 500" className="w-full h-full" style={{ minHeight: 400 }}>
          {edges.map((e) => (
            <g key={e.id}>
              <path d={getEdgePath(e.source, e.target)} stroke="#94a3b8" strokeWidth={1.5} fill="none" markerEnd="url(#arrow)" />
            </g>
          ))}

          <defs>
            <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
              <path d="M0,0 L0,6 L9,3 z" fill="#94a3b8" />
            </marker>
          </defs>

          {nodes.map((n) => {
            const isSelected = selectedNode === n.id
            return (
              <g
                key={n.id}
                transform={`translate(${n.x}, ${n.y})`}
                className="cursor-pointer"
                onClick={() => setSelectedNode(isSelected ? null : n.id)}
              >
                <circle
                  r={24}
                  fill={isSelected ? '#dbeafe' : '#f3f4f6'}
                  stroke={isSelected ? '#3b82f6' : '#d1d5db'}
                  strokeWidth={isSelected ? 2 : 1}
                />
                <text textAnchor="middle" dy="0.35em" fontSize={10} fill="#374151" className="pointer-events-none">
                  {n.label.slice(0, 4)}
                </text>
                {isSelected && (
                  <g transform="translate(0, -36)">
                    <rect x="-60" y="-20" width="120" height="36" rx="4" fill="#1f2937" />
                    <text textAnchor="middle" dy="-4" fontSize={10} fill="#fff">
                      {n.label}
                    </text>
                    <text textAnchor="middle" dy="10" fontSize={9} fill="#9ca3af">
                      {n.type}
                    </text>
                  </g>
                )}
              </g>
            )
          })}
        </svg>
      </div>

      {selectedNode && (
        <div className="border-t px-4 py-2 bg-gray-50 text-xs text-gray-600">
          选中页面: {pages.find((p) => p.page_id === selectedNode)?.page_name} | 类型:{' '}
          {pages.find((p) => p.page_id === selectedNode)?.page_type}
        </div>
      )}
    </div>
  )
}
