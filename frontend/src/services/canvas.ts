import api from './api'

export interface CanvasNode {
  id: string
  type?: string
  position: { x: number; y: number }
  data?: {
    label?: string
    status?: string
    progress?: number
    stageId?: string
    skillType?: 'primary' | 'auxiliary'
    gateType?: string
    decisionStatus?: string
    [key: string]: unknown
  }
  style?: Record<string, unknown>
  width?: number
  height?: number
}

export interface CanvasEdge {
  id: string
  source: string
  target: string
  type?: string
  animated?: boolean
  style?: Record<string, unknown>
  label?: string
}

export interface Viewport {
  x: number
  y: number
  zoom: number
}

export interface CanvasState {
  project_id: string
  nodes: CanvasNode[]
  edges: CanvasEdge[]
  viewport: Viewport
  updated_at: string | null
}

export interface CanvasStatePayload {
  nodes: CanvasNode[]
  edges: CanvasEdge[]
  viewport?: Viewport
}

export interface MergeStagePayload {
  source_stage_id: string
  target_stage_id: string
}

export interface MergeStageResult {
  project_id: string
  merged_stage_id: string
  nodes: CanvasNode[]
  edges: CanvasEdge[]
  message: string
}

export async function fetchCanvasState(projectId: string): Promise<CanvasState> {
  const res = await api.get<CanvasState>(`/v1/projects/${projectId}/canvas/state`)
  return res.data
}

export async function saveCanvasState(
  projectId: string,
  payload: CanvasStatePayload,
): Promise<CanvasState> {
  const res = await api.post<CanvasState>(`/v1/projects/${projectId}/canvas/state`, payload)
  return res.data
}

export async function mergeCanvasStages(
  projectId: string,
  payload: MergeStagePayload,
): Promise<MergeStageResult> {
  const res = await api.post<MergeStageResult>(
    `/v1/projects/${projectId}/canvas/merge-stages`,
    payload,
  )
  return res.data
}
