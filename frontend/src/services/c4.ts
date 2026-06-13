import api from './api'

export interface C4DslCurrent {
  content: string
  format: string
}

export interface C4DslEditPayload {
  project_id: string
  content: string
  edit_reason?: string
  editor?: string
}

export interface C4DslEditResult {
  version: string
  message: string
}

export interface C4DslVersion {
  version: string
  created_at: string
  editor: string | null
  edit_reason: string | null
}

export interface C4DslVersionsResult {
  versions: C4DslVersion[]
}

export interface C4DslRollbackPayload {
  project_id: string
  version: string
}

export async function getC4DslCurrent(projectId: string): Promise<C4DslCurrent> {
  const resp = await api.get('/v1/c4/dsl/current', { params: { project_id: projectId } })
  return resp.data
}

export async function editC4Dsl(payload: C4DslEditPayload): Promise<C4DslEditResult> {
  const { project_id, ...body } = payload
  const resp = await api.post('/v1/c4/dsl/edit', body, { params: { project_id } })
  return resp.data
}

export async function listC4DslVersions(projectId: string): Promise<C4DslVersionsResult> {
  const resp = await api.get('/v1/c4/dsl/versions', { params: { project_id: projectId } })
  return resp.data
}

export async function rollbackC4Dsl(payload: C4DslRollbackPayload): Promise<{ version: string }> {
  const { project_id, version } = payload
  const resp = await api.post('/v1/c4/dsl/rollback', { version }, { params: { project_id } })
  return resp.data
}

export interface C4OrphanComponent {
  id: string
  name: string
  container_id?: string
  source: string
  implemented: boolean
  intentional_orphan: boolean
  source_file?: string
}

export interface C4RegistryStats {
  project_id: string
  systems: number
  actors: number
  containers: number
  components: number
  interfaces: number
  relationships: number
  orphan_count: number
  intentional_orphan_count: number
  effective_orphan_count: number
  orphans: C4OrphanComponent[]
}

export interface C4ExtractResult {
  project_id: string
  message: string
  stats: C4RegistryStats
}

export async function extractC4Registry(projectId: string): Promise<C4ExtractResult> {
  const resp = await api.post('/v1/c4/registry/extract', null, { params: { project_id: projectId } })
  return resp.data
}

export async function getC4RegistryStats(projectId: string): Promise<C4RegistryStats> {
  const resp = await api.get('/v1/c4/registry/stats', { params: { project_id: projectId } })
  return resp.data
}

export interface C4RelationshipTuple {
  source: string
  target: string
  description?: string
}

export interface C4RegistryDiff {
  project_id: string
  since: string
  components_added: string[]
  components_removed: string[]
  components_changed: { id: string; before?: string; after?: string }[]
  relationships_added: C4RelationshipTuple[]
  relationships_removed: C4RelationshipTuple[]
  orphan_count_before: number
  orphan_count_after: number
  components_before: number
  components_after: number
  relationships_before: number
  relationships_after: number
}

export async function getC4RegistryDiff(projectId: string, since: string): Promise<C4RegistryDiff> {
  const resp = await api.get('/v1/c4/registry/diff', { params: { project_id: projectId, since } })
  return resp.data
}

export async function toggleIntentionalOrphan(projectId: string, componentId: string): Promise<{ project_id: string; component_id: string; intentional_orphan: boolean }> {
  const resp = await api.post(`/v1/c4/registry/orphans/${encodeURIComponent(componentId)}/intentional`, null, { params: { project_id: projectId } })
  return resp.data
}
