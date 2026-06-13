import api from './api'

export interface GateDecision {
  decision_id: string
  gate_id: string
  project_id: string
  gate_type: string
  status: 'pending' | 'passed' | 'rejected' | 'bypassed'
  confidence: 'high' | 'medium' | 'low' | null
  decision_type: 'approve' | 'reject' | 'retry' | 'bypass' | null
  decision_by: string | null
  decision_at: string | null
  duration_sec: number | null
  reason: string | null
  unlocked_stages: string[]
  created_at: string
  updated_at: string
}

interface PageResponse<T> {
  data: T[]
  total: number
}

export async function fetchGates(params?: {
  project_id?: string
  gate_type?: string
  status?: string
}): Promise<GateDecision[]> {
  const res = await api.get<PageResponse<GateDecision>>('/v1/gates', { params })
  return res.data.data
}

export async function fetchGateDetail(gateId: string): Promise<GateDecision> {
  const res = await api.get<GateDecision>(`/v1/gates/${gateId}`)
  return res.data
}

export async function approveGate(gateId: string): Promise<void> {
  await api.post(`/v1/gates/${gateId}/approve`)
}

export async function rejectGate(gateId: string, reason: string): Promise<void> {
  await api.post(`/v1/gates/${gateId}/reject`, { reason })
}

export async function retryGate(gateId: string): Promise<void> {
  await api.post(`/v1/gates/${gateId}/retry`)
}

export async function fetchGateHistory(params?: {
  project_id?: string
  gate_type?: string
  decision_type?: string
  start_date?: string
  end_date?: string
}): Promise<GateDecision[]> {
  const res = await api.get<PageResponse<GateDecision>>('/v1/gates/history', { params })
  return res.data.data
}
