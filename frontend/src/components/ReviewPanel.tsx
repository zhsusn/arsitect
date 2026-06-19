import { useState } from 'react'

export interface Annotation {
  id: string
  text: string
  author?: string
  createdAt?: string
}

interface ReviewPanelProps {
  annotations: Annotation[]
  onSubmit: (comment: string) => void
}

export default function ReviewPanel({ annotations, onSubmit }: ReviewPanelProps) {
  const [comment, setComment] = useState('')

  const handleSubmit = () => {
    if (!comment.trim()) return
    onSubmit(comment.trim())
    setComment('')
  }

  return (
    <div style={{ borderTop: '1px solid #e5e7eb', padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: '#111827' }}>审查批注</div>
      <div style={{ maxHeight: 160, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 8 }}>
        {annotations.length === 0 && <div style={{ fontSize: 12, color: '#9ca3af' }}>暂无批注</div>}
        {annotations.map((a) => (
          <div key={a.id} style={{ padding: 8, background: '#f9fafb', borderRadius: 4, fontSize: 12, color: '#374151' }}>
            <div style={{ fontWeight: 500, marginBottom: 2 }}>{a.author || '匿名'}</div>
            <div>{a.text}</div>
          </div>
        ))}
      </div>
      <textarea
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        placeholder="输入批注..."
        style={{
          width: '100%',
          padding: 8,
          fontSize: 12,
          border: '1px solid #e5e7eb',
          borderRadius: 4,
          resize: 'none',
          minHeight: 60,
          fontFamily: 'inherit',
        }}
      />
      <button
        onClick={handleSubmit}
        disabled={!comment.trim()}
        style={{
          padding: '6px 12px',
          fontSize: 12,
          background: comment.trim() ? '#2563eb' : '#e5e7eb',
          color: comment.trim() ? '#fff' : '#9ca3af',
          border: 'none',
          borderRadius: 4,
          cursor: comment.trim() ? 'pointer' : 'not-allowed',
        }}
      >
        提交审查
      </button>
    </div>
  )
}
