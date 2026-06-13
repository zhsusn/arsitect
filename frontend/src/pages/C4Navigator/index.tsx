import React, { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router'
import { useC4NavigatorStore } from '../../stores/c4NavigatorStore'
import C4Editor from './components/C4Editor'
import { C4Renderer } from '../../components/C4Renderer'
import NodeDetailPanel from './components/NodeDetailPanel'
import ExportPanel from './components/ExportPanel'
import Breadcrumb from './components/Breadcrumb'

const LEVELS = [
  { key: 'L1', label: 'L1 系统上下文' },
  { key: 'L2', label: 'L2 容器' },
  { key: 'L3', label: 'L3 组件' },
  { key: 'L4', label: 'L4 代码' },
]

const C4Navigator: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>()
  const resolvedProjectId = projectId || 'sdlc-visualizer'

  const {
    dslContent,
    loading,
    error,
    previewLevel,
    currentProjectName,
    selectedNode,
    isNodeDetailOpen,
    exportPanelOpen,
    breadcrumb,
    versions,
    versionsOpen,
    registryStats,
    syncLoading,
    orphanDrawerOpen,
    fetchDslCurrent,
    editDsl,
    listVersions,
    rollback,
    setPreviewLevel,
    fetchProjectName,
    closeNodeDetail,
    openExportPanel,
    closeExportPanel,
    initBreadcrumb,
    openVersionsPanel,
    closeVersionsPanel,
    syncRegistry,
    fetchRegistryStats,
    openOrphanDrawer,
    closeOrphanDrawer,
    toggleOrphanIntentional,
  } = useC4NavigatorStore()

  const [svgContent, setSvgContent] = useState('')
  const [editorContent, setEditorContent] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)
  const [isFullScreen, setIsFullScreen] = useState(false)
  const previewWrapRef = useRef<HTMLDivElement>(null)

  // Fetch project name, DSL and registry stats on mount
  useEffect(() => {
    if (!resolvedProjectId) return
    fetchProjectName(resolvedProjectId)
    fetchDslCurrent(resolvedProjectId)
    fetchRegistryStats(resolvedProjectId)
  }, [resolvedProjectId, fetchProjectName, fetchDslCurrent, fetchRegistryStats])

  // Sync editor content from store
  useEffect(() => {
    setEditorContent(dslContent)
  }, [dslContent])

  // Init breadcrumb when project name is available
  useEffect(() => {
    if (currentProjectName && breadcrumb.length === 0) {
      initBreadcrumb(resolvedProjectId, currentProjectName)
    }
  }, [currentProjectName, breadcrumb.length, resolvedProjectId, initBreadcrumb])

  // Receive SVG from C4Renderer when rendering completes
  const handleRenderComplete = (svgHtml: string | null) => {
    if (svgHtml) {
      setSvgContent(svgHtml)
    }
  }

  const handleSave = async () => {
    await editDsl(resolvedProjectId, editorContent)
  }

  const handleOpenVersions = async () => {
    await listVersions(resolvedProjectId)
    openVersionsPanel()
  }

  const handleRollback = async (version: string) => {
    await rollback(resolvedProjectId, version)
  }

  const toggleFullScreen = () => {
    setIsFullScreen((prev) => !prev)
  }

  return (
    <div className="relative flex flex-col h-[calc(100vh-120px)]">
      {/* Breadcrumb */}
      <Breadcrumb items={breadcrumb} />

      {/* Toolbar — hidden in full-screen mode */}
      {!isFullScreen && (
        <div className="flex items-center gap-2 mb-3 flex-wrap">
          {LEVELS.map((lv) => (
            <button
              key={lv.key}
              onClick={() => setPreviewLevel(lv.key)}
              className={`px-3.5 py-1.5 rounded text-sm border transition-colors ${
                previewLevel === lv.key
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              {lv.label}
            </button>
          ))}

          <div className="ml-auto flex items-center gap-2">
            <button
              onClick={() => {
                syncRegistry(resolvedProjectId).then(() => setRefreshKey((k) => k + 1))
              }}
              disabled={syncLoading || loading}
              className="px-3 py-1.5 rounded text-sm border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
              title="从设计文档和代码重新提取 C4 关系并同步"
            >
              {syncLoading ? '同步中...' : '↻ 重新同步关系'}
            </button>
            <button
              onClick={() => fetchDslCurrent(resolvedProjectId)}
              disabled={loading}
              className="px-3 py-1.5 rounded text-sm border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
            >
              刷新 DSL
            </button>
            <button
              onClick={openOrphanDrawer}
              className="px-3 py-1.5 rounded text-sm border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 transition-colors"
            >
              孤立节点
            </button>
            <button
              onClick={openExportPanel}
              disabled={!svgContent}
              className="px-3 py-1.5 rounded text-sm border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
            >
              导出
            </button>
            <button
              onClick={handleOpenVersions}
              disabled={loading}
              className="px-3 py-1.5 rounded text-sm border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
            >
              版本历史
            </button>
            <button
              onClick={toggleFullScreen}
              className="px-3 py-1.5 rounded text-sm border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 transition-colors"
              title="全屏预览"
            >
              ⛶ 全屏
            </button>
            <button
              onClick={handleSave}
              disabled={loading}
              className="px-3 py-1.5 rounded text-sm bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              保存
            </button>
          </div>
        </div>
      )}

      {/* Registry stats */}
      {registryStats && !isFullScreen && (
        <div className="mb-3 px-3 py-2 bg-gray-50 text-gray-700 text-xs rounded border border-gray-200 flex flex-wrap gap-x-4 gap-y-1">
          <span>组件: <b>{registryStats.components}</b></span>
          <span>关系: <b>{registryStats.relationships}</b></span>
          <span>孤立: <b>{registryStats.orphan_count}</b></span>
          <span>有效孤立: <b className="text-orange-600">{registryStats.effective_orphan_count}</b></span>
          <span> intentional: <b className="text-blue-600">{registryStats.intentional_orphan_count}</b></span>
          <span>接口: <b>{registryStats.interfaces}</b></span>
        </div>
      )}

      {/* Error banner */}
      {error && (
        <div className="mb-3 px-3 py-2 bg-red-50 text-red-800 text-sm rounded border border-red-200">
          {error}
        </div>
      )}

      {/* Main content */}
      <div className={`flex flex-1 gap-4 min-h-0 ${isFullScreen ? 'relative' : ''}`}>
        {!isFullScreen && (
          <div className="flex-1 flex flex-col min-w-0">
            <C4Editor value={editorContent} onChange={setEditorContent} />
          </div>
        )}
        <div className={`min-w-0 ${isFullScreen ? 'flex-1 absolute inset-0 z-10 bg-white' : 'flex-1'}`} ref={previewWrapRef}>
          <C4Renderer
            projectId={resolvedProjectId}
            initialLevel={previewLevel as 'L1' | 'L2' | 'L3' | 'L4'}
            level={previewLevel as 'L1' | 'L2' | 'L3' | 'L4'}
            onLevelChange={(l) => setPreviewLevel(l)}
            hideToolbar={false}
            refreshKey={refreshKey}
            onRenderComplete={handleRenderComplete}
            fullScreen={isFullScreen}
            onToggleFullScreen={toggleFullScreen}
          />
        </div>
      </div>

      {/* Node Detail Panel */}
      <NodeDetailPanel
        node={selectedNode}
        isOpen={isNodeDetailOpen}
        onClose={closeNodeDetail}
        currentLevel={previewLevel}
      />

      {/* Export Panel */}
      <ExportPanel
        isOpen={exportPanelOpen}
        onClose={closeExportPanel}
        svgContent={svgContent}
      />

      {/* Orphan Management Drawer */}
      {orphanDrawerOpen && (
        <div className="fixed inset-y-0 right-0 z-50 w-[420px] bg-white shadow-xl border-l border-gray-200 flex flex-col">
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <h3 className="text-lg font-semibold text-gray-800">
              孤立节点管理
              {registryStats && registryStats.effective_orphan_count > 0 && (
                <span className="ml-2 text-sm font-normal text-orange-600">
                  ({registryStats.effective_orphan_count} 个有效孤立)
                </span>
              )}
            </h3>
            <button
              onClick={closeOrphanDrawer}
              className="text-gray-400 hover:text-gray-600 transition-colors text-2xl leading-none"
              aria-label="关闭"
            >
              ×
            </button>
          </div>
          <div className="flex-1 overflow-auto p-4">
            {!registryStats || registryStats.effective_orphan_count === 0 ? (
              <div className="text-gray-400 text-center py-10">当前没有有效孤立节点</div>
            ) : (
              <ul className="space-y-3">
                {registryStats.orphans
                  .filter((o) => !o.intentional_orphan)
                  .map((orphan) => (
                    <li key={orphan.id} className="px-4 py-3 border rounded hover:bg-gray-50">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <div className="text-sm font-medium text-gray-900 truncate" title={orphan.id}>
                            {orphan.name}
                          </div>
                          <div className="text-xs text-gray-500 mt-0.5 truncate">
                            ID: {orphan.id} · 来源: {orphan.source}
                          </div>
                          {orphan.source_file && (
                            <div className="text-xs text-gray-400 truncate mt-0.5" title={orphan.source_file}>
                              {orphan.source_file}
                            </div>
                          )}
                        </div>
                        <button
                          onClick={() => toggleOrphanIntentional(resolvedProjectId, orphan.id)}
                          className="shrink-0 px-2 py-1 text-xs border border-gray-300 rounded bg-white text-gray-700 hover:bg-gray-50"
                          title="标记为 intentional orphan"
                        >
                          标记豁免
                        </button>
                      </div>
                      {orphan.source_file && (
                        <a
                          href={`vscode://file/${orphan.source_file}`}
                          className="mt-2 inline-block text-xs text-blue-600 hover:underline"
                        >
                          在 VS Code 中打开源文件
                        </a>
                      )}
                    </li>
                  ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {/* Versions Panel */}
      {versionsOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-lg shadow-xl w-[600px] max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
              <h3 className="text-lg font-semibold text-gray-800">版本历史</h3>
              <button
                onClick={closeVersionsPanel}
                className="text-gray-400 hover:text-gray-600 transition-colors text-2xl leading-none"
                aria-label="关闭"
              >
                ×
              </button>
            </div>
            <div className="flex-1 overflow-auto p-5">
              {versions.length === 0 ? (
                <div className="text-gray-400 text-center py-10">暂无版本历史</div>
              ) : (
                <ul className="space-y-3">
                  {versions.map((v) => (
                    <li
                      key={v.version}
                      className="flex items-center justify-between px-4 py-3 border rounded hover:bg-gray-50"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-900">
                          版本 {v.version}
                        </div>
                        <div className="text-xs text-gray-500 mt-0.5">
                          {v.created_at}
                          {v.editor && ` · 编辑者: ${v.editor}`}
                          {v.edit_reason && ` · ${v.edit_reason}`}
                        </div>
                      </div>
                      <button
                        onClick={() => handleRollback(v.version)}
                        disabled={loading}
                        className="ml-3 px-3 py-1 text-sm border border-gray-300 rounded bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
                      >
                        回滚
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default C4Navigator
