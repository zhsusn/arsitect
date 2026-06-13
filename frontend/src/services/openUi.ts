import api from './api'

export interface OpenUISpec {
  spec_id: string
  project_id: string
  spec_name: string
  prompt_text: string | null
  page_count: number | null
  page_titles_json: string | null
  service_status: string
  generation_duration_ms: number | null
  content_hash: string | null
  status: string
  created_at: string | null
  updated_at: string | null
}

export interface OpenUIPage {
  page_id: string
  spec_id: string
  project_id: string
  container_id: string | null
  page_title: string
  html_content: string | null
  page_index: number
  status: string
  created_at: string | null
  updated_at: string | null
}

export interface OpenUIHealth {
  status: string
  available: boolean
}

export interface OpenUIGeneratePayload {
  c4_baseline_version?: string | null
}

export async function listOpenUISpecs(projectId: string): Promise<OpenUISpec[]> {
  const res = await api.get<OpenUISpec[]>(`/v1/projects/${projectId}/open-ui-specs`)
  return res.data
}

export async function generateOpenUISpec(projectId: string, payload: OpenUIGeneratePayload): Promise<OpenUISpec> {
  const res = await api.post<OpenUISpec>(`/v1/projects/${projectId}/open-ui-specs/generate`, payload)
  return res.data
}

export async function getOpenUISpec(specId: string): Promise<OpenUISpec> {
  const res = await api.get<OpenUISpec>(`/v1/open-ui-specs/${specId}`)
  return res.data
}

export async function deleteOpenUISpec(specId: string): Promise<void> {
  await api.delete(`/v1/open-ui-specs/${specId}`)
}

export async function checkOpenUIHealth(specId: string): Promise<OpenUIHealth> {
  const res = await api.get<OpenUIHealth>(`/v1/open-ui-specs/${specId}/health`)
  return res.data
}

export async function listOpenUIPages(projectId: string, specId?: string): Promise<OpenUIPage[]> {
  const params = specId ? `?spec_id=${specId}` : ''
  const res = await api.get<OpenUIPage[]>(`/v1/projects/${projectId}/open-ui-pages${params}`)
  return res.data
}
