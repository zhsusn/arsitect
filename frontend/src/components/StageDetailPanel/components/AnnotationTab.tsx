import { useEffect, useState } from 'react'
import { useStageDetailStore } from '../../../stores/stageDetailStore'
import { api } from '../../../services/api'
import type { StageAnnotation } from '../../../types/stage-detail'

const TYPE_OPTIONS = [
  { value: 'P0', label: 'P0 阻塞', color: 'bg-red-100 text-red-700' },
  { value: 'P1', label: 'P1 建议', color: 'bg-amber-100 text-amber-700' },
  { value: 'P2', label: 'P2 优化', color: 'bg-blue-100 text-blue-700' },
  { value: 'question', label: '提问', color: 'bg-purple-100 text-purple-700' },
]

const TYPE_MAP: Record<string, { label: string; color: string }> = {
  P0: { label: 'P0 阻塞', color: 'bg-red-100 text-red-700' },
  P1: { label: 'P1 建议', color: 'bg-amber-100 text-amber-700' },
  P2: { label: 'P2 优化', color: 'bg-blue-100 text-blue-700' },
  question: { label: '提问', color: 'bg-purple-100 text-purple-700' },
  comment: { label: '评论', color: 'bg-gray-100 text-gray-700' },
}

export default function AnnotationTab() {
  const stageId = useStageDetailStore((s) => s.stageId)
  const [annotations, setAnnotations] = useState<StageAnnotation[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [content, setContent] = useState('')
  const [annotationType, setAnnotationType] = useState('P1')
  const [author, setAuthor] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!stageId) return
    let cancelled = false
    setLoading(true)
    setError(null)

    api
      .get<{ data: StageAnnotation[] }>(`/v1/stages/${stageId}/annotations`)
      .then((res) => {
        if (!cancelled) setAnnotations(res.data.data)
      })
      .catch((err) => {
        if (!cancelled) setError(err?.response?.data?.detail || '加载批注失败')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [stageId])

  const handleSubmit = async () => {
    if (!stageId || !content.trim() || !author.trim()) return
    setSubmitting(true)
    try {
      const dto = {
        annotation_id: crypto.randomUUID(),
        author: author.trim(),
        content: content.trim(),
        annotation_type: annotationType,
        status: 'REVIEW_PENDING',
      }
      await api.post(`/v1/stages/${stageId}/annotations`, dto)
      // Refresh
      const res = await api.get<{ data: StageAnnotation[] }>(
        `/v1/stages/${stageId}/annotations`
      )
      setAnnotations(res.data.data)
      setContent('')
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        '提交失败'
      setError(msg)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 2 }).map((_, i) => (
          <div key={i} className="animate-pulse rounded-lg border border-gray-200 p-3">
            <div className="mb-2 h-3 w-20 rounded bg-gray-200" />
            <div className="h-3 w-full rounded bg-gray-200" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col gap-3">
      {/* Create form */}
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
        <div className="mb-2 text-xs font-medium text-gray-600">添加批注</div>
        <div className="mb-2 flex items-center gap-2">
          <input
            type="text"
            placeholder="作者"
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            className="flex-1 rounded-md border border-gray-300 px-2 py-1.5 text-xs outline-none focus:border-blue-500"
          />
          <select
            value={annotationType}
            onChange={(e) => setAnnotationType(e.target.value)}
            className="rounded-md border border-gray-300 px-2 py-1.5 text-xs outline-none focus:border-blue-500"
          >
            {TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        <textarea
          placeholder="输入批注内容..."
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={3}
          className="mb-2 w-full resize-none rounded-md border border-gray-300 px-2 py-1.5 text-xs outline-none focus:border-blue-500"
        />
        <button
          type="button"
          onClick={handleSubmit}
          disabled={submitting || !content.trim() || !author.trim()}
          className="rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {submitting ? '提交中...' : '提交'}
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700">
          {error}
        </div>
      )}

      {/* List */}
      <div className="flex-1 space-y-2 overflow-auto">
        {annotations.length === 0 && (
          <div className="py-6 text-center text-sm text-gray-400">暂无批注</div>
        )}
        {annotations.map((ann) => {
          const typeInfo = TYPE_MAP[ann.annotation_type] || TYPE_MAP.comment
          return (
            <div key={ann.annotation_id} className="rounded-lg border border-gray-200 bg-white p-3">
              <div className="mb-1 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${typeInfo.color}`}>
                    {typeInfo.label}
                  </span>
                  <span className="text-xs font-medium text-gray-700">{ann.author}</span>
                </div>
                <span className="text-[10px] text-gray-400">
                  {ann.annotation_id.slice(0, 8)}
                </span>
              </div>
              <div className="text-xs text-gray-700 whitespace-pre-wrap">{ann.content}</div>
              <div className="mt-1 text-[10px] text-gray-400">状态: {ann.status}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
