import api from './api'

export interface AnnotationCreatePayload {
  project_id: string
  content: string
  author: string
  annotation_type?: string
}

export interface AnnotationItem {
  annotation_id: string
  stage_id: string
  author: string
  content: string
  annotation_type: string
  status: string
  created_at: string
}

export async function createAnnotation(payload: AnnotationCreatePayload): Promise<AnnotationItem> {
  const res = await api.post<AnnotationItem>('/v1/annotations', payload)
  return res.data
}
