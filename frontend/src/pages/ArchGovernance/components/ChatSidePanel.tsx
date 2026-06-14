import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { CheckCircle2, X } from 'lucide-react'
import { ChatSession } from '@/components/chat'
import type { ChatCard } from '@/components/chat/types'
import type { C4FixPlanResponse } from '../types'

interface ChatSidePanelProps {
  projectId: string
  plan: C4FixPlanResponse
  onClose: () => void
  onCompleted: () => void
}

export default function ChatSidePanel({
  projectId,
  plan,
  onClose,
  onCompleted,
}: ChatSidePanelProps) {
  const dispatchedRef = useRef(false)

  const totalChanges = useMemo(
    () => plan.plans.reduce((sum, p) => sum + (p.changes?.length || 0), 0),
    [plan],
  )

  const requiresConfirmationCount = useMemo(
    () =>
      plan.plans.reduce(
        (sum, p) => sum + (p.changes?.filter((c) => c.requires_confirmation).length || 0),
        0,
      ),
    [plan],
  )

  const [resolvedKeys, setResolvedKeys] = useState<Set<string>>(new Set())
  const pendingCount = Math.max(0, requiresConfirmationCount - resolvedKeys.size)

  const getCardKey = useCallback((card: ChatCard) => {
    const d = card.data || {}
    return `${d.issue_id || ''}-${d.target_path || ''}-${d.action || ''}`
  }, [])

  const handleCardAction = useCallback(
    (command: string, card: ChatCard) => {
      if (card.type === 'arch-decision' && command !== 'edit') {
        setResolvedKeys((prev) => new Set(prev).add(getCardKey(card)))
      }
      console.log('[ChatSidePanel] action', command, card.type, card.data)
    },
    [getCardKey],
  )

  const confirmIfPending = useCallback(
    (callback: () => void) => {
      if (pendingCount > 0) {
        const ok = window.confirm(
          `还有 ${pendingCount} 条变更待确认，关闭面板后将不再通过此处执行。是否继续？`,
        )
        if (!ok) return
      }
      callback()
    },
    [pendingCount],
  )

  const handleClose = useCallback(() => {
    confirmIfPending(onClose)
  }, [confirmIfPending, onClose])

  const handleCompleted = useCallback(() => {
    confirmIfPending(onCompleted)
  }, [confirmIfPending, onCompleted])

  useEffect(() => {
    dispatchedRef.current = false
  }, [plan])

  const subtitle = useMemo(() => {
    if (requiresConfirmationCount === 0) {
      return totalChanges > 0 ? '系统将自动执行全部变更' : '暂无需要执行的变更'
    }
    return `共 ${totalChanges} 条变更，待确认 ${pendingCount}/${requiresConfirmationCount} 条`
  }, [totalChanges, requiresConfirmationCount, pendingCount])

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-[520px] max-w-full bg-white shadow-2xl flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gray-900 flex items-center justify-center">
            <span className="text-white text-xs font-bold">AI</span>
          </div>
          <div>
            <h2 className="text-sm font-bold text-gray-800">AI 修复助手</h2>
            <p className="text-xs text-gray-500">{subtitle}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleCompleted}
            className="inline-flex items-center gap-1 px-3 py-1.5 text-xs rounded-lg bg-gray-900 text-white hover:bg-gray-800"
          >
            <CheckCircle2 size={14} />
            完成
          </button>
          <button
            type="button"
            onClick={handleClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-200"
          >
            <X size={18} />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        <ChatSession
          projectId={projectId}
          taskMode="arch-fix"
          initialProvider="kimi-cli"
          placeholder="确认修复方案或输入补充说明"
          autoSend={{
            text: 'apply_arch_fix_plan',
            metadata: {
              action: 'apply_arch_fix_plan',
              project_id: projectId,
              plan,
              strategy_prompt: plan.strategy_prompt || '',
            },
          }}
          onCardAction={handleCardAction}
        />
      </div>
    </div>
  )
}
