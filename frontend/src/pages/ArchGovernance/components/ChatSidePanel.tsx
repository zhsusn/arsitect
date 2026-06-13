import { useCallback, useEffect, useRef } from 'react'
import { ChatSession } from '@/components/chat'
import type { ChatCard } from '@/components/chat/types'
import type { C4FixPlanResponse } from '../types'

interface ChatSidePanelProps {
  projectId: string
  plan: C4FixPlanResponse
  onClose: () => void
  onCompleted: () => void
}

export default function ChatSidePanel({ projectId, plan, onClose, onCompleted }: ChatSidePanelProps) {
  const dispatchedRef = useRef(false)

  const handleCardAction = useCallback(
    (command: string, card: ChatCard, metadata?: Record<string, unknown>) => {
      console.log('[ChatSidePanel] action', command, card.type, metadata)
      if (command === 'done') {
        onCompleted()
      }
    },
    [onCompleted],
  )

  useEffect(() => {
    dispatchedRef.current = false
  }, [plan])

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-[480px] max-w-full bg-white shadow-2xl flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <div>
          <h2 className="text-base font-bold text-gray-800">AI 修复助手</h2>
          <p className="text-xs text-gray-500">已加载修复方案，请逐条确认</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onCompleted}
            className="px-3 py-1.5 text-xs rounded bg-blue-600 text-white hover:bg-blue-700"
          >
            完成
          </button>
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 text-xs rounded border hover:bg-gray-50"
          >
            关闭
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
