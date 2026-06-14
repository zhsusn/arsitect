import { useCallback, useEffect, useRef, useState } from 'react'
import ChatComposer from './ChatComposer'
import MessageList from './MessageList'
import { useChatSession } from './useChatSession'
import type { ChatCard, ChatMessage, LLMProviderOption } from './types'

interface ChatSessionProps {
  projectId: string
  sessionId?: string
  taskMode?: string
  initialProvider?: LLMProviderOption
  placeholder?: string
  autoSend?: { text: string; metadata?: Record<string, unknown> }
  onCardAction?: (command: string, card: ChatCard, metadata?: Record<string, unknown>) => void
  onMessage?: (message: ChatMessage) => void
}

export default function ChatSession({
  projectId,
  sessionId,
  taskMode,
  initialProvider = 'kimi-cli',
  placeholder,
  autoSend,
  onCardAction,
  onMessage,
}: ChatSessionProps) {
  const [provider, setProvider] = useState<LLMProviderOption>(initialProvider)
  const [agentMode, setAgentMode] = useState(false)

  const { status, messages, sendCommand, sendAction } = useChatSession({
    projectId,
    sessionId,
    taskMode,
    llmProvider: provider,
    onMessage,
  })

  const handleCardActionWrapper = useCallback(
    (command: string, card: ChatCard, metadata?: Record<string, unknown>) => {
      sendAction(command, metadata)
      onCardAction?.(command, card, metadata)
    },
    [onCardAction, sendAction],
  )

  const autoSentRef = useRef(false)
  useEffect(() => {
    if (status === 'open' && autoSend && !autoSentRef.current) {
      autoSentRef.current = true
      sendCommand(autoSend.text, autoSend.metadata)
    }
  }, [status, autoSend, sendCommand])

  const handleSend = (text: string) => {
    const metadata: Record<string, unknown> = {
      provider,
      agent_mode: agentMode,
    }
    sendCommand(text, metadata)
  }

  const isDisabled = status === 'error' || status === 'closed'

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden">
      <div className="px-4 py-2 border-b border-gray-200 bg-white flex items-center justify-between">
        <div className="text-sm text-gray-500">
          状态:{' '}
          <span
            className={`font-medium ${
              status === 'open'
                ? 'text-green-600'
                : status === 'error'
                  ? 'text-red-600'
                  : 'text-amber-600'
            }`}
          >
            {status === 'open' ? '已连接' : status === 'error' ? '连接失败' : '连接中'}
          </span>
        </div>
      </div>

      <MessageList
        messages={messages}
        onCardAction={handleCardActionWrapper}
        onCopy={(text) => void navigator.clipboard.writeText(text)}
      />

      <div className="p-4 border-t border-gray-200 bg-white">
        <ChatComposer
          placeholder={placeholder}
          disabled={isDisabled}
          provider={provider}
          agentMode={agentMode}
          onSend={handleSend}
          onProviderChange={setProvider}
          onAgentModeChange={setAgentMode}
        />
      </div>
    </div>
  )
}
