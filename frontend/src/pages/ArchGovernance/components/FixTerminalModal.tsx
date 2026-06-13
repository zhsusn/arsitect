import { useCallback, useEffect, useRef, useState } from 'react'
import Terminal, { type TerminalHandle } from '@/components/cli/Terminal'
import CliCard from '@/components/cli/CliCard'
import { useCliSession } from '@/components/cli/hooks/useCliSession'
import type { CliCard as CliCardType, CliResponse, SocketStatus } from '@/components/cli/types'
import type { C4FixPlanResponse, C4ChangeSet } from '../types'

interface FixTerminalModalProps {
  projectId: string
  plan: C4FixPlanResponse
  onClose: () => void
  onCompleted: () => void
}

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

export default function FixTerminalModal({ projectId, plan, onClose, onCompleted }: FixTerminalModalProps) {
  const terminalRef = useRef<TerminalHandle>(null)
  const [pendingCard, setPendingCard] = useState<CliCardType | null>(null)
  const [editingChange, setEditingChange] = useState<C4ChangeSet | null>(null)
  const [editValue, setEditValue] = useState('')
  const [isDone, setIsDone] = useState(false)
  const dispatchedRef = useRef(false)

  const handleMessage = useCallback((response: CliResponse) => {
    const term = terminalRef.current
    if (!term) return

    switch (response.type) {
      case 'text':
        if (response.payload?.text) {
          term.write(`\x1b[36m[AI]\x1b[0m ${response.payload.text}\r\n`)
        }
        break
      case 'thinking':
        if (response.payload?.text) {
          term.write(`\x1b[35m[思考]\x1b[0m ${response.payload.text}\r\n`)
        }
        break
      case 'error':
        term.write(
          `\x1b[31m[错误]\x1b[0m ${response.payload?.error?.message || '未知错误'}\r\n`,
        )
        break
      case 'done':
        term.write(`\x1b[32m[成功]\x1b[0m 修复计划处理完成\r\n`)
        setIsDone(true)
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
    if (card.type === 'arch-decision') {
      setPendingCard(card)
    }
  }, [])

  const { status, sendCommand, sendAction, clearSession } = useCliSession({
    projectId,
    mode: 'arch',
    onMessage: handleMessage,
    onCard: handleCard,
  })

  useEffect(() => {
    if (status !== 'open' || dispatchedRef.current) return
    dispatchedRef.current = true
    terminalRef.current?.write(`\x1b[90m[系统]\x1b[0m 已加载确认后的修复方案，开始推送治理卡片\r\n$ `)
    sendCommand('apply_arch_fix_plan', {
      action: 'apply_arch_fix_plan',
      project_id: projectId,
      plan,
      strategy_prompt: plan.strategy_prompt || '',
    })
  }, [status, projectId, plan, sendCommand])

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

  const handleCardAction = useCallback(
    (command: string, metadata?: Record<string, unknown>) => {
      const change = metadata?.change as C4ChangeSet | undefined
      if (!change) return

      if (command === 'edit') {
        setEditingChange(change)
        setEditValue(change.after || '')
        return
      }

      if (command === 'fix' && change.risk_level === 'HIGH') {
        const confirmed = window.confirm(
          `该变更为 HIGH 风险：\n${change.rationale}\n\n确认执行吗？`
        )
        if (!confirmed) return
      }

      sendAction(command, {
        change,
        project_id: projectId,
        strategy_prompt: plan.strategy_prompt || '',
      })
      setPendingCard(null)
      terminalRef.current?.write(`\x1b[90m[系统]\x1b[0m 已发送: ${command}\r\n$ `)
    },
    [sendAction, projectId, plan.strategy_prompt],
  )

  const handleEditSubmit = useCallback(() => {
    if (!editingChange) return
    sendAction('edit', {
      change: editingChange,
      edited_after: editValue,
      project_id: projectId,
      strategy_prompt: plan.strategy_prompt || '',
    })
    setEditingChange(null)
    setPendingCard(null)
    terminalRef.current?.write(`\x1b[90m[系统]\x1b[0m 已发送: edit\r\n$ `)
  }, [editingChange, editValue, projectId, sendAction, plan.strategy_prompt])

  const handleClear = useCallback(() => {
    terminalRef.current?.clear()
    terminalRef.current?.write('$ ')
  }, [])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-5xl h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-4 py-3">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-bold text-gray-800">AI CLI 修复终端</h2>
            <span className="text-sm text-gray-500">
              状态: <span style={{ color: STATUS_COLOR[status] }}>{STATUS_LABEL[status]}</span>
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={clearSession}
              className="px-3 py-1.5 text-sm rounded border hover:bg-gray-50"
            >
              重连
            </button>
            <button
              onClick={handleClear}
              className="px-3 py-1.5 text-sm rounded border hover:bg-gray-50"
            >
              清空
            </button>
            <button
              onClick={onClose}
              className="px-3 py-1.5 text-sm rounded bg-blue-600 text-white hover:bg-blue-700"
            >
              关闭
            </button>
          </div>
        </div>

        {/* Terminal area */}
        <div className="flex-1 relative overflow-hidden bg-slate-900 rounded-b-lg">
          <Terminal ref={terminalRef} onSubmit={handleSubmit} />
          {pendingCard && !editingChange && !isDone && (
            <CliCard card={pendingCard} onAction={handleCardAction} />
          )}

          {/* Completion overlay */}
          {isDone && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80 z-20">
              <div className="bg-white rounded-lg shadow-xl p-6 max-w-md text-center">
                <div className="text-4xl mb-3">✅</div>
                <h3 className="text-lg font-bold text-gray-800 mb-2">修复计划已处理完成</h3>
                <p className="text-sm text-gray-600 mb-4">
                  所有变更卡片已推送至终端。关闭后将刷新治理分析结果。
                </p>
                <div className="flex justify-center gap-3">
                  <button
                    onClick={onClose}
                    className="px-4 py-2 text-sm rounded border hover:bg-gray-50"
                  >
                    暂不关闭
                  </button>
                  <button
                    onClick={onCompleted}
                    className="px-4 py-2 text-sm rounded bg-blue-600 text-white hover:bg-blue-700"
                  >
                    完成并关闭
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Inline edit overlay */}
          {editingChange && (
            <div className="absolute inset-x-4 bottom-20 bg-white border rounded-lg shadow-xl p-4 max-h-[60%] overflow-auto">
              <div className="text-sm font-semibold text-gray-800 mb-2">
                编辑变更: {editingChange.target_path}
              </div>
              <textarea
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                className="w-full h-48 p-2 text-xs font-mono border rounded bg-gray-50"
                spellCheck={false}
              />
              <div className="flex justify-end gap-2 mt-3">
                <button
                  onClick={() => setEditingChange(null)}
                  className="px-3 py-1.5 text-sm rounded border hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handleEditSubmit}
                  className="px-3 py-1.5 text-sm rounded bg-blue-600 text-white hover:bg-blue-700"
                >
                  保存并执行
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
