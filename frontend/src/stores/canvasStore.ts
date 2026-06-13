import { create } from 'zustand'
import {
  fetchCanvasState,
  saveCanvasState,
  type CanvasState,
  type CanvasStatePayload,
} from '../services/canvas'

interface CanvasStoreState {
  loading: boolean
  saving: boolean
  error: string | null

  loadCanvas: (projectId: string) => Promise<CanvasState | null>
  saveCanvas: (projectId: string, payload: CanvasStatePayload) => Promise<void>
  reset: () => void
}

export const useCanvasStore = create<CanvasStoreState>((set) => ({
  loading: false,
  saving: false,
  error: null,

  loadCanvas: async (projectId) => {
    set({ loading: true, error: null })
    try {
      const data = await fetchCanvasState(projectId)
      set({ loading: false })
      return data
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载画布失败'
      if (typeof err === 'object' && err !== null && 'response' in err) {
        const axiosErr = err as { response?: { status?: number } }
        if (axiosErr.response?.status === 404) {
          set({ loading: false, error: null })
          return null
        }
      }
      set({ error: msg, loading: false })
      return null
    }
  },

  saveCanvas: async (projectId, payload) => {
    set({ saving: true, error: null })
    try {
      await saveCanvasState(projectId, payload)
      set({ saving: false })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '保存画布失败'
      set({ error: msg, saving: false })
    }
  },

  reset: () =>
    set({
      loading: false,
      saving: false,
      error: null,
    }),
}))
