import { create } from 'zustand'
import api from '../services/api'

export interface Application {
  application_id: string
  application_name: string
  description: string | null
  local_path: string
  workspace_id: string
  path_accessible: boolean
}

interface AppDashboardState {
  applications: Application[]
  loading: boolean
  error: string | null
  searchQuery: string
  fetchApplications: () => Promise<void>
  createApplication: (app: Omit<Application, 'path_accessible'>) => Promise<void>
  deleteApplication: (id: string) => Promise<void>
  setSearchQuery: (q: string) => void
  filteredApps: () => Application[]
}

export const useAppDashboardStore = create<AppDashboardState>((set, get) => ({
  applications: [],
  loading: false,
  error: null,
  searchQuery: '',

  fetchApplications: async () => {
    set({ loading: true, error: null })
    try {
      const res = await api.get('/v1/applications')
      const list = (res.data as { data?: Application[] })?.data ?? []
      set({ applications: list, loading: false })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '未知错误'
      set({ error: msg, loading: false })
    }
  },

  createApplication: async (app) => {
    try {
      await api.post('/v1/applications', app)
      await get().fetchApplications()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '创建失败'
      set({ error: msg })
      throw err
    }
  },

  deleteApplication: async (id) => {
    try {
      await api.delete(`/v1/applications/${id}`)
      await get().fetchApplications()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '删除失败'
      set({ error: msg })
      throw err
    }
  },

  setSearchQuery: (q) => set({ searchQuery: q }),

  filteredApps: () => {
    const { applications, searchQuery } = get()
    if (!searchQuery) return applications
    const q = searchQuery.toLowerCase()
    return applications.filter(
      (a) =>
        a.application_name.toLowerCase().includes(q) ||
        a.local_path.toLowerCase().includes(q),
    )
  },
}))
