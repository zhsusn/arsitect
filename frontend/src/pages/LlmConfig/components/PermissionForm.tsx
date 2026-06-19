import { useEffect, useMemo, useState } from 'react'
import { type LlmPolicy, type LlmPolicyRule, type PolicyUpdate } from '../../../services/llm'
import { llmPolicyApi } from '../../../services/llm'
import { type LlmPermission } from '../../../services/llm'
import { DEFAULT_MODES, normalizeRules, reorderRulesWithinGroups } from '../types'
import DetailHeader from './DetailHeader'
import RuleEditor from './RuleEditor'
import StickyActionBar from './StickyActionBar'
import { useFormDraft } from '../hooks/useFormDraft'
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts'

interface PermissionFormProps {
  policy: LlmPolicy | null
  isNew: boolean
  saving: boolean
  error: string | null
  onSave: (data: PolicyUpdate) => void
  onCancel: () => void
  onChange?: () => void
}

interface FormData {
  name: string
  description: string
  priority: number
  default_mode: LlmPermission
  rules: LlmPolicyRule[]
  templateId: string | null
}

const FORM_ID = 'llm-config-form'

function initialData(policy: LlmPolicy | null): FormData {
  return {
    name: policy?.name || '',
    description: policy?.description || '',
    priority: policy?.priority ?? 0,
    default_mode: policy?.default_mode || 'ask',
    rules: normalizeRules(policy?.rules || []),
    templateId: policy?.template_id || null,
  }
}

export default function PermissionForm({
  policy,
  isNew,
  saving,
  error,
  onSave,
  onCancel,
  onChange,
}: PermissionFormProps) {
  const [form, setForm] = useState<FormData>(initialData(policy))
  const [touched, setTouched] = useState(false)
  const [isDirty, setIsDirty] = useState(false)
  const [templateLabel, setTemplateLabel] = useState<string | null>(null)

  useEffect(() => {
    setForm(initialData(policy))
    setTouched(false)
    setIsDirty(false)
    setTemplateLabel(null)
  }, [policy])

  const { clearDraft } = useFormDraft<FormData>({
    key: `llm-config-draft-policy-${policy?.id || 'new'}`,
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
    return errors
  }, [form])

  const updateForm = (patch: Partial<FormData>) => {
    setForm((f) => ({ ...f, ...patch }))
    setIsDirty(true)
    onChange?.()
  }

  const handleApplyTemplate = async (templateId: string) => {
    if (form.rules.length > 0 && !window.confirm('切换模板将覆盖当前规则，是否继续？')) {
      return
    }
    if (!policy) return
    try {
      const updated = await llmPolicyApi.applyTemplate(templateId, policy.id)
      updateForm({
        rules: normalizeRules(updated.rules),
        default_mode: updated.default_mode,
        templateId: updated.template_id,
      })
      setTemplateLabel(null)
    } catch (err) {
      alert(err instanceof Error ? err.message : '应用模板失败')
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setTouched(true)
    if (validation.length > 0) return
    clearDraft()
    setIsDirty(false)
    onSave({
      name: form.name,
      description: form.description || undefined,
      priority: form.priority,
      default_mode: form.default_mode,
      rules: reorderRulesWithinGroups(form.rules),
      template_id: form.templateId,
    })
  }

  const handleCancel = () => {
    clearDraft()
    setIsDirty(false)
    onCancel()
  }

  useKeyboardShortcuts({ formId: FORM_ID, hasChanges: isDirty, onCancel: handleCancel })

  const isCustomized = Boolean(policy?.template_id && form.rules.length > 0 && templateLabel === null)

  return (
    <div className="h-full overflow-y-auto p-6">
      <form id={FORM_ID} onSubmit={handleSubmit} className="max-w-3xl">
        <DetailHeader mode={isNew ? 'new' : 'edit'} tab="permission" name={form.name} />

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
                data-testid="permission-name-input"
                value={form.name}
                onChange={(e) => updateForm({ name: e.target.value })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </Field>
            <Field label="标识 key">
              <input
                type="text"
                value={policy?.key || ''}
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
                value={policy?.scope || 'global'}
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
            <Field label="默认模式" required>
              <select
                value={form.default_mode}
                onChange={(e) => updateForm({ default_mode: e.target.value as LlmPermission })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {DEFAULT_MODES.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="场景模板">
              <TemplateSelector
                currentTemplateId={form.templateId}
                customized={isCustomized}
                onApply={handleApplyTemplate}
              />
            </Field>
          </div>

          <RuleEditor
            rules={form.rules}
            onChange={(rules) => updateForm({ rules })}
            onMarkUnsaved={onChange}
          />
        </div>

        <StickyActionBar onCancel={handleCancel} saving={saving} />
      </form>
    </div>
  )
}

function TemplateSelector({
  currentTemplateId,
  customized,
  onApply,
}: {
  currentTemplateId: string | null
  customized: boolean
  onApply: (id: string) => void
}) {
  const [templates, setTemplates] = useState<{ id: string; name: string }[]>([])

  useEffect(() => {
    llmPolicyApi.listTemplates().then((res) => {
      setTemplates(res.items.map((t) => ({ id: t.id, name: t.name })))
    })
  }, [])

  const selectedName = templates.find((t) => t.id === currentTemplateId)?.name || '未选择模板'

  return (
    <div className="space-y-2">
      <select
        value={currentTemplateId || ''}
        onChange={(e) => e.target.value && onApply(e.target.value)}
        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">{customized ? `自定义（基于 ${selectedName}）` : selectedName}</option>
        {templates
          .filter((t) => t.id !== currentTemplateId)
          .map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
      </select>
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
