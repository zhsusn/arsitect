import { useEffect, useCallback, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router'
import { useArtifactViewerStore } from '../../stores/artifactViewerStore'
import {
  fetchStageProgress,
  type StageProgressItem,
} from '../../services/stage'
import ArtifactTree from './components/ArtifactTree'
import ArtifactPreview from './components/ArtifactPreview'
import VersionHistoryDrawer from './components/VersionHistoryDrawer'

export default function ArtifactViewer() {
  const [searchParams] = useSearchParams()
  const projectId = searchParams.get('project_id') || 'demo-project-001'
  const initialArtifactId = searchParams.get('artifact_id')

  const [stageMap, setStageMap] = useState<Record<string, StageProgressItem>>({})

  const {
    tree,
    selectedArtifact,
    content,
    contentMeta,
    versions,
    loading,
    searchQuery,
    filterType,
    filterStage,
    filterSkill,
    fetchTree,
    selectArtifact,
    findArtifactById,
    fetchContent,
    saveContent,
    rollback,
    fetchArtifactStatus,
    updateArtifactStatus,
    setSearchQuery,
    setFilterType,
    setFilterStage,
    setFilterSkill,
  } = useArtifactViewerStore()

  // Load tree and stage metadata
  useEffect(() => {
    void fetchTree(projectId)
    fetchStageProgress(projectId)
      .then((progress) => {
        const map: Record<string, StageProgressItem> = {}
        progress.stages.forEach((s) => {
          map[s.project_stage_id] = s
        })
        setStageMap(map)
      })
      .catch((err) => {
        console.error('Failed to load stage progress:', err)
      })
  }, [fetchTree, projectId])

  // Auto-select artifact from URL query
  useEffect(() => {
    if (!initialArtifactId || loading || !tree?.files?.length) return
    const artifact = findArtifactById(initialArtifactId)
    if (artifact) {
      selectArtifact(artifact)
    }
  }, [initialArtifactId, loading, tree?.files?.length, findArtifactById, selectArtifact])

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

  const stageOptions = useMemo(() => {
    const ids = Array.from(new Set((tree?.files || []).map((f) => f.stage_id).filter(Boolean)))
    return ids.map((id) => ({
      value: id as string,
      label: stageMap[id as string]?.business_stage_key || id,
    }))
  }, [tree?.files, stageMap])

  const skillOptions = useMemo(() => {
    return Array.from(new Set((tree?.files || []).map((f) => f.skill_id).filter(Boolean))) as string[]
  }, [tree?.files])

  const handleRefresh = useCallback(() => {
    void fetchTree(projectId)
  }, [fetchTree, projectId])

  return (
    <div className="h-[calc(100vh-80px)] flex flex-col">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3 px-4 py-3 border-b border-gray-200 bg-white">
        <h1 className="text-lg font-semibold text-gray-800 mr-4">产物浏览器</h1>
        <input
          type="text"
          placeholder="搜索文件名..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="flex-1 min-w-[120px] max-w-xs px-3 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
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
        <select
          value={filterStage}
          onChange={(e) => {
            setFilterStage(e.target.value)
            void fetchTree(projectId, { stageId: e.target.value })
          }}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">全部阶段</option>
          {stageOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <select
          value={filterSkill}
          onChange={(e) => {
            setFilterSkill(e.target.value)
            void fetchTree(projectId, { skillId: e.target.value })
          }}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">全部 Skill</option>
          {skillOptions.map((id) => (
            <option key={id} value={id}>
              {id}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={handleRefresh}
          className="px-3 py-1.5 text-sm rounded border border-gray-300 hover:bg-gray-100"
        >
          刷新
        </button>
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
                directories={tree?.directories || []}
                files={tree?.files || []}
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
