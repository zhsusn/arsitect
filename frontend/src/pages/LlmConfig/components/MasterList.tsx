import { useEffect, useMemo, useRef, useState } from 'react'
import { Plus, Search, Star } from 'lucide-react'
import type { LlmPolicy, LlmProvider } from '../../../services/llm'
import {
  getPermissionLabel,
  getProviderTypeLabel,
  getScopeLabel,
  isProvider,
  type TabKey,
} from '../types'

interface MasterListProps {
  tab: TabKey
  entities: LlmProvider[] | LlmPolicy[]
  selectedId: string | null
  draftNodeId?: string | null
  loading: boolean
  onSelect: (id: string) => void
  onAdd: () => void
  onSetDefault?: (id: string) => void
}

type SortKey = 'priority' | 'updated_at' | 'name'
type SortOrder = 'asc' | 'desc'

export default function MasterList({
  tab,
  entities,
  selectedId,
  draftNodeId,
  loading,
  onSelect,
  onAdd,
  onSetDefault,
}: MasterListProps) {
  const [search, setSearch] = useState('')
  const [scopeFilter, setScopeFilter] = useState<string[]>([])
  const [sortBy, setSortBy] = useState<SortKey>('priority')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')
  const listRef = useRef<HTMLDivElement>(null)

  const placeholder = tab === 'provider' ? '搜索节点名称、key...' : '搜索策略名称、key...'

  useEffect(() => {
    if (selectedId && listRef.current) {
      const active = listRef.current.querySelector(`[data-node-id="${selectedId}"]`)
      active?.scrollIntoView({ block: 'nearest' })
    }
  }, [selectedId])

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase()
    let items = entities.filter((n) => {
      if (scopeFilter.length > 0 && !scopeFilter.includes(n.scope)) return false
      if (!term) return true
      return (
        n.name.toLowerCase().includes(term) ||
        n.key.toLowerCase().includes(term) ||
        (n.description || '').toLowerCase().includes(term)
      )
    })
    items = [...items].sort((a, b) => {
      let cmp = 0
      if (sortBy === 'priority') cmp = a.priority - b.priority
      else if (sortBy === 'name') cmp = a.name.localeCompare(b.name)
      else cmp = new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime()
      return sortOrder === 'asc' ? cmp : -cmp
    })
    return items
  }, [entities, scopeFilter, search, sortBy, sortOrder])

  const cycleSort = (key: SortKey) => {
    if (sortBy === key) {
      setSortOrder((o) => (o === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortBy(key)
      setSortOrder('desc')
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-gray-200 space-y-3">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={placeholder}
            className="w-full pl-9 pr-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="flex items-center justify-between">
          <select
            value={scopeFilter.join(',')}
            onChange={(e) => setScopeFilter(e.target.value ? e.target.value.split(',') : [])}
            className="text-xs border border-gray-300 rounded px-2 py-1"
          >
            <option value="">全部作用域</option>
            <option value="global">全局</option>
            <option value="project">项目</option>
            <option value="user">用户</option>
            <option value="managed">托管</option>
          </select>
          <div className="flex gap-2 text-xs text-gray-500">
            <button
              type="button"
              onClick={() => cycleSort('priority')}
              className={`hover:text-gray-900 ${sortBy === 'priority' ? 'font-medium text-gray-900' : ''}`}
            >
              优先级{sortBy === 'priority' ? (sortOrder === 'desc' ? '↓' : '↑') : ''}
            </button>
            <button
              type="button"
              onClick={() => cycleSort('updated_at')}
              className={`hover:text-gray-900 ${sortBy === 'updated_at' ? 'font-medium text-gray-900' : ''}`}
            >
              更新时间{sortBy === 'updated_at' ? (sortOrder === 'desc' ? '↓' : '↑') : ''}
            </button>
          </div>
        </div>
      </div>

      <div ref={listRef} className="flex-1 overflow-y-auto p-3 space-y-2">
        {loading ? (
          <div className="text-sm text-gray-500 text-center py-8">加载中...</div>
        ) : filtered.length === 0 ? (
          <div className="text-sm text-gray-500 text-center py-12">
            未找到匹配节点
            <div className="mt-4">
              <EmptyAddButton tab={tab} onAdd={onAdd} />
            </div>
          </div>
        ) : (
          filtered.map((node) => (
            <MasterCard
              key={node.id}
              tab={tab}
              node={node}
              selected={selectedId === node.id}
              isDraft={draftNodeId === node.id}
              onClick={() => onSelect(node.id)}
              onSetDefault={onSetDefault}
            />
          ))
        )}
      </div>

      <div className="p-3 border-t border-gray-200">
        <EmptyAddButton tab={tab} onAdd={onAdd} fullWidth />
      </div>
    </div>
  )
}

function MasterCard({
  tab,
  node,
  selected,
  isDraft,
  onClick,
  onSetDefault,
}: {
  tab: TabKey
  node: LlmProvider | LlmPolicy
  selected: boolean
  isDraft: boolean
  onClick: () => void
  onSetDefault?: (id: string) => void
}) {
  const provider = isProvider(node) ? node : null
  const policy = !provider ? (node as LlmPolicy) : null
  const typeLabel = provider
    ? getProviderTypeLabel(provider.provider_type)
    : getPermissionLabel(policy?.default_mode)

  return (
    <button
      type="button"
      data-node-id={node.id}
      onClick={onClick}
      className={`group w-full text-left rounded-lg border p-3 transition-colors ${
        isDraft
          ? 'border-dashed border-amber-400 bg-amber-50'
          : selected
            ? 'border-l-2 border-l-blue-500 border-gray-200 bg-blue-50'
            : 'border-gray-200 hover:bg-gray-50'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <div className="text-sm font-medium text-gray-900 truncate">{node.name}</div>
            {isDraft && (
              <span className="shrink-0 inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium text-amber-700 bg-amber-100 border border-amber-200">
                未保存
              </span>
            )}
          </div>
          <div className="text-xs text-gray-400 font-mono mt-0.5">{node.key}</div>
        </div>
        {provider?.is_default ? (
          <span title="当前默认 Provider" className="text-amber-500 shrink-0">
            <Star size={14} fill="currentColor" />
          </span>
        ) : tab === 'provider' && onSetDefault ? (
          <button
            type="button"
            title="设为默认 Provider"
            onClick={(e) => {
              e.stopPropagation()
              onSetDefault(node.id)
            }}
            className="shrink-0 opacity-0 group-hover:opacity-100 text-gray-400 hover:text-amber-500 transition-opacity"
          >
            <Star size={14} />
          </button>
        ) : null}
      </div>
      <div className="mt-2 flex items-center gap-2 text-xs text-gray-500">
        <span>{typeLabel}</span>
        <span>·</span>
        <span>{getScopeLabel(node.scope)}</span>
        {policy && (
          <>
            <span>·</span>
            <span>{policy.rules.length} 条规则</span>
          </>
        )}
      </div>
    </button>
  )
}

function EmptyAddButton({
  tab,
  onAdd,
  fullWidth = false,
}: {
  tab: TabKey
  onAdd: () => void
  fullWidth?: boolean
}) {
  const label = tab === 'provider' ? '新增 Provider' : '新增策略'
  return (
    <button
      type="button"
      onClick={onAdd}
      className={`inline-flex items-center justify-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg text-sm hover:bg-gray-800 ${
        fullWidth ? 'w-full' : ''
      }`}
    >
      <Plus size={16} />
      {label}
    </button>
  )
}
