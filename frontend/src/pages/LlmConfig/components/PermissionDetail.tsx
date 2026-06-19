import { useEffect, useMemo, useState } from 'react'
import { Edit2, Trash2 } from 'lucide-react'
import { llmPolicyApi, type LlmPolicy, type PolicyUpdate } from '../../../services/llm'
import { getPermissionColor, getPermissionLabel, getScopeLabel } from '../types'
import DetailHeader from './DetailHeader'
import PermissionForm from './PermissionForm'

interface PermissionDetailProps {
  policy: LlmPolicy
  isNew: boolean
  onSaved: () => void
  onCancel: () => void
  onDeleted: () => void
  onMarkUnsaved?: () => void
}

const PREVIEW_LIMIT = 5

export default function PermissionDetail({
  policy,
  isNew,
  onSaved,
  onCancel,
  onDeleted,
  onMarkUnsaved,
}: PermissionDetailProps) {
  const [isEditing, setIsEditing] = useState(isNew)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    setIsEditing(isNew)
    setError(null)
    setExpanded(false)
  }, [policy.id, isNew])

  const rules = useMemo(() => policy.rules || [], [policy.rules])

  const handleSave = async (data: PolicyUpdate) => {
    setSaving(true)
    setError(null)
    try {
      await llmPolicyApi.update(policy.id, data)
      setIsEditing(false)
      onSaved()
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!window.confirm(`确定删除权限策略「${policy.name}」？`)) return
    try {
      await llmPolicyApi.remove(policy.id)
      onDeleted()
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    }
  }

  if (isEditing) {
    return (
      <PermissionForm
        policy={policy}
        isNew={isNew}
        saving={saving}
        error={error}
        onSave={handleSave}
        onCancel={() => {
          setIsEditing(false)
          onCancel()
        }}
        onChange={onMarkUnsaved}
      />
    )
  }

  const previewRules = expanded ? rules : rules.slice(0, PREVIEW_LIMIT)
  const hasMore = rules.length > PREVIEW_LIMIT

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-3xl">
        <div className="flex items-start justify-between mb-4">
          <DetailHeader mode="read" tab="permission" name={policy.name} />
          <div className="flex items-center gap-2 shrink-0 mt-1">
            <button
              type="button"
              onClick={() => setIsEditing(true)}
              className="inline-flex items-center gap-1 px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              <Edit2 size={14} /> 编辑
            </button>
            <button
              type="button"
              onClick={handleDelete}
              className="inline-flex items-center gap-1 px-3 py-1.5 text-sm border border-red-200 text-red-600 rounded-lg hover:bg-red-50"
            >
              <Trash2 size={14} /> 删除
            </button>
          </div>
        </div>

        {error && <div className="mb-4 rounded-lg bg-red-50 text-red-700 px-4 py-3 text-sm">{error}</div>}

        <dl className="divide-y divide-gray-100 border border-gray-200 rounded-xl overflow-hidden mb-6">
          <DetailRow label="名称" value={policy.name} />
          <DetailRow label="作用域" value={getScopeLabel(policy.scope)} />
          <DetailRow label="默认模式">
            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs ${getPermissionColor(policy.default_mode)}`}>
              {getPermissionLabel(policy.default_mode)}
            </span>
          </DetailRow>
          <DetailRow label="规则数" value={`${rules.length}`} />
        </dl>

        <div className="border border-gray-200 rounded-xl overflow-hidden">
          <div className="bg-gray-50 px-4 py-2 text-sm font-medium text-gray-700 flex items-center justify-between">
            <span>规则列表</span>
            {hasMore && (
              <button
                type="button"
                onClick={() => setExpanded((v) => !v)}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                {expanded ? '收起' : `展开全部（${rules.length}）`}
              </button>
            )}
          </div>
          {rules.length === 0 ? (
            <div className="px-4 py-6 text-sm text-gray-400 text-center">暂无规则，将使用默认模式</div>
          ) : (
            <div className="divide-y divide-gray-100 px-4 py-2">
              {expanded && (
                <div className="grid grid-cols-[110px_80px_1fr_1fr_32px] gap-2 pb-2 text-xs text-gray-500 border-b border-gray-100">
                  <div>操作类型</div>
                  <div>权限</div>
                  <div>匹配模式</div>
                  <div>描述</div>
                  <div></div>
                </div>
              )}
              {previewRules.map((rule, idx) => (
                <div key={idx} className="py-2 text-sm flex items-center gap-3">
                  {!expanded && <span className="text-gray-400 w-6">{idx + 1}.</span>}
                  {expanded && <span className="text-gray-400 w-6 text-xs">{idx + 1}.</span>}
                  <span className="w-24 shrink-0 text-xs text-gray-600">{rule.category}</span>
                  <span className={`px-2 py-0.5 rounded text-xs ${getPermissionColor(rule.permission)}`}>
                    {getPermissionLabel(rule.permission)}
                  </span>
                  <span className="text-gray-600 truncate flex-1" title={rule.pattern || '-'}>
                    {rule.pattern || '-'}
                  </span>
                  {rule.description && <span className="text-gray-400 text-xs truncate max-w-[200px]">{rule.description}</span>}
                </div>
              ))}
              {!expanded && hasMore && (
                <div className="px-4 py-2 text-xs text-gray-400">... 等 {rules.length - PREVIEW_LIMIT} 条规则</div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function DetailRow({
  label,
  value,
  children,
}: {
  label: string
  value?: React.ReactNode
  children?: React.ReactNode
}) {
  return (
    <div className="px-4 py-3 sm:grid sm:grid-cols-3 sm:gap-4 bg-white">
      <dt className="text-sm font-medium text-gray-500">{label}</dt>
      <dd className="mt-1 text-sm text-gray-900 sm:col-span-2 sm:mt-0">{children || value || '-'}</dd>
    </div>
  )
}
