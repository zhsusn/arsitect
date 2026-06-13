import type { Components } from 'react-markdown'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
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
    <div className="flex items-center gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
      {content && (
        <button
          type="button"
          onClick={() => onCopy?.(content)}
          className="p-1 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600"
          title="复制"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
          </svg>
        </button>
      )}
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="p-1 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600"
          title="重新生成"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.3" />
          </svg>
        </button>
      )}
      <button
        type="button"
        className="p-1 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600"
        title="点赞"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
        </svg>
      </button>
      <button
        type="button"
        className="p-1 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600"
        title="点踩"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3" />
        </svg>
      </button>
    </div>
  )
}

export default function MessageItem({ message, onCardAction, onCopy, onRetry }: MessageItemProps) {
  const isUser = message.role === 'user'
  const isThinking = message.role === 'thinking'
  const isSystem = message.role === 'system'

  const avatar = isUser ? '👤' : isThinking ? '💭' : '🤖'

  return (
    <div className={`group flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center text-sm flex-shrink-0 ${
          isUser ? 'bg-blue-100' : isThinking ? 'bg-purple-100' : 'bg-gray-100'
        }`}
      >
        {avatar}
      </div>

      <div className={`max-w-[80%] ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>
        {isSystem ? (
          <div className="text-xs text-gray-500 py-1 px-2 bg-gray-50 rounded">
            {message.content}
            {(() => {
              const error = message.metadata?.error as { message?: string } | undefined
              return error?.message ? (
                <span className="text-red-500 ml-1">({error.message})</span>
              ) : null
            })()}
          </div>
        ) : isThinking ? (
          <div className="text-sm text-purple-700 bg-purple-50 rounded-2xl px-4 py-2.5 border border-purple-100">
            <div className="flex items-center gap-2 mb-1 text-xs font-medium text-purple-500">
              <span className="animate-pulse">●</span>
              思考中...
            </div>
            <ReactMarkdown remarkPlugins={[remarkGfm]} className="text-sm leading-relaxed">
              {message.content || ''}
            </ReactMarkdown>
          </div>
        ) : (
          <div
            className={`text-sm rounded-2xl px-4 py-2.5 ${
              isUser
                ? 'bg-blue-600 text-white rounded-br-none'
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
                            isUser ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-800'
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
