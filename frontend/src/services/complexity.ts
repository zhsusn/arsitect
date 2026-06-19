import api from './api'

export interface ComplexityInput {
  module_count: number
  interface_count: number
  page_count: number
  tech_complexity: string
  risk_level: string
}

export interface SizeEstimate {
  estimate_id: string
  project_id: string
  module_count: number
  interface_count: number
  page_count: number
  tech_complexity: string
  risk_level: string
  optimistic_score: number | null
  expected_score: number | null
  conservative_score: number | null
  complexity_level: string | null
  created_at: string | null
}

export interface ComplexityAssessInput {
  module_count: number
  interface_complexity: number
  page_count: number
  entity_count: number
  integration_count: number
}

export interface ComplexityAssessResult {
  optimistic_score: number
  expected_score: number
  conservative_score: number
  complexity_level: string
  radar_values: Record<string, number> | null
}

export interface ComplexityTemplate {
  level: string
  label: string
  recommended_template: string
  description: string
  stage_count: number
  estimated_skill_count: number
  default_execution_strategy?: string | null
  merge_policy_json?: {
    groups?: Array<{
      group_id: string
      label: string
      business_stage_keys: string[]
      gate_at_end?: boolean
      auto_advance?: boolean
    }>
  } | null
}

export interface PathDecision {
  decision_id: string
  project_id: string | null
  decision_type: string
  from_path: string | null
  to_path: string
  reason: string | null
  created_at: string | null
}

export interface PathDecisionInput {
  project_id?: string | null
  decision_type: string
  from_path?: string | null
  to_path: string
  reason?: string | null
}

export async function createSizeEstimate(
  projectId: string,
  input: ComplexityInput,
): Promise<SizeEstimate> {
  const resp = await api.post(`/v1/projects/${projectId}/size-estimates`, input)
  return resp.data
}

export async function listSizeEstimates(projectId: string): Promise<SizeEstimate[]> {
  const resp = await api.get(`/v1/projects/${projectId}/size-estimates`)
  return resp.data
}

export async function getTemplateRecommendation(level: string): Promise<ComplexityTemplate> {
  const resp = await api.get(`/v1/complexity/templates/${level}`)
  return resp.data
}

export async function assessComplexity(input: ComplexityAssessInput): Promise<ComplexityAssessResult> {
  const resp = await api.post('/v1/complexity/assess', input)
  return resp.data
}

export async function listAllTemplates(): Promise<ComplexityTemplate[]> {
  const resp = await api.get('/v1/complexity/templates')
  return resp.data
}

export async function createDecision(input: PathDecisionInput): Promise<PathDecision> {
  const resp = await api.post('/v1/complexity/decisions', input)
  return resp.data
}

export async function listDecisions(projectId?: string): Promise<PathDecision[]> {
  const resp = await api.get('/v1/complexity/decisions', {
    params: projectId ? { project_id: projectId } : undefined,
  })
  return resp.data
}
