import { create } from 'zustand'
import {
  createSizeEstimate,
  getTemplateRecommendation,
  type ComplexityInput,
  type ComplexityTemplate,
  type SizeEstimate,
} from '../services/complexity'

interface ComplexityState {
  estimate: SizeEstimate | null
  template: ComplexityTemplate | null
  loading: boolean
  error: string | null
  createEstimate: (projectId: string, input: ComplexityInput) => Promise<void>
  fetchTemplate: (level: string) => Promise<void>
  clear: () => void
}

export const useComplexityStore = create<ComplexityState>((set) => ({
  estimate: null,
  template: null,
  loading: false,
  error: null,

  createEstimate: async (projectId, input) => {
    set({ loading: true, error: null })
    try {
      const data = await createSizeEstimate(projectId, input)
      set({ estimate: data, loading: false })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '评估失败'
      set({ error: msg, loading: false })
    }
  },

  fetchTemplate: async (level) => {
    set({ loading: true, error: null })
    try {
      const data = await getTemplateRecommendation(level)
      set({ template: data, loading: false })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '获取模板推荐失败'
      set({ error: msg, loading: false })
    }
  },

  clear: () => set({ estimate: null, template: null, error: null }),
}))
