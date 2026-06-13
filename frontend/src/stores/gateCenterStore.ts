import { create } from 'zustand'
import {
  fetchGates,
  fetchGateDetail,
  approveGate,
  rejectGate,
  retryGate,
  fetchGateHistory,
  type GateDecision,
} from '@/services/gate'
import { getGateBypass, applyBypass, listBypassApplications, type BypassRecord } from '@/services/bypass'
import { createAnnotation } from '@/services/annotation'
import { fetchGateSelfCheck, type SelfCheckData } from '@/services/selfCheck'

export interface GateStats {
  pending: number
  passed: number
  rejected: number
  bypassed: number
}

export interface GateFilters {
  project_id?: string
  gate_type?: string
  status?: string
}

export interface GateHistoryFilters {
  project_id?: string
  gate_type?: string
  decision_type?: string
  start_date?: string
  end_date?: string
}

interface GateCenterState {
  gates: GateDecision[]
  selectedGate: GateDecision | null
  stats: GateStats
  filters: GateFilters
  loading: boolean
  error: string | null
  history: GateDecision[]
  historyLoading: boolean
  historyError: string | null
  historyFilters: GateHistoryFilters
  selectedGateBypass: BypassRecord | null
  selfCheckData: SelfCheckData | null
  bypassMap: Record<string, BypassRecord | null>

  fetchGates: () => Promise<void>
  fetchGateDetail: (gateId: string) => Promise<void>
  approveGate: (gateId: string) => Promise<void>
  rejectGate: (gateId: string, reason: string) => Promise<void>
  retryGate: (gateId: string) => Promise<void>
  fetchStats: () => Promise<void>
  setFilter: (key: keyof GateFilters, value: string | undefined) => void
  fetchHistory: () => Promise<void>
  setHistoryFilter: (key: keyof GateHistoryFilters, value: string | undefined) => void
  applyBypass: (gateId: string, payload: {
    stage_id: string
    skill_id: string
    triggered_by: string
    reason: string
    authorizer_token: string
    deadline_hours?: number
  }) => Promise<void>
  fetchGateBypass: (gateId: string) => Promise<void>
  createRejectionAnnotation: (projectId: string, content: string) => Promise<void>
  fetchSelfCheck: (gateId: string) => Promise<void>
}

export const useGateCenterStore = create<GateCenterState>((set, get) => ({
  gates: [],
  selectedGate: null,
  stats: { pending: 0, passed: 0, rejected: 0, bypassed: 0 },
  filters: {},
  loading: false,
  error: null,
  history: [],
  historyLoading: false,
  historyError: null,
  historyFilters: {},
  selectedGateBypass: null,
  selfCheckData: null,
  bypassMap: {},

  fetchGates: async () => {
    const { project_id } = get().filters
    if (!project_id) {
      set({ gates: [], stats: computeStats([]), loading: false, error: null })
      return
    }
    set({ loading: true, error: null })
    try {
      const data = await fetchGates(get().filters)
      const bypassMap: Record<string, BypassRecord | null> = {}
      if (get().filters.project_id) {
        try {
          const bypassRecords = await listBypassApplications(get().filters.project_id!)
          for (const r of bypassRecords) {
            if (r.gate_decision_id) {
              bypassMap[r.gate_decision_id] = r
            }
          }
        } catch {
          // ignore
        }
      }
      set({ gates: data, loading: false, stats: computeStats(data), bypassMap })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载 Gate 列表失败'
      set({ error: msg, loading: false })
    }
  },

  fetchGateDetail: async (gateId) => {
    set({ loading: true, error: null })
    try {
      const data = await fetchGateDetail(gateId)
      set({ selectedGate: data, loading: false })
      await get().fetchGateBypass(gateId)
      await get().fetchSelfCheck(gateId)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载 Gate 详情失败'
      set({ error: msg, loading: false })
    }
  },

  approveGate: async (gateId) => {
    try {
      await approveGate(gateId)
      await get().fetchGateDetail(gateId)
      await get().fetchGates()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '审批失败'
      set({ error: msg })
      throw err
    }
  },

  rejectGate: async (gateId, reason) => {
    try {
      await rejectGate(gateId, reason)
      const gate = get().selectedGate
      if (gate) {
        try {
          await get().createRejectionAnnotation(gate.project_id, reason)
        } catch {
          // Silently ignore annotation failure
        }
      }
      await get().fetchGateDetail(gateId)
      await get().fetchGates()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '驳回失败'
      set({ error: msg })
      throw err
    }
  },

  retryGate: async (gateId) => {
    try {
      await retryGate(gateId)
      await get().fetchGateDetail(gateId)
      await get().fetchGates()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '重试失败'
      set({ error: msg })
      throw err
    }
  },

  fetchStats: async () => {
    try {
      const data = await fetchGates(get().filters)
      set({ gates: data, stats: computeStats(data) })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载统计失败'
      set({ error: msg })
    }
  },

  setFilter: (key, value) => {
    set((state) => ({
      filters: { ...state.filters, [key]: value },
    }))
  },

  fetchHistory: async () => {
    const { project_id } = get().historyFilters
    if (!project_id) {
      set({ history: [], historyLoading: false, historyError: null })
      return
    }
    set({ historyLoading: true, historyError: null })
    try {
      const data = await fetchGateHistory(get().historyFilters)
      set({ history: data, historyLoading: false })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载历史记录失败'
      set({ historyError: msg, historyLoading: false })
    }
  },

  setHistoryFilter: (key, value) => {
    set((state) => ({
      historyFilters: { ...state.historyFilters, [key]: value },
    }))
  },

  applyBypass: async (gateId, payload) => {
    await applyBypass(gateId, {
      stage_id: payload.stage_id,
      skill_id: payload.skill_id,
      triggered_by: payload.triggered_by,
      reason: payload.reason,
      authorizer_token: payload.authorizer_token,
      deadline_hours: payload.deadline_hours,
    })
    await get().fetchGateDetail(gateId)
    await get().fetchGates()
  },

  fetchGateBypass: async (gateId) => {
    try {
      const record = await getGateBypass(gateId)
      set({ selectedGateBypass: record })
    } catch {
      set({ selectedGateBypass: null })
    }
  },

  createRejectionAnnotation: async (projectId, content) => {
    const author = typeof window !== 'undefined'
      ? localStorage.getItem('X-User-Name') || localStorage.getItem('X-User-Role') || 'system'
      : 'system'
    await createAnnotation({
      project_id: projectId,
      content: `驳回理由：${content}`,
      author,
      annotation_type: 'comment',
    })
  },

  fetchSelfCheck: async (gateId) => {
    try {
      const data = await fetchGateSelfCheck(gateId)
      set({ selfCheckData: data })
    } catch {
      set({ selfCheckData: null })
    }
  },
}))

function computeStats(gates: GateDecision[]): GateStats {
  return gates.reduce(
    (acc, g) => {
      if (g.status === 'pending') acc.pending += 1
      else if (g.status === 'passed') acc.passed += 1
      else if (g.status === 'rejected') acc.rejected += 1
      else if (g.status === 'bypassed') acc.bypassed += 1
      return acc
    },
    { pending: 0, passed: 0, rejected: 0, bypassed: 0 },
  )
}
