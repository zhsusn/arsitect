import api from './api'

export type LlmScope = 'managed' | 'global' | 'project' | 'user'

export type LlmProviderType = 'kimi-cli' | 'kimi-api' | 'openai' | 'arsitect-agent'

export interface LlmProviderConfigJson {
  provider?: string
  kimi_cli_path?: string
  api_base?: string
  model?: string
  timeout?: number
}

export interface LlmProvider {
  id: string
  name: string
  key: string
  scope: LlmScope
  scope_target: string | null
  priority: number
  provider_type: LlmProviderType
  config_json: LlmProviderConfigJson
  has_api_key: boolean
  description: string | null
  is_default: boolean
  is_enabled: boolean
  created_at: string
  updated_at: string
}

export type LlmPermission = 'allow' | 'ask' | 'deny'

export type LlmRuleCategory = 'high_risk' | 'file_system' | 'terminal' | 'network'

export type LlmActionType =
  | 'file_read'
  | 'file_write'
  | 'file_delete'
  | 'terminal'
  | 'web_fetch'
  | 'external_api'

export interface LlmPolicyRule {
  id?: string
  category: LlmRuleCategory
  action_type: LlmActionType
  permission: LlmPermission
  pattern: string
  description: string | null
  sort_order: number
}

export interface LlmPolicy {
  id: string
  name: string
  key: string
  scope: LlmScope
  scope_target: string | null
  priority: number
  default_mode: LlmPermission
  description: string | null
  template_id: string | null
  is_customized: boolean
  is_enabled: boolean
  rules: LlmPolicyRule[]
  created_at: string
  updated_at: string
}

export interface PolicyTemplate {
  id: 'personal' | 'team' | 'enterprise'
  name: string
  description: string | null
  default_mode: LlmPermission
  rules_json: LlmPolicyRule[]
}

export interface ProviderTestResult {
  success: boolean
  message: string
  latency_ms?: number
}

export interface PermissionCheckRequest {
  policy_id?: string
  policy_key?: string
  scope?: LlmScope
  scope_target?: string | null
  action_type: LlmActionType
  target: string
  project_id?: string
  user_id?: string
}

export interface PermissionCheckResult {
  allowed: boolean
  permission: LlmPermission
  matched_rule: LlmPolicyRule | null
  message: string
  suggest_whitelist: boolean
}

export interface ProviderCreate {
  name: string
  key: string
  scope: LlmScope
  scope_target?: string | null
  priority?: number
  provider_type: LlmProviderType
  config_json?: LlmProviderConfigJson
  api_key?: string | null
  description?: string | null
  is_enabled?: boolean
  is_default?: boolean
}

export interface ProviderUpdate {
  name?: string
  priority?: number
  config_json?: LlmProviderConfigJson
  api_key?: string | null
  description?: string | null
  is_enabled?: boolean
  is_default?: boolean
}

export interface PolicyCreate {
  name: string
  key: string
  scope: LlmScope
  scope_target?: string | null
  priority?: number
  default_mode: LlmPermission
  description?: string | null
  rules?: LlmPolicyRule[]
  template_id?: string | null
  is_enabled?: boolean
}

export interface PolicyUpdate {
  name?: string
  priority?: number
  default_mode?: LlmPermission
  description?: string | null
  rules?: LlmPolicyRule[]
  template_id?: string | null
  is_enabled?: boolean
}

export interface ListParams {
  scope?: LlmScope | ''
  scope_target?: string | null
  keyword?: string
  is_enabled?: boolean | ''
  page?: number
  size?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
}

function buildParams(params?: ListParams): Record<string, unknown> {
  if (!params) return {}
  const result: Record<string, unknown> = {}
  if (params.scope) result.scope = params.scope
  if (params.scope_target !== undefined && params.scope_target !== null) {
    result.scope_target = params.scope_target
  }
  if (params.keyword) result.keyword = params.keyword
  if (params.is_enabled !== undefined && params.is_enabled !== '') {
    result.is_enabled = params.is_enabled
  }
  if (params.page !== undefined) result.page = params.page
  if (params.size !== undefined) result.size = params.size
  return result
}

export const llmProviderApi = {
  list: (params?: ListParams) =>
    api
      .get<PaginatedResponse<LlmProvider>>('/v1/llm/providers', { params: buildParams(params) })
      .then((r) => r.data),

  get: (id: string) => api.get<LlmProvider>(`/v1/llm/providers/${id}`).then((r) => r.data),

  create: (data: ProviderCreate) =>
    api.post<LlmProvider>('/v1/llm/providers', data).then((r) => r.data),

  update: (id: string, data: ProviderUpdate) =>
    api.put<LlmProvider>(`/v1/llm/providers/${id}`, data).then((r) => r.data),

  remove: (id: string) => api.delete(`/v1/llm/providers/${id}`),

  clone: (id: string) =>
    api.post<LlmProvider>(`/v1/llm/providers/${id}/clone`).then((r) => r.data),

  setDefault: (id: string) =>
    api.post<LlmProvider>(`/v1/llm/providers/${id}/set-default`).then((r) => r.data),

  test: (id: string) =>
    api.post<ProviderTestResult>(`/v1/llm/providers/${id}/test`).then((r) => r.data),
}

export const llmPolicyApi = {
  list: (params?: ListParams) =>
    api
      .get<PaginatedResponse<LlmPolicy>>('/v1/llm/policies', { params: buildParams(params) })
      .then((r) => r.data),

  get: (id: string) => api.get<LlmPolicy>(`/v1/llm/policies/${id}`).then((r) => r.data),

  create: (data: PolicyCreate) => api.post<LlmPolicy>('/v1/llm/policies', data).then((r) => r.data),

  update: (id: string, data: PolicyUpdate) =>
    api.put<LlmPolicy>(`/v1/llm/policies/${id}`, data).then((r) => r.data),

  remove: (id: string) => api.delete(`/v1/llm/policies/${id}`),

  listTemplates: () =>
    api.get<PaginatedResponse<PolicyTemplate>>('/v1/llm/policies/templates').then((r) => r.data),

  applyTemplate: (templateId: string, basePolicyId?: string) =>
    api
      .post<LlmPolicy>('/v1/llm/policies/apply-template', {
        template_id: templateId,
        base_policy_id: basePolicyId,
      })
      .then((r) => r.data),

  addRule: (policyId: string, rule: Omit<LlmPolicyRule, 'id'>) =>
    api.post<LlmPolicyRule>(`/v1/llm/policies/${policyId}/rules`, rule).then((r) => r.data),

  updateRuleOrder: (policyId: string, ruleIds: string[]) =>
    api
      .put<LlmPolicyRule[]>(`/v1/llm/policies/${policyId}/rules/order`, { rule_ids: ruleIds })
      .then((r) => r.data),

  check: (data: PermissionCheckRequest) =>
    api.post<PermissionCheckResult>('/v1/llm/policies/check', data).then((r) => r.data),
}
