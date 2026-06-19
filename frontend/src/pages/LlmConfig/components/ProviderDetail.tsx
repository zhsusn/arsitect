import { useEffect, useState } from 'react'
import { Copy, Edit2, Star, TestTube, Trash2 } from 'lucide-react'
import { llmProviderApi, type LlmProvider, type ProviderUpdate } from '../../../services/llm'
import { getProviderTypeLabel, getScopeLabel } from '../types'
import DetailHeader from './DetailHeader'
import ProviderForm from './ProviderForm'

interface ProviderDetailProps {
  provider: LlmProvider
  isNew: boolean
  onSaved: () => void
  onCancel: () => void
  onDeleted: () => void
  onMarkUnsaved?: () => void
}

interface TestResult {
  success: boolean
  message: string
  latency_ms?: number
}

export default function ProviderDetail({
  provider,
  isNew,
  onSaved,
  onCancel,
  onDeleted,
  onMarkUnsaved,
}: ProviderDetailProps) {
  const [isEditing, setIsEditing] = useState(isNew)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<TestResult | null>(null)
  const [testing, setTesting] = useState(false)

  useEffect(() => {
    setIsEditing(isNew)
    setError(null)
    setTestResult(null)
  }, [provider.id, isNew])

  const handleSave = async (data: ProviderUpdate) => {
    setSaving(true)
    setError(null)
    try {
      await llmProviderApi.update(provider.id, data)
      setIsEditing(false)
      onSaved()
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (provider.is_default) {
      window.alert('默认节点不可删除，请先设置其他节点为默认。')
      return
    }
    if (!window.confirm(`确定删除 Provider 节点「${provider.name}」？`)) return
    try {
      await llmProviderApi.remove(provider.id)
      onDeleted()
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    }
  }

  const handleClone = async () => {
    try {
      await llmProviderApi.clone(provider.id)
      onSaved()
    } catch (err) {
      setError(err instanceof Error ? err.message : '复制失败')
    }
  }

  const handleTest = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const result = await llmProviderApi.test(provider.id)
      setTestResult(result)
    } catch (err) {
      setTestResult({ success: false, message: err instanceof Error ? err.message : '测试失败' })
    } finally {
      setTesting(false)
    }
  }

  const handleSetDefault = async () => {
    try {
      await llmProviderApi.setDefault(provider.id)
      onSaved()
    } catch (err) {
      setError(err instanceof Error ? err.message : '设置默认失败')
    }
  }

  if (isEditing) {
    return (
      <ProviderForm
        provider={provider}
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

  const config = provider.config_json || {}

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-3xl">
        <div className="flex items-start justify-between mb-4">
          <DetailHeader mode="read" tab="provider" name={provider.name} />
          <div className="flex items-center gap-2 shrink-0 mt-1">
            <button
              type="button"
              onClick={handleTest}
              disabled={testing}
              className="inline-flex items-center gap-1 px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              <TestTube size={14} />
              {testing ? '测试中...' : '测试'}
            </button>
            <button
              type="button"
              onClick={() => setIsEditing(true)}
              className="inline-flex items-center gap-1 px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              <Edit2 size={14} /> 编辑
            </button>
            <button
              type="button"
              onClick={handleClone}
              className="inline-flex items-center gap-1 px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              <Copy size={14} /> 复制
            </button>
            {!provider.is_default && (
              <button
                type="button"
                onClick={handleSetDefault}
                className="inline-flex items-center gap-1 px-3 py-1.5 text-sm border border-amber-300 text-amber-700 rounded-lg hover:bg-amber-50"
              >
                <Star size={14} /> 设为默认
              </button>
            )}
            <button
              type="button"
              onClick={handleDelete}
              disabled={provider.is_default}
              className="inline-flex items-center gap-1 px-3 py-1.5 text-sm border border-red-200 text-red-600 rounded-lg hover:bg-red-50 disabled:opacity-50"
            >
              <Trash2 size={14} /> 删除
            </button>
          </div>
        </div>

        {error && <div className="mb-4 rounded-lg bg-red-50 text-red-700 px-4 py-3 text-sm">{error}</div>}
        {testResult && (
          <div
            className={`mb-4 rounded-lg px-4 py-3 text-sm ${
              testResult.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
            }`}
          >
            {testResult.message}
            {testResult.latency_ms ? `（${testResult.latency_ms}ms）` : ''}
          </div>
        )}

        <dl className="divide-y divide-gray-100 border border-gray-200 rounded-xl overflow-hidden">
          <DetailRow label="名称" value={provider.name} />
          <DetailRow label="标识 key" value={provider.key} />
          <DetailRow label="作用域" value={`${getScopeLabel(provider.scope)}${provider.scope_target ? ` / ${provider.scope_target}` : ''}`} />
          <DetailRow label="目标 ID" value={provider.scope_target || '-'} />
          <DetailRow label="优先级" value={String(provider.priority)} />
          <DetailRow label="默认节点" value={provider.is_default ? '★ 默认' : '-'} />
          <DetailRow label="Provider 类型" value={getProviderTypeLabel(provider.provider_type)} />
          <DetailRow label="Kimi CLI 路径" value={(config.kimi_cli_path as string) || '-'} hidden={provider.provider_type !== 'kimi-cli'} />
          <DetailRow label="API Base" value={(config.api_base as string) || '-'} hidden={!['openai', 'kimi-api'].includes(provider.provider_type)} />
          <DetailRow label="模型" value={(config.model as string) || '-'} hidden={!['openai', 'kimi-api'].includes(provider.provider_type)} />
          <DetailRow label="API Key" value={provider.has_api_key ? '••••••' : '-'} hidden={!['openai', 'kimi-api'].includes(provider.provider_type)} />
          <DetailRow label="超时时间" value={`${config.timeout || 120}s`} />
        </dl>
      </div>
    </div>
  )
}

function DetailRow({
  label,
  value,
  hidden,
}: {
  label: string
  value: React.ReactNode
  hidden?: boolean
}) {
  if (hidden) return null
  return (
    <div className="px-4 py-3 sm:grid sm:grid-cols-3 sm:gap-4 bg-white">
      <dt className="text-sm font-medium text-gray-500">{label}</dt>
      <dd className="mt-1 text-sm text-gray-900 sm:col-span-2 sm:mt-0">{value || '-'}</dd>
    </div>
  )
}
