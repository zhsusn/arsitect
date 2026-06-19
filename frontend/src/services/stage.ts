import api from './api'

export interface StageProgressItem {
  project_stage_id: string
  stage_id: string
  order_index: number
  business_stage_key: string | null
  merge_group_label?: string | null
  runtime_status: string
  primary_skill_id: string | null
  started_at: string | null
  completed_at: string | null
  progress_percent: number
}

export interface StageProgressResponse {
  project_id: string
  execution_strategy: string
  current_stage_id: string | null
  progress_percent: number
  stages: StageProgressItem[]
}

export interface StageExecuteResponse {
  project_stage_id: string
  execution_ids: string[]
  status: string
  next_stage_id: string | null
}

export interface StageAdvanceResponse {
  project_stage_id: string
  status: string
  next_stage_id: string | null
}

export interface StageGateDecisionResponse {
  project_stage_id: string
  status: string
  next_stage_id: string | null
}

export interface StageGateDecision {
  decision_id: string
  gate_id: string
  project_id: string
  gate_type: string
  status: string
  confidence: string | null
  decision_type: string | null
  decision_by: string | null
  decision_at: string | null
  duration_sec: number | null
  reason: string | null
  unlocked_stages: string[]
  created_at: string | null
  updated_at: string | null
}

export async function fetchStageProgress(projectId: string): Promise<StageProgressResponse> {
  const res = await api.get<StageProgressResponse>(`/v1/projects/${projectId}/stage-progress`)
  return res.data
}

export async function executeProjectStage(
  projectId: string,
  stageId: string,
): Promise<StageExecuteResponse> {
  const res = await api.post<StageExecuteResponse>(
    `/v1/projects/${projectId}/stages/${stageId}/execute`,
  )
  return res.data
}

export async function advanceProjectStage(
  projectId: string,
  stageId: string,
): Promise<StageAdvanceResponse> {
  const res = await api.post<StageAdvanceResponse>(
    `/v1/projects/${projectId}/stages/${stageId}/advance`,
  )
  return res.data
}

export async function decideProjectStageGate(
  projectId: string,
  stageId: string,
  decision: 'pass' | 'reject',
  reason?: string,
): Promise<StageGateDecisionResponse> {
  const res = await api.post<StageGateDecisionResponse>(
    `/v1/projects/${projectId}/stages/${stageId}/gate/decide`,
    { decision, reason },
  )
  return res.data
}

export async function startProject(projectId: string): Promise<{ project_id: string; current_stage_id: string; status: string }> {
  const res = await api.post<{ project_id: string; current_stage_id: string; status: string }>(
    `/v1/projects/${projectId}/start`,
  )
  return res.data
}

export async function fetchProjectStageGate(
  projectId: string,
  stageId: string,
): Promise<StageGateDecision | null> {
  const res = await api.get<StageGateDecision | null>(
    `/v1/projects/${projectId}/stages/${stageId}/gate`,
  )
  return res.data
}

export interface StageDetailResponse {
  project_stage_id: string
  project_id: string
  stage_id: string
  status: string
  order_index: number
  review_status: string
  annotations_count: number
}

export async function fetchStageDetail(stageId: string): Promise<StageDetailResponse> {
  const res = await api.get<StageDetailResponse>(`/v1/stages/${stageId}`)
  return res.data
}

export interface StageRollbackResponse {
  project_id: string
  target_stage_id: string
  reset_stage_ids: string[]
  stale_artifact_ids: string[]
}

export async function rollbackProjectStage(
  projectId: string,
  stageId: string,
  targetStageId: string,
  reason?: string,
): Promise<StageRollbackResponse> {
  const res = await api.post<StageRollbackResponse>(
    `/v1/projects/${projectId}/stages/${stageId}/rollback`,
    { target_stage_id: targetStageId, reason },
  )
  return res.data
}

export async function fetchPreviousStage(
  projectId: string,
  currentStageId: string,
): Promise<StageProgressItem | null> {
  const progress = await fetchStageProgress(projectId)
  const current = progress.stages.find((s) => s.project_stage_id === currentStageId)
  if (!current) return null
  return (
    progress.stages.find((s) => s.order_index === current.order_index - 1) || null
  )
}

export interface StageExecutionStatus {
  stage_id: string
  runtime_status: string
  current_phase: string
  overall_status: string
  progress_percent: number
  error_summary: string | null
  artifact_paths: string[]
  running_execution_ids: string[]
  latest_execution: {
    execution_id: string
    skill_name: string
    overall_status: string
    current_phase: string
  } | null
}

export async function fetchStageExecutionStatus(stageId: string): Promise<StageExecutionStatus> {
  const res = await api.get<StageExecutionStatus>(`/v1/stages/${stageId}/execution-status`)
  return res.data
}

export async function stopExecution(executionId: string): Promise<void> {
  await api.post(`/v1/executions/${executionId}/stop`)
}
