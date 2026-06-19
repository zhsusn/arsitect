import { useCallback, useEffect, useMemo, useState } from 'react'
import { useProjectContext } from '../../App'
import { listWireframes, generateWireframe, deleteWireframe, listWireframePages, listWireframeNavLinks, type Wireframe, type WireframePage, type WireframeNavLink } from '../../services/wireframe'
import { WireframeViewer } from '../../components/WireframeViewer'
import NavRelationGraph from './components/NavRelationGraph'

export default function WireframeCanvas() {
  const { currentProjectId } = useProjectContext()
  const projectId = currentProjectId
  const [wireframes, setWireframes] = useState<Wireframe[]>([])
  const [pages, setPages] = useState<WireframePage[]>([])
  const [links, setLinks] = useState<WireframeNavLink[]>([])
  const [selectedPageId, setSelectedPageId] = useState<string | null>(null)
  const [showNavGraph, setShowNavGraph] = useState(false)
  const [showNewWireframe, setShowNewWireframe] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadAll = useCallback(async () => {
    if (!projectId.trim()) return
    try {
      const [wfs, ps, ls] = await Promise.all([
        listWireframes(projectId),
        listWireframePages(projectId),
        listWireframeNavLinks(projectId),
      ])
      setWireframes(wfs)
      setPages(ps)
      setLinks(ls)
      if (ps.length > 0) {
        setSelectedPageId((prev) => prev || ps[0].page_id)
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '加载失败')
    }
  }, [projectId])

  useEffect(() => { loadAll() }, [loadAll])

  const handleGenerate = async () => {
    if (!projectId.trim()) return
    setLoading(true)
    setError(null)
    try {
      await generateWireframe(projectId, {})
      await loadAll()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '生成失败')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('确认删除?')) return
    try { await deleteWireframe(id); await loadAll() } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '删除失败')
    }
  }

  const selectedPage = useMemo(() => pages.find(p => p.page_id === selectedPageId) || null, [pages, selectedPageId])
  const pageLinks = useMemo(() => {
    if (!selectedPage) return []
    return links.filter(l => l.source_page_id === selectedPage.page_id || l.target_page_id === selectedPage.page_id)
  }, [links, selectedPage])

  // 树形层级结构
  const { rootPages, childrenMap } = useMemo(() => {
    const pageByName = new Map(pages.map((p) => [p.page_name, p]))
    const childMap = new Map<string, WireframePage[]>()
    const hasParent = new Set<string>()
    for (const p of pages) {
      let targets: string[] = []
      try {
        targets = p.nav_targets_json ? JSON.parse(p.nav_targets_json) : []
      } catch { targets = [] }
      const children: WireframePage[] = []
      for (const name of targets) {
        const child = pageByName.get(name)
        if (child && child.page_id !== p.page_id) {
          children.push(child)
          hasParent.add(child.page_id)
        }
      }
      if (children.length > 0) childMap.set(p.page_id, children)
    }
    let roots = pages.filter((p) => !hasParent.has(p.page_id))
    if (roots.length === 0 && pages.length > 0) roots = pages
    return { rootPages: roots, childrenMap: childMap }
  }, [pages])

  const [expandedRoots, setExpandedRoots] = useState<Set<string>>(new Set())

  if (!projectId) {
    return <div className="h-screen flex items-center justify-center text-gray-400">请先在顶部选择项目</div>
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <div className="bg-white border-b px-4 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-bold text-gray-800">WireframeEngine</h1>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => { setShowNewWireframe(false); setShowNavGraph((s) => !s); }}
            className={`px-3 py-2 border rounded text-sm ${showNavGraph && !showNewWireframe ? 'bg-blue-50 border-blue-300 text-blue-700' : 'border-gray-300 hover:bg-gray-50'}`}>
            {showNavGraph ? '返回预览' : '跳转关系图'}
          </button>
          <button onClick={() => { setShowNavGraph(false); setShowNewWireframe((s) => !s); }}
            className={`px-3 py-2 border rounded text-sm ${showNewWireframe ? 'bg-blue-50 border-blue-300 text-blue-700' : 'border-gray-300 hover:bg-gray-50'}`}>
            {showNewWireframe ? '返回预览' : '新版线框图'}
          </button>
          <button onClick={handleGenerate} disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:bg-gray-300">
            {loading ? '生成中...' : '从 C4 生成线框图'}
          </button>
        </div>
      </div>
      {error && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-2 text-sm text-red-700 flex justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-500">✕</button>
        </div>
      )}
      <div className="flex-1 flex overflow-hidden">
        {/* Left sidebar — 树形页面列表 */}
        <div className="w-72 bg-white border-r flex flex-col">
          <div className="px-3 py-2 border-b text-xs font-semibold text-gray-500">页面列表 ({pages.length})</div>
          <div className="flex-1 overflow-auto p-2 space-y-1">
            {pages.length === 0 && <div className="text-center text-gray-400 text-sm py-8">暂无页面，请先生成</div>}
            {rootPages.map((root) => {
              const children = childrenMap.get(root.page_id) || []
              const isExpanded = expandedRoots.has(root.page_id)
              const isSelected = selectedPageId === root.page_id
              return (
                <div key={root.page_id}>
                  <button onClick={() => setSelectedPageId(root.page_id)}
                    className={`w-full text-left px-3 py-2 rounded text-sm border transition flex items-center gap-1 ${isSelected ? 'bg-blue-50 border-blue-300 text-blue-700' : 'border-transparent text-gray-700 hover:bg-gray-50'}`}>
                    <span className="text-xs text-gray-400 w-4 text-center select-none"
                      onClick={(e) => { e.stopPropagation(); if (children.length > 0) { setExpandedRoots((prev) => { const next = new Set(prev); if (next.has(root.page_id)) next.delete(root.page_id); else next.add(root.page_id); return next }) } }}>
                      {children.length > 0 ? (isExpanded ? '▼' : '▶') : ''}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{root.page_name}</div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[10px] px-1.5 py-0.5 bg-gray-100 rounded text-gray-500">{root.page_type}</span>
                        {root.confidence !== null && (
                          <span className={`text-[10px] ${root.confidence >= 80 ? 'text-green-600' : root.confidence >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                            {root.confidence}%
                          </span>
                        )}
                      </div>
                    </div>
                  </button>
                  {isExpanded && children.map((child) => (
                    <button key={child.page_id} onClick={() => setSelectedPageId(child.page_id)}
                      className={`w-full text-left pl-9 pr-3 py-2 rounded text-sm border transition mt-1 flex items-center gap-1 ${selectedPageId === child.page_id ? 'bg-blue-50 border-blue-300 text-blue-700' : 'border-transparent text-gray-600 hover:bg-gray-50'}`}>
                      <span className="text-xs text-gray-300 select-none">└</span>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate">{child.page_name}</div>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-[10px] px-1.5 py-0.5 bg-gray-100 rounded text-gray-500">{child.page_type}</span>
                          {child.confidence !== null && (
                            <span className={`text-[10px] ${child.confidence >= 80 ? 'text-green-600' : child.confidence >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                              {child.confidence}%
                            </span>
                          )}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )
            })}
          </div>
          {wireframes.length > 0 && (
            <div className="border-t p-2">
              <div className="text-xs font-semibold text-gray-500 mb-1">会话</div>
              {wireframes.map(wf => (
                <div key={wf.wireframe_id} className="flex items-center justify-between text-xs bg-gray-50 px-2 py-1 rounded mb-1">
                  <span className="truncate">{wf.name}</span>
                  <button onClick={() => handleDelete(wf.wireframe_id)} className="text-red-400 hover:text-red-600 ml-1">✕</button>
                </div>
              ))}
            </div>
          )}
        </div>
        {/* Main preview or nav graph */}
        <div className="flex-1 bg-gray-100 flex flex-col overflow-hidden">
          {showNewWireframe ? (
            <WireframeViewer projectId={projectId} />
          ) : showNavGraph ? (
            <NavRelationGraph pages={pages} links={links} />
          ) : selectedPage ? (
            <>
              <div className="bg-white border-b px-4 py-2 flex items-center justify-between shrink-0">
                <div>
                  <span className="text-sm font-medium text-gray-800">{selectedPage.page_name}</span>
                  <span className="ml-2 text-xs text-gray-400">{selectedPage.page_type} · {selectedPage.mapping_source}</span>
                </div>
                <div className="text-xs text-gray-500">
                  置信度: <span className={selectedPage.confidence && selectedPage.confidence >= 80 ? 'text-green-600' : 'text-yellow-600'}>{selectedPage.confidence ?? '--'}%</span>
                </div>
              </div>
              <div className="flex-1 overflow-auto p-6 flex items-start justify-center">
                {selectedPage.svg_content ? (
                  <div className="bg-white shadow rounded-lg p-4" dangerouslySetInnerHTML={{ __html: selectedPage.svg_content }} />
                ) : <div className="text-gray-400 text-sm">无 SVG 内容</div>}
              </div>
              {/* 页面元数据面板 */}
              <div className="bg-white border-t px-4 py-2 shrink-0">
                <div className="text-xs text-gray-500 flex gap-4 flex-wrap">
                  <span>字段: {selectedPage.fields_json ? JSON.parse(selectedPage.fields_json).length : 0}</span>
                  <span>按钮: {selectedPage.buttons_json ? JSON.parse(selectedPage.buttons_json).length : 0}</span>
                  <span>跳转: {selectedPage.nav_targets_json ? JSON.parse(selectedPage.nav_targets_json).join(', ') || '无' : '无'}</span>
                  {selectedPage.source_module_id && <span className="text-indigo-500">来源: {selectedPage.source_module_id}</span>}
                </div>
              </div>
              {pageLinks.length > 0 && (
                <div className="bg-white border-t px-4 py-2 shrink-0">
                  <div className="text-xs font-semibold text-gray-500 mb-1">跳转关系</div>
                  <div className="flex gap-3 flex-wrap">
                    {pageLinks.map(l => {
                      const src = pages.find(p => p.page_id === l.source_page_id)
                      const tgt = pages.find(p => p.page_id === l.target_page_id)
                      return (
                        <div key={l.link_id} className="text-xs flex items-center gap-1 bg-gray-50 px-2 py-1 rounded border">
                          <span className="text-gray-600">{src?.page_name || '?'}</span>
                          <span className={l.relation_strength === 'strong' ? 'text-blue-600 font-bold' : 'text-gray-400'}>→</span>
                          <span className="text-gray-600">{tgt?.page_name || '?'}</span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-400">请从左侧选择一个页面</div>
          )}
        </div>
      </div>
    </div>
  )
}
