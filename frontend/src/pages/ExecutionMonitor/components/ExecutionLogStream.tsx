import { useEffect, useRef, useState, useCallback } from 'react'
import { api } from '@/services/api'
import { useProjectSSE } from '@/hooks/useProjectSSE'
import type { LogEntry, LogQueryResult, SkillExecution } from '@/types/skill-execution'

interface ExecutionLogStreamProps {
  executionId: string
}

const levelColors: Record<LogEntry['level'], string> = {
  INFO: '#2563eb',
  WARN: '#ca8a04',
  ERROR: '#dc2626',
  DEBUG: '#6b7280',
}

const levelBgColors: Record<LogEntry['level'], string> = {
  INFO: '#eff6ff',
  WARN: '#fefce8',
  ERROR: '#fef2f2',
  DEBUG: '#f3f4f6',
}

export default function ExecutionLogStream({ executionId }: ExecutionLogStreamProps) {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [filterLevel, setFilterLevel] = useState<string>('ALL')
  const [searchKeyword, setSearchKeyword] = useState('')
  const [isPaused, setIsPaused] = useState(false)
  const [anchor, setAnchor] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [projectId, setProjectId] = useState<string | undefined>(undefined)
  const containerRef = useRef<HTMLDivElement>(null)
  const isPausedRef = useRef(isPaused)

  useEffect(() => {
    isPausedRef.current = isPaused
  }, [isPaused])

  const fetchLogs = useCallback(async () => {
    setIsLoading(true)
    try {
      const params = anchor ? { anchor } : {}
      const res = await api.get<LogQueryResult>(`/v1/executions/${executionId}/logs`, {
        params,
      })
      const data = res.data
      if (data.log_entries.length > 0) {
        setLogs((prev) => [...prev, ...data.log_entries])
      }
      if (data.next_anchor) {
        setAnchor(data.next_anchor)
      }
    } catch (err: unknown) {
      console.error('获取日志失败', err instanceof Error ? err.message : err)
    } finally {
      setIsLoading(false)
    }
  }, [executionId, anchor])

  // Resolve project id for SSE subscription.
  useEffect(() => {
    let cancelled = false
    api
      .get<SkillExecution>(`/v1/executions/${executionId}`)
      .then((res) => {
        if (!cancelled) setProjectId(res.data.project_id)
      })
      .catch((err) => console.error('Failed to load execution project id:', err))
    return () => {
      cancelled = true
    }
  }, [executionId])

  useEffect(() => {
    fetchLogs()
  }, [fetchLogs])

  useProjectSSE(projectId, fetchLogs)

  useEffect(() => {
    if (isPausedRef.current) return
    const el = containerRef.current
    if (el) {
      el.scrollTop = el.scrollHeight
    }
  }, [logs])

  const filteredLogs = logs.filter((log) => {
    if (filterLevel !== 'ALL' && log.level !== filterLevel) {
      return false
    }
    if (searchKeyword && !log.content.toLowerCase().includes(searchKeyword.toLowerCase())) {
      return false
    }
    return true
  })

  const handleDownload = () => {
    const lines = filteredLogs.map(
      (log) => `${new Date(log.timestamp).toISOString()} [${log.level}] ${log.content}`,
    )
    const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `execution-${executionId}.log`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div style={{ border: '1px solid #e5e7eb', borderRadius: 8, background: '#fff' }}>
      <div
        style={{
          display: 'flex',
          gap: 12,
          padding: '12px 16px',
          borderBottom: '1px solid #e5e7eb',
          alignItems: 'center',
          flexWrap: 'wrap',
        }}
      >
        <strong style={{ fontSize: 14 }}>实时日志</strong>
        <select
          value={filterLevel}
          onChange={(e) => setFilterLevel(e.target.value)}
          style={{ padding: '4px 8px', fontSize: 13 }}
        >
          <option value="ALL">全部级别</option>
          <option value="INFO">INFO</option>
          <option value="WARN">WARN</option>
          <option value="ERROR">ERROR</option>
          <option value="DEBUG">DEBUG</option>
        </select>
        <input
          type="text"
          placeholder="搜索关键词..."
          value={searchKeyword}
          onChange={(e) => setSearchKeyword(e.target.value)}
          style={{ padding: '4px 8px', fontSize: 13, flex: 1, minWidth: 120 }}
        />
        <button
          onClick={handleDownload}
          className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors"
        >
          下载日志
        </button>
        <span style={{ fontSize: 12, color: '#6b7280' }}>
          {isPaused ? '已暂停自动滚动' : '自动滚动中'}
        </span>
      </div>

      <div
        ref={containerRef}
        onMouseEnter={() => setIsPaused(true)}
        onMouseLeave={() => setIsPaused(false)}
        style={{
          height: 400,
          overflowY: 'auto',
          padding: '8px 12px',
          fontFamily: 'monospace',
          fontSize: 13,
          lineHeight: 1.6,
          background: '#f9fafb',
        }}
      >
        {filteredLogs.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#9ca3af', padding: 24 }}>
            {isLoading ? '加载中...' : '暂无日志'}
          </div>
        ) : (
          filteredLogs.map((log, idx) => (
            <div
              key={`${log.timestamp}-${idx}`}
              style={{
                display: 'flex',
                gap: 8,
                alignItems: 'flex-start',
                padding: '4px 0',
                borderBottom: '1px solid #f3f4f6',
              }}
            >
              <span style={{ color: '#9ca3af', whiteSpace: 'nowrap', minWidth: 160 }}>
                {new Date(log.timestamp).toLocaleString()}
              </span>
              <span
                style={{
                  padding: '0 6px',
                  borderRadius: 4,
                  fontSize: 11,
                  fontWeight: 600,
                  color: levelColors[log.level],
                  background: levelBgColors[log.level],
                  whiteSpace: 'nowrap',
                }}
              >
                {log.level}
              </span>
              <span style={{ color: '#374151', wordBreak: 'break-all' }}>{log.content}</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
