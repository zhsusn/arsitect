import { useEffect, useMemo, useState, lazy, Suspense } from 'react'
import { useProjectContext } from '../../../App'
import { fetchArtifacts, type ArtifactSummary } from '../../../services/requirementStudio'
import { getArtifactContent, saveArtifactContent } from '../../../services/artifact'

// Dynamic import for react-md-editor to avoid SSR issues
const MDEditor = lazy(() => import('@uiw/react-md-editor'))

const LoadingEditor = () => (
  <div style={{ padding: 24, color: '#6b7280', textAlign: 'center' }}>编辑器加载中...</div>
)

const ARTIFACT_CATEGORIES = [
  { id: 'all', label: '全部', icon: '📁' },
  { id: 'requirement', label: '需求', icon: '📝' },
  { id: 'design', label: '设计', icon: '🏗️' },
  { id: 'openapi', label: '接口', icon: '🔌' },
  { id: 'test', label: '测试', icon: '🧪' },
  { id: 'code', label: '代码', icon: '💻' },
  { id: 'other', label: '其他', icon: '📎' },
]

const FILE_TYPE_MAP: Record<string, 'markdown' | 'yaml' | 'code'> = {
  requirement: 'markdown',
  design: 'markdown',
  openapi: 'yaml',
  test: 'code',
  code: 'code',
}

interface TerminalMessage {
  time: string
  type: 'info' | 'error' | 'success' | 'warning'
  content: string
}

export default function CodeDevPage() {
  const { currentProjectId } = useProjectContext()
  const projectId = currentProjectId

  const [artifacts, setArtifacts] = useState<ArtifactSummary[]>([])
  const [selectedArtifactId, setSelectedArtifactId] = useState<string | null>(null)
  const [artifactContent, setArtifactContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [_error, setError] = useState<string | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [editContent, setEditContent] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [terminalMessages, setTerminalMessages] = useState<TerminalMessage[]>([])

  // 加载产物列表
  useEffect(() => {
    if (!projectId) return
    setLoading(true)
    fetchArtifacts(projectId)
      .then((data) => {
        const items = Array.isArray(data) ? data : []
        setArtifacts(items)
        if (items.length > 0 && !selectedArtifactId) {
          setSelectedArtifactId(items[0].artifact_id)
        }
        setError(null)
      })
      .catch((err) => {
        setArtifacts([])
        setError(err instanceof Error ? err.message : '加载失败')
      })
      .finally(() => setLoading(false))
  }, [projectId, selectedArtifactId])

  // 加载产物内容
  useEffect(() => {
    if (!projectId || !selectedArtifactId) return
    setLoading(true)
    getArtifactContent(selectedArtifactId)
      .then((content) => {
        setArtifactContent(content)
        setEditContent(content)
        setIsEditing(false)
      })
      .catch((err) => {
        const selected = artifacts.find((a) => a.artifact_id === selectedArtifactId)
        const fallback = selected?.content_preview || `// 文件: ${selected?.file_name || 'unknown'}\n// 加载失败: ${err instanceof Error ? err.message : '未知错误'}`
        setArtifactContent(fallback)
        setEditContent(fallback)
        setError('加载产物内容失败')
      })
      .finally(() => setLoading(false))
  }, [projectId, selectedArtifactId])

  // 连接 SSE 终端
  useEffect(() => {
    if (!projectId) return
    const es = new EventSource(`/api/v1/projects/${projectId}/sse`)
    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        const type = data.type || 'info'
        const content = data.log || event.data
        setTerminalMessages((prev) => [...prev, { time: new Date().toLocaleTimeString(), type, content }])
      } catch {
        setTerminalMessages((prev) => [...prev, { time: new Date().toLocaleTimeString(), type: 'info', content: event.data }])
      }
    }
    return () => { es.close() }
  }, [projectId])

  const filteredArtifacts = useMemo(() => {
    return (Array.isArray(artifacts) ? artifacts : []).filter((a) => {
      const matchCategory = selectedCategory === 'all' || a.file_type === selectedCategory
      const matchSearch = !searchQuery || a.file_name.toLowerCase().includes(searchQuery.toLowerCase())
      return matchCategory && matchSearch
    })
  }, [artifacts, selectedCategory, searchQuery])

  const selectedArtifact = useMemo(() => {
    return artifacts.find((a) => a.artifact_id === selectedArtifactId) || null
  }, [artifacts, selectedArtifactId])

  const artifactType = useMemo(() => {
    if (!selectedArtifact) return 'markdown'
    return FILE_TYPE_MAP[selectedArtifact.file_type] || 'markdown'
  }, [selectedArtifact])

  const handleSave = async () => {
    if (!selectedArtifactId) return
    try {
      await saveArtifactContent(selectedArtifactId, editContent)
      setArtifactContent(editContent)
      setIsEditing(false)
      setTerminalMessages((prev) => [...prev, { time: new Date().toLocaleTimeString(), type: 'success', content: `已保存: ${selectedArtifact?.file_name || selectedArtifactId}` }])
    } catch (err) {
      setError(`保存失败: ${err instanceof Error ? err.message : '未知错误'}`)
      setTerminalMessages((prev) => [...prev, { time: new Date().toLocaleTimeString(), type: 'error', content: `保存失败: ${err instanceof Error ? err.message : '未知错误'}` }])
    }
  }

  const handleCancel = () => {
    setEditContent(artifactContent)
    setIsEditing(false)
  }

  if (!projectId) {
    return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280' }}>请先在顶部选择项目</div>
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#fff', borderRadius: 8, border: '1px solid #e5e7eb', overflow: 'hidden' }}>
      {/* 顶部 */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 16px', borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>代码开发</h2>
          {selectedArtifact && (
            <span style={{ fontSize: 13, color: '#6b7280' }}>
              {selectedArtifact.file_name} ({selectedArtifact.file_type})
            </span>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {isEditing ? (
            <>
              <button onClick={handleSave} style={{ padding: '4px 12px', fontSize: 12, background: '#2563eb', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}>保存</button>
              <button onClick={handleCancel} style={{ padding: '4px 12px', fontSize: 12, background: '#fff', color: '#374151', border: '1px solid #e5e7eb', borderRadius: 4, cursor: 'pointer' }}>取消</button>
            </>
          ) : (
            <button
              onClick={() => setIsEditing(true)}
              disabled={!selectedArtifact}
              style={{ padding: '4px 12px', fontSize: 12, background: '#fff', color: '#2563eb', border: '1px solid #2563eb', borderRadius: 4, cursor: selectedArtifact ? 'pointer' : 'not-allowed' }}
            >
              编辑
            </button>
          )}
        </div>
      </div>

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* 左侧：产物文件树 */}
        <div style={{ width: 260, minWidth: 260, borderRight: '1px solid #e5e7eb', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* 搜索 */}
          <div style={{ padding: '8px 12px', borderBottom: '1px solid #e5e7eb' }}>
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索产物..."
              style={{ width: '100%', padding: '6px 10px', fontSize: 12, border: '1px solid #e5e7eb', borderRadius: 4, boxSizing: 'border-box' }}
            />
          </div>
          {/* 分类 */}
          <div style={{ padding: '6px 12px', borderBottom: '1px solid #e5e7eb', display: 'flex', gap: 4, flexWrap: 'wrap' }}>
            {ARTIFACT_CATEGORIES.map((cat) => {
              const count = cat.id === 'all' ? artifacts.length : artifacts.filter((a) => a.file_type === cat.id).length
              return (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  style={{
                    padding: '3px 8px',
                    fontSize: 11,
                    borderRadius: 4,
                    border: '1px solid #e5e7eb',
                    background: selectedCategory === cat.id ? '#eff6ff' : '#fff',
                    color: selectedCategory === cat.id ? '#2563eb' : '#374151',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 2,
                  }}
                >
                  <span>{cat.icon}</span>
                  <span>{count}</span>
                </button>
              )
            })}
          </div>
          {/* 文件列表 */}
          <div style={{ flex: 1, overflowY: 'auto' }}>
            {loading && <div style={{ padding: 24, textAlign: 'center', color: '#9ca3af', fontSize: 13 }}>加载中...</div>}
            {filteredArtifacts.length === 0 && !loading && (
              <div style={{ padding: 24, textAlign: 'center', color: '#9ca3af', fontSize: 13 }}>暂无产物</div>
            )}
            {filteredArtifacts.map((artifact) => {
              const isSelected = selectedArtifactId === artifact.artifact_id
              const catIcon = ARTIFACT_CATEGORIES.find((c) => c.id === artifact.file_type)?.icon || '📎'
              return (
                <div
                  key={artifact.artifact_id}
                  onClick={() => setSelectedArtifactId(artifact.artifact_id)}
                  style={{
                    padding: '8px 12px',
                    cursor: 'pointer',
                    borderLeft: isSelected ? '3px solid #2563eb' : '3px solid transparent',
                    background: isSelected ? '#eff6ff' : 'transparent',
                    borderBottom: '1px solid #f3f4f6',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                  }}
                >
                  <span style={{ fontSize: 14 }}>{catIcon}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: '#111827', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {artifact.file_name}
                    </div>
                    <div style={{ fontSize: 11, color: '#9ca3af' }}>
                      {artifact.file_type} | {artifact.created_at?.slice(0, 10) || ''}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* 中间：代码预览 */}
        <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          {isEditing && artifactType === 'markdown' ? (
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
          ) : isEditing ? (
            <textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              style={{ flex: 1, padding: 16, fontFamily: 'monospace', fontSize: 13, border: 'none', resize: 'none', lineHeight: 1.5, outline: 'none' }}
            />
          ) : (
            <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
              <ArtifactContent content={artifactContent} type={artifactType} />
            </div>
          )}
        </div>

        {/* 右侧：AI 执行终端 */}
        <div style={{ width: 320, minWidth: 320, borderLeft: '1px solid #e5e7eb', display: 'flex', flexDirection: 'column', overflow: 'hidden', background: '#1f2937' }}>
          <div style={{ padding: '8px 12px', borderBottom: '1px solid #374151', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 12, color: '#e5e7eb', fontWeight: 600 }}>AI 执行终端</span>
            <span style={{ fontSize: 11, color: '#6b7280' }}>{terminalMessages.length} 条消息</span>
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: 12, fontFamily: 'monospace', fontSize: 12, color: '#e5e7eb', lineHeight: 1.6 }}>
            {terminalMessages.length === 0 && (
              <div style={{ color: '#6b7280', textAlign: 'center', marginTop: 24 }}>
                等待 AI 执行...<br />
                <span style={{ fontSize: 11 }}>连接 SSE 实时接收日志</span>
              </div>
            )}
            {terminalMessages.map((msg: TerminalMessage, idx: number) => (
              <div key={idx} style={{ marginBottom: 8, padding: '4px 0', borderBottom: '1px solid #374151' }}>
                <span style={{ color: '#6b7280', fontSize: 11 }}>[{msg.time}]</span>{' '}
                <span style={{ color: msg.type === 'error' ? '#ef4444' : msg.type === 'success' ? '#22c55e' : '#e5e7eb' }}>
                  {msg.content}
                </span>
              </div>
            ))}
          </div>
          <div style={{ padding: '8px 12px', borderTop: '1px solid #374151' }}>
            <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 4 }}>快捷命令</div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {['生成代码', '运行测试', '代码审查', '修复 Bug'].map((cmd) => (
                <button
                  key={cmd}
                  style={{ padding: '3px 8px', fontSize: 11, background: '#374151', color: '#e5e7eb', border: 'none', borderRadius: 4, cursor: 'pointer' }}
                >
                  {cmd}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function ArtifactContent({ content, type }: { content: string; type: 'markdown' | 'yaml' | 'code' }) {
  if (type === 'markdown') {
    return (
      <div style={{ fontSize: 13, lineHeight: 1.6 }}>
        <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontFamily: 'inherit', margin: 0 }}>{content}</pre>
      </div>
    )
  }
  if (type === 'yaml') {
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
          margin: 0,
        }}
      >
        <code>{content}</code>
      </pre>
    )
  }
  // code
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
        margin: 0,
      }}
    >
      <code>{content}</code>
    </pre>
  )
}
