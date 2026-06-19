import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { useStageDetailStore } from '../../../stores/stageDetailStore'
import { api } from '../../../services/api'
import type { StageArtifactDirectory, StageArtifactFile } from '../../../types/stage-detail'

const FILE_TYPE_ICONS: Record<string, string> = {
  md: '📝',
  yaml: '⚙️',
  json: '📋',
  openapi: '🔌',
  mermaid: '📊',
  txt: '📄',
  other: '📦',
}

const FILE_TYPE_LABELS: Record<string, string> = {
  md: 'Markdown',
  yaml: 'YAML',
  json: 'JSON',
  openapi: 'OpenAPI',
  mermaid: 'Mermaid',
  txt: 'Text',
  other: 'Other',
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

export default function ArtifactCardsTab() {
  const stageId = useStageDetailStore((s) => s.stageId)
  const projectId = useStageDetailStore((s) => s.projectId)
  const [directories, setDirectories] = useState<StageArtifactDirectory[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [previewArtifact, setPreviewArtifact] = useState<{
    artifactId: string
    fileName: string
    fileType: string
    content: string
  } | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)

  useEffect(() => {
    if (!stageId) return
    let cancelled = false
    setLoading(true)
    setError(null)

    api
      .get<StageArtifactDirectory[]>(`/v1/stages/${stageId}/artifacts`)
      .then((res) => {
        if (!cancelled) setDirectories(res.data)
      })
      .catch((err) => {
        if (!cancelled) setError(err?.response?.data?.detail || '加载产物列表失败')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [stageId])

  const handleOpenPreview = async (file: StageArtifactFile) => {
    setPreviewLoading(true)
    try {
      const res = await api.get<{ artifact_id: string; content: string }>(
        `/v1/artifacts/${file.artifact_id}/content`
      )
      setPreviewArtifact({
        artifactId: file.artifact_id,
        fileName: file.file_name,
        fileType: file.file_type,
        content: res.data.content,
      })
    } catch (err: unknown) {
      setError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          '预览加载失败'
      )
    } finally {
      setPreviewLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="animate-pulse rounded-lg border border-gray-200 p-3">
            <div className="mb-2 h-4 w-1/3 rounded bg-gray-200" />
            <div className="h-3 w-1/2 rounded bg-gray-200" />
          </div>
        ))}
      </div>
    )
  }

  if (error && !previewArtifact) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        {error}
      </div>
    )
  }

  const allFiles = directories.flatMap((d) => d.files)

  if (allFiles.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-gray-400">
        暂无产物
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {projectId && (
        <div className="flex items-center justify-between">
          <div className="text-xs text-gray-500">
            共 {allFiles.length} 个产物
          </div>
          <Link
            to={`/artifacts?project_id=${projectId}&stage_id=${stageId}`}
            className="text-xs font-medium text-blue-600 hover:text-blue-800"
          >
            在产物浏览器中查看 →
          </Link>
        </div>
      )}
      {directories.map((dir) => (
        <div key={dir.directory}>
          <div className="mb-1 text-xs font-medium text-gray-400">{dir.directory}</div>
          <div className="space-y-2">
            {dir.files.map((file) => (
              <button
                key={file.artifact_id}
                type="button"
                onClick={() => handleOpenPreview(file)}
                className="w-full rounded-lg border border-gray-200 bg-white p-3 text-left shadow-sm transition hover:border-blue-300 hover:shadow"
              >
                <div className="flex items-center gap-2">
                  <span className="text-lg">
                    {FILE_TYPE_ICONS[file.file_type] || FILE_TYPE_ICONS.other}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="truncate text-sm font-medium text-gray-800">
                      {file.file_name}
                    </div>
                    <div className="mt-0.5 flex items-center gap-2 text-xs text-gray-500">
                      <span>{FILE_TYPE_LABELS[file.file_type] || file.file_type}</span>
                      <span>·</span>
                      <span>{formatBytes(file.file_size_bytes)}</span>
                      <span>·</span>
                      <span>v{file.current_version}</span>
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      ))}

      {/* Preview Modal */}
      {previewArtifact && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 p-4">
          <div className="flex max-h-[80vh] w-full max-w-2xl flex-col rounded-lg bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
              <div className="text-sm font-semibold text-gray-800">
                {previewArtifact.fileName}
              </div>
              <button
                type="button"
                onClick={() => setPreviewArtifact(null)}
                className="flex h-8 w-8 items-center justify-center rounded-md text-gray-500 hover:bg-gray-100"
              >
                <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4">
              {previewLoading ? (
                <div className="animate-pulse space-y-2">
                  <div className="h-4 w-full rounded bg-gray-200" />
                  <div className="h-4 w-5/6 rounded bg-gray-200" />
                  <div className="h-4 w-4/6 rounded bg-gray-200" />
                </div>
              ) : (
                <pre className="whitespace-pre-wrap rounded-md bg-gray-50 p-3 text-xs text-gray-700">
                  {previewArtifact.content}
                </pre>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
