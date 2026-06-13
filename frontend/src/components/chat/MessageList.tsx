import { useEffect, useRef } from 'react'
import MessageItem from './MessageItem'
import type { ChatCard, ChatMessage } from './types'

interface MessageListProps {
  messages: ChatMessage[]
  onCardAction?: (command: string, card: ChatCard, metadata?: Record<string, unknown>) => void
  onCopy?: (text: string) => void
  onRetry?: (messageId: string) => void
}

export default function MessageList({ messages, onCardAction, onCopy, onRetry }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
        开始一个新会话
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-5">
      {messages.map((message) => (
        <MessageItem
          key={message.id}
          message={message}
          onCardAction={onCardAction}
          onCopy={onCopy}
          onRetry={onRetry ? () => onRetry(message.id) : undefined}
        />
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
