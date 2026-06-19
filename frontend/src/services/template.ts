import api from './api'

export interface Template {
  template_id: string
  template_name: string
  description: string
  stage_count: number
  estimated_skill_count: number
  applicable_complexity: string
  config_json?: Record<string, unknown> | null
  default_execution_strategy: string
  merge_policy_json?: { groups?: Array<{ group_id: string; label: string; business_stage_keys: string[]; gate_at_end?: boolean; auto_advance?: boolean }> } | null
}

export interface TemplateStage {
  stage_id: string
  stage_name: string
  business_stage_key: string | null
  order_index: number
  template_id: string
  primary_skill_id: string | null
  auxiliary_skill_ids: string[] | null
  gate_id: string | null
  skippable: boolean
  merge_group_id: string | null
}

export interface ProjectStage {
  project_stage_id: string
  project_id: string
  stage_id: string
  order_index: number
  status: string
  primary_skill_id: string | null
  skippable: boolean
  is_frozen: boolean
  merge_group_id: string | null
  execution_status: string
}

export interface TemplateDetail {
  template: Template
  stages: TemplateStage[]
}

export interface ImpactPreview {
  frozen_count: number
  removed_count: number
  added_count: number
  retained_count: number
}

export interface DeviationItem {
  stage_id: string
  stage_name: string
  change_type: string
  old_skill_id?: string | null
  new_skill_id?: string | null
  old_auxiliary_skill_ids?: string[] | null
  new_auxiliary_skill_ids?: string[] | null
}

export interface DeviationLog {
  deviation_id: string
  project_id: string
  decision_type: string
  reason: string | null
  details_json: string | null
  operator_id: string | null
  created_at: string | null
}

export async function fetchTemplates(): Promise<Template[]> {
  const res = await api.get<Template[]>('/v1/templates')
  return res.data
}

export async function fetchTemplateDetail(level: string): Promise<TemplateDetail> {
  const res = await api.get<TemplateDetail>(`/v1/templates/${level}`)
  return res.data
}

export async function fetchStageSequence(projectId: string): Promise<ProjectStage[]> {
  const res = await api.get<ProjectStage[]>(`/v1/templates/projects/${projectId}/stage-sequence`)
  return res.data
}

export async function previewDeviation(
  projectId: string,
  newTemplateId: string,
): Promise<ImpactPreview> {
  const res = await api.post<ImpactPreview>(
    `/v1/templates/projects/${projectId}/template-deviation/preview`,
    { new_template_id: newTemplateId },
  )
  return res.data
}

export async function confirmDeviation(
  projectId: string,
  newTemplateId: string,
): Promise<{ success: boolean; project_id: string }> {
  const res = await api.post<{ success: boolean; project_id: string }>(
    `/v1/templates/projects/${projectId}/template-deviation`,
    { new_template_id: newTemplateId },
  )
  return res.data
}

export async function confirmDeviationWithReason(
  projectId: string,
  payload: {
    new_template_id: string
    reason: string
    risk_acknowledged: boolean
    deviation_items: DeviationItem[]
  },
): Promise<{ frozen: number; removed: number; added: number }> {
  const res = await api.post<{ frozen: number; removed: number; added: number }>(
    `/v1/templates/projects/${projectId}/template-deviation`,
    payload,
  )
  return res.data
}

export async function fetchDeviationLogs(projectId: string): Promise<DeviationLog[]> {
  const res = await api.get<DeviationLog[]>(
    `/v1/templates/projects/${projectId}/template-deviation-logs`,
  )
  return res.data
}

export async function updateStageSkippable(
  projectId: string,
  stageId: string,
  skippable: boolean,
): Promise<ProjectStage> {
  const res = await api.put<ProjectStage>(
    `/v1/templates/projects/${projectId}/stages/${stageId}/skippable`,
    { skippable },
  )
  return res.data
}

export async function reorderStages(
  projectId: string,
  stageOrders: [string, number][],
): Promise<ProjectStage[]> {
  const res = await api.put<ProjectStage[]>(
    `/v1/templates/projects/${projectId}/stages/reorder`,
    { stage_orders: stageOrders },
  )
  return res.data
}

export async function mergeStages(
  projectId: string,
  sourceStageId: string,
  targetStageId: string,
  newStageName?: string,
): Promise<ProjectStage[]> {
  const res = await api.post<ProjectStage[]>(
    `/v1/templates/projects/${projectId}/stages/merge`,
    { source_stage_id: sourceStageId, target_stage_id: targetStageId, new_stage_name: newStageName },
  )
  return res.data
}

export async function splitStage(
  projectId: string,
  stageId: string,
  firstStageName?: string,
  secondStageName?: string,
): Promise<ProjectStage[]> {
  const res = await api.post<ProjectStage[]>(
    `/v1/templates/projects/${projectId}/stages/split`,
    { stage_id: stageId, first_stage_name: firstStageName, second_stage_name: secondStageName },
  )
  return res.data
}

export async function freezeTemplate(projectId: string): Promise<{ frozen_count: number; project_id: string }> {
  const res = await api.post<{ frozen_count: number; project_id: string }>(
    `/v1/templates/projects/${projectId}/freeze-template`,
  )
  return res.data
}

export interface TemplateStageUpdatePayload {
  primary_skill_id?: string | null
  auxiliary_skill_ids?: string[] | null
}

export async function updateTemplateStage(
  level: string,
  stageId: string,
  payload: TemplateStageUpdatePayload,
): Promise<TemplateStage> {
  const res = await api.put<TemplateStage>(
    `/v1/templates/${level}/stages/${stageId}`,
    payload,
  )
  return res.data
}

export interface TemplateExecutionStrategyUpdatePayload {
  default_execution_strategy: string
}

export async function updateTemplateExecutionStrategy(
  level: string,
  payload: TemplateExecutionStrategyUpdatePayload,
): Promise<Template> {
  const res = await api.put<Template>(
    `/v1/templates/${level}/execution-strategy`,
    payload,
  )
  return res.data
}
