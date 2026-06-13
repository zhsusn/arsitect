import api from './api'

export interface Sketch {
  sketch_id: string
  project_id: string
  name: string
  source_story_ids: string | null
  page_count: number | null
  coverage_percent: number | null
  validation_report: string | null
  status: 'DRAFT' | 'GENERATING' | 'GENERATED' | 'REVIEW_PENDING' | 'APPROVED' | 'REJECTED' | 'ARCHIVED'
  created_at: string | null
  updated_at: string | null
}

export interface SketchCreatePayload {
  name: string
  source_story_ids?: string | null
  status?: string
}

export interface SketchUpdatePayload {
  name?: string
  source_story_ids?: string | null
  page_count?: number
  coverage_percent?: number
  status?: string
}

export interface SketchGeneratePayload {
  story_ids?: string[] | null
}

export interface SketchGenerateFromRequirementsPayload {
  story_ids?: string[] | null
}

export async function listSketches(projectId: string): Promise<Sketch[]> {
  const res = await api.get<Sketch[]>(`/v1/projects/${projectId}/sketches`)
  return res.data
}

export async function createSketch(projectId: string, payload: SketchCreatePayload): Promise<Sketch> {
  const res = await api.post<Sketch>(`/v1/projects/${projectId}/sketches`, payload)
  return res.data
}

export async function generateSketch(projectId: string, payload: SketchGeneratePayload): Promise<Sketch> {
  const res = await api.post<Sketch>(`/v1/projects/${projectId}/sketches/generate`, payload)
  return res.data
}

export async function generateSketchFromRequirements(
  projectId: string,
  payload: SketchGenerateFromRequirementsPayload,
): Promise<Sketch> {
  const res = await api.post<Sketch>(`/v1/projects/${projectId}/sketches/generate-from-requirements`, payload)
  return res.data
}

export async function getSketch(sketchId: string): Promise<Sketch> {
  const res = await api.get<Sketch>(`/v1/sketches/${sketchId}`)
  return res.data
}

export async function updateSketch(sketchId: string, payload: SketchUpdatePayload): Promise<Sketch> {
  const res = await api.patch<Sketch>(`/v1/sketches/${sketchId}`, payload)
  return res.data
}

export async function deleteSketch(sketchId: string): Promise<void> {
  await api.delete(`/v1/sketches/${sketchId}`)
}
