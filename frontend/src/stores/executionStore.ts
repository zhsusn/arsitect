import { create } from 'zustand'

interface ExecutionState {
  projectId: string
  currentView: string
  tasks: unknown[]
  selectedTaskId: string | null
  taskGroups: Record<string, unknown[]>
  issues: unknown[]
  selectedIssueId: string | null
  activeExecutions: unknown[]
  executionLogs: Record<string, string[]>
  executionProgress: number
  currentPhase: string
  sseConnection: EventSource | null
  loading: boolean
  error: string | null

  setProjectId: (id: string) => void
  setCurrentView: (view: string) => void
  setTasks: (tasks: unknown[]) => void
  selectTask: (taskId: string) => void
  setIssues: (issues: unknown[]) => void
  selectIssue: (issueId: string) => void
  setActiveExecutions: (executions: unknown[]) => void
  appendExecutionLog: (executionId: string, log: string) => void
  clearExecutionLogs: (executionId: string) => void
  setExecutionProgress: (progress: number) => void
  setCurrentPhase: (phase: string) => void
  connectSSE: (projectId: string) => void
  disconnectSSE: () => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useExecutionStore = create<ExecutionState>((set, get) => ({
  projectId: '',
  currentView: 'task-center',
  tasks: [],
  selectedTaskId: null,
  taskGroups: {},
  issues: [],
  selectedIssueId: null,
  activeExecutions: [],
  executionLogs: {},
  executionProgress: 0,
  currentPhase: 'idle',
  sseConnection: null,
  loading: false,
  error: null,

  setProjectId: (id) => set({ projectId: id }),
  setCurrentView: (view) => set({ currentView: view }),
  setTasks: (tasks) => set({ tasks }),
  selectTask: (taskId) => set({ selectedTaskId: taskId }),
  setIssues: (issues) => set({ issues }),
  selectIssue: (issueId) => set({ selectedIssueId: issueId }),
  setActiveExecutions: (executions) => set({ activeExecutions: executions }),
  appendExecutionLog: (executionId, log) =>
    set((state) => ({
      executionLogs: {
        ...state.executionLogs,
        [executionId]: [...(state.executionLogs[executionId] || []), log],
      },
    })),
  clearExecutionLogs: (executionId) =>
    set((state) => ({
      executionLogs: {
        ...state.executionLogs,
        [executionId]: [],
      },
    })),
  setExecutionProgress: (progress) => set({ executionProgress: progress }),
  setCurrentPhase: (phase) => set({ currentPhase: phase }),
  connectSSE: (projectId) => {
    const existing = get().sseConnection
    if (existing) {
      existing.close()
    }
    const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
    const es = new EventSource(`${baseUrl}/sse/projects/${projectId}/executions`)
    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.log) {
          get().appendExecutionLog(data.executionId || 'default', data.log)
        }
        if (data.progress !== undefined) {
          get().setExecutionProgress(data.progress)
        }
        if (data.phase) {
          get().setCurrentPhase(data.phase)
        }
      } catch {
        get().appendExecutionLog('default', event.data)
      }
    }
    es.onerror = () => {
      console.warn('SSE connection error, will retry...')
    }
    set({ sseConnection: es })
  },
  disconnectSSE: () => {
    const es = get().sseConnection
    if (es) {
      es.close()
      set({ sseConnection: null })
    }
  },
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}))
