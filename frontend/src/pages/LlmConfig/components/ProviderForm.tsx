import { useEffect, useMemo, useState } from 'react'
import type { LlmProvider, ProviderUpdate } from '../../../services/llm'
import { getDefaultProviderConfig, PROVIDER_TYPES } from '../types'
import DetailHeader from './DetailHeader'
import StickyActionBar from './StickyActionBar'
import { useFormDraft } from '../hooks/useFormDraft'
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts'

interface ProviderFormProps {
  provider: LlmProvider | null
  isNew: boolean
  saving: boolean
  error: string | null
  onSave: (data: ProviderUpdate) => void
  onCancel: () => void
  onChange?: () => void
}

interface FormData {
  name: string
  description: string
  priority: number
  provider_type: string
  kimi_cli_path: string
  api_base: string
  api_key: string
  model: string
  timeout: number
}

const FORM_ID = 'llm-config-form'

function initialData(provider: LlmProvider | null): FormData {
  const config = provider?.config_json || { provider: 'kimi-cli' }
  return {
    name: provider?.name || '',
    description: provider?.description || '',
    priority: provider?.priority ?? 0,
    provider_type: provider?.provider_type || (config.provider as string) || 'kimi-cli',
    kimi_cli_path: (config.kimi_cli_path as string) || 'kimi',
    api_base: (config.api_base as string) || '',
    api_key: '',
    model: (config.model as string) || '',
    timeout: (config.timeout as number) || 120,
  }
}

export default function ProviderForm({
  provider,
  isNew,
  saving,
  error,
  onSave,
  onCancel,
  onChange,
}: ProviderFormProps) {
  const [form, setForm] = useState<FormData>(initialData(provider))
  const [touched, setTouched] = useState(false)
  const [isDirty, setIsDirty] = useState(false)

  useEffect(() => {
    setForm(initialData(provider))
    setTouched(false)
    setIsDirty(false)
  }, [provider])

  const { clearDraft } = useFormDraft<FormData>({
    key: `llm-config-draft-provider-${provider?.id || 'new'}`,
    form,
    isDirty,
    onRestore: (draft) => {
      setForm(draft)
      setIsDirty(true)
      onChange?.()
    },
  })

  const validation = useMemo(() => {
    const errors: string[] = []
    if (!form.name.trim()) errors.push('名称不能为空')
    if (form.provider_type === 'kimi-cli' && !form.kimi_cli_path.trim()) errors.push('Kimi CLI 路径不能为空')
    return errors
  }, [form])

  const updateForm = (patch: Partial<FormData>) => {
    setForm((f) => ({ ...f, ...patch }))
    setIsDirty(true)
    onChange?.()
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setTouched(true)
    if (validation.length > 0) return

    const config: Record<string, unknown> = {
      timeout: form.timeout,
    }
    if (form.provider_type === 'kimi-cli') {
      config.kimi_cli_path = form.kimi_cli_path
    }
    if (form.provider_type === 'openai' || form.provider_type === 'kimi-api') {
      config.api_base = form.api_base
      config.model = form.model
    }
    const payload: ProviderUpdate = {
      name: form.name,
      description: form.description || undefined,
      priority: form.priority,
      config_json: config,
    }
    if (form.api_key && form.api_key !== '••••••' && !form.api_key.startsWith('•')) {
      payload.api_key = form.api_key
    }
    clearDraft()
    setIsDirty(false)
    onSave(payload)
  }

  const handleCancel = () => {
    clearDraft()
    setIsDirty(false)
    onCancel()
  }

  useKeyboardShortcuts({ formId: FORM_ID, hasChanges: isDirty, onCancel: handleCancel })

  return (
    <div className="h-full overflow-y-auto p-6">
      <form id={FORM_ID} onSubmit={handleSubmit} className="max-w-3xl">
        <DetailHeader mode={isNew ? 'new' : 'edit'} tab="provider" name={form.name} />

        {(error || (touched && validation.length > 0)) && (
          <div className="mb-4 rounded-lg bg-red-50 text-red-700 px-4 py-3 text-sm space-y-1">
            {error && <div>{error}</div>}
            {touched && validation.map((msg) => <div key={msg}>{msg}</div>)}
          </div>
        )}

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Field label="名称" required>
              <input
                type="text"
                data-testid="provider-name-input"
                value={form.name}
                onChange={(e) => updateForm({ name: e.target.value })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </Field>
            <Field label="标识 key" required>
              <input
                type="text"
                value={provider?.key || ''}
                disabled
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm bg-gray-100 text-gray-500"
              />
              <p className="mt-1 text-xs text-gray-400">系统自动生成，创建后不可修改</p>
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Field label="作用域">
              <input
                type="text"
                value={provider?.scope || 'global'}
                disabled
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm bg-gray-100 text-gray-500"
              />
            </Field>
            <Field label="优先级">
              <input
                type="number"
                value={form.priority}
                onChange={(e) => updateForm({ priority: parseInt(e.target.value, 10) || 0 })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </Field>
          </div>

          <Field label="描述">
            <textarea
              value={form.description}
              onChange={(e) => updateForm({ description: e.target.value })}
              rows={3}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </Field>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Provider 类型" required>
              <select
                value={form.provider_type}
                disabled={!isNew}
                onChange={(e) => {
                  const p = e.target.value
                  const defaults = getDefaultProviderConfig(p as LlmProvider['provider_type'])
                  updateForm({
                    provider_type: defaults.provider_type,
                    kimi_cli_path: (defaults.config_json.kimi_cli_path as string) || '',
                    api_base: (defaults.config_json.api_base as string) || '',
                    model: (defaults.config_json.model as string) || '',
                  })
                }}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm disabled:bg-gray-100"
              >
                {PROVIDER_TYPES.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="超时时间（秒）">
              <input
                type="number"
                value={form.timeout}
                onChange={(e) => updateForm({ timeout: parseInt(e.target.value, 10) || 0 })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </Field>
          </div>

          {form.provider_type === 'kimi-cli' && (
            <Field label="Kimi CLI 路径" required>
              <input
                type="text"
                value={form.kimi_cli_path}
                onChange={(e) => updateForm({ kimi_cli_path: e.target.value })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </Field>
          )}

          {(form.provider_type === 'openai' || form.provider_type === 'kimi-api') && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <Field label="API Base">
                  <input
                    type="text"
                    value={form.api_base}
                    onChange={(e) => updateForm({ api_base: e.target.value })}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </Field>
                <Field label="模型">
                  <input
                    type="text"
                    value={form.model}
                    onChange={(e) => updateForm({ model: e.target.value })}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </Field>
              </div>
              <Field label="API Key">
                <input
                  type="password"
                  value={form.api_key}
                  placeholder={!isNew ? '不修改请留空' : ''}
                  onChange={(e) => updateForm({ api_key: e.target.value })}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </Field>
            </>
          )}
        </div>

        <StickyActionBar onCancel={handleCancel} saving={saving} />
      </form>
    </div>
  )
}

function Field({
  label,
  required,
  children,
}: {
  label: string
  required?: boolean
  children: React.ReactNode
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-700 mb-1">
        {label}
        {required && <span className="text-red-500 ml-0.5">*</span>}
      </label>
      {children}
    </div>
  )
}
