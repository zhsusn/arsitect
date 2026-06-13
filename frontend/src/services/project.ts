import api from './api'

export interface PageResponse<T> {
  data: T[]
  total_count: number
  page: number
  page_size: number
  total_pages: number
  has_next: boolean
  has_previous: boolean
}

export interface ApplicationItem {
  application_id: string
  application_name: string
  description: string | null
  local_path: string
  workspace_id: string
  path_accessible: boolean
}

export interface Project {
  project_id: string
  project_name: string
  project_description: string | null
  project_status: 'Draft' | 'Active' | 'Archived' | 'Cancelled'
  application_id: string
  template_level: string
  progress_percent: number
  current_stage: string | null
  risk_level: 'None' | 'Low' | 'Medium' | 'High'
  last_activity_at: string | null
  last_activity_type: string | null
  size_estimate_id: string | null
  created_at: string
  updated_at: string
}

export interface RiskAlert {
  alert_type: string
  severity: 'Low' | 'Medium' | 'High'
  message: string
  project_id: string | null
  stage_id: string | null
}

export interface TimeboxEntry {
  stage_id: string
  stage_name: string
  planned_days: number
  elapsed_days: number
  remaining_days: number
  deviation_percent: number
  alert_level: string | null
}

export interface ProjectCreatePayload {
  project_id?: string
  project_name: string
  project_description?: string | null
  template_level: string
}

export interface ProjectUpdatePayload {
  project_name?: string
  project_description?: string | null
}

export interface StageProgress {
  stage_id: string
  stage_name: string
  order_index: number
  status: string
  execution_status: string
  progress_percent: number
  planned_days: number | null
  elapsed_days: number | null
  skippable: boolean
}

export interface ArtifactSummary {
  artifact_id: string
  file_name: string
  file_type: string
  stage_id: string | null
  created_at: string | null
}

export interface OperationLogItem {
  log_id: string
  action: string
  operator_id: string | null
  target_type: string | null
  detail: string | null
  created_at: string | null
}

export interface SizeEstimateResult {
  estimate_id: string | null
  module_count: number | null
  interface_count: number | null
  page_count: number | null
  tech_complexity: string | null
  risk_level: string | null
  optimistic_score: number | null
  expected_score: number | null
  conservative_score: number | null
  complexity_level: string | null
}

export interface ProjectOverview {
  project: Project
  size_estimate: SizeEstimateResult | null
  stages: StageProgress[]
  artifacts: ArtifactSummary[]
  operation_logs: OperationLogItem[]
}

export interface ComplexityAssessPayload {
  module_count: number
  interface_complexity: number
  page_count: number
  entity_count: number
  integration_count: number
}

export interface ComplexityAssessResult {
  optimistic_score: number
  expected_score: number
  conservative_score: number
  complexity_level: string
  radar_values: Record<string, number> | null
}

export interface SizeEstimatePayload {
  module_count: number
  interface_count: number
  page_count: number
  tech_complexity: string
  risk_level: string
}

export interface SizeEstimateResponse {
  estimate_id: string
  project_id: string
  module_count: number
  interface_count: number
  page_count: number
  tech_complexity: string
  risk_level: string
  optimistic_score: number | null
  expected_score: number | null
  conservative_score: number | null
  complexity_level: string | null
  created_at: string | null
}

export async function fetchProjects(appId: string): Promise<Project[]> {
  const res = await api.get(`/v1/applications/${appId}/projects`)
  return (res.data as { data?: Project[] })?.data ?? []
}

export async function createProject(
  appId: string,
  payload: ProjectCreatePayload,
): Promise<Project> {
  const res = await api.post<Project>(`/v1/applications/${appId}/projects`, payload)
  return res.data
}

export async function getProject(projectId: string): Promise<Project> {
  const res = await api.get<Project>(`/v1/projects/${projectId}`)
  return res.data
}

export async function updateProject(
  projectId: string,
  payload: ProjectUpdatePayload,
): Promise<Project> {
  const res = await api.patch<Project>(`/v1/projects/${projectId}`, payload)
  return res.data
}

export async function archiveProject(projectId: string): Promise<void> {
  await api.post(`/v1/projects/${projectId}/archive`)
}

export async function activateProject(projectId: string): Promise<Project> {
  const res = await api.post<Project>(`/v1/projects/${projectId}/activate`)
  return res.data
}

export async function cancelProject(projectId: string): Promise<Project> {
  const res = await api.post<Project>(`/v1/projects/${projectId}/cancel`)
  return res.data
}

export async function fetchRiskAlerts(projectId: string): Promise<RiskAlert[]> {
  const res = await api.get<RiskAlert[]>(`/v1/projects/${projectId}/risk-alerts`)
  return res.data
}

export async function fetchTimebox(projectId: string): Promise<TimeboxEntry[]> {
  const res = await api.get<TimeboxEntry[]>(`/v1/projects/${projectId}/timebox`)
  return res.data
}

export async function fetchProjectOverview(projectId: string): Promise<ProjectOverview> {
  const res = await api.get<ProjectOverview>(`/v1/projects/${projectId}/overview`)
  return res.data
}

export async function fetchProjectStages(projectId: string): Promise<StageProgress[]> {
  const res = await api.get<StageProgress[]>(`/v1/projects/${projectId}/stages`)
  return res.data
}

export async function fetchProjectOperationLogs(
  projectId: string,
  limit = 20,
): Promise<OperationLogItem[]> {
  const res = await api.get<OperationLogItem[]>(`/v1/projects/${projectId}/operation-logs`, {
    params: { limit },
  })
  return res.data
}

export async function calculateComplexity(
  payload: ComplexityAssessPayload,
): Promise<ComplexityAssessResult> {
  const res = await api.post<ComplexityAssessResult>('/v1/assess', payload)
  return res.data
}

export async function createSizeEstimate(
  projectId: string,
  payload: SizeEstimatePayload,
): Promise<SizeEstimateResponse> {
  const res = await api.post<SizeEstimateResponse>(
    `/v1/projects/${projectId}/size-estimates`,
    payload,
  )
  return res.data
}

export async function bindSizeEstimate(
  projectId: string,
  estimateId: string | null,
): Promise<{ status: string; project_id: string }> {
  const res = await api.patch(`/v1/projects/${projectId}/size-estimate`, {
    estimate_id: estimateId,
  })
  return res.data
}

export async function fetchApplications(): Promise<PageResponse<ApplicationItem>> {
  const res = await api.get<PageResponse<ApplicationItem>>('/v1/applications?page_size=100')
  return res.data
}
