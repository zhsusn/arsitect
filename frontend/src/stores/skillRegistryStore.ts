import { create } from 'zustand'
import api from '../services/api'

export interface Skill {
  skill_id: string
  skill_name: string
  version: string
  pattern: string
  tags: string[] | null
  platforms: string[] | null
  description: string | null
  directory_path: string
  parse_status: string
  created_at?: string
  updated_at?: string
}

export interface SkillDetail extends Skill {
  created_at: string
  updated_at: string
}

export interface SkillExecution {
  execution_id: string
  stage_id: string
  skill_name: string
  trigger_action: string
  overall_status: string
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export interface BoundStage {
  stage_id: string
  stage_name: string
  template_id: string | null
  binding_type: string
}

export interface DAGNode {
  node_id: string
  skill_id: string
  position_x: number
  position_y: number
}

export interface DAGEdge {
  edge_id: string
  source_node_id: string
  target_node_id: string
  confidence: number
  is_auto_parsed: boolean
}

export interface DAGSnapshot {
  nodes: DAGNode[]
  edges: DAGEdge[]
}

export interface DAGChangeLog {
  log_id: string
  session_id: string
  operation_type: string
  target_id: string
  before_snapshot: string | null
  after_snapshot: string | null
  created_at: string
}

export interface SkillConflict {
  new_skill: Skill
  existing_skill: Skill | null
}

export interface SkillScanResult {
  parsed_skills: Skill[]
  conflicts: SkillConflict[]
  errors: string[]
}

export interface ConflictResolution {
  skill_name: string
  action: string
  new_name: string | null
}

interface SkillRegistryState {
  skills: Skill[]
  loading: boolean
  error: string | null
  searchQuery: string
  patternFilter: string
  statusFilter: string
  dag: DAGSnapshot
  dagSessionId: string
  selectedSkillId: string | null
  skillDetail: SkillDetail | null
  skillExecutions: SkillExecution[]
  boundStages: BoundStage[]
  changeLogs: DAGChangeLog[]
  fetchSkills: () => Promise<void>
  scanSkills: (directoryPath: string) => Promise<SkillScanResult>
  confirmImport: (
    skills: Skill[],
    resolutions?: ConflictResolution[],
  ) => Promise<{ imported: number; skipped: number; errors: string[] }>
  deleteSkill: (id: string) => Promise<void>
  fetchDAG: () => Promise<void>
  addDAGNode: (node: DAGNode) => Promise<void>
  deleteDAGNode: (nodeId: string) => Promise<void>
  addDAGEdge: (edge: DAGEdge) => Promise<void>
  deleteDAGEdge: (edgeId: string) => Promise<void>
  undoDAG: () => Promise<void>
  redoDAG: () => Promise<void>
  saveDAG: () => Promise<void>
  fetchSkillDetail: (skillId: string) => Promise<void>
  fetchSkillExecutions: (skillId: string) => Promise<void>
  fetchBoundStages: (skillId: string) => Promise<void>
  fetchChangeLogs: () => Promise<void>
  setSelectedSkillId: (id: string | null) => void
  setSearchQuery: (q: string) => void
  setPatternFilter: (p: string) => void
  setStatusFilter: (s: string) => void
  filteredSkills: () => Skill[]
}

export const useSkillRegistryStore = create<SkillRegistryState>((set, get) => ({
  skills: [],
  loading: false,
  error: null,
  searchQuery: '',
  patternFilter: '',
  statusFilter: '',
  dag: { nodes: [], edges: [] },
  dagSessionId: 'default',
  selectedSkillId: null,
  skillDetail: null,
  skillExecutions: [],
  boundStages: [],
  changeLogs: [],

  fetchSkills: async () => {
    set({ loading: true, error: null })
    try {
      const res = await api.get<{ data: Skill[]; total_count: number }>('/v1/skills')
      set({ skills: res.data.data, loading: false })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '未知错误'
      set({ error: msg, loading: false })
    }
  },

  scanSkills: async (directoryPath: string) => {
    const res = await api.post<SkillScanResult>('/v1/skills/import/scan', {
      directory_path: directoryPath,
    })
    return res.data
  },

  confirmImport: async (
    skillsToImport: Skill[],
    resolutions?: ConflictResolution[],
  ) => {
    const res = await api.post<{ imported: number; skipped: number; errors: string[] }>(
      '/v1/skills/import/confirm',
      { skills_to_import: skillsToImport, resolutions },
    )
    await get().fetchSkills()
    return res.data
  },

  deleteSkill: async (id: string) => {
    await api.delete(`/v1/skills/${id}`)
    await get().fetchSkills()
  },

  fetchDAG: async () => {
    const res = await api.get<DAGSnapshot>('/v1/skills/dag')
    set({ dag: res.data })
  },

  addDAGNode: async (node: DAGNode) => {
    await api.post('/v1/skills/dag/nodes', node)
    await get().fetchDAG()
  },

  deleteDAGNode: async (nodeId: string) => {
    await api.delete(`/v1/skills/dag/nodes/${nodeId}`)
    await get().fetchDAG()
  },

  addDAGEdge: async (edge: DAGEdge) => {
    await api.post('/v1/skills/dag/edges', edge)
    await get().fetchDAG()
  },

  deleteDAGEdge: async (edgeId: string) => {
    await api.delete(`/v1/skills/dag/edges/${edgeId}`)
    await get().fetchDAG()
  },

  undoDAG: async () => {
    await api.post('/v1/skills/dag/undo', { session_id: get().dagSessionId })
    await get().fetchDAG()
  },

  redoDAG: async () => {
    await api.post('/v1/skills/dag/redo', { session_id: get().dagSessionId })
    await get().fetchDAG()
  },

  saveDAG: async () => {
    await api.post('/v1/skills/dag/save')
  },

  fetchSkillDetail: async (skillId: string) => {
    const res = await api.get<SkillDetail>(`/v1/skills/${skillId}`)
    set({ skillDetail: res.data })
  },

  fetchSkillExecutions: async (skillId: string) => {
    const res = await api.get<SkillExecution[]>(`/v1/skills/${skillId}/executions`)
    set({ skillExecutions: res.data })
  },

  fetchBoundStages: async (skillId: string) => {
    const res = await api.get<BoundStage[]>(`/v1/skills/${skillId}/stages`)
    set({ boundStages: res.data })
  },

  fetchChangeLogs: async () => {
    const res = await api.get<DAGChangeLog[]>('/v1/skills/dag/changelog')
    set({ changeLogs: res.data })
  },

  setSelectedSkillId: (id) => set({ selectedSkillId: id }),
  setSearchQuery: (q) => set({ searchQuery: q }),
  setPatternFilter: (p) => set({ patternFilter: p }),
  setStatusFilter: (s) => set({ statusFilter: s }),

  filteredSkills: () => {
    const { skills, searchQuery, patternFilter, statusFilter } = get()
    return skills.filter((s) => {
      if (searchQuery && !s.skill_name.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false
      }
      if (patternFilter && s.pattern !== patternFilter) {
        return false
      }
      if (statusFilter && s.parse_status !== statusFilter) {
        return false
      }
      return true
    })
  },
}))
