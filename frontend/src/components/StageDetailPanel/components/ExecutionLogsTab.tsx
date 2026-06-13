import { useCallback, useEffect, useRef, useState } from 'react'
import { useStageDetailStore } from '../../../stores/stageDetailStore'
import { api } from '../../../services/api'
import type { StageLogEntry, StageLogResult } from '../../../types/stage-detail'

const LEVEL_STYLES: Record<string, { bg: string; text: string; badge: string }> = {
  INFO: { bg: 'bg-blue-50', text: 'text-blue-700', badge: 'bg-blue-100 text-blue-700' },
  WARN: { bg: 'bg-amber-50', text: 'text-amber-700', badge: 'bg-amber-100 text-amber-700' },
  ERROR: { bg: 'bg-red-50', text: 'text-red-700', badge: 'bg-red-100 text-red-700' },
  DEBUG: { bg: 'bg-gray-50', text: 'text-gray-600', badge: 'bg-gray-100 text-gray-600' },
}

export default function ExecutionLogsTab() {
  const stageId = useStageDetailStore((s) => s.stageId)
  const [logs, setLogs] = useState<StageLogEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [keyword, setKeyword] = useState('')
  const [levelFilter, setLevelFilter] = useState<string>('ALL')
  const [polling, setPolling] = useState(true)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchLogs = useCallback(async () => {
    if (!stageId) return
    try {
      const params = new URLSearchParams()
      if (keyword) params.append('keyword', keyword)
      if (levelFilter !== 'ALL') params.append('level', levelFilter)
      const res = await api.get<StageLogResult>(
        `/v1/stages/${stageId}/logs?${params.toString()}`
      )
      setLogs(res.data.log_entries)
      setError(null)
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        '加载日志失败'
      setError(msg)
    }
  }, [stageId, keyword, levelFilter])

  useEffect(() => {
    if (!stageId) return
    setLoading(true)
    fetchLogs().finally(() => setLoading(false))
  }, [fetchLogs, stageId])

  useEffect(() => {
    if (!polling || !stageId) {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
      return
    }
    timerRef.current = setInterval(() => {
      fetchLogs()
    }, 5000)
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }
  }, [fetchLogs, polling, stageId])

  // Group by skill name (MVP: we don't have skill_name in log entries, so display flat)
  // Future: when logs include skill_name, group by it.

  const filteredLogs = logs.filter((log) => {
    if (levelFilter !== 'ALL' && log.level !== levelFilter) return false
    if (keyword && !log.content.toLowerCase().includes(keyword.toLowerCase())) return false
    return true
  })

  return (
    <div className="flex h-full flex-col">
      {/* Filters */}
      <div className="mb-3 flex items-center gap-2">
        <input
          type="text"
          placeholder="搜索日志关键字..."
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          className="flex-1 rounded-md border border-gray-300 px-3 py-1.5 text-xs outline-none focus:border-blue-500"
        />
        <select
          value={levelFilter}
          onChange={(e) => setLevelFilter(e.target.value)}
          className="rounded-md border border-gray-300 px-2 py-1.5 text-xs outline-none focus:border-blue-500"
        >
          <option value="ALL">全部级别</option>
          <option value="INFO">INFO</option>
          <option value="WARN">WARN</option>
          <option value="ERROR">ERROR</option>
          <option value="DEBUG">DEBUG</option>
        </select>
        <button
          type="button"
          onClick={() => setPolling((p) => !p)}
          className={`rounded-md px-2 py-1.5 text-xs font-medium ${
            polling
              ? 'bg-green-100 text-green-700'
              : 'bg-gray-100 text-gray-600'
          }`}
        >
          {polling ? '轮询中' : '已暂停'}
        </button>
      </div>

      {loading && logs.length === 0 && (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="animate-pulse rounded-md border border-gray-200 p-2">
              <div className="mb-1 h-3 w-16 rounded bg-gray-200" />
              <div className="h-3 w-full rounded bg-gray-200" />
            </div>
          ))}
        </div>
      )}

      {error && (
        <div className="mb-2 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700">
          {error}
        </div>
      )}

      <div className="flex-1 space-y-1 overflow-auto">
        {filteredLogs.length === 0 && !loading && (
          <div className="py-8 text-center text-sm text-gray-400">暂无日志</div>
        )}
        {filteredLogs.map((log, idx) => {
          const style = LEVEL_STYLES[log.level] || LEVEL_STYLES.DEBUG
          return (
            <div
              key={idx}
              className={`rounded-md border border-gray-100 p-2 text-xs ${style.bg}`}
            >
              <div className="mb-1 flex items-center gap-2">
                <span className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${style.badge}`}>
                  {log.level}
                </span>
                <span className="text-gray-400">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <div className={`whitespace-pre-wrap break-words ${style.text}`}>{log.content}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
