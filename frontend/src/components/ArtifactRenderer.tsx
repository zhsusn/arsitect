import { useState, useCallback, lazy, Suspense } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

// Dynamic import for react-md-editor to avoid SSR issues
const MDEditor = lazy(() => import('@uiw/react-md-editor'))

const LoadingEditor = () => (
  <div style={{ padding: 24, color: '#6b7280', textAlign: 'center' }}>编辑器加载中...</div>
)

type ArtifactType = 'markdown' | 'swagger' | 'svg' | 'html' | 'yaml'

interface ArtifactRendererProps {
  content: string
  type: ArtifactType
  onEdit?: (content: string) => void
}

export default function ArtifactRenderer({ content, type, onEdit }: ArtifactRendererProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editContent, setEditContent] = useState(content)

  const handleSave = useCallback(() => {
    if (onEdit) {
      onEdit(editContent)
    }
    setIsEditing(false)
  }, [onEdit, editContent])

  const handleCancel = useCallback(() => {
    setEditContent(content)
    setIsEditing(false)
  }, [content])

  if (isEditing && onEdit && type === 'markdown') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div style={{ display: 'flex', gap: 8, padding: '8px 0', justifyContent: 'flex-end' }}>
          <button
            onClick={handleSave}
            style={{
              padding: '6px 12px',
              fontSize: 12,
              background: '#2563eb',
              color: '#fff',
              border: 'none',
              borderRadius: 4,
              cursor: 'pointer',
            }}
          >
            保存
          </button>
          <button
            onClick={handleCancel}
            style={{
              padding: '6px 12px',
              fontSize: 12,
              background: '#fff',
              color: '#374151',
              border: '1px solid #e5e7eb',
              borderRadius: 4,
              cursor: 'pointer',
            }}
          >
            取消
          </button>
        </div>
        <div style={{ flex: 1, overflow: 'auto' }}>
          <Suspense fallback={<LoadingEditor />}>
            <MDEditor
              value={editContent}
              onChange={(val: string | undefined) => setEditContent(val || '')}
              height="100%"
              data-color-mode="light"
            />
          </Suspense>
        </div>
      </div>
    )
  }

  if (isEditing && onEdit) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div style={{ display: 'flex', gap: 8, padding: '8px 0', justifyContent: 'flex-end' }}>
          <button
            onClick={handleSave}
            style={{
              padding: '6px 12px',
              fontSize: 12,
              background: '#2563eb',
              color: '#fff',
              border: 'none',
              borderRadius: 4,
              cursor: 'pointer',
            }}
          >
            保存
          </button>
          <button
            onClick={handleCancel}
            style={{
              padding: '6px 12px',
              fontSize: 12,
              background: '#fff',
              color: '#374151',
              border: '1px solid #e5e7eb',
              borderRadius: 4,
              cursor: 'pointer',
            }}
          >
            取消
          </button>
        </div>
        <textarea
          value={editContent}
          onChange={(e) => setEditContent(e.target.value)}
          style={{
            flex: 1,
            fontFamily: 'monospace',
            fontSize: 13,
            padding: 12,
            border: '1px solid #e5e7eb',
            borderRadius: 4,
            resize: 'none',
            lineHeight: 1.5,
          }}
        />
      </div>
    )
  }

  return (
    <div style={{ position: 'relative', height: '100%' }}>
      {onEdit && (
        <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '8px 0' }}>
          <button
            onClick={() => setIsEditing(true)}
            style={{
              padding: '6px 12px',
              fontSize: 12,
              background: '#fff',
              color: '#2563eb',
              border: '1px solid #2563eb',
              borderRadius: 4,
              cursor: 'pointer',
            }}
          >
            编辑
          </button>
        </div>
      )}
      <div style={{ overflow: 'auto', height: onEdit ? 'calc(100% - 40px)' : '100%' }}>
        <ArtifactContent content={content} type={type} />
      </div>
    </div>
  )
}

function ArtifactContent({ content, type }: { content: string; type: ArtifactType }) {
  switch (type) {
    case 'markdown':
      return (
        <div className="prose max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
        </div>
      )
    case 'swagger':
      return (
        <div
          style={{
            padding: 24,
            textAlign: 'center',
            color: '#6b7280',
            background: '#f9fafb',
            borderRadius: 8,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
          }}
        >
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>Swagger UI Preview</div>
          <p style={{ fontSize: 13 }}>OpenAPI 文档预览占位</p>
        </div>
      )
    case 'svg':
      return (
        <div style={{ padding: 24, display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%' }}>
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: '#6b7280' }}>SVG Preview</div>
          <div dangerouslySetInnerHTML={{ __html: content }} style={{ maxWidth: '100%', overflow: 'auto' }} />
        </div>
      )
    case 'html':
      return (
        <iframe
          srcDoc={content}
          style={{ width: '100%', height: '100%', border: '1px solid #e5e7eb', borderRadius: 4 }}
          sandbox="allow-scripts"
          title="html-preview"
        />
      )
    case 'yaml':
      return (
        <pre
          style={{
            background: '#1f2937',
            color: '#e5e7eb',
            padding: 16,
            borderRadius: 4,
            overflow: 'auto',
            fontSize: 13,
            fontFamily: 'monospace',
            lineHeight: 1.5,
          }}
        >
          <code>{content}</code>
        </pre>
      )
    default:
      return (
        <pre
          style={{
            background: '#f3f4f6',
            padding: 16,
            borderRadius: 4,
            overflow: 'auto',
            fontSize: 13,
            fontFamily: 'monospace',
          }}
        >
          <code>{content}</code>
        </pre>
      )
  }
}
