import api from './api'

export interface SelfCheckData {
  confidence: string
  artifact_integrity: string
  quality_gate: string
  risk_level: string
  artifact_count: number
  required_artifacts: number
}

export async function fetchGateSelfCheck(gateId: string): Promise<SelfCheckData> {
  const res = await api.get<SelfCheckData>(`/v1/gates/${gateId}/self-check`)
  return res.data
}
