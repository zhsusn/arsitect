import { create } from 'zustand'

interface AppState {
  isLoading: boolean
  backendOnline: boolean | null
  error: string | null
  setLoading: (loading: boolean) => void
  setBackendOnline: (online: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
}

export const useAppStore = create<AppState>((set) => ({
  isLoading: false,
  backendOnline: null,
  error: null,
  setLoading: (loading) => set({ isLoading: loading }),
  setBackendOnline: (online) => set({ backendOnline: online }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}))
