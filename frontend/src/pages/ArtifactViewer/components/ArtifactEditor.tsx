import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import mermaid from 'mermaid'
import type { ArtifactFile } from '../../../stores/artifactViewerStore'

interface ArtifactEditorProps {
  artifact: ArtifactFile
  initialContent: string
  initialHash: string
  onSave: (content: string, expectedHash: string) => Promise<void>
  onCancel: () => void
}

function highlightCode(code: string, fileType: string): string {
  let html = code
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  switch (fileType) {
    case 'json':
      html = html
        .replace(/("(?:\\.|[^"\\])*")/g, '<span class="text-green-600">$1</span>')
        .replace(/\b(true|false|null)\b/g, '<span class="text-purple-600">$1</span>')
        .replace(/\b(\d+(?:\.\d+)?)\b/g, '<span class="text-yellow-600">$1</span>')
      break
    case 'yaml':
    case 'openapi':
      html = html
        .replace(/^(#[^\n]*)$/gm, '<span class="text-gray-500">$1</span>')
        .replace(/^([a-zA-Z0-9_-]+)(:)/gm, '<span class="text-blue-600">$1</span>$2')
        .replace(/(: )(.+)/g, '$1<span class="text-green-600">$2</span>')
      break
    case 'md':
      html = html
        .replace(/^(#{1,6}\s+.*)$/gm, '<span class="text-blue-600 font-bold">$1</span>')
        .replace(/(\*\*.*?\*\*)/g, '<span class="text-purple-600 font-bold">$1</span>')
        .replace(/(`[^`]+`)/g, '<span class="text-yellow-600 bg-yellow-50">$1</span>')
        .replace(/^(\s*[-*+]\s+)/gm, '<span class="text-orange-500">$1</span>')
      break
    default:
      break
  }
  return html
}

function validateSyntax(content: string, fileType: string): number[] {
  const errors: number[] = []
  if (fileType === 'json') {
    try {
      JSON.parse(content)
    } catch (e) {
      if (e instanceof SyntaxError && e.message) {
        const match = e.message.match(/line (\d+)/)
        if (match) errors.push(parseInt(match[1], 10))
        else errors.push(1)
      }
    }
  } else if (fileType === 'yaml' || fileType === 'openapi') {
    const lines = content.split('\n')
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      if (line.includes('\t')) {
        errors.push(i + 1)
      }
    }
  }
  return errors
}

export default function ArtifactEditor({
  artifact,
  initialContent,
  initialHash,
  onSave,
  onCancel,
}: ArtifactEditorProps) {
  const [editContent, setEditContent] = useState(initialContent)
  const [saving, setSaving] = useState(false)
  const [errorLines, setErrorLines] = useState<number[]>([])
  const lineNoRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const previewRef = useRef<HTMLDivElement>(null)

  const lines = useMemo(() => editContent.split('\n'), [editContent])
  const lineCount = lines.length

  useEffect(() => {
    mermaid.initialize({ startOnLoad: false })
  }, [])

  useEffect(() => {
    setEditContent(initialContent)
  }, [initialContent])

  useEffect(() => {
    if (artifact.file_type === 'mermaid' && previewRef.current) {
      const nodes = Array.from(previewRef.current.querySelectorAll('.mermaid')) as HTMLElement[]
      if (nodes.length > 0) {
        void mermaid.run({ nodes })
      }
    }
  }, [editContent, artifact.file_type])

  const handleScroll = useCallback(() => {
    if (lineNoRef.current && textareaRef.current) {
      lineNoRef.current.scrollTop = textareaRef.current.scrollTop
    }
  }, [])

  const handleBlur = useCallback(() => {
    const errors = validateSyntax(editContent, artifact.file_type)
    setErrorLines(errors)
  }, [editContent, artifact.file_type])

  const handleSave = async () => {
    setSaving(true)
    try {
      await onSave(editContent, initialHash)
    } catch {
      // Error handled by parent
    } finally {
      setSaving(false)
    }
  }

  const highlighted = useMemo(
    () => highlightCode(editContent, artifact.file_type),
    [editContent, artifact.file_type]
  )

  const renderPreview = () => {
    const ft = artifact.file_type
    if (ft === 'md') {
      return <ReactMarkdown remarkPlugins={[remarkGfm]}>{editContent}</ReactMarkdown>
    }
    if (ft === 'mermaid') {
      return (
        <div ref={previewRef}>
          <div className="mermaid">{editContent}</div>
        </div>
      )
    }
    if (ft === 'yaml' || ft === 'json' || ft === 'openapi') {
      return (
        <pre className="bg-gray-900 text-gray-100 p-4 rounded overflow-auto text-sm font-mono">
          <code>{editContent}</code>
        </pre>
      )
    }
    return (
      <pre className="bg-gray-50 p-4 rounded overflow-auto text-sm font-mono border border-gray-200">
        {editContent}
      </pre>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-sm font-medium text-gray-700 truncate">{artifact.file_name}</span>
          <span className="text-xs text-gray-400 shrink-0">v{artifact.current_version}</span>
          {errorLines.length > 0 && (
            <span className="text-xs px-1.5 py-0.5 rounded bg-red-100 text-red-600 shrink-0">
              语法错误 {errorLines.length} 处
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={onCancel}
            className="px-3 py-1 text-sm rounded border border-gray-300 hover:bg-gray-100"
          >
            取消
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-3 py-1 text-sm rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? '保存中...' : '保存'}
          </button>
        </div>
      </div>

      {/* Dual pane */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Source editor */}
        <div className="w-1/2 border-r border-gray-200 flex flex-col">
          <div className="text-xs px-3 py-1 bg-gray-100 text-gray-500 border-b border-gray-200">源码</div>
          <div className="flex flex-1 overflow-hidden relative">
            {/* Line numbers */}
            <div
              ref={lineNoRef}
              className="w-12 bg-gray-50 text-right pr-2 pt-3 text-gray-400 text-sm select-none overflow-hidden shrink-0"
            >
              {Array.from({ length: lineCount }, (_, i) => (
                <div
                  key={i}
                  className={`leading-6 ${errorLines.includes(i + 1) ? 'text-red-500 bg-red-50' : ''}`}
                >
                  {i + 1}
                </div>
              ))}
            </div>
            {/* Editor with syntax highlight layer */}
            <div className="flex-1 relative">
              <pre
                className="absolute inset-0 m-0 p-3 overflow-hidden whitespace-pre text-sm font-mono leading-6 pointer-events-none"
                aria-hidden="true"
              >
                <code dangerouslySetInnerHTML={{ __html: highlighted }} />
              </pre>
              <textarea
                ref={textareaRef}
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                onScroll={handleScroll}
                onBlur={handleBlur}
                spellCheck={false}
                className="absolute inset-0 w-full h-full p-3 bg-transparent text-transparent caret-black resize-none outline-none text-sm font-mono leading-6"
              />
            </div>
          </div>
        </div>

        {/* Right: Live preview */}
        <div className="w-1/2 flex flex-col overflow-hidden">
          <div className="text-xs px-3 py-1 bg-gray-100 text-gray-500 border-b border-gray-200">实时预览</div>
          <div className="flex-1 overflow-auto p-4">
            {renderPreview()}
          </div>
        </div>
      </div>
    </div>
  )
}
