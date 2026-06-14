import type { Components } from 'react-markdown'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Copy, RefreshCw, ThumbsDown, ThumbsUp } from 'lucide-react'
import type { ChatCard, ChatMessage } from './types'
import ChatCardComponent from './ChatCard'

interface MessageItemProps {
  message: ChatMessage
  onCardAction?: (command: string, card: ChatCard, metadata?: Record<string, unknown>) => void
  onCopy?: (text: string) => void
  onRetry?: () => void
}

function MessageActions({
  content,
  onCopy,
  onRetry,
}: {
  content?: string
  onCopy?: (text: string) => void
  onRetry?: () => void
}) {
  return (
    <div className="flex items-center gap-1 mt-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
      {content && (
        <button
          type="button"
          onClick={() => onCopy?.(content)}
          className="p-1.5 rounded-md hover:bg-gray-100 text-gray-400 hover:text-gray-600"
          title="复制"
        >
          <Copy size={14} />
        </button>
      )}
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="p-1.5 rounded-md hover:bg-gray-100 text-gray-400 hover:text-gray-600"
          title="重新生成"
        >
          <RefreshCw size={14} />
        </button>
      )}
      <button
        type="button"
        className="p-1.5 rounded-md hover:bg-gray-100 text-gray-400 hover:text-gray-600"
        title="点赞"
      >
        <ThumbsUp size={14} />
      </button>
      <button
        type="button"
        className="p-1.5 rounded-md hover:bg-gray-100 text-gray-400 hover:text-gray-600"
        title="点踩"
      >
        <ThumbsDown size={14} />
      </button>
    </div>
  )
}

export default function MessageItem({ message, onCardAction, onCopy, onRetry }: MessageItemProps) {
  const isUser = message.role === 'user'
  const isThinking = message.role === 'thinking'
  const isSystem = message.role === 'system'

  return (
    <div className={`group flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0 ${
          isUser
            ? 'bg-gray-900 text-white'
            : isThinking
              ? 'bg-purple-100 text-purple-700'
              : 'bg-gray-100 text-gray-700'
        }`}
      >
        {isUser ? '我' : isThinking ? '思' : 'AI'}
      </div>

      <div className={`${isUser ? 'max-w-[80%] items-end' : 'max-w-[95%] items-start'} flex flex-col`}>
        {isSystem ? (
          <div className="text-xs text-gray-500 py-1.5 px-3 bg-gray-100 rounded-full">
            {message.content}
            {(() => {
              const error = message.metadata?.error as { message?: string } | undefined
              const detail = error?.message
              // Avoid duplicating the same text when content already equals the detail.
              if (!detail || detail === message.content) return null
              return <span className="text-red-500 ml-1">({detail})</span>
            })()}
          </div>
        ) : isThinking ? (
          <div className="text-sm text-purple-700 bg-purple-50 rounded-2xl rounded-tl-none px-4 py-3 border border-purple-100">
            <div className="flex items-center gap-2 mb-1 text-xs font-medium text-purple-500">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-500 animate-pulse" />
              思考中...
            </div>
            <ReactMarkdown remarkPlugins={[remarkGfm]} className="text-sm leading-relaxed">
              {message.content || ''}
            </ReactMarkdown>
          </div>
        ) : (
          <div
            className={`text-sm rounded-2xl px-4 py-3 ${
              isUser
                ? 'bg-gray-900 text-white rounded-br-none'
                : 'bg-white border border-gray-200 text-gray-800 rounded-bl-none shadow-sm'
            }`}
          >
            {message.content && (
              <div
                className={`markdown-body ${isUser ? 'text-white' : 'text-gray-800'}`}
                style={{ lineHeight: 1.6 }}
              >
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    p: ({ children }) => <p className="mb-2 last:mb-0">{children as React.ReactNode}</p>,
                    ul: ({ children }) => <ul className="list-disc pl-5 mb-2">{children as React.ReactNode}</ul>,
                    ol: ({ children }) => <ol className="list-decimal pl-5 mb-2">{children as React.ReactNode}</ol>,
                    li: ({ children }) => <li className="mb-1">{children as React.ReactNode}</li>,
                    h3: ({ children }) => <h3 className="font-bold text-base mt-3 mb-2">{children as React.ReactNode}</h3>,
                    h4: ({ children }) => <h4 className="font-semibold text-sm mt-2 mb-1">{children as React.ReactNode}</h4>,
                    code: ({ children, className }) => {
                      const isInline = !className
                      const content = children as React.ReactNode
                      return isInline ? (
                        <code
                          className={`px-1 py-0.5 rounded text-xs ${
                            isUser ? 'bg-gray-700 text-white' : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {content}
                        </code>
                      ) : (
                        <pre className="bg-gray-900 text-gray-100 p-3 rounded-lg overflow-auto text-xs my-2">
                          <code>{content}</code>
                        </pre>
                      )
                    },
                  } as Components}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            )}

            {message.card && (
              <div className="mt-2">
                <ChatCardComponent
                  card={message.card}
                  onAction={(command, metadata) =>
                    onCardAction?.(command, message.card!, metadata)
                  }
                />
              </div>
            )}
          </div>
        )}

        {!isSystem && (
          <MessageActions
            content={message.content}
            onCopy={onCopy}
            onRetry={!isUser ? onRetry : undefined}
          />
        )}
      </div>
    </div>
  )
}
