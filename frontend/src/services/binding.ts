import api from './api'

export interface BindingRule {
  rule_id: string
  project_id: string
  source_field: string
  target_field: string
  transform_type: 'DIRECT' | 'MAP' | 'FORMAT' | 'FILTER'
  transform_config: string | null
  status: 'ACTIVE' | 'INACTIVE'
  created_at: string | null
  updated_at: string | null
}

export interface BindingCreatePayload {
  source_field: string
  target_field: string
  transform_type?: string
  transform_config?: string | null
  status?: string
}

export interface BindingUpdatePayload {
  source_field?: string
  target_field?: string
  transform_type?: string
  transform_config?: string | null
  status?: string
}

export interface CoverageScan {
  scan_id: string
  project_id: string
  status: string
  coverage_percent: number | null
  gap_count: number | null
  redundant_count: number | null
  diff_count: number | null
  wireframe_page_count: number | null
  openui_page_count: number | null
  c4_interface_count: number | null
  summary_json: string | null
  created_at: string | null
  updated_at: string | null
}

export interface CoverageScanItem {
  item_id: string
  scan_id: string
  project_id: string
  interface_name: string
  endpoint_path: string | null
  method_type: string | null
  source_location: string | null
  source_type: string
  result_type: string
  expected_params: string | null
  actual_params: string | null
  is_selected_for_writeback: boolean
  review_status: string | null
  created_at: string | null
}

export interface CoverageScanDetail {
  scan: CoverageScan
  items: CoverageScanItem[]
}

export interface WritebackResult {
  scan_id: string
  created_count: number
  contracts: Array<{ contract_id: string; path: string; method: string }>
}

export async function listBindingRules(projectId: string): Promise<BindingRule[]> {
  const res = await api.get<BindingRule[]>(`/v1/projects/${projectId}/binding-rules`)
  return res.data
}

export async function createBindingRule(projectId: string, payload: BindingCreatePayload): Promise<BindingRule> {
  const res = await api.post<BindingRule>(`/v1/projects/${projectId}/binding-rules`, payload)
  return res.data
}

export async function getBindingRule(ruleId: string): Promise<BindingRule> {
  const res = await api.get<BindingRule>(`/v1/binding-rules/${ruleId}`)
  return res.data
}

export async function updateBindingRule(ruleId: string, payload: BindingUpdatePayload): Promise<BindingRule> {
  const res = await api.patch<BindingRule>(`/v1/binding-rules/${ruleId}`, payload)
  return res.data
}

export async function deleteBindingRule(ruleId: string): Promise<void> {
  await api.delete(`/v1/binding-rules/${ruleId}`)
}

export async function listCoverageScans(projectId: string): Promise<CoverageScan[]> {
  const res = await api.get<CoverageScan[]>(`/v1/projects/${projectId}/coverage-scans`)
  return res.data
}

export async function createCoverageScan(projectId: string): Promise<CoverageScan> {
  const res = await api.post<CoverageScan>(`/v1/projects/${projectId}/coverage-scans`)
  return res.data
}

export async function getCoverageScan(scanId: string, resultType?: string): Promise<CoverageScanDetail> {
  const res = await api.get<CoverageScanDetail>(`/v1/coverage-scans/${scanId}`, {
    params: resultType ? { result_type: resultType } : undefined,
  })
  return res.data
}

export async function toggleWriteback(itemId: string, selected: boolean): Promise<CoverageScanItem> {
  const res = await api.patch<CoverageScanItem>(`/v1/coverage-scan-items/${itemId}/writeback`, { selected })
  return res.data
}

export async function applyWriteback(scanId: string): Promise<WritebackResult> {
  const res = await api.post<WritebackResult>(`/v1/coverage-scans/${scanId}/writeback`)
  return res.data
}

export async function reviewItem(itemId: string, status: 'approved' | 'rejected'): Promise<CoverageScanItem> {
  const res = await api.post<CoverageScanItem>(`/v1/coverage-scan-items/${itemId}/review`, { status })
  return res.data
}
