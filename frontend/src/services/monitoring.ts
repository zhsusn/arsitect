import api from './api'

export interface MonitoringOverview {
  total_projects: number
  active_projects: number
  risk_projects: number
  pending_gates: number
  total_executions: number
}

export interface ProjectStats {
  stage_count: number
  execution_count: number
  gate_count: number
  log_count: number
}

export interface OperationLog {
  log_id: string
  project_id: string
  operator_id: string | null
  action: string
  target_type: string | null
  target_id: string | null
  detail: string | null
  created_at: string | null
}

export interface OperationLogList {
  logs: OperationLog[]
  total: number
}

export async function fetchMonitoringOverview(): Promise<MonitoringOverview> {
  const res = await api.get<MonitoringOverview>('/v1/monitoring/overview')
  return res.data
}

export async function fetchProjectStats(projectId: string): Promise<ProjectStats> {
  const res = await api.get<ProjectStats>(`/v1/monitoring/projects/${projectId}/stats`)
  return res.data
}

export async function fetchOperationLogs(projectId: string, limit = 50): Promise<OperationLog[]> {
  const res = await api.get<OperationLogList>(`/v1/monitoring/projects/${projectId}/operation-logs`, {
    params: { limit },
  })
  return res.data.logs
}
