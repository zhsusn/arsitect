import { create } from 'zustand'
import { api } from '@/services/api'
import type { ExecutionPlanDetail } from '@/types/execution-plan'

interface ExecutionPlanState {
  plan: ExecutionPlanDetail | null
  isLoading: boolean
  error: string | null
  fetchPlan: (planId: string) => Promise<void>
  executePlan: (planId: string) => Promise<void>
  freezePlan: (planId: string) => Promise<void>
  pollPlan: (planId: string) => Promise<void>
  updateNodeStatus: (nodeId: string, status: string) => void
}

export const useExecutionPlanStore = create<ExecutionPlanState>((set, get) => ({
  plan: null,
  isLoading: false,
  error: null,

  fetchPlan: async (planId: string) => {
    set({ isLoading: true, error: null })
    try {
      const res = await api.get<ExecutionPlanDetail>(`/v1/execution-plans/${planId}`)
      set({
        plan: res.data,
        isLoading: false,
      })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '未知错误'
      set({ error: msg, isLoading: false })
    }
  },

  pollPlan: async (planId: string) => {
    try {
      const res = await api.get<ExecutionPlanDetail>(`/v1/execution-plans/${planId}`)
      set({ plan: res.data })
    } catch (err: unknown) {
      console.error('Poll plan failed:', err)
    }
  },

  executePlan: async (planId: string) => {
    set({ isLoading: true, error: null })
    try {
      await api.post(`/v1/execution-plans/${planId}/execute`)
      await get().fetchPlan(planId)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '未知错误'
      set({ error: msg, isLoading: false })
    }
  },

  freezePlan: async (planId: string) => {
    set({ isLoading: true, error: null })
    try {
      await api.post(`/v1/execution-plans/${planId}/freeze`)
      await get().fetchPlan(planId)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '未知错误'
      set({ error: msg, isLoading: false })
    }
  },

  updateNodeStatus: (nodeId: string, status: string) => {
    set((state) => {
      if (!state.plan) return state
      const nodes = state.plan.nodes.map((n) =>
        n.node_id === nodeId ? { ...n, status } : n,
      )
      return { plan: { ...state.plan, nodes } }
    })
  },
}))
