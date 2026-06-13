import api from './api'

export interface BypassRecord {
  record_id: string
  gate_decision_id?: string
  plan_id: string
  stage_id: string
  skill_id: string
  triggered_by: string
  reason: string | null
  status: string
  deadline_at: string | null
  closed_at: string | null
  created_at: string | null
}

export interface BypassApplyPayload {
  plan_id?: string
  stage_id: string
  skill_id: string
  triggered_by: string
  reason: string
  authorizer_token: string
  deadline_hours?: number
}

export interface BypassApprovePayload {
  approved_by: string
}

export async function applyBypass(gateId: string, payload: BypassApplyPayload): Promise<BypassRecord> {
  const res = await api.post<BypassRecord>(`/v1/gates/${gateId}/bypass`, payload)
  return res.data
}

export async function getGateBypass(gateId: string): Promise<BypassRecord | null> {
  try {
    const res = await api.get<BypassRecord>(`/v1/gates/${gateId}/bypass`)
    return res.data
  } catch {
    return null
  }
}

export async function listBypassApplications(projectId: string): Promise<BypassRecord[]> {
  const res = await api.get<BypassRecord[]>(`/v1/projects/${projectId}/bypass-applications`)
  return res.data
}

export async function approveBypass(recordId: string, payload: BypassApprovePayload): Promise<BypassRecord> {
  const res = await api.post<BypassRecord>(`/v1/bypass-applications/${recordId}/approve`, payload)
  return res.data
}
