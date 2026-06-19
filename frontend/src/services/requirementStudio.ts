import api from './api'

export interface StageStatus {
  stage_id: string
  stage_name: string
  status: string
  locked: boolean
  completed: boolean
  progress_percent: number
}

export interface RequirementStudioStatus {
  project_id: string
  stages: StageStatus[]
  current_stage_id: string | null
  overall_progress: number
}

export interface ArtifactSummary {
  artifact_id: string
  file_name: string
  file_type: string
  stage_id: string | null
  created_at: string | null
  content_preview?: string
  file_path?: string
}

export interface BaselinePayload {
  name: string
  description?: string
  stage_ids?: string[]
}

export interface StaleAnalysisResult {
  stale_artifacts: Array<{
    artifact_id: string
    artifact_name: string
    stage_id: string
    last_updated: string
    stale_reason: string
  }>
  summary: string
}

export interface ChangeRequestPayload {
  title: string
  description: string
  affected_artifacts: string[]
  target_stage_id: string
}

export async function fetchStudioStatus(projectId: string): Promise<RequirementStudioStatus> {
  const res = await api.get<RequirementStudioStatus>(`/v1/requirement-studio/${projectId}/status`)
  return res.data
}

export async function executeStage(projectId: string, stageId: string): Promise<void> {
  await api.post(`/v1/requirement-studio/${projectId}/stage/${stageId}/execute`)
}

export async function fetchArtifacts(projectId: string): Promise<ArtifactSummary[]> {
  const res = await api.get<ArtifactSummary[]>(`/v1/requirement-studio/${projectId}/artifacts`)
  return res.data
}

export async function createBaseline(projectId: string, payload: BaselinePayload): Promise<void> {
  await api.post(`/v1/requirement-studio/${projectId}/governance/baseline`, payload)
}

export async function fetchStaleAnalysis(projectId: string): Promise<StaleAnalysisResult> {
  const res = await api.get<StaleAnalysisResult>(
    `/v1/requirement-studio/${projectId}/governance/stale-analysis`,
  )
  return res.data
}

export async function createChangeRequest(
  projectId: string,
  payload: ChangeRequestPayload,
): Promise<void> {
  await api.post(`/v1/requirement-studio/${projectId}/governance/change-request`, payload)
}
