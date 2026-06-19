import api from './api'

export interface Wireframe {
  wireframe_id: string
  project_id: string
  name: string
  c4_baseline_version: string | null
  pipeline_stage: string
  page_count: number | null
  avg_confidence: number | null
  status: string
  created_at: string | null
  updated_at: string | null
}

export interface WireframePage {
  page_id: string
  wireframe_id: string
  project_id: string
  entity_id: string | null
  entity_name: string | null
  page_name: string
  page_type: string
  confidence: number | null
  mapping_source: string
  svg_content: string | null
  layout_json: string | null
  status: string
  sort_order: number
  created_at: string | null
  updated_at: string | null
  // 扩展字段（页面元数据）
  fields_json?: string | null
  buttons_json?: string | null
  nav_targets_json?: string | null
  source_module_id?: string | null
}

export interface WireframeNavLink {
  link_id: string
  wireframe_id: string
  project_id: string
  source_page_id: string
  target_page_id: string
  relation_strength: string
  interface_count: number
}

export interface WireframeCreatePayload {
  name: string
  c4_baseline_version?: string | null
  status?: string
}

export interface WireframeGeneratePayload {
  c4_baseline_version?: string | null
}

export async function listWireframes(projectId: string): Promise<Wireframe[]> {
  const res = await api.get<Wireframe[]>(`/v1/projects/${projectId}/wireframes`)
  return res.data
}

export async function createWireframe(projectId: string, payload: WireframeCreatePayload): Promise<Wireframe> {
  const res = await api.post<Wireframe>(`/v1/projects/${projectId}/wireframes`, payload)
  return res.data
}

export async function generateWireframe(projectId: string, payload: WireframeGeneratePayload): Promise<Wireframe> {
  const res = await api.post<Wireframe>(`/v1/projects/${projectId}/wireframes/generate`, payload)
  return res.data
}

export async function getWireframe(wireframeId: string): Promise<Wireframe> {
  const res = await api.get<Wireframe>(`/v1/wireframes/${wireframeId}`)
  return res.data
}

export async function deleteWireframe(wireframeId: string): Promise<void> {
  await api.delete(`/v1/wireframes/${wireframeId}`)
}

export async function listWireframePages(projectId: string, wireframeId?: string): Promise<WireframePage[]> {
  const params = wireframeId ? `?wireframe_id=${wireframeId}` : ''
  const res = await api.get<WireframePage[]>(`/v1/projects/${projectId}/wireframe-pages${params}`)
  return res.data
}

export async function listWireframeNavLinks(projectId: string, wireframeId?: string): Promise<WireframeNavLink[]> {
  const params = wireframeId ? `?wireframe_id=${wireframeId}` : ''
  const res = await api.get<WireframeNavLink[]>(`/v1/projects/${projectId}/wireframe-nav-links${params}`)
  return res.data
}
