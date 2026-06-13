import api from './api'

export interface ArchValidationSession {
  session_id: string
  project_id: string
  level: string
  baseline_dsl: string | null
  current_dsl: string | null
  status: string
  diff_summary: string | null
  created_at: string
}

export async function triggerValidation(
  projectId: string,
  level: string
): Promise<ArchValidationSession> {
  const res = await api.post<ArchValidationSession>(
    `/v1/projects/${projectId}/arch-validation/trigger`,
    { level }
  )
  return res.data
}

export async function fetchSessions(
  projectId: string
): Promise<ArchValidationSession[]> {
  const res = await api.get<ArchValidationSession[]>(
    `/v1/projects/${projectId}/arch-validation/diffs`
  )
  return res.data
}

export async function updateBaseline(
  projectId: string,
  level: string
): Promise<ArchValidationSession> {
  const res = await api.post<ArchValidationSession>(
    `/v1/projects/${projectId}/arch-validation/baseline/update`,
    { level }
  )
  return res.data
}
