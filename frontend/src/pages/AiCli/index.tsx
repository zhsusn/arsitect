import { useCallback, useEffect, useRef, useState } from 'react'
import Terminal, { type TerminalHandle } from '@/components/cli/Terminal'
import CliCard from '@/components/cli/CliCard'
import { useCliSession } from '@/components/cli/hooks/useCliSession'
import type { CliCard as CliCardType, CliMode, CliResponse, SocketStatus } from '@/components/cli/types'

const LS_PROJECT_KEY = 'arsitect:lastProjectId'

const MODES: { value: CliMode; label: string }[] = [
  { value: 'bug', label: 'Bug' },
  { value: 'arch', label: '架构' },
]

const STATUS_LABEL: Record<SocketStatus, string> = {
  connecting: '连接中',
  open: '已连接',
  closed: '已断开',
  error: '连接失败',
}

const STATUS_COLOR: Record<SocketStatus, string> = {
  connecting: '#f59e0b',
  open: '#22c55e',
  closed: '#6b7280',
  error: '#ef4444',
}

export default function AiCliPage() {
  const [projectId] = useState(() => {
    try {
      return localStorage.getItem(LS_PROJECT_KEY) || 'default'
    } catch {
      return 'default'
    }
  })
  const terminalRef = useRef<TerminalHandle>(null)
  const [pendingCard, setPendingCard] = useState<CliCardType | null>(null)
  const [mode, setMode] = useState<CliMode>('bug')

  const handleMessage = useCallback((response: CliResponse) => {
    const term = terminalRef.current
    if (!term) return

    switch (response.type) {
      case 'text':
        if (response.payload?.text) {
          term.write(`\x1b[36m[AI]\x1b[0m ${response.payload.text}\r\n`)
        }
        break
      case 'error':
        term.write(
          `\x1b[31m[错误]\x1b[0m ${response.payload?.error?.message || '未知错误'}\r\n`,
        )
        break
      case 'done':
        term.write(`\x1b[32m[成功]\x1b[0m 任务完成\r\n`)
        break
      case 'progress':
        if (response.payload?.progress) {
          const { current, total, label } = response.payload.progress
          term.write(`\x1b[90m[系统]\x1b[0m ${label || '进度'} ${current}/${total}\r\n`)
        }
        break
      case 'pong':
        break
      default:
        break
    }
    term.write('$ ')
  }, [])

  const handleCard = useCallback((card: CliCardType) => {
    setPendingCard(card)
  }, [])

  const { status, sendCommand, sendAction, clearSession } = useCliSession({
    projectId,
    mode,
    onMessage: handleMessage,
    onCard: handleCard,
  })

  useEffect(() => {
    const hint =
      mode === 'bug'
        ? 'Bug 模式：粘贴异常信息或输入错误描述'
        : '架构模式：输入架构问题或选择治理项'
    terminalRef.current?.write(`\x1b[90m[系统]\x1b[0m ${hint}\r\n$ `)
  }, [mode])

  const handleSubmit = useCallback(
    (line: string) => {
      if (!line.trim()) {
        terminalRef.current?.write('$ ')
        return
      }
      sendCommand(line)
    },
    [sendCommand],
  )

  const handlePasteError = useCallback(async () => {
    try {
      const text = await navigator.clipboard.readText()
      terminalRef.current?.write(`\x1b[37m$ ${text}\x1b[0m\r\n`)
      sendCommand(text)
    } catch {
      terminalRef.current?.write(`\x1b[31m[错误]\x1b[0m 无法读取剪贴板\r\n$ `)
    }
  }, [sendCommand])

  const handleClear = useCallback(() => {
    terminalRef.current?.clear()
    terminalRef.current?.write('$ ')
  }, [])

  const handleCardAction = useCallback(
    (command: string, metadata?: Record<string, unknown>) => {
      sendAction(command, metadata)
      setPendingCard(null)
      terminalRef.current?.write(`\x1b[90m[系统]\x1b[0m 已发送: ${command}\r\n$ `)
    },
    [sendAction],
  )

  const handleModeChange = useCallback((newMode: CliMode) => {
    setMode(newMode)
  }, [])

  return (
    <div style={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '12px 16px',
          borderBottom: '1px solid #e5e7eb',
          background: '#f9fafb',
          borderRadius: '8px 8px 0 0',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <h2 style={{ margin: 0, fontSize: 16 }}>AI CLI 终端</h2>
          <div
            style={{
              display: 'flex',
              background: '#e5e7eb',
              borderRadius: 6,
              padding: 2,
            }}
          >
            {MODES.map((m) => (
              <button
                key={m.value}
                onClick={() => handleModeChange(m.value)}
                style={{
                  padding: '4px 12px',
                  borderRadius: 4,
                  border: 'none',
                  background: mode === m.value ? '#fff' : 'transparent',
                  color: mode === m.value ? '#3b82f6' : '#6b7280',
                  fontSize: 13,
                  fontWeight: 500,
                  cursor: 'pointer',
                  boxShadow: mode === m.value ? '0 1px 2px rgba(0,0,0,0.1)' : 'none',
                }}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 13, color: '#6b7280' }}>
            状态:{' '}
            <span style={{ color: STATUS_COLOR[status] }}>{STATUS_LABEL[status]}</span>
          </span>
          <button
            onClick={clearSession}
            style={{
              padding: '4px 12px',
              borderRadius: 4,
              border: '1px solid #d1d5db',
              background: '#fff',
              color: '#374151',
              fontSize: 13,
              cursor: 'pointer',
            }}
          >
            重连
          </button>
        </div>
      </div>

      {/* Terminal area */}
      <div
        style={{
          flex: 1,
          position: 'relative',
          overflow: 'hidden',
          background: '#0f172a',
          borderRadius: '0 0 8px 8px',
        }}
      >
        <Terminal ref={terminalRef} onSubmit={handleSubmit} />
        {pendingCard && <CliCard card={pendingCard} onAction={handleCardAction} />}
      </div>

      {/* Bottom actions */}
      <div
        style={{
          display: 'flex',
          gap: 8,
          padding: '12px 16px',
          borderTop: '1px solid #e5e7eb',
          background: '#f9fafb',
        }}
      >
        <button
          onClick={handlePasteError}
          style={{
            padding: '6px 14px',
            borderRadius: 4,
            border: '1px solid #d1d5db',
            background: '#fff',
            color: '#374151',
            fontSize: 13,
            cursor: 'pointer',
          }}
        >
          粘贴异常
        </button>
        <button
          onClick={handleClear}
          style={{
            padding: '6px 14px',
            borderRadius: 4,
            border: '1px solid #d1d5db',
            background: '#fff',
            color: '#374151',
            fontSize: 13,
            cursor: 'pointer',
          }}
        >
          清空终端
        </button>
      </div>
    </div>
  )
}
