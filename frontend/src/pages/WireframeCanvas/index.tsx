import { useCallback, useEffect, useMemo, useState } from 'react'
import ProjectSelector from '../../components/ProjectSelector'
import {
  listWireframes,
  generateWireframe,
  deleteWireframe,
  listWireframePages,
  listWireframeNavLinks,
  type Wireframe,
  type WireframePage,
  type WireframeNavLink,
} from '../../services/wireframe'
import { WireframeViewer } from '../../components/WireframeViewer'
import NavRelationGraph from './components/NavRelationGraph'

const LS_PROJECT_KEY = 'arsitect:lastProjectId'

export default function WireframeCanvas() {
  const [projectId, setProjectId] = useState(() => {
    try { return localStorage.getItem(LS_PROJECT_KEY) || '' } catch { return '' }
  })
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

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <div className="bg-white border-b px-4 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-bold text-gray-800">WireframeEngine</h1>
          <ProjectSelector value={projectId} onChange={(id) => { setProjectId(id); localStorage.setItem(LS_PROJECT_KEY, id) }} />
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
        {/* Left sidebar */}
        <div className="w-72 bg-white border-r flex flex-col">
          <div className="px-3 py-2 border-b text-xs font-semibold text-gray-500">页面列表 ({pages.length})</div>
          <div className="flex-1 overflow-auto p-2 space-y-1">
            {pages.length === 0 && <div className="text-center text-gray-400 text-sm py-8">暂无页面，请先生成</div>}
            {pages.map(p => (
              <button key={p.page_id} onClick={() => setSelectedPageId(p.page_id)}
                className={`w-full text-left px-3 py-2 rounded text-sm border transition ${selectedPageId === p.page_id ? 'bg-blue-50 border-blue-300 text-blue-700' : 'border-transparent text-gray-700 hover:bg-gray-50'}`}>
                <div className="font-medium truncate">{p.page_name}</div>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-[10px] px-1.5 py-0.5 bg-gray-100 rounded text-gray-500">{p.page_type}</span>
                  {p.confidence !== null && (
                    <span className={`text-[10px] ${p.confidence >= 80 ? 'text-green-600' : p.confidence >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                      {p.confidence}%
                    </span>
                  )}
                </div>
              </button>
            ))}
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
