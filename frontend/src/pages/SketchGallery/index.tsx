import { useCallback, useEffect, useMemo, useState } from 'react'
import ProjectSelector from '../../components/ProjectSelector'
import {
  listUserStories,
  createUserStory,
  updateUserStory,
  deleteUserStory,
  importUserStoriesFromRequirements,
  type UserStory,
  type UserStoryCreatePayload,
  type UserStoryUpdatePayload,
} from '../../services/userStory'
import {
  listSketches,
  generateSketch,
  generateSketchFromRequirements,
  deleteSketch,
  type Sketch,
} from '../../services/sketch'
import {
  listSketchPages,
  deleteSketchPage,
  updateSketchPage,
  type SketchPage,
} from '../../services/sketchPage'
import {
  createProjectReview,
} from '../../services/projectReview'
import { SketchViewer } from '../../components/SketchViewer'
import SketchReviewPanel from './components/SketchReviewPanel'

const LS_PROJECT_KEY = 'arsitect:lastProjectId'

type ViewMode = 'stories' | 'generate' | 'canvas' | 'review'

interface ValidationReport {
  coverage_percent?: number
  missing_edges?: Array<Record<string, unknown>>
  orphan_pages?: Array<Record<string, unknown>>
  missing_pages?: Array<Record<string, unknown>>
}

export default function SketchGallery() {
  const [projectId, setProjectId] = useState(() => {
    try {
      return localStorage.getItem(LS_PROJECT_KEY) || ''
    } catch {
      return ''
    }
  })
  const [view, setView] = useState<ViewMode>('stories')

  // Stories state
  const [stories, setStories] = useState<UserStory[]>([])
  const [storyLoading, setStoryLoading] = useState(false)

  // Sketch session state
  const [sketches, setSketches] = useState<Sketch[]>([])

  // Pages state (canvas)
  const [pages, setPages] = useState<SketchPage[]>([])
  const [selectedPageId, setSelectedPageId] = useState<string | null>(null)

  // Loading / error
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Create story modal
  const [showCreateStory, setShowCreateStory] = useState(false)
  const [newStory, setNewStory] = useState<UserStoryCreatePayload>({
    title: '',
    description: '',
    page_desc: '',
    priority: 'P1',
    status: 'DRAFT',
  })

  // Edit story modal
  const [editingStory, setEditingStory] = useState<UserStory | null>(null)

  // Generate selection
  const [selectedStoryIds, setSelectedStoryIds] = useState<Set<string>>(new Set())
  const [generateMode, setGenerateMode] = useState<'from-stories' | 'from-requirements'>('from-stories')
  const [lastValidationReport, setLastValidationReport] = useState<ValidationReport | null>(null)

  const loadStories = useCallback(async () => {
    if (!projectId.trim()) return
    setStoryLoading(true)
    try {
      const data = await listUserStories(projectId)
      setStories(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '加载用户故事失败')
    } finally {
      setStoryLoading(false)
    }
  }, [projectId])

  const loadSketches = useCallback(async () => {
    if (!projectId.trim()) return
    try {
      const data = await listSketches(projectId)
      setSketches(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '加载草图失败')
    }
  }, [projectId])

  const loadPages = useCallback(async () => {
    if (!projectId.trim()) return
    try {
      const data = await listSketchPages(projectId)
      setPages(data)
      if (data.length > 0) {
        setSelectedPageId((prev) => prev || data[0].page_id)
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '加载草图页面失败')
    }
  }, [projectId])

  useEffect(() => {
    loadStories()
    loadSketches()
    loadPages()
  }, [loadStories, loadSketches, loadPages])

  const handleCreateStory = async () => {
    if (!projectId.trim() || !newStory.title?.trim()) return
    setLoading(true)
    setError(null)
    try {
      await createUserStory(projectId, newStory)
      setNewStory({
        title: '',
        description: '',
        page_desc: '',
        priority: 'P1',
        status: 'DRAFT',
      })
      setShowCreateStory(false)
      await loadStories()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '创建失败')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateStory = async (storyId: string, payload: UserStoryUpdatePayload) => {
    setLoading(true)
    try {
      await updateUserStory(storyId, payload)
      setEditingStory(null)
      await loadStories()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '更新失败')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteStory = async (id: string) => {
    if (!confirm('确认删除该用户故事?')) return
    try {
      await deleteUserStory(id)
      await loadStories()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '删除失败')
    }
  }

  const handleImportFromRequirements = async () => {
    if (!projectId.trim()) {
      setError('请先选择项目')
      return
    }
    if (!confirm('将从详细需求文档自动导入用户故事，是否继续？')) return
    setLoading(true)
    setError(null)
    try {
      const result = await importUserStoriesFromRequirements(projectId)
      await loadStories()
      setError(`导入完成：成功 ${result.imported_count} 条，跳过 ${result.skipped_count} 条`)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '导入失败')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerate = async () => {
    if (!projectId.trim()) return
    if (selectedStoryIds.size === 0) {
      setError('请至少选择一个用户故事')
      return
    }
    setLoading(true)
    setError(null)
    setLastValidationReport(null)
    try {
      await generateSketch(projectId, {
        story_ids: Array.from(selectedStoryIds),
      })
      await loadSketches()
      await loadPages()
      setView('canvas')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '生成失败')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateFromRequirements = async () => {
    if (!projectId.trim()) return
    setLoading(true)
    setError(null)
    setLastValidationReport(null)
    try {
      const sketch = await generateSketchFromRequirements(projectId, {
        story_ids: selectedStoryIds.size > 0 ? Array.from(selectedStoryIds) : undefined,
      })
      await loadSketches()
      await loadPages()
      if (sketch.validation_report) {
        try {
          setLastValidationReport(JSON.parse(sketch.validation_report) as ValidationReport)
        } catch {
          // ignore parse error
        }
      }
      setView('canvas')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '从详细需求生成失败')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteSketch = async (id: string) => {
    if (!confirm('确认删除该草图会话及其页面?')) return
    try {
      await deleteSketch(id)
      await loadSketches()
      await loadPages()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '删除失败')
    }
  }

  const selectedPage = useMemo(
    () => pages.find((p) => p.page_id === selectedPageId) || null,
    [pages, selectedPageId]
  )

  // Tree navigation: build from nav_targets_json
  const { rootPages, childrenMap } = useMemo(() => {
    // Deduplicate by page_name — keep the most recently updated one
    const latestByName = new Map<string, SketchPage>()
    for (const p of pages) {
      const existing = latestByName.get(p.page_name)
      if (!existing || (p.updated_at || '') > (existing.updated_at || '')) {
        latestByName.set(p.page_name, p)
      }
    }
    const uniquePages = Array.from(latestByName.values())

    const pageByName = new Map(uniquePages.map((p) => [p.page_name, p]))
    const childMap = new Map<string, SketchPage[]>()
    const hasParent = new Set<string>()

    for (const p of uniquePages) {
      let targets: string[] = []
      try {
        targets = p.nav_targets_json ? JSON.parse(p.nav_targets_json) : []
      } catch {
        targets = []
      }
      const children: SketchPage[] = []
      for (const name of targets) {
        const child = pageByName.get(name)
        if (child && child.page_id !== p.page_id) {
          children.push(child)
          hasParent.add(child.page_id)
        }
      }
      if (children.length > 0) {
        childMap.set(p.page_id, children)
      }
    }

    let roots = uniquePages.filter((p) => !hasParent.has(p.page_id))
    if (roots.length === 0 && uniquePages.length > 0) {
      roots = uniquePages
    }
    return { rootPages: roots, childrenMap: childMap }
  }, [pages])

  const [expandedRoots, setExpandedRoots] = useState<Set<string>>(() => new Set<string>())

  const toggleStorySelection = (storyId: string) => {
    setSelectedStoryIds((prev) => {
      const next = new Set(prev)
      if (next.has(storyId)) {
        next.delete(storyId)
      } else {
        next.add(storyId)
      }
      return next
    })
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-4 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-bold text-gray-800">需求草图服务</h1>
          <ProjectSelector
            value={projectId}
            onChange={(id) => {
              setProjectId(id)
              localStorage.setItem(LS_PROJECT_KEY, id)
            }}
          />
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setView('stories')}
            className={`px-3 py-1.5 rounded text-sm font-medium transition ${
              view === 'stories'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            用户故事
          </button>
          <button
            onClick={() => setView('generate')}
            className={`px-3 py-1.5 rounded text-sm font-medium transition ${
              view === 'generate'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            生成草图
          </button>
          <button
            onClick={() => setView('canvas')}
            className={`px-3 py-1.5 rounded text-sm font-medium transition ${
              view === 'canvas'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            草图画布
          </button>
          <button
            onClick={() => setView('review')}
            className={`px-3 py-1.5 rounded text-sm font-medium transition ${
              view === 'review'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            审查
          </button>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-2 text-sm text-red-700 flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700">
            ✕
          </button>
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 overflow-hidden">
        {view === 'stories' && (
          <div className="h-full flex flex-col p-4 gap-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-gray-700">用户故事列表</h2>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleImportFromRequirements}
                  disabled={loading}
                  className="px-4 py-2 bg-emerald-600 text-white rounded text-sm hover:bg-emerald-700 disabled:opacity-50"
                >
                  📥 从需求导入
                </button>
                <button
                  onClick={() => setShowCreateStory(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                >
                  + 新建用户故事
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-auto bg-white rounded-lg border">
              <table className="w-full text-sm text-left">
                <thead className="bg-gray-50 text-gray-600 sticky top-0">
                  <tr>
                    <th className="px-4 py-3 font-medium">标题</th>
                    <th className="px-4 py-3 font-medium">页面描述</th>
                    <th className="px-4 py-3 font-medium">优先级</th>
                    <th className="px-4 py-3 font-medium">状态</th>
                    <th className="px-4 py-3 font-medium text-right">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {storyLoading && (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                        加载中...
                      </td>
                    </tr>
                  )}
                  {!storyLoading && stories.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                        暂无用户故事，点击右上角新建
                      </td>
                    </tr>
                  )}
                  {stories.map((s) => (
                    <tr key={s.story_id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-800">{s.title}</td>
                      <td className="px-4 py-3 text-gray-500 max-w-xs truncate">
                        {s.page_desc || s.description || '-'}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                            s.priority === 'P0'
                              ? 'bg-red-100 text-red-700'
                              : s.priority === 'P1'
                                ? 'bg-orange-100 text-orange-700'
                                : 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          {s.priority}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-500">{s.status}</td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => setEditingStory(s)}
                          className="text-blue-600 hover:text-blue-800 mr-3"
                        >
                          编辑
                        </button>
                        <button
                          onClick={() => handleDeleteStory(s.story_id)}
                          className="text-red-600 hover:text-red-800"
                        >
                          删除
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {view === 'generate' && (
          <div className="h-full flex flex-col p-4 gap-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-gray-700">生成草图</h2>
              {generateMode === 'from-stories' && (
                <button
                  onClick={handleGenerate}
                  disabled={loading || selectedStoryIds.size === 0}
                  className="px-4 py-2 bg-green-600 text-white rounded text-sm hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  {loading ? '生成中...' : `生成草图 (${selectedStoryIds.size})`}
                </button>
              )}
              {generateMode === 'from-requirements' && (
                <button
                  onClick={handleGenerateFromRequirements}
                  disabled={loading}
                  className="px-4 py-2 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  {loading ? '生成中...' : '从详细需求生成'}
                </button>
              )}
            </div>

            {/* Mode tabs */}
            <div className="flex gap-2">
              <button
                onClick={() => setGenerateMode('from-stories')}
                className={`px-3 py-1.5 rounded text-sm font-medium transition ${
                  generateMode === 'from-stories'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                基于用户故事
              </button>
              <button
                onClick={() => setGenerateMode('from-requirements')}
                className={`px-3 py-1.5 rounded text-sm font-medium transition ${
                  generateMode === 'from-requirements'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                基于详细需求
              </button>
            </div>

            {generateMode === 'from-stories' && (
              <div className="flex-1 overflow-auto bg-white rounded-lg border p-4">
                <p className="text-sm text-gray-500 mb-4">
                  选择包含页面描述的用户故事（至少1个），系统将自动生成低保真草图。
                </p>
                <div className="space-y-2">
                  {stories.map((s) => {
                    const hasPageDesc = !!s.page_desc
                    const selected = selectedStoryIds.has(s.story_id)
                    return (
                      <div
                        key={s.story_id}
                        onClick={() => hasPageDesc && toggleStorySelection(s.story_id)}
                        className={`flex items-start gap-3 p-3 rounded border transition ${
                          selected
                            ? 'border-blue-400 bg-blue-50'
                            : hasPageDesc
                              ? 'border-gray-200 hover:border-blue-300 hover:bg-gray-50 cursor-pointer'
                              : 'border-gray-100 bg-gray-50 opacity-60 cursor-not-allowed'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={selected}
                          disabled={!hasPageDesc}
                          onChange={() => {}}
                          className="mt-1"
                        />
                        <div className="flex-1">
                          <div className="font-medium text-gray-800">{s.title}</div>
                          <div className="text-xs text-gray-500 mt-1">
                            {hasPageDesc ? s.page_desc : '无页面描述，无法生成草图'}
                          </div>
                        </div>
                        <span className="text-xs text-gray-400 shrink-0">{s.priority}</span>
                      </div>
                    )
                  })}
                  {stories.length === 0 && (
                    <div className="text-center text-gray-400 py-8">
                      暂无用户故事，请先前往"用户故事"标签页创建
                    </div>
                  )}
                </div>
              </div>
            )}

            {generateMode === 'from-requirements' && (
              <div className="flex-1 overflow-auto bg-white rounded-lg border p-4 flex flex-col gap-4">
                <div className="bg-indigo-50 border border-indigo-100 rounded p-3 text-sm text-indigo-800">
                  <strong>直接从详细需求生成</strong>
                  <p className="mt-1 text-indigo-700">
                    系统将扫描项目目录下的 <code>openspec/changes/*/detailed-requirements/**/module-requirements.md</code>，解析页面清单、字段表和交互规格，自动生成完整的草图页面。
                  </p>
                </div>

                <div>
                  <p className="text-sm text-gray-600 mb-2">
                    可选：勾选用户故事用于路径验证（检查页面跳转是否有断层）
                  </p>
                  <div className="space-y-2 max-h-64 overflow-auto">
                    {stories.map((s) => {
                      const selected = selectedStoryIds.has(s.story_id)
                      return (
                        <div
                          key={s.story_id}
                          onClick={() => toggleStorySelection(s.story_id)}
                          className={`flex items-start gap-3 p-2 rounded border transition cursor-pointer ${
                            selected
                              ? 'border-blue-400 bg-blue-50'
                              : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                          }`}
                        >
                          <input type="checkbox" checked={selected} onChange={() => {}} className="mt-1" />
                          <div className="flex-1">
                            <div className="font-medium text-gray-800 text-sm">{s.title}</div>
                            <div className="text-xs text-gray-500 mt-0.5">{s.page_desc || s.description || '-'}</div>
                          </div>
                          <span className="text-xs text-gray-400 shrink-0">{s.priority}</span>
                        </div>
                      )
                    })}
                    {stories.length === 0 && (
                      <div className="text-center text-gray-400 py-4 text-sm">
                        无用户故事可选，直接生成亦可
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {view === 'review' && (
          <div className="h-full">
            <SketchReviewPanel
              pages={pages}
              onApprove={async (pageId) => {
                try {
                  await updateSketchPage(pageId, { status: 'APPROVED' })
                  setPages((prev) => prev.map((p) => (p.page_id === pageId ? { ...p, status: 'APPROVED' } : p)))
                } catch (err) {
                  setError(`审批通过失败: ${err instanceof Error ? err.message : '未知错误'}`)
                }
              }}
              onReject={async (pageId, reason) => {
                try {
                  await updateSketchPage(pageId, { status: 'REJECTED' })
                  if (projectId) {
                    await createProjectReview(projectId, {
                      review_type: 'code_review',
                      item_id: pageId,
                      item_type: 'sketch_page',
                      status: 'rejected',
                      notes: reason,
                    })
                  }
                  setPages((prev) => prev.map((p) => (p.page_id === pageId ? { ...p, status: 'REJECTED' } : p)))
                } catch (err) {
                  setError(`驳回失败: ${err instanceof Error ? err.message : '未知错误'}`)
                }
              }}
              onAddAnnotation={async (pageId, content) => {
                if (!projectId) return
                try {
                  await createProjectReview(projectId, {
                    review_type: 'code_review',
                    item_id: pageId,
                    item_type: 'sketch_annotation',
                    status: 'pending',
                    notes: content,
                  })
                } catch (err) {
                  setError(`保存批注失败: ${err instanceof Error ? err.message : '未知错误'}`)
                }
              }}
            />
          </div>
        )}

        {view === 'canvas' && (
          <div className="h-full flex">
            {/* Left: page list */}
            <div className="w-64 bg-white border-r flex flex-col">
              <div className="px-4 py-3 border-b font-semibold text-gray-700 text-sm">
                草图页面 ({pages.length})
              </div>
              <div className="flex-1 overflow-auto p-2 space-y-1">
                {pages.length === 0 && (
                  <div className="text-center text-gray-400 text-sm py-8">
                    暂无草图页面，请先生成
                  </div>
                )}
                {rootPages.map((root) => {
                  const children = childrenMap.get(root.page_id) || []
                  const isExpanded = expandedRoots.has(root.page_id)
                  const isSelected = selectedPageId === root.page_id
                  return (
                    <div key={root.page_id}>
                      <div
                        onClick={() => setSelectedPageId(root.page_id)}
                        className={`flex items-center gap-2 px-3 py-2 rounded text-sm cursor-pointer transition border ${
                          isSelected
                            ? 'bg-blue-50 text-blue-700 border-blue-200'
                            : 'text-gray-700 hover:bg-gray-50 border-transparent'
                        }`}
                      >
                        <span
                          className="text-xs text-gray-400 w-4 text-center select-none"
                          onClick={(e) => {
                            if (children.length > 0) {
                              e.stopPropagation()
                              setExpandedRoots((prev) => {
                                const next = new Set(prev)
                                if (next.has(root.page_id)) next.delete(root.page_id)
                                else next.add(root.page_id)
                                return next
                              })
                            }
                          }}
                        >
                          {children.length > 0 ? (isExpanded ? '▼' : '▶') : ''}
                        </span>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium truncate">{root.page_name}</div>
                          <div className="text-xs text-gray-400 mt-0.5">
                            {root.page_type} · {root.status}
                          </div>
                        </div>
                      </div>
                      {isExpanded &&
                        children.map((child) => (
                          <div
                            key={child.page_id}
                            onClick={() => setSelectedPageId(child.page_id)}
                            className={`flex items-center gap-2 pl-9 pr-3 py-2 rounded text-sm cursor-pointer transition mt-1 border ${
                              selectedPageId === child.page_id
                                ? 'bg-blue-50 text-blue-700 border-blue-200'
                                : 'text-gray-600 hover:bg-gray-50 border-transparent'
                            }`}
                          >
                            <span className="text-xs text-gray-300 select-none">└</span>
                            <div className="flex-1 min-w-0">
                              <div className="font-medium truncate">{child.page_name}</div>
                              <div className="text-xs text-gray-400 mt-0.5">
                                {child.page_type} · {child.status}
                              </div>
                            </div>
                          </div>
                        ))}
                    </div>
                  )
                })}
              </div>
              {/* Sketch sessions */}
              <div className="border-t">
                <div className="px-4 py-2 border-b text-xs font-semibold text-gray-500">
                  生成会话
                </div>
                <div className="p-2 space-y-1 max-h-40 overflow-auto">
                  {sketches.map((sk) => (
                    <div
                      key={sk.sketch_id}
                      className="px-2 py-1.5 rounded text-xs bg-gray-50 text-gray-600 flex items-center justify-between"
                    >
                      <span className="truncate">{sk.name}</span>
                      <button
                        onClick={() => handleDeleteSketch(sk.sketch_id)}
                        className="text-red-400 hover:text-red-600 ml-2"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Validation report */}
              {lastValidationReport && (
                <div className="border-t">
                  <div className="px-4 py-2 border-b text-xs font-semibold text-gray-500">
                    路径验证报告
                  </div>
                  <div className="p-2 max-h-48 overflow-auto text-xs space-y-2">
                    <div className="flex justify-between text-gray-600">
                      <span>覆盖率</span>
                      <span className="font-medium">{lastValidationReport.coverage_percent ?? 0}%</span>
                    </div>
                    {Array.isArray(lastValidationReport.missing_edges) && lastValidationReport.missing_edges.length > 0 && (
                      <div>
                        <div className="text-orange-600 font-medium mb-1">缺失跳转 ({lastValidationReport.missing_edges.length})</div>
                        <ul className="space-y-1">
                          {lastValidationReport.missing_edges.map((item: Record<string, unknown>, idx: number) => (
                            <li key={idx} className="text-gray-600 bg-orange-50 rounded px-2 py-1">
                              {String(item.from ?? '?')} → {String(item.to ?? '?')}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {Array.isArray(lastValidationReport.orphan_pages) && lastValidationReport.orphan_pages.length > 0 && (
                      <div>
                        <div className="text-amber-600 font-medium mb-1">孤立页面 ({lastValidationReport.orphan_pages.length})</div>
                        <ul className="space-y-1">
                          {lastValidationReport.orphan_pages.map((item: Record<string, unknown>, idx: number) => (
                            <li key={idx} className="text-gray-600 bg-amber-50 rounded px-2 py-1">
                              {String(item.page ?? '?')}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {Array.isArray(lastValidationReport.missing_pages) && lastValidationReport.missing_pages.length > 0 && (
                      <div>
                        <div className="text-red-600 font-medium mb-1">未知页面 ({lastValidationReport.missing_pages.length})</div>
                        <ul className="space-y-1">
                          {lastValidationReport.missing_pages.map((item: Record<string, unknown>, idx: number) => (
                            <li key={idx} className="text-gray-600 bg-red-50 rounded px-2 py-1">
                              {String(item.page ?? '?')}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {(!lastValidationReport.missing_edges?.length && !lastValidationReport.orphan_pages?.length && !lastValidationReport.missing_pages?.length) && (
                      <div className="text-green-600 bg-green-50 rounded px-2 py-1">✓ 路径完整，无断层</div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Right: canvas */}
            <div className="flex-1 bg-gray-100 flex flex-col">
              {selectedPage ? (
                <>
                  <div className="bg-white border-b px-4 py-2 flex items-center justify-between shrink-0">
                    <div className="text-sm font-medium text-gray-700">
                      {selectedPage.page_name}
                      <span className="ml-2 text-xs text-gray-400 font-normal">
                        {selectedPage.page_type}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={async () => {
                          if (!confirm('确认删除该页面?')) return
                          try {
                            await deleteSketchPage(selectedPage.page_id)
                            await loadPages()
                          } catch (e: unknown) {
                            setError(e instanceof Error ? e.message : '删除失败')
                          }
                        }}
                        className="text-xs text-red-600 hover:text-red-800"
                      >
                        删除页面
                      </button>
                    </div>
                  </div>
                  <div className="flex-1 overflow-auto p-6 flex flex-col">
                    <div className="flex items-center gap-2 mb-2">
                      <button
                        onClick={() => setSelectedPageId(null)}
                        className="text-xs px-2 py-1 bg-gray-100 rounded hover:bg-gray-200"
                      >
                        显示全部草图
                      </button>
                    </div>
                    {selectedPageId === null ? (
                      <SketchViewer projectId={projectId} />
                    ) : selectedPage?.svg_content ? (
                      <div
                        className="bg-white shadow rounded-lg p-4"
                        dangerouslySetInnerHTML={{ __html: selectedPage.svg_content }}
                      />
                    ) : (
                      <div className="text-gray-400 text-sm">该页面无 SVG 内容</div>
                    )}
                  </div>
                  {/* Page meta */}
                  <div className="bg-white border-t px-4 py-2 shrink-0">
                    <div className="text-xs text-gray-500 flex gap-4 flex-wrap">
                      <span>
                        字段:{' '}
                        {selectedPage.fields_json
                          ? JSON.parse(selectedPage.fields_json).length
                          : 0}
                      </span>
                      <span>
                        按钮:{' '}
                        {selectedPage.buttons_json
                          ? JSON.parse(selectedPage.buttons_json).length
                          : 0}
                      </span>
                      <span>
                        跳转:{' '}
                        {selectedPage.nav_targets_json
                          ? JSON.parse(selectedPage.nav_targets_json).join(', ') || '无'
                          : '无'}
                      </span>
                      {selectedPage.source_module_id && (
                        <span className="text-indigo-500">
                          来源: {selectedPage.source_module_id}
                        </span>
                      )}
                    </div>
                  </div>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center text-gray-400">
                  请从左侧选择一个页面
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Create story modal */}
      {showCreateStory && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg p-6">
            <h3 className="text-lg font-bold text-gray-800 mb-4">新建用户故事</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">标题</label>
                <input
                  type="text"
                  value={newStory.title}
                  onChange={(e) => setNewStory((p) => ({ ...p, title: e.target.value }))}
                  className="w-full border rounded px-3 py-2 text-sm"
                  placeholder="例如：作为管理员，我希望..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
                <textarea
                  value={newStory.description || ''}
                  onChange={(e) => setNewStory((p) => ({ ...p, description: e.target.value }))}
                  className="w-full border rounded px-3 py-2 text-sm h-20"
                  placeholder="用户故事详细描述..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  页面描述（用于草图生成）
                </label>
                <textarea
                  value={newStory.page_desc || ''}
                  onChange={(e) => setNewStory((p) => ({ ...p, page_desc: e.target.value }))}
                  className="w-full border rounded px-3 py-2 text-sm h-20"
                  placeholder="描述该故事涉及的页面结构、字段、按钮、跳转等..."
                />
              </div>
              <div className="flex gap-4">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 mb-1">优先级</label>
                  <select
                    value={newStory.priority}
                    onChange={(e) => setNewStory((p) => ({ ...p, priority: e.target.value }))}
                    className="w-full border rounded px-3 py-2 text-sm"
                  >
                    <option value="P0">P0</option>
                    <option value="P1">P1</option>
                    <option value="P2">P2</option>
                    <option value="P3">P3</option>
                  </select>
                </div>
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 mb-1">状态</label>
                  <select
                    value={newStory.status}
                    onChange={(e) => setNewStory((p) => ({ ...p, status: e.target.value }))}
                    className="w-full border rounded px-3 py-2 text-sm"
                  >
                    <option value="DRAFT">DRAFT</option>
                    <option value="ACTIVE">ACTIVE</option>
                  </select>
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowCreateStory(false)}
                className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded"
              >
                取消
              </button>
              <button
                onClick={handleCreateStory}
                disabled={loading || !newStory.title?.trim()}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300"
              >
                {loading ? '保存中...' : '创建'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit story modal */}
      {editingStory && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg p-6">
            <h3 className="text-lg font-bold text-gray-800 mb-4">编辑用户故事</h3>
            <EditStoryForm
              story={editingStory}
              onSave={handleUpdateStory}
              onCancel={() => setEditingStory(null)}
              loading={loading}
            />
          </div>
        </div>
      )}
    </div>
  )
}

function EditStoryForm({
  story,
  onSave,
  onCancel,
  loading,
}: {
  story: UserStory
  onSave: (id: string, payload: UserStoryUpdatePayload) => void
  onCancel: () => void
  loading: boolean
}) {
  const [payload, setPayload] = useState<UserStoryUpdatePayload>({
    title: story.title,
    description: story.description,
    page_desc: story.page_desc,
    priority: story.priority,
    status: story.status,
  })

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">标题</label>
        <input
          type="text"
          value={payload.title || ''}
          onChange={(e) => setPayload((p) => ({ ...p, title: e.target.value }))}
          className="w-full border rounded px-3 py-2 text-sm"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
        <textarea
          value={payload.description || ''}
          onChange={(e) => setPayload((p) => ({ ...p, description: e.target.value }))}
          className="w-full border rounded px-3 py-2 text-sm h-20"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">页面描述</label>
        <textarea
          value={payload.page_desc || ''}
          onChange={(e) => setPayload((p) => ({ ...p, page_desc: e.target.value }))}
          className="w-full border rounded px-3 py-2 text-sm h-20"
        />
      </div>
      <div className="flex gap-4">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">优先级</label>
          <select
            value={payload.priority || 'P1'}
            onChange={(e) => setPayload((p) => ({ ...p, priority: e.target.value }))}
            className="w-full border rounded px-3 py-2 text-sm"
          >
            <option value="P0">P0</option>
            <option value="P1">P1</option>
            <option value="P2">P2</option>
            <option value="P3">P3</option>
          </select>
        </div>
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">状态</label>
          <select
            value={payload.status || 'DRAFT'}
            onChange={(e) => setPayload((p) => ({ ...p, status: e.target.value }))}
            className="w-full border rounded px-3 py-2 text-sm"
          >
            <option value="DRAFT">DRAFT</option>
            <option value="ACTIVE">ACTIVE</option>
          </select>
        </div>
      </div>
      <div className="flex justify-end gap-2 mt-6">
        <button
          onClick={onCancel}
          className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded"
        >
          取消
        </button>
        <button
          onClick={() => onSave(story.story_id, payload)}
          disabled={loading}
          className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300"
        >
          {loading ? '保存中...' : '保存'}
        </button>
      </div>
    </div>
  )
}
