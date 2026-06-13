import { create } from 'zustand'
import {
  fetchProjects,
  createProject,
  archiveProject,
  activateProject,
  cancelProject,
  fetchRiskAlerts,
  fetchProjectOverview,
  updateProject,
  type Project,
  type RiskAlert,
  type ProjectOverview,
  type ProjectCreatePayload,
  type ProjectUpdatePayload,
} from '../services/project'

interface ProjectDashboardState {
  projects: Project[]
  loading: boolean
  error: string | null
  searchQuery: string
  statusFilter: string
  riskFilter: string
  sortField: 'created_at' | 'updated_at' | 'project_name'
  sortOrder: 'asc' | 'desc'
  riskAlerts: RiskAlert[]
  projectOverview: ProjectOverview | null
  overviewLoading: boolean
  viewMode: 'grid' | 'list'

  fetchProjects: (appId: string) => Promise<void>
  createProject: (appId: string, payload: ProjectCreatePayload) => Promise<void>
  archiveProject: (projectId: string) => Promise<void>
  activateProject: (projectId: string) => Promise<void>
  cancelProject: (projectId: string) => Promise<void>
  updateProject: (projectId: string, payload: ProjectUpdatePayload) => Promise<void>
  setSearchQuery: (q: string) => void
  setStatusFilter: (s: string) => void
  setRiskFilter: (r: string) => void
  setSortField: (f: 'created_at' | 'updated_at' | 'project_name') => void
  setSortOrder: (o: 'asc' | 'desc') => void
  setViewMode: (m: 'grid' | 'list') => void
  fetchRiskAlerts: (projectId: string) => Promise<void>
  fetchProjectOverview: (projectId: string) => Promise<void>
  clearProjectOverview: () => void
  filteredProjects: () => Project[]
}

export const useProjectDashboardStore = create<ProjectDashboardState>((set, get) => ({
  projects: [],
  loading: false,
  error: null,
  searchQuery: '',
  statusFilter: '',
  riskFilter: '',
  sortField: 'created_at',
  sortOrder: 'desc',
  riskAlerts: [],
  projectOverview: null,
  overviewLoading: false,
  viewMode: 'grid',

  fetchProjects: async (appId) => {
    set({ loading: true, error: null })
    try {
      const data = await fetchProjects(appId)
      set({ projects: data, loading: false })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载项目失败'
      set({ error: msg, loading: false })
    }
  },

  createProject: async (appId, payload) => {
    try {
      await createProject(appId, payload)
      await get().fetchProjects(appId)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '创建项目失败'
      set({ error: msg })
      throw err
    }
  },

  archiveProject: async (projectId) => {
    await archiveProject(projectId)
    const state = get()
    if (state.projects.length > 0) {
      await state.fetchProjects(state.projects[0].application_id)
    }
  },

  activateProject: async (projectId) => {
    await activateProject(projectId)
    const state = get()
    if (state.projects.length > 0) {
      await state.fetchProjects(state.projects[0].application_id)
    }
  },

  cancelProject: async (projectId) => {
    await cancelProject(projectId)
    const state = get()
    if (state.projects.length > 0) {
      await state.fetchProjects(state.projects[0].application_id)
    }
  },

  updateProject: async (projectId, payload) => {
    try {
      await updateProject(projectId, payload)
      const state = get()
      if (state.projects.length > 0) {
        await state.fetchProjects(state.projects[0].application_id)
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '更新项目失败'
      set({ error: msg })
      throw err
    }
  },

  setSearchQuery: (q) => set({ searchQuery: q }),
  setStatusFilter: (s) => set({ statusFilter: s }),
  setRiskFilter: (r) => set({ riskFilter: r }),
  setSortField: (f) => set({ sortField: f }),
  setSortOrder: (o) => set({ sortOrder: o }),
  setViewMode: (m) => set({ viewMode: m }),

  fetchRiskAlerts: async (projectId) => {
    try {
      const data = await fetchRiskAlerts(projectId)
      set({ riskAlerts: data })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载风险预警失败'
      set({ error: msg })
    }
  },

  fetchProjectOverview: async (projectId) => {
    set({ overviewLoading: true })
    try {
      const data = await fetchProjectOverview(projectId)
      set({ projectOverview: data, overviewLoading: false })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载项目详情失败'
      set({ error: msg, overviewLoading: false })
    }
  },

  clearProjectOverview: () => set({ projectOverview: null }),

  filteredProjects: () => {
    const { projects, searchQuery, statusFilter, riskFilter, sortField, sortOrder } = get()
    let result = [...projects]

    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      result = result.filter(
        (p) =>
          p.project_name.toLowerCase().includes(q) ||
          (p.project_description ?? '').toLowerCase().includes(q),
      )
    }

    if (statusFilter) {
      result = result.filter((p) => p.project_status === statusFilter)
    }

    if (riskFilter) {
      result = result.filter((p) => p.risk_level === riskFilter)
    }

    result.sort((a, b) => {
      const aVal = a[sortField]
      const bVal = b[sortField]
      if (aVal === null || bVal === null) return 0
      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1
      return 0
    })

    return result
  },
}))
