import type { CliCard as CliCardType, CliCardAction } from './types'

interface CliCardProps {
  card: CliCardType
  onAction: (command: string, metadata?: Record<string, unknown>) => void
}

function getActionStyle(style?: string): { background: string; color: string; border: string } {
  switch (style) {
    case 'primary':
      return { background: '#2563eb', color: '#fff', border: '1px solid #2563eb' }
    case 'danger':
      return { background: '#dc2626', color: '#fff', border: '1px solid #dc2626' }
    default:
      return { background: '#fff', color: '#374151', border: '1px solid #d1d5db' }
  }
}

export default function CliCard({ card, onAction }: CliCardProps) {
  const { type, data, actions } = card

  const handleClick = (action: CliCardAction) => {
    onAction(action.command, { cardType: type, ...data })
  }

  const title =
    typeof data.title === 'string'
      ? data.title
      : typeof data.summary === 'string'
        ? data.summary
        : `${type}`

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 80,
        right: 24,
        width: 360,
        maxWidth: 'calc(100% - 48px)',
        background: '#fff',
        border: '1px solid #e5e7eb',
        borderRadius: 8,
        boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)',
        padding: 16,
        zIndex: 50,
      }}
    >
      <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 8, color: '#111827' }}>
        {title}
      </div>
      {typeof data.description === 'string' && (
        <div
          style={{
            fontSize: 13,
            color: '#4b5563',
            marginBottom: 12,
            lineHeight: 1.5,
          }}
        >
          {data.description}
        </div>
      )}
      {typeof data.diff === 'string' && (
        <pre
          style={{
            background: '#f3f4f6',
            padding: 8,
            borderRadius: 4,
            fontSize: 12,
            maxHeight: 160,
            overflow: 'auto',
            marginBottom: 12,
          }}
        >
          {data.diff}
        </pre>
      )}
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
        {actions.map((action) => (
          <button
            key={action.command}
            onClick={() => handleClick(action)}
            style={{
              padding: '6px 12px',
              borderRadius: 4,
              fontSize: 13,
              fontWeight: 500,
              cursor: 'pointer',
              ...getActionStyle(action.style),
            }}
          >
            {action.label}
          </button>
        ))}
      </div>
    </div>
  )
}
