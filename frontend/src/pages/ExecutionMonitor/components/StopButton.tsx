import { useState } from 'react'

interface StopButtonProps {
  executionId: string
  status: string
  onStop: (executionId: string) => Promise<void>
}

export default function StopButton({ executionId, status, onStop }: StopButtonProps) {
  const [stopping, setStopping] = useState(false)
  const canStop = status === 'RUNNING' || status === 'NOT_STARTED'

  const handleClick = async () => {
    if (!canStop || stopping) return
    setStopping(true)
    try {
      await onStop(executionId)
    } catch (err: unknown) {
      console.error('停止失败', err instanceof Error ? err.message : err)
    } finally {
      setStopping(false)
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={!canStop || stopping}
      title={canStop ? '停止执行' : '当前状态不可停止'}
      className="px-2 py-1 text-xs font-medium text-red-600 bg-red-50 border border-red-200 rounded hover:bg-red-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
    >
      {stopping ? '停止中...' : '停止'}
    </button>
  )
}
