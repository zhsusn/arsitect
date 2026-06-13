import api from './api'

export interface SketchPage {
  page_id: string
  project_id: string
  story_id: string | null
  page_name: string
  page_type: string
  svg_content: string | null
  fields_json: string | null
  buttons_json: string | null
  nav_targets_json: string | null
  source_module_id: string | null
  source_md_path: string | null
  status: string
  sort_order: number
  created_at: string | null
  updated_at: string | null
}

export interface SketchPageCreatePayload {
  story_id?: string | null
  page_name: string
  page_type?: string
  svg_content?: string | null
  fields_json?: string | null
  buttons_json?: string | null
  nav_targets_json?: string | null
  status?: string
  sort_order?: number
}

export interface SketchPageUpdatePayload {
  page_name?: string
  page_type?: string
  svg_content?: string | null
  fields_json?: string | null
  buttons_json?: string | null
  nav_targets_json?: string | null
  status?: string
  sort_order?: number
}

export async function listSketchPages(projectId: string): Promise<SketchPage[]> {
  const res = await api.get<SketchPage[]>(`/v1/projects/${projectId}/sketch-pages`)
  return res.data
}

export async function createSketchPage(projectId: string, payload: SketchPageCreatePayload): Promise<SketchPage> {
  const res = await api.post<SketchPage>(`/v1/projects/${projectId}/sketch-pages`, payload)
  return res.data
}

export async function getSketchPage(pageId: string): Promise<SketchPage> {
  const res = await api.get<SketchPage>(`/v1/sketch-pages/${pageId}`)
  return res.data
}

export async function updateSketchPage(pageId: string, payload: SketchPageUpdatePayload): Promise<SketchPage> {
  const res = await api.patch<SketchPage>(`/v1/sketch-pages/${pageId}`, payload)
  return res.data
}

export async function deleteSketchPage(pageId: string): Promise<void> {
  await api.delete(`/v1/sketch-pages/${pageId}`)
}
