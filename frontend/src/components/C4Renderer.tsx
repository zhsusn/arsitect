import { useEffect, useRef, useState, useCallback } from 'react'
import mermaid from 'mermaid'

interface AnalysisIssue {
  rule_id: string
  severity: string
  message: string
  node_ids: string[]
  fix_hint: string
}

interface AnalysisReport {
  passed: boolean
  issues: AnalysisIssue[]
  summary: Record<string, number>
}

interface ConsistencyIssue {
  rule_id: string
  severity: string
  message: string
  c4_node_id: string
  code_entity_id: string
  fix_hint: string
  fix_action: string
}

interface ConsistencyReport {
  passed: boolean
  issues: ConsistencyIssue[]
  summary: Record<string, number>
  code_scan_summary: Record<string, number>
}

interface RenderResponse {
  mermaid_code: string
  view_level: string
  node_count: number
  edge_count: number
  debug_info?: string
  analysis_report?: AnalysisReport
  consistency_report?: ConsistencyReport
}

interface Props {
  projectId: string
  initialLevel?: 'L1' | 'L2' | 'L3' | 'L4'
  level?: 'L1' | 'L2' | 'L3' | 'L4'
  onLevelChange?: (level: 'L1' | 'L2' | 'L3' | 'L4') => void
  hideToolbar?: boolean
  refreshKey?: number
  onRenderComplete?: (svgHtml: string | null) => void
  fullScreen?: boolean
  onToggleFullScreen?: () => void
}

export function C4Renderer({
  projectId,
  initialLevel = 'L2',
  level: controlledLevel,
  onLevelChange,
  hideToolbar = false,
  refreshKey = 0,
  onRenderComplete,
  fullScreen = false,
  onToggleFullScreen,
}: Props) {
  const [internalLevel, setInternalLevel] = useState(initialLevel)
  const level = controlledLevel ?? internalLevel
  const [data, setData] = useState<RenderResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [scale, setScale] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [svgInfo, setSvgInfo] = useState<string>('')
  const [lastMermaidPreview, setLastMermaidPreview] = useState<string>('')
  const dragStart = useRef({ x: 0, y: 0 })
  const panStart = useRef({ x: 0, y: 0 })
  const mermaidRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  // Guard against stale async renders when user toggles rapidly
  const renderSeq = useRef(0)
  // L3 container folding: undefined = all expanded, [] = all collapsed, ['id'] = partial
  const [expandedContainers, setExpandedContainers] = useState<string[] | undefined>(undefined)
  const [showContainerMenu, setShowContainerMenu] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowContainerMenu(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'default',
      securityLevel: 'loose',
      flowchart: { useMaxWidth: true, htmlLabels: false, curve: 'basis' },
    })
  }, [])

  const notifySvg = useCallback(() => {
    if (!mermaidRef.current || !onRenderComplete) return
    const svg = mermaidRef.current.querySelector('svg')
    onRenderComplete(svg ? svg.outerHTML : null)
  }, [onRenderComplete])

  const renderDiagram = async (refresh = false, expanded?: string[]) => {
    const seq = ++renderSeq.current
    console.log(`[C4Render] start seq=${seq}, level=${level}, expanded=${JSON.stringify(expanded)}, renderSeq=${renderSeq.current}`)
    if (refresh) {
      setSyncing(true)
    } else {
      setLoading(true)
    }
    try {
      let url = `/api/v1/c4/render?project_id=${projectId}&level=${level}&_t=${Date.now()}`
      if (refresh) url += '&refresh=1'
      if (level === 'L3' && expanded !== undefined) {
        if (expanded.length === 0) {
          url += '&expanded='
        } else {
          url += '&expanded=' + encodeURIComponent(expanded.join(','))
        }
      }
      console.log(`[C4Render] seq=${seq} fetching ${url}`)
      const res = await fetch(url)
      if (!res.ok) {
        const errText = await res.text()
        console.error(`[C4Render] API error ${res.status}:`, errText)
        if (seq === renderSeq.current && mermaidRef.current) {
          mermaidRef.current.innerHTML = `<div style="color:red">后端错误 ${res.status}: 请检查后端日志或联系管理员</div>`
        }
        return
      }
      const d = await res.json()
      console.log(`[C4Render] seq=${seq} fetch done, staleCheck=${seq !== renderSeq.current}`)
      // Ignore stale renders
      if (seq !== renderSeq.current) {
        console.log(`[C4Render] seq=${seq} ABORTED (stale)`)
        return
      }
      setData(d)
      setLastMermaidPreview(d?.mermaid_code?.split('\n').slice(0, 8).join('\n') || 'N/A')
      if (mermaidRef.current) {
        const code = d?.mermaid_code || 'graph TD\n  A[No C4 DSL found]'
        try {
          const id = `mermaid-${projectId}-${level}-${Date.now()}`
          console.log(`[C4Render] seq=${seq} mermaid.render start, codeLines=${code.split('\n').length}`)
          const { svg } = await mermaid.render(id, code)
          console.log(`[C4Render] seq=${seq} mermaid.render done, svgLen=${svg.length}, staleCheck=${seq !== renderSeq.current}`)
          // Guard against stale renders and unmounted component
          if (seq !== renderSeq.current || !mermaidRef.current) {
            console.log(`[C4Render] seq=${seq} ABORTED after render (stale or unmounted)`)
            return
          }
          mermaidRef.current.innerHTML = svg
          console.log(`[C4Render] seq=${seq} DOM updated`)
          // Apply vector-effect to edge paths (exclude marker paths inside <defs>)
          const paths = mermaidRef.current.querySelectorAll('svg path')
          let edgePathCount = 0
          paths.forEach((p) => {
            // Skip marker paths inside <defs>
            if (p.closest('defs')) return
            p.setAttribute('vector-effect', 'non-scaling-stroke')
            const existingStroke = p.getAttribute('stroke')
            if (!existingStroke || existingStroke === 'none') {
              p.setAttribute('stroke', '#333')
            }
            const existingWidth = p.getAttribute('stroke-width')
            if (!existingWidth || existingWidth === '0') {
              p.setAttribute('stroke-width', '2')
            }
            edgePathCount++
          })
          // Collect SVG diagnostics
          const svgEl = mermaidRef.current.querySelector('svg')
          const vb = svgEl?.getAttribute('viewBox') || 'N/A'
          const w = svgEl?.getAttribute('width') || 'N/A'
          const h = svgEl?.getAttribute('height') || 'N/A'
          setSvgInfo(`paths: ${edgePathCount}, viewBox: ${vb}, size: ${w}x${h}`)
        } catch (renderErr) {
          console.error('Mermaid render error:', renderErr)
          if (seq === renderSeq.current && mermaidRef.current) {
            mermaidRef.current.innerHTML = `<div style="color:red">渲染失败: ${String(renderErr)}</div>`
          }
        }
        notifySvg()
      }
    } catch (e) {
      console.error(e)
    }
    // Only clear loading state for the latest render
    if (seq === renderSeq.current) {
      setLoading(false)
      setSyncing(false)
      console.log(`[C4Render] seq=${seq} finished, loading cleared`)
    } else {
      console.log(`[C4Render] seq=${seq} finished, loading NOT cleared (stale)`)
    }
  }

  // Initialize expanded state when switching to/from L3, and trigger render for all levels
  useEffect(() => {
    if (level === 'L3') {
      setExpandedContainers([])
    } else {
      setExpandedContainers(undefined)
    }
    renderDiagram()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, level])

  // Trigger render whenever expanded container list changes (L3 only)
  useEffect(() => {
    console.log(`[C4Effect] expandedContainers effect fired, level=${level}, expanded=${JSON.stringify(expandedContainers)}`)
    if (level !== 'L3') return
    renderDiagram(false, expandedContainers)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [expandedContainers])

  useEffect(() => {
    if (refreshKey > 0) {
      renderDiagram(true, expandedContainers)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey])

  // Zoom with mouse wheel (Ctrl/Cmd + scroll)
  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const handler = (e: WheelEvent) => {
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault()
        const delta = e.deltaY > 0 ? 0.9 : 1.1
        setScale((prev) => Math.max(0.2, Math.min(5, prev * delta)))
      }
    }
    el.addEventListener('wheel', handler, { passive: false })
    return () => el.removeEventListener('wheel', handler)
  }, [])

  // Pan with mouse drag
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button !== 0) return
    setIsDragging(true)
    dragStart.current = { x: e.clientX, y: e.clientY }
    panStart.current = { ...pan }
  }, [pan])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDragging) return
    const dx = (e.clientX - dragStart.current.x) / scale
    const dy = (e.clientY - dragStart.current.y) / scale
    setPan({ x: panStart.current.x + dx, y: panStart.current.y + dy })
  }, [isDragging, scale])

  const handleMouseUp = useCallback(() => {
    setIsDragging(false)
  }, [])

  const handleReset = () => {
    setScale(1)
    setPan({ x: 0, y: 0 })
  }

  const handleLevelChange = (l: 'L1' | 'L2' | 'L3' | 'L4') => {
    setScale(1)
    setPan({ x: 0, y: 0 })
    if (onLevelChange) {
      onLevelChange(l)
    } else {
      setInternalLevel(l)
    }
  }

  const toggleContainer = (cid: string) => {
    setExpandedContainers((prev) => {
      const current = prev || []
      const next = current.includes(cid)
        ? current.filter((c) => c !== cid)
        : [...current, cid]
      return next
    })
  }

  const expandAllContainers = () => {
    setExpandedContainers(undefined)
  }

  const collapseAllContainers = () => {
    setExpandedContainers([])
  }

  return (
    <div className="c4-renderer flex flex-col h-full">
      {!hideToolbar && (
        <div className="toolbar flex flex-col gap-2 mb-2">
          <div className="flex gap-2 items-center flex-wrap">
            {(['L1', 'L2', 'L3', 'L4'] as const).map((l) => (
              <button
                key={l}
                className={`px-3 py-1 text-sm rounded border ${
                  level === l
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
                onClick={() => handleLevelChange(l)}
              >
                {l === 'L1'
                  ? 'System'
                  : l === 'L2'
                    ? 'Container'
                    : l === 'L3'
                      ? 'Component'
                      : 'Code'}
              </button>
            ))}
            <button
              className="px-3 py-1 text-sm rounded border bg-white text-gray-700 border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={() => renderDiagram(true, expandedContainers)}
              disabled={syncing || loading}
              title="从设计文档重新解析关系并同步"
            >
              {syncing ? '同步中...' : '↻ 重新同步关系'}
            </button>
            <div className="flex items-center gap-1 ml-1">
              <button
                className="px-2 py-1 text-sm rounded border bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                onClick={() => setScale((s) => Math.max(0.2, s - 0.2))}
                title="缩小"
              >
                −
              </button>
              <span className="text-xs text-gray-500 w-12 text-center">{Math.round(scale * 100)}%</span>
              <button
                className="px-2 py-1 text-sm rounded border bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                onClick={() => setScale((s) => Math.min(5, s + 0.2))}
                title="放大"
              >
                +
              </button>
              <button
                className="px-2 py-1 text-sm rounded border bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                onClick={handleReset}
                title="重置视图"
              >
                ⟲
              </button>
            </div>
            {onToggleFullScreen && (
              <button
                className="px-3 py-1 text-sm rounded border bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                onClick={onToggleFullScreen}
                title={fullScreen ? '退出全屏' : '全屏预览'}
              >
                {fullScreen ? '⛶ 退出全屏' : '⛶ 全屏'}
              </button>
            )}
            {data && (
              <span className="text-xs text-gray-500 ml-2">
                {data.node_count} nodes, {data.edge_count} edges
              </span>
            )}
            {svgInfo && (
              <span className="text-xs text-gray-400 ml-2" title="SVG diagnostics">
                {svgInfo}
              </span>
            )}
          </div>
          {/* L3 container folding controls */}
          {level === 'L3' && data && (
            <div className="flex gap-2 items-center">
              {(() => {
                const code = data.mermaid_code || ''
                // Parse metadata comments: %% @container {name} {count}
                const metaMatches = code.matchAll(/%%\s*@container\s+(\S+)\s+(\d+)/g)
                const containerMap = new Map<string, number>()
                for (const m of metaMatches) {
                  containerMap.set(m[1], parseInt(m[2], 10))
                }
                // Fallback for older renders without metadata
                if (containerMap.size === 0) {
                  const hubMatches = code.matchAll(/\w+_hub\["([^<]+)<br\/>\((\d+)\s+components\)"\]/g)
                  for (const m of hubMatches) {
                    const name = m[1].trim()
                    if (!containerMap.has(name)) {
                      containerMap.set(name, parseInt(m[2], 10))
                    }
                  }
                }
                const containers = Array.from(containerMap.entries())
                if (containers.length === 0) return null
                return (
                  <div className="relative" ref={menuRef}>
                    <button
                      onClick={() => setShowContainerMenu((v) => !v)}
                      className="px-2 py-0.5 text-xs rounded border bg-white text-gray-700 border-gray-300 hover:bg-gray-50 flex items-center gap-1"
                    >
                      <span>容器</span>
                      <span className="bg-gray-100 text-gray-600 px-1.5 rounded-full text-[10px]">
                        {expandedContainers === undefined ? '全部' : expandedContainers.length}
                      </span>
                      <span>{showContainerMenu ? '▲' : '▼'}</span>
                    </button>
                    {showContainerMenu && (
                      <div className="absolute z-20 mt-1 bg-white border border-gray-200 rounded shadow-lg p-2 w-64 max-h-72 overflow-y-auto">
                        <div className="flex items-center justify-between mb-1 pb-1 border-b border-gray-100">
                          <span className="text-xs text-gray-500 font-medium">选择展开的容器</span>
                        </div>
                        {containers.map(([cid, count]) => {
                          const isExpanded = expandedContainers === undefined || expandedContainers.includes(cid)
                          return (
                            <label
                              key={cid}
                              className="flex items-center gap-2 px-2 py-1.5 text-xs rounded cursor-pointer hover:bg-gray-50"
                            >
                              <input
                                type="checkbox"
                                checked={isExpanded}
                                onChange={() => toggleContainer(cid)}
                                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                              />
                              <span className="flex-1 truncate text-gray-700" title={cid}>{cid}</span>
                              <span className="text-gray-400 text-[10px] shrink-0">{count} 组件</span>
                            </label>
                          )
                        })}
                        <div className="flex gap-2 mt-1 pt-1 border-t border-gray-100">
                          <button
                            onClick={() => { expandAllContainers(); setShowContainerMenu(false) }}
                            disabled={expandedContainers === undefined}
                            className="flex-1 px-2 py-1 text-[10px] rounded border bg-white text-gray-600 border-gray-200 hover:bg-gray-50 disabled:opacity-40"
                          >
                            展开全部
                          </button>
                          <button
                            onClick={() => { collapseAllContainers(); setShowContainerMenu(false) }}
                            disabled={expandedContainers !== undefined && expandedContainers.length === 0}
                            className="flex-1 px-2 py-1 text-[10px] rounded border bg-white text-gray-600 border-gray-200 hover:bg-gray-50 disabled:opacity-40"
                          >
                            折叠全部
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })()}
            </div>
          )}
          {/* Diagnostics — collapsible */}
          {data && (
            <DiagnosticsPanel
              data={data}
              expandedContainers={expandedContainers}
              lastMermaidPreview={lastMermaidPreview}
            />
          )}
        </div>
      )}
      <div
        ref={containerRef}
        className="mermaid-container bg-white border rounded p-4 min-h-[300px] relative flex-1 overflow-hidden cursor-grab active:cursor-grabbing"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {(loading || syncing) && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/80 z-10">
            <div className="text-gray-500">
              {syncing ? '正在从设计文档解析关系并同步...' : 'Rendering...'}
            </div>
          </div>
        )}
        <div
          ref={mermaidRef}
          style={{
            transform: `scale(${scale}) translate(${pan.x}px, ${pan.y}px)`,
            transformOrigin: 'top left',
            transition: isDragging ? 'none' : 'transform 0.1s ease-out',
          }}
        />
        <div className="absolute bottom-2 right-2 text-xs text-gray-400 bg-white/80 px-2 py-1 rounded pointer-events-none select-none">
          Ctrl+滚轮缩放 · 拖拽平移
        </div>
      </div>
    </div>
  )
}

function DiagnosticsPanel({
  data,
  expandedContainers,
  lastMermaidPreview,
}: {
  data: RenderResponse
  expandedContainers: string[] | undefined
  lastMermaidPreview: string
}) {
  const [open, setOpen] = useState(false)

  return (
    <div className="mt-1 border border-gray-200 rounded bg-gray-50">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded"
      >
        <span className="font-medium">
          诊断信息
          {data.analysis_report && !data.analysis_report.passed && (
            <span className="ml-1 text-red-500">({data.analysis_report.issues.length})</span>
          )}
          {data.consistency_report && !data.consistency_report.passed && (
            <span className="ml-1 text-amber-500">({data.consistency_report.issues.length})</span>
          )}
        </span>
        <span>{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="px-2 pb-2 flex flex-col gap-1 text-xs text-gray-500">
          {/* Self-diagnosis: backend param mismatch */}
          {expandedContainers !== undefined && expandedContainers.length === 0 && lastMermaidPreview.includes('subgraph') && (
            <div className="text-red-600 font-semibold text-xs">
              ⚠️ 前端请求了折叠态，但后端返回了展开态代码。请确认后端已重启。
            </div>
          )}
          {/* Architecture analysis report */}
          {data.analysis_report && (
            <div className="mt-1">
              <div className={`font-semibold text-xs ${data.analysis_report.passed ? 'text-green-600' : 'text-red-600'}`}>
                {data.analysis_report.passed
                  ? '✓ 架构检查通过'
                  : `✗ 架构检查未通过 (BLOCKER:${data.analysis_report.summary.BLOCKER || 0} ERROR:${data.analysis_report.summary.ERROR || 0} WARNING:${data.analysis_report.summary.WARNING || 0})`}
              </div>
              {!data.analysis_report.passed && data.analysis_report.issues.length > 0 && (
                <div className="mt-1 space-y-1 max-h-32 overflow-y-auto">
                  {data.analysis_report.issues.map((issue, idx) => {
                    const color = issue.severity === 'BLOCKER' ? 'text-red-700 bg-red-50 border-red-200'
                      : issue.severity === 'ERROR' ? 'text-orange-700 bg-orange-50 border-orange-200'
                      : issue.severity === 'WARNING' ? 'text-yellow-700 bg-yellow-50 border-yellow-200'
                      : 'text-blue-700 bg-blue-50 border-blue-200'
                    return (
                      <div key={idx} className={`px-2 py-1 rounded border text-[10px] ${color}`}>
                        <div className="font-semibold">[{issue.severity}] {issue.rule_id}</div>
                        <div>{issue.message}</div>
                        {issue.fix_hint && <div className="mt-0.5 text-gray-500">💡 {issue.fix_hint}</div>}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )}
          {/* Design ↔ Code consistency report */}
          {data.consistency_report && (
            <div className="mt-1">
              <div className={`font-semibold text-xs ${data.consistency_report.passed ? 'text-green-600' : 'text-amber-600'}`}>
                {data.consistency_report.passed
                  ? '✓ 文档与代码一致'
                  : `⚠ 文档与代码不一致 (ERROR:${data.consistency_report.summary.ERROR || 0} WARNING:${data.consistency_report.summary.WARNING || 0})`}
              </div>
              {!data.consistency_report.passed && data.consistency_report.issues.length > 0 && (
                <div className="mt-1 space-y-1 max-h-32 overflow-y-auto">
                  {data.consistency_report.issues.map((issue, idx) => {
                    const actionColor = issue.fix_action === 'UPDATE_DOC' ? 'border-purple-200 bg-purple-50 text-purple-700'
                      : issue.fix_action === 'UPDATE_CODE' ? 'border-teal-200 bg-teal-50 text-teal-700'
                      : 'border-gray-200 bg-gray-50 text-gray-700'
                    const severityColor = issue.severity === 'ERROR' ? 'text-red-600' : 'text-amber-600'
                    return (
                      <div key={idx} className={`px-2 py-1 rounded border text-[10px] ${actionColor}`}>
                        <div className="font-semibold flex items-center gap-1">
                          <span className={severityColor}>[{issue.severity}]</span>
                          <span>{issue.rule_id}</span>
                          {issue.fix_action && (
                            <span className="ml-auto px-1 rounded bg-white/60 text-[9px]">
                              {issue.fix_action === 'UPDATE_DOC' ? '📝 改文档' : issue.fix_action === 'UPDATE_CODE' ? '💻 改代码' : '🔧 两者都改'}
                            </span>
                          )}
                        </div>
                        <div>{issue.message}</div>
                        {(issue.c4_node_id || issue.code_entity_id) && (
                          <div className="text-gray-500 mt-0.5">
                            {issue.c4_node_id && <span>C4: {issue.c4_node_id} </span>}
                            {issue.code_entity_id && <span>Code: {issue.code_entity_id}</span>}
                          </div>
                        )}
                        {issue.fix_hint && <div className="mt-0.5 text-gray-500">💡 {issue.fix_hint}</div>}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
