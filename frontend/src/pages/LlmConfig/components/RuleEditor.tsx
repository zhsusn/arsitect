import { GripVertical, Trash2 } from 'lucide-react'
import { useState } from 'react'
import {
  ACTION_TYPES,
  getRuleCategory,
  PERMISSIONS,
  type LlmPolicyRule,
} from '../types'

interface RuleEditorProps {
  rules: LlmPolicyRule[]
  onChange: (rules: LlmPolicyRule[]) => void
  onMarkUnsaved?: () => void
}

const HEADER_COLS = 'grid-cols-[24px_110px_90px_minmax(200px,1fr)_1fr_32px]'

export default function RuleEditor({ rules, onChange, onMarkUnsaved }: RuleEditorProps) {
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null)

  const addRule = () => {
    onChange([
      {
        category: 'file_system',
        action_type: 'file_read',
        permission: 'allow',
        pattern: '${PROJECT_ROOT}/**',
        description: null,
        sort_order: 0,
      },
      ...rules,
    ])
    onMarkUnsaved?.()
  }

  const updateRule = (index: number, patch: Partial<LlmPolicyRule>) => {
    const next = rules.map((r, i) => (i === index ? { ...r, ...patch } : r))
    onChange(next)
    onMarkUnsaved?.()
  }

  const removeRule = (index: number) => {
    onChange(rules.filter((_, i) => i !== index))
    onMarkUnsaved?.()
  }

  const moveRule = (from: number, to: number) => {
    if (from === to) return
    const next = [...rules]
    const [item] = next.splice(from, 1)
    next.splice(to, 0, item)
    onChange(next)
    onMarkUnsaved?.()
  }

  const handleDragStart = (e: React.DragEvent, index: number) => {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', String(index))
  }

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    setDragOverIndex(index)
  }

  const handleDrop = (e: React.DragEvent, toIndex: number) => {
    e.preventDefault()
    const fromIndex = Number(e.dataTransfer.getData('text/plain'))
    setDragOverIndex(null)
    if (Number.isNaN(fromIndex)) return
    moveRule(fromIndex, toIndex)
  }

  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden bg-white">
      <div className="px-3 py-2 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">规则列表（{rules.length}）</span>
        <button
          type="button"
          onClick={addRule}
          className="inline-flex items-center gap-1 text-xs text-gray-700 hover:text-gray-900 border border-gray-300 rounded px-2 py-1 bg-white"
        >
          + 添加规则
        </button>
      </div>

      {rules.length === 0 ? (
        <div className="px-4 py-8 text-sm text-gray-400 text-center">
          暂无规则，所有请求将按默认模式处理
        </div>
      ) : (
        <div className="max-h-[360px] overflow-y-auto">
          {/* Header */}
          <div
            className={`grid ${HEADER_COLS} gap-2 px-3 py-2 text-xs text-gray-500 border-b border-gray-100 bg-white sticky top-0 z-10`}
          >
            <div></div>
            <div>操作类型</div>
            <div>权限</div>
            <div>匹配模式</div>
            <div>描述</div>
            <div></div>
          </div>

          {rules.map((rule, index) => (
            <RuleRow
              key={`${index}-${rule.action_type}-${rule.permission}`}
              rule={rule}
              isOver={dragOverIndex === index}
              onChange={(patch) => updateRule(index, patch)}
              onRemove={() => removeRule(index)}
              onDragStart={(e) => handleDragStart(e, index)}
              onDragOver={(e) => handleDragOver(e, index)}
              onDrop={(e) => handleDrop(e, index)}
              onDragLeave={() => setDragOverIndex(null)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function RuleRow({
  rule,
  isOver,
  onChange,
  onRemove,
  onDragStart,
  onDragOver,
  onDrop,
  onDragLeave,
}: {
  rule: LlmPolicyRule
  isOver: boolean
  onChange: (patch: Partial<LlmPolicyRule>) => void
  onRemove: () => void
  onDragStart: (e: React.DragEvent) => void
  onDragOver: (e: React.DragEvent) => void
  onDrop: (e: React.DragEvent) => void
  onDragLeave: () => void
}) {
  const handleActionTypeChange = (actionType: string) => {
    onChange({
      action_type: actionType as LlmPolicyRule['action_type'],
      category: getRuleCategory(actionType),
    })
  }

  return (
    <div
      draggable
      onDragStart={onDragStart}
      onDragOver={onDragOver}
      onDrop={onDrop}
      onDragLeave={onDragLeave}
      className={`grid ${HEADER_COLS} gap-2 px-3 py-2 items-center border-b border-gray-100 last:border-b-0 transition-colors ${
        isOver ? 'bg-blue-50' : 'bg-white hover:bg-gray-50'
      }`}
    >
      <div className="text-gray-300 cursor-grab active:cursor-grabbing">
        <GripVertical size={16} />
      </div>

      <select
        value={rule.action_type}
        onChange={(e) => handleActionTypeChange(e.target.value)}
        className="w-full rounded border border-gray-300 px-2 py-1 text-xs"
      >
        {ACTION_TYPES.map((c) => (
          <option key={c.value} value={c.value}>
            {c.label}
          </option>
        ))}
      </select>

      <select
        value={rule.permission}
        onChange={(e) => onChange({ permission: e.target.value as LlmPolicyRule['permission'] })}
        className="w-full rounded border border-gray-300 px-2 py-1 text-xs"
      >
        {PERMISSIONS.map((d) => (
          <option key={d.value} value={d.value}>
            {d.label}
          </option>
        ))}
      </select>

      <input
        type="text"
        value={rule.pattern}
        title={rule.pattern}
        onChange={(e) => onChange({ pattern: e.target.value })}
        placeholder="匹配模式（glob）"
        className="w-full min-w-[200px] rounded border border-gray-300 px-2 py-1 text-xs"
      />

      <input
        type="text"
        value={rule.description || ''}
        onChange={(e) => onChange({ description: e.target.value || null })}
        placeholder="说明"
        className="w-full rounded border border-gray-300 px-2 py-1 text-xs"
      />

      <button
        type="button"
        onClick={onRemove}
        className="p-1 text-gray-400 hover:text-red-600"
      >
        <Trash2 size={14} />
      </button>
    </div>
  )
}
