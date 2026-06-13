import api from './api'

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy'
  version?: string
}

export async function checkHealth(): Promise<HealthStatus> {
  const response = await api.get<HealthStatus>('/v1/health')
  return response.data
}
