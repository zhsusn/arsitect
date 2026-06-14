import api from './api'

export interface ConfigNode {
  id: string
  node_type: string
  scope: 'managed' | 'global' | 'project' | 'user'
  scope_target: string | null
  key: string
  name: string
  description?: string
  is_enabled: boolean
  is_default: boolean
  priority: number
  config_json: Record<string, unknown>
  secret_json?: Record<string, unknown> | null
  created_by?: string | null
  updated_by?: string | null
  created_at: string
  updated_at: string
}

export interface ConfigNodeList {
  items: ConfigNode[]
  total: number
}

export interface ConfigNodeCreate {
  node_type: string
  scope: 'managed' | 'global' | 'project' | 'user'
  scope_target?: string | null
  key: string
  name: string
  description?: string
  is_enabled?: boolean
  is_default?: boolean
  priority?: number
  config_json?: Record<string, unknown>
  secret_json?: Record<string, unknown> | null
}

export interface ConfigNodeUpdate {
  name?: string
  description?: string
  is_enabled?: boolean
  is_default?: boolean
  priority?: number
  config_json?: Record<string, unknown>
  secret_json?: Record<string, unknown> | null
}

export interface ProviderTestResult {
  success: boolean
  message: string
  latency_ms?: number
}

export interface PermissionCheckRequest {
  category: 'file_read' | 'file_write' | 'terminal' | 'web_fetch' | 'external_api'
  path?: string
  command?: string
  domain?: string
  project_id?: string
  user_id?: string
}

export interface PermissionCheckResult {
  category: string
  decision: 'allow' | 'ask' | 'deny'
  default_mode: 'allow' | 'ask' | 'deny'
  rules: Array<{
    node_id: string
    node_name: string
    scope: string
    scope_target: string | null
    decision: string
    matched_pattern: string | null
  }>
}

export const configNodeApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<ConfigNodeList>('/v1/config/nodes', { params }).then((r) => r.data),

  get: (id: string) => api.get<ConfigNode>(`/v1/config/nodes/${id}`).then((r) => r.data),

  create: (data: ConfigNodeCreate) =>
    api.post<ConfigNode>('/v1/config/nodes', data).then((r) => r.data),

  update: (id: string, data: ConfigNodeUpdate) =>
    api.put<ConfigNode>(`/v1/config/nodes/${id}`, data).then((r) => r.data),

  remove: (id: string) => api.delete(`/v1/config/nodes/${id}`),

  clone: (id: string) =>
    api.post<ConfigNode>(`/v1/config/nodes/${id}/clone`).then((r) => r.data),

  testProvider: (id: string) =>
    api.post<ProviderTestResult>(`/v1/config/nodes/${id}/test`).then((r) => r.data),

  resolve: (nodeType: string, projectId?: string, userId?: string) =>
    api
      .post<{
        node_type: string
        project_id: string | null
        user_id: string | null
        config: Record<string, unknown>
        source_nodes: ConfigNode[]
      }>('/v1/config/resolve', { node_type: nodeType, project_id: projectId, user_id: userId })
      .then((r) => r.data),

  checkPermission: (data: PermissionCheckRequest) =>
    api.post<PermissionCheckResult>('/v1/config/check-permission', data).then((r) => r.data),

  defaultProvider: () =>
    api.get<Record<string, unknown>>('/v1/config/default-llm-provider').then((r) => r.data),

  defaultPermissionPolicy: () =>
    api.get<Record<string, unknown>>('/v1/config/default-permission-policy').then((r) => r.data),
}
