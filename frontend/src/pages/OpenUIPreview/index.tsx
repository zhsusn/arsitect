import { useCallback, useEffect, useMemo, useState } from 'react'
import { useProjectContext } from '../../App'
import {
  listOpenUISpecs,
  generateOpenUISpec,
  deleteOpenUISpec,
  checkOpenUIHealth,
  listOpenUIPages,
  type OpenUISpec,
  type OpenUIPage,
} from '../../services/openUi'
import ServiceSetupGuide from './components/ServiceSetupGuide'

type Viewport = 'desktop' | 'tablet' | 'mobile'

const VIEWPORT_WIDTHS: Record<Viewport, number> = {
  desktop: 1280,
  tablet: 768,
  mobile: 375,
}

export default function OpenUIPreview() {
  const { currentProjectId } = useProjectContext()
  const projectId = currentProjectId
  const [specs, setSpecs] = useState<OpenUISpec[]>([])
  const [pages, setPages] = useState<OpenUIPage[]>([])
  const [selectedPageId, setSelectedPageId] = useState<string | null>(null)
  const [viewport, setViewport] = useState<Viewport>('desktop')
  const [serviceStatus, setServiceStatus] = useState<string>('UNKNOWN')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showSetupGuide, setShowSetupGuide] = useState(false)

  const loadAll = useCallback(async () => {
    if (!projectId.trim()) return
    try {
      const [sp, pg] = await Promise.all([
        listOpenUISpecs(projectId),
        listOpenUIPages(projectId),
      ])
      setSpecs(sp)
      setPages(pg)
      if (pg.length > 0 && !selectedPageId) setSelectedPageId(pg[0].page_id)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '加载失败')
    }
  }, [projectId, selectedPageId])

  useEffect(() => { loadAll() }, [loadAll])

  const firstSpecId = specs[0]?.spec_id

  const checkHealth = useCallback(async () => {
    if (!projectId.trim()) return
    try {
      const result = await checkOpenUIHealth(firstSpecId || 'health')
      setServiceStatus(result.status)
    } catch {
      setServiceStatus('UNAVAILABLE')
    }
  }, [projectId, firstSpecId])

  useEffect(() => {
    checkHealth()
    const timer = setInterval(checkHealth, 10000)
    return () => clearInterval(timer)
  }, [checkHealth])

  const handleGenerate = async () => {
    if (!projectId.trim()) return
    setLoading(true)
    setError(null)
    try {
      await generateOpenUISpec(projectId, {})
      await loadAll()
      await checkHealth()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '生成失败')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('确认删除?')) return
    try { await deleteOpenUISpec(id); await loadAll() } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '删除失败')
    }
  }

  const selectedPage = useMemo(() => pages.find(p => p.page_id === selectedPageId) || null, [pages, selectedPageId])
  const isFallback = specs.some(s => s.status === 'FALLBACK')

  const statusColor = serviceStatus === 'AVAILABLE' ? 'bg-green-500' : serviceStatus === 'STARTING' ? 'bg-yellow-500' : serviceStatus === 'UNAVAILABLE' ? 'bg-red-500' : 'bg-gray-400'
  const statusText = serviceStatus === 'AVAILABLE' ? '服务可用' : serviceStatus === 'STARTING' ? '启动中' : serviceStatus === 'UNAVAILABLE' ? '不可用' : '未检测'

  if (!projectId) {
    return <div className="h-screen flex items-center justify-center text-gray-400">请先在顶部选择项目</div>
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-4 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-bold text-gray-800">OpenUI 原型预览</h1>
        </div>
        <div className="flex items-center gap-3">
          {/* Service status */}
          <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-50 rounded text-sm">
            <span className={`w-2.5 h-2.5 rounded-full ${statusColor}`} />
            <span className="text-gray-600">{statusText}</span>
            <button onClick={checkHealth} className="text-xs text-blue-600 hover:underline ml-1">刷新</button>
          </div>
          <button onClick={() => setShowSetupGuide(true)}
            className="px-3 py-2 border border-gray-300 rounded text-sm hover:bg-gray-50">
            启动指南
          </button>
          <button onClick={handleGenerate} disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:bg-gray-300">
            {loading ? '生成中...' : '生成原型'}
          </button>
        </div>
      </div>

      {/* Fallback banner */}
      {isFallback && (
        <div className="bg-yellow-50 border-b border-yellow-200 px-4 py-2 text-sm text-yellow-800 flex items-center justify-between">
          <span>⚠️ OpenUI 服务不可用，当前为 Wireframe 降级预览，请检查 Docker 状态。</span>
          <div className="flex gap-2">
            <button onClick={() => setShowSetupGuide(true)} className="text-yellow-700 hover:underline text-xs font-medium">查看启动指南</button>
            <button onClick={checkHealth} className="text-yellow-700 hover:underline text-xs font-medium">重试检测</button>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-2 text-sm text-red-700 flex justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-500">✕</button>
        </div>
      )}

      <div className="flex-1 flex overflow-hidden">
        {/* Left sidebar */}
        <div className="w-64 bg-white border-r flex flex-col">
          <div className="px-3 py-2 border-b text-xs font-semibold text-gray-500">页面列表 ({pages.length})</div>
          <div className="flex-1 overflow-auto p-2 space-y-1">
            {pages.length === 0 && <div className="text-center text-gray-400 text-sm py-8">暂无页面，请先生成</div>}
            {pages.map(p => (
              <button key={p.page_id} onClick={() => setSelectedPageId(p.page_id)}
                className={`w-full text-left px-3 py-2 rounded text-sm border transition ${selectedPageId === p.page_id ? 'bg-blue-50 border-blue-300 text-blue-700' : 'border-transparent text-gray-700 hover:bg-gray-50'}`}>
                <div className="font-medium truncate">{p.page_title}</div>
                <div className="text-[10px] text-gray-400 mt-0.5">{p.status}</div>
              </button>
            ))}
          </div>
          {specs.length > 0 && (
            <div className="border-t p-2">
              <div className="text-xs font-semibold text-gray-500 mb-1">会话</div>
              {specs.map(s => (
                <div key={s.spec_id} className="flex items-center justify-between text-xs bg-gray-50 px-2 py-1 rounded mb-1">
                  <span className="truncate">{s.spec_name}</span>
                  <button onClick={() => handleDelete(s.spec_id)} className="text-red-400 hover:text-red-600 ml-1">✕</button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Main preview */}
        <div className="flex-1 bg-gray-100 flex flex-col overflow-hidden">
          {selectedPage ? (
            <>
              {/* Toolbar */}
              <div className="bg-white border-b px-4 py-2 flex items-center justify-between shrink-0">
                <div className="text-sm font-medium text-gray-700">
                  {selectedPage.page_title}
                  <span className="ml-2 text-xs text-gray-400 font-normal">{selectedPage.status}</span>
                </div>
                <div className="flex items-center gap-1 bg-gray-100 rounded p-0.5">
                  {(['desktop', 'tablet', 'mobile'] as Viewport[]).map(v => (
                    <button key={v} onClick={() => setViewport(v)}
                      className={`px-3 py-1 rounded text-xs font-medium transition ${viewport === v ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>
                      {v === 'desktop' ? '桌面' : v === 'tablet' ? '平板' : '手机'}
                    </button>
                  ))}
                </div>
              </div>
              {/* Iframe area */}
              <div className="flex-1 overflow-auto p-4 flex justify-center">
                <div
                  className="bg-white shadow-lg rounded-lg overflow-hidden transition-all duration-300"
                  style={{ width: VIEWPORT_WIDTHS[viewport], maxWidth: '100%' }}
                >
                  {selectedPage.html_content ? (
                    <iframe
                      title={selectedPage.page_title}
                      srcDoc={selectedPage.html_content}
                      className="w-full border-0"
                      style={{ height: viewport === 'mobile' ? '667px' : viewport === 'tablet' ? '1024px' : '800px', minHeight: '500px' }}
                      sandbox="allow-scripts"
                    />
                  ) : (
                    <div className="h-96 flex items-center justify-center text-gray-400 text-sm">无 HTML 内容</div>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-400">请从左侧选择一个页面</div>
          )}
        </div>
      </div>

      <ServiceSetupGuide
        open={showSetupGuide}
        onClose={() => setShowSetupGuide(false)}
        onStartService={() => {
          setServiceStatus('AVAILABLE')
          checkHealth()
        }}
      />
    </div>
  )
}
