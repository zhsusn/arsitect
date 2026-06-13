import { useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router'
import { useArtifactViewerStore } from '../../stores/artifactViewerStore'
import ArtifactTree from './components/ArtifactTree'
import ArtifactPreview from './components/ArtifactPreview'
import VersionHistoryDrawer from './components/VersionHistoryDrawer'

export default function ArtifactViewer() {
  const [searchParams] = useSearchParams()
  const projectId = searchParams.get('project_id') || 'demo-project-001'

  const {
    tree,
    selectedArtifact,
    content,
    contentMeta,
    versions,
    loading,
    searchQuery,
    filterType,
    fetchTree,
    selectArtifact,
    fetchContent,
    saveContent,
    rollback,
    fetchArtifactStatus,
    updateArtifactStatus,
    setSearchQuery,
    setFilterType,
  } = useArtifactViewerStore()

  useEffect(() => {
    void fetchTree(projectId)
  }, [fetchTree, projectId])

  // External deletion detection: poll every 5s for selected artifact
  const selectedArtifactId = selectedArtifact?.artifact_id
  useEffect(() => {
    if (!selectedArtifactId) return
    const interval = setInterval(() => {
      void fetchArtifactStatus(selectedArtifactId).then((status) => {
        if (status) {
          updateArtifactStatus(selectedArtifactId, {
            external_status: status.external_status,
            current_version: status.current_version,
            file_size_bytes: status.file_size_bytes,
          })
        }
      })
    }, 5000)
    return () => clearInterval(interval)
  }, [selectedArtifactId, fetchArtifactStatus, updateArtifactStatus])

  const handleLoadMore = useCallback(() => {
    if (!selectedArtifact) return
    const currentLines = content.split('\n').length
    void fetchContent(selectedArtifact.artifact_id, currentLines, 1000, true)
  }, [selectedArtifact, content, fetchContent])

  const handleSave = useCallback(
    async (artifactId: string, newContent: string, expectedHash?: string) => {
      await saveContent(artifactId, newContent, expectedHash)
    },
    [saveContent]
  )

  const handleRollback = useCallback(
    async (versionNumber: number, backupCurrent: boolean) => {
      if (!selectedArtifact) return
      if (backupCurrent) {
        await saveContent(selectedArtifact.artifact_id, content)
      }
      await rollback(selectedArtifact.artifact_id, versionNumber)
    },
    [selectedArtifact, content, saveContent, rollback]
  )

  return (
    <div className="h-[calc(100vh-80px)] flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200 bg-white">
        <h1 className="text-lg font-semibold text-gray-800 mr-4">产物浏览器</h1>
        <input
          type="text"
          placeholder="搜索文件名..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="flex-1 max-w-xs px-3 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">全部类型</option>
          <option value="md">Markdown</option>
          <option value="yaml">YAML</option>
          <option value="json">JSON</option>
          <option value="mermaid">Mermaid</option>
          <option value="openapi">OpenAPI</option>
          <option value="txt">Text</option>
        </select>
        {selectedArtifact && (
          <VersionHistoryDrawer
            versions={versions}
            onRollback={handleRollback}
            currentVersion={selectedArtifact.current_version}
          />
        )}
      </div>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {loading ? (
          <div className="flex-1 flex items-center justify-center text-gray-500">加载中...</div>
        ) : (
          <>
            <div className="w-1/3 border-r border-gray-200 overflow-hidden bg-white">
              <ArtifactTree
                directories={tree.directories}
                files={tree.files}
                searchQuery={searchQuery}
                filterType={filterType}
                selectedArtifact={selectedArtifact}
                onSelect={selectArtifact}
              />
            </div>
            <div className="w-2/3 overflow-hidden bg-white">
              {selectedArtifact ? (
                <ArtifactPreview
                  artifact={selectedArtifact}
                  content={content}
                  contentMeta={contentMeta}
                  onSave={handleSave}
                  onLoadMore={handleLoadMore}
                />
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400">
                  请选择左侧文件查看内容
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
