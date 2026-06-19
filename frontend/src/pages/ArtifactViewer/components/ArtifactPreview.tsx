import { useState } from 'react'
import ArtifactRenderer from '../../../components/ArtifactRenderer'
import api from '../../../services/api'
import type { ArtifactFile } from '../../../stores/artifactViewerStore'
import ArtifactEditor from './ArtifactEditor'
import ConflictConfirmDialog from './ConflictConfirmDialog'

interface ArtifactPreviewProps {
  artifact: ArtifactFile
  content: string
  contentMeta: { totalLines: number; contentHash: string; isPartial: boolean }
  onSave: (artifactId: string, content: string, expectedHash?: string) => Promise<void>
  onLoadMore: () => void
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

export default function ArtifactPreview({
  artifact,
  content,
  contentMeta,
  onSave,
  onLoadMore,
}: ArtifactPreviewProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [showConflict, setShowConflict] = useState(false)
  const [pendingContent, setPendingContent] = useState('')
  const [showMeta, setShowMeta] = useState(true)
  const [downloading, setDownloading] = useState(false)

  const handleSave = async (newContent: string, expectedHash: string) => {
    try {
      await onSave(artifact.artifact_id, newContent, expectedHash)
      setIsEditing(false)
    } catch (err: unknown) {
      if (err instanceof Error && err.message.startsWith('CONFLICT')) {
        setPendingContent(newContent)
        setShowConflict(true)
      }
    }
  }

  const handleForceOverwrite = async () => {
    setShowConflict(false)
    try {
      await onSave(artifact.artifact_id, pendingContent)
      setIsEditing(false)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '保存失败'
      alert(`保存失败: ${msg}`)
    }
  }

  const handleCancelConflict = () => {
    setShowConflict(false)
    setIsEditing(false)
    window.location.reload()
  }

  const handleDownload = async () => {
    setDownloading(true)
    try {
      const res = await api.get(`/v1/artifacts/${artifact.artifact_id}/download`, {
        responseType: 'blob',
      })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', artifact.file_name)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '下载失败'
      alert(`下载失败: ${msg}`)
    } finally {
      setDownloading(false)
    }
  }

  const handleCopyPath = async () => {
    try {
      await navigator.clipboard.writeText(artifact.file_path)
    } catch {
      alert('复制路径失败')
    }
  }

  const fileType = artifact.file_type
  const renderType: 'markdown' | 'swagger' | 'yaml' =
    fileType === 'openapi'
      ? 'swagger'
      : fileType === 'md' || fileType === 'mermaid' || fileType === 'txt' || fileType === 'other'
        ? 'markdown'
        : 'yaml'
  const isDeleted = artifact.external_status === 'deleted'


  if (isEditing) {
    return (
      <>
        <ArtifactEditor
          artifact={artifact}
          initialContent={content}
          initialHash={contentMeta.contentHash}
          onSave={handleSave}
          onCancel={() => setIsEditing(false)}
        />
        {showConflict && (
          <ConflictConfirmDialog
            onForceOverwrite={handleForceOverwrite}
            onCancel={handleCancelConflict}
          />
        )}
      </>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-sm font-medium text-gray-700 truncate">{artifact.file_name}</span>
          <span className="text-xs text-gray-400 shrink-0">v{artifact.current_version}</span>
          {artifact.stale_flag && (
            <span className="text-xs px-1.5 py-0.5 rounded bg-red-100 text-red-600 shrink-0">
              已过期
            </span>
          )}
          {isDeleted && (
            <span className="text-xs px-1.5 py-0.5 rounded bg-yellow-100 text-yellow-700 shrink-0">
              已删除
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={() => setShowMeta((v) => !v)}
            className="px-3 py-1 text-sm rounded border border-gray-300 hover:bg-gray-100"
          >
            {showMeta ? '隐藏元信息' : '元信息'}
          </button>
          <button
            type="button"
            onClick={handleCopyPath}
            className="px-3 py-1 text-sm rounded border border-gray-300 hover:bg-gray-100"
          >
            复制路径
          </button>
          {!isDeleted && (
            <button
              type="button"
              onClick={handleDownload}
              disabled={downloading}
              className="px-3 py-1 text-sm rounded border border-gray-300 hover:bg-gray-100 disabled:opacity-50"
            >
              {downloading ? '下载中...' : '下载'}
            </button>
          )}
          {!isDeleted && (
            <button
              type="button"
              onClick={() => setIsEditing(true)}
              className="px-3 py-1 text-sm rounded border border-gray-300 hover:bg-gray-100"
            >
              编辑
            </button>
          )}
        </div>
      </div>

      {/* Metadata panel */}
      {showMeta && (
        <div className="px-4 py-2 border-b border-gray-200 bg-gray-50 text-xs text-gray-600">
          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
            <div className="truncate" title={artifact.file_path}>
              <span className="text-gray-400">路径:</span> {artifact.file_path}
            </div>
            <div>
              <span className="text-gray-400">大小:</span> {formatBytes(artifact.file_size_bytes)}
            </div>
            {artifact.stage_id && (
              <div className="truncate">
                <span className="text-gray-400">阶段:</span> {artifact.stage_id}
              </div>
            )}
            {artifact.skill_id && (
              <div className="truncate">
                <span className="text-gray-400">Skill:</span> {artifact.skill_id}
              </div>
            )}
            {artifact.execution_id && (
              <div className="truncate">
                <span className="text-gray-400">执行:</span> {artifact.execution_id}
              </div>
            )}
            <div>
              <span className="text-gray-400">更新:</span>{' '}
              {artifact.updated_at ? new Date(artifact.updated_at).toLocaleString() : '-'}
            </div>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        {isDeleted ? (
          <div className="flex flex-col items-center justify-center h-full text-yellow-600">
            <span className="text-4xl mb-2">⚠️</span>
            <p className="text-lg font-medium">文件已被外部删除</p>
            <p className="text-sm text-gray-500 mt-1">该文件在磁盘上已不存在，但版本历史仍保留</p>
          </div>
        ) : (
          <div className="max-w-none">
            <ArtifactRenderer content={content} type={renderType} />

            {/* Pagination */}
            {contentMeta.isPartial && (
              <div className="mt-4 flex flex-col items-center gap-2 py-4 border-t border-gray-200">
                <p className="text-xs text-gray-500">
                  已加载 {content.split('\n').length} / {contentMeta.totalLines} 行
                </p>
                <button
                  type="button"
                  onClick={onLoadMore}
                  className="px-4 py-2 text-sm rounded border border-gray-300 hover:bg-gray-100"
                >
                  加载更多
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
