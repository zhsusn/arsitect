import { create } from 'zustand'
import { api } from '@/services/api'
import type { SkillExecution } from '@/types/skill-execution'

interface ExecutionMonitorState {
  executions: SkillExecution[]
  isLoading: boolean
  error: string | null
  filterStatus: string
  fetchExecutions: (projectId?: string) => Promise<void>
  setFilterStatus: (status: string) => void
  stopExecution: (executionId: string) => Promise<void>
}

export const useExecutionMonitorStore = create<ExecutionMonitorState>((set, get) => ({
  executions: [],
  isLoading: false,
  error: null,
  filterStatus: 'ALL',

  fetchExecutions: async (projectId?: string) => {
    set({ isLoading: true, error: null })
    try {
      const params = projectId ? { project_id: projectId } : {}
      const res = await api.get<SkillExecution[]>('/v1/executions', { params })
      set({ executions: res.data, isLoading: false })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '未知错误'
      set({ error: msg, isLoading: false })
    }
  },

  setFilterStatus: (status: string) => set({ filterStatus: status }),

  stopExecution: async (executionId: string) => {
    await api.post(`/v1/executions/${executionId}/stop`)
    await get().fetchExecutions()
  },
}))
