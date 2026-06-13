import api from './api'

export interface HistorySummary {
  project_id: string
  total_stages: number
  total_executions: number
  total_gates: number
  total_reworks: number
}

export interface TimelineEvent {
  event_id: string
  event_type: string
  stage_id: string
  description: string
  created_at: string
}

export interface ReworkAnalysisItem {
  reason: string | null
  count: number
}

export async function fetchHistorySummary(projectId: string): Promise<HistorySummary> {
  const res = await api.get<HistorySummary>(`/v1/applications/${projectId}/history/summary`)
  return res.data
}

export async function fetchTimeline(projectId: string): Promise<TimelineEvent[]> {
  const res = await api.get<TimelineEvent[]>(`/v1/projects/${projectId}/history/timeline`)
  return res.data
}

export async function fetchReworkAnalysis(projectId: string): Promise<ReworkAnalysisItem[]> {
  const res = await api.get<ReworkAnalysisItem[]>(`/v1/projects/${projectId}/history/rework-analysis`)
  return res.data
}
