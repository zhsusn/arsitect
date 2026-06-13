import type { ChatCard, ChatCardAction } from './types'

interface ChatCardProps {
  card: ChatCard
  onAction: (command: string, metadata?: Record<string, unknown>) => void
}

function getActionClass(style?: string): string {
  switch (style) {
    case 'primary':
      return 'bg-blue-600 text-white hover:bg-blue-700 border-transparent'
    case 'danger':
      return 'bg-red-600 text-white hover:bg-red-700 border-transparent'
    default:
      return 'bg-white text-gray-700 hover:bg-gray-50 border-gray-300'
  }
}

export default function ChatCardComponent({ card, onAction }: ChatCardProps) {
  const handleClick = (action: ChatCardAction) => {
    onAction(action.command, { cardType: card.type, ...card.data })
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-4 max-w-md">
      <div className="font-semibold text-sm text-gray-900 mb-2">{card.title}</div>
      {card.description && (
        <div className="text-sm text-gray-600 mb-3 leading-relaxed">{card.description}</div>
      )}
      {typeof card.data.diff === 'string' && (
        <pre className="bg-gray-50 p-3 rounded-lg text-xs font-mono max-h-40 overflow-auto mb-3">
          {card.data.diff}
        </pre>
      )}
      <div className="flex flex-wrap gap-2 justify-end">
        {card.actions.map((action) => (
          <button
            key={action.command}
            type="button"
            onClick={() => handleClick(action)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${getActionClass(
              action.style,
            )}`}
          >
            {action.label}
          </button>
        ))}
      </div>
    </div>
  )
}
