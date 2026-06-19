import type {
  LlmActionType,
  LlmPermission,
  LlmPolicy,
  LlmPolicyRule,
  LlmProvider,
  LlmProviderType,
  LlmRuleCategory,
  LlmScope,
  PolicyTemplate,
} from '../../services/llm'

export type { LlmPolicy, LlmPolicyRule, LlmProvider, PolicyTemplate }

export type TabKey = 'provider' | 'permission'

export type ConfigEntity = LlmProvider | LlmPolicy

export type ProviderFormData = {
  name: string
  description: string
  priority: number
  provider_type: LlmProviderType
  kimi_cli_path: string
  api_base: string
  api_key: string
  model: string
  timeout: number
}

export type PolicyFormData = {
  name: string
  description: string
  priority: number
  default_mode: LlmPermission
  rules: LlmPolicyRule[]
}

export const PROVIDER_TYPES: { value: LlmProviderType; label: string }[] = [
  { value: 'kimi-cli', label: 'Kimi CLI' },
  { value: 'kimi-api', label: 'Kimi API' },
  { value: 'openai', label: 'OpenAI 兼容' },
  { value: 'arsitect-agent', label: 'Arsitect Agent' },
] as const

export const ACTION_TYPES: { value: LlmActionType; label: string; category: LlmRuleCategory }[] = [
  { value: 'file_read', label: '文件读取', category: 'file_system' },
  { value: 'file_write', label: '文件写入', category: 'file_system' },
  { value: 'file_delete', label: '文件删除', category: 'file_system' },
  { value: 'terminal', label: '终端执行', category: 'terminal' },
  { value: 'web_fetch', label: '网页抓取', category: 'network' },
  { value: 'external_api', label: '外部 API', category: 'network' },
] as const

export const RULE_CATEGORIES: { value: LlmRuleCategory; label: string }[] = [
  { value: 'high_risk', label: '高危拦截' },
  { value: 'file_system', label: '文件系统' },
  { value: 'terminal', label: '终端执行' },
  { value: 'network', label: '网络访问' },
] as const

export const PERMISSIONS: { value: LlmPermission; label: string; color: string }[] = [
  { value: 'allow', label: '允许', color: 'text-green-600 bg-green-50' },
  { value: 'ask', label: '询问', color: 'text-amber-600 bg-amber-50' },
  { value: 'deny', label: '拒绝', color: 'text-red-600 bg-red-50' },
] as const

export const DEFAULT_MODES: { value: LlmPermission; label: string }[] = [
  { value: 'allow', label: '全部允许' },
  { value: 'ask', label: '默认询问' },
  { value: 'deny', label: '全部拒绝' },
] as const

export const SCOPE_OPTIONS: { value: LlmScope; label: string }[] = [
  { value: 'global', label: '全局' },
  { value: 'project', label: '项目' },
  { value: 'user', label: '用户' },
  { value: 'managed', label: '托管' },
] as const

export function isProvider(entity: ConfigEntity): entity is LlmProvider {
  return 'provider_type' in entity
}

export function isPolicy(entity: ConfigEntity): entity is LlmPolicy {
  return 'default_mode' in entity
}

export function getProviderTypeLabel(value?: LlmProviderType | string): string {
  return PROVIDER_TYPES.find((p) => p.value === value)?.label || value || '-'
}

export function getPermissionLabel(value?: LlmPermission | string): string {
  return PERMISSIONS.find((p) => p.value === value)?.label || value || '-'
}

export function getPermissionColor(value?: LlmPermission | string): string {
  return PERMISSIONS.find((p) => p.value === value)?.color || ''
}

export function getScopeLabel(value?: LlmScope | string): string {
  return SCOPE_OPTIONS.find((s) => s.value === value)?.label || value || '-'
}

export function getActionTypeLabel(value?: LlmActionType | string): string {
  return ACTION_TYPES.find((a) => a.value === value)?.label || value || '-'
}

export function getCategoryLabel(value?: LlmRuleCategory | string): string {
  return RULE_CATEGORIES.find((c) => c.value === value)?.label || value || '-'
}

export function getRuleCategory(actionType: LlmActionType | string): LlmRuleCategory {
  const action = ACTION_TYPES.find((a) => a.value === actionType)
  if (action) return action.category
  const lowered = String(actionType).toLowerCase()
  if (lowered.includes('rm -rf') || lowered.includes('sudo') || lowered.includes('curl') || lowered.includes('wget')) {
    return 'high_risk'
  }
  if (lowered.includes('file')) return 'file_system'
  if (lowered.includes('terminal')) return 'terminal'
  return 'network'
}

export function getCategoryByActionType(actionType: LlmActionType): LlmRuleCategory {
  return getRuleCategory(actionType)
}

export function cloneEntity<T>(entity: T): T {
  return JSON.parse(JSON.stringify(entity))
}

export function normalizeRules(rules: LlmPolicyRule[]): LlmPolicyRule[] {
  return rules.map((rule, index) => ({
    ...rule,
    category: rule.category || getRuleCategory(rule.action_type),
    sort_order: rule.sort_order ?? index,
  }))
}

export function rulesEqual(a: LlmPolicyRule[], b: LlmPolicyRule[]): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
}

export function getDefaultProviderConfig(type: LlmProviderType): {
  provider_type: LlmProviderType
  config_json: Record<string, unknown>
} {
  switch (type) {
    case 'kimi-cli':
      return { provider_type: 'kimi-cli', config_json: { kimi_cli_path: 'kimi' } }
    case 'kimi-api':
      return { provider_type: 'kimi-api', config_json: { api_base: '', model: 'kimi' } }
    case 'openai':
      return {
        provider_type: 'openai',
        config_json: { api_base: 'https://api.openai.com/v1', model: 'gpt-4o-mini' },
      }
    case 'arsitect-agent':
      return { provider_type: 'arsitect-agent', config_json: {} }
    default:
      return { provider_type: type, config_json: {} }
  }
}

export function groupRulesByCategory(rules: LlmPolicyRule[]): Record<LlmRuleCategory, LlmPolicyRule[]> {
  const groups: Record<LlmRuleCategory, LlmPolicyRule[]> = {
    high_risk: [],
    file_system: [],
    terminal: [],
    network: [],
  }
  for (const rule of rules) {
    const category = rule.category || getRuleCategory(rule.action_type)
    groups[category].push(rule)
  }
  return groups
}

export function reorderRulesWithinGroups(rules: LlmPolicyRule[]): LlmPolicyRule[] {
  const groups = groupRulesByCategory(rules)
  const ordered: LlmPolicyRule[] = []
  const categories: LlmRuleCategory[] = ['high_risk', 'file_system', 'terminal', 'network']
  for (const category of categories) {
    ordered.push(
      ...groups[category].map((rule, index) => ({
        ...rule,
        category,
        sort_order: index,
      })),
    )
  }
  return ordered
}

export function buildEmptyRule(category: LlmRuleCategory): LlmPolicyRule {
  const actionType = ACTION_TYPES.find((a) => a.category === category)?.value ?? 'terminal'
  return {
    category,
    action_type: actionType,
    permission: 'ask',
    pattern: category === 'high_risk' ? 'rm -rf *' : '*',
    description: null,
    sort_order: 0,
  }
}

export function buildEmptyProvider(): LlmProvider {
  const now = new Date().toISOString()
  return {
    id: '',
    name: '新 Provider',
    key: `new-provider-${Date.now()}`,
    scope: 'global',
    scope_target: null,
    priority: 0,
    provider_type: 'kimi-cli',
    config_json: { kimi_cli_path: 'kimi', timeout: 120 },
    has_api_key: false,
    description: null,
    is_default: false,
    is_enabled: true,
    created_at: now,
    updated_at: now,
  }
}

export function buildEmptyPolicy(): LlmPolicy {
  const now = new Date().toISOString()
  return {
    id: '',
    name: '新权限策略',
    key: `new-policy-${Date.now()}`,
    scope: 'global',
    scope_target: null,
    priority: 0,
    default_mode: 'ask',
    description: null,
    template_id: null,
    is_customized: false,
    is_enabled: true,
    rules: [],
    created_at: now,
    updated_at: now,
  }
}
