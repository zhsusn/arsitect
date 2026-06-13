import { useCallback, useEffect, useRef } from 'react'
import type { Node } from '@xyflow/react'

export type ContextMenuAction =
  | 'execute'
  | 'detail'
  | 'merge'
  | 'retry'
  | 'logs'
  | 'artifacts'
  | 'approve'

interface MenuItem {
  key: ContextMenuAction
  label: string
  icon?: string
}

const STAGE_MENU: MenuItem[] = [
  { key: 'execute', label: '执行', icon: '▶' },
  { key: 'detail', label: '查看详情', icon: 'ℹ' },
  { key: 'merge', label: '合并阶段', icon: '⇄' },
  { key: 'retry', label: '重试', icon: '↻' },
]

const SKILL_MENU: MenuItem[] = [
  { key: 'execute', label: '执行', icon: '▶' },
  { key: 'logs', label: '查看日志', icon: '📋' },
  { key: 'artifacts', label: '查看产物', icon: '📄' },
]

const GATE_MENU: MenuItem[] = [{ key: 'approve', label: '前往审批', icon: '✓' }]

interface NodeContextMenuProps {
  node: Node | null
  x: number
  y: number
  onAction: (node: Node, action: ContextMenuAction) => void
  onClose: () => void
}

export default function NodeContextMenu({ node, x, y, onAction, onClose }: NodeContextMenuProps) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as HTMLElement)) {
        onClose()
      }
    }
    document.addEventListener('click', handleClick)
    return () => document.removeEventListener('click', handleClick)
  }, [onClose])

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleEsc)
    return () => document.removeEventListener('keydown', handleEsc)
  }, [onClose])

  const handleAction = useCallback(
    (action: ContextMenuAction) => {
      if (node) onAction(node, action)
      onClose()
    },
    [node, onAction, onClose],
  )

  if (!node) return null

  const nodeType = (node.type || 'stage') as string
  let items: MenuItem[] = []
  if (nodeType === 'stage') items = STAGE_MENU
  else if (nodeType === 'skill') items = SKILL_MENU
  else if (nodeType === 'gate') items = GATE_MENU

  return (
    <div
      ref={ref}
      style={{
        position: 'fixed',
        top: y,
        left: x,
        zIndex: 1000,
      }}
      className="bg-white border border-gray-200 rounded-lg shadow-lg py-1 min-w-[140px]"
    >
      {items.map((item) => (
        <button
          key={item.key}
          onClick={() => handleAction(item.key)}
          className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2 transition-colors"
        >
          <span className="text-xs w-4 text-center">{item.icon}</span>
          {item.label}
        </button>
      ))}
    </div>
  )
}
