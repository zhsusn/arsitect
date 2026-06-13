import { create } from 'zustand'
import {
  fetchTemplates,
  fetchTemplateDetail,
  fetchStageSequence,
  previewDeviation,
  confirmDeviation,
  type Template,
  type TemplateStage,
  type ImpactPreview,
} from '../services/template'

interface TemplateState {
  templates: Template[]
  selectedTemplateId: string | null
  stages: TemplateStage[]
  loading: boolean
  error: string | null
  impact: ImpactPreview | null
  impactLoading: boolean

  fetchTemplates: () => Promise<void>
  selectTemplate: (id: string) => Promise<void>
  fetchStages: (projectId: string) => Promise<void>
  previewImpact: (projectId: string, newTemplateId: string) => Promise<void>
  confirmSwitch: (projectId: string, newTemplateId: string) => Promise<boolean>
  clearImpact: () => void
}

export const useTemplateStore = create<TemplateState>((set) => ({
  templates: [],
  selectedTemplateId: null,
  stages: [],
  loading: false,
  error: null,
  impact: null,
  impactLoading: false,

  fetchTemplates: async () => {
    set({ loading: true, error: null })
    try {
      const data = await fetchTemplates()
      set({ templates: data, loading: false })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载模板失败'
      set({ error: msg, loading: false })
    }
  },

  selectTemplate: async (id) => {
    set({ selectedTemplateId: id, loading: true, error: null })
    try {
      const detail = await fetchTemplateDetail(id)
      set({ stages: detail.stages, loading: false })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载模板详情失败'
      set({ error: msg, loading: false })
    }
  },

  fetchStages: async (projectId) => {
    set({ loading: true, error: null })
    try {
      const data = await fetchStageSequence(projectId)
      set({ stages: data as unknown as TemplateStage[], loading: false })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载 Stage 序列失败'
      set({ error: msg, loading: false })
    }
  },

  previewImpact: async (projectId, newTemplateId) => {
    set({ impactLoading: true, error: null })
    try {
      const data = await previewDeviation(projectId, newTemplateId)
      set({ impact: data, impactLoading: false })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '预览影响失败'
      set({ error: msg, impactLoading: false })
    }
  },

  confirmSwitch: async (projectId, newTemplateId) => {
    set({ impactLoading: true, error: null })
    try {
      await confirmDeviation(projectId, newTemplateId)
      set({ impactLoading: false, impact: null })
      return true
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '切换模板失败'
      set({ error: msg, impactLoading: false })
      return false
    }
  },

  clearImpact: () => set({ impact: null }),
}))
