import { create } from 'zustand'

interface Annotation {
  id: string
  type: 'inline' | 'global' | 'suggestion'
  content: string
  targetText?: string
  createdAt: string
}

interface SizeEstimate {
  moduleCount: number
  interfaceCount: number
  pageCount: number
  entityCount: number
  complexity: string
  riskLevel: string
  recommendedPath: string
  estimatedWeeks: number
  estimatedPersonMonths: number
  breakdown?: Array<{ moduleName: string; estimatedHours: number }>
}

interface RequirementStudioState {
  projectId: string
  currentStage: string
  currentView: 'outline' | 'detailed' | 'history'
  selectedTab: string
  stageStatus: Record<string, { status: string; progress: number; tasks: unknown[] }>
  selectedTaskId: string | null
  selectedArtifactId: string | null
  artifactContent: string
  artifactVersions: unknown[]
  isEditing: boolean
  hasConflict: boolean
  annotations: Annotation[]
  executionStatus: string
  executionProgress: number
  executionLogs: string[]
  sizeEstimate: SizeEstimate | null
  projectStatus: 'draft' | 'active' | 'archived'
  loading: boolean
  error: string | null

  setProjectId: (id: string) => void
  setCurrentStage: (stage: string) => void
  setCurrentView: (view: 'outline' | 'detailed' | 'history') => void
  setSelectedTab: (tab: string) => void
  setStageStatus: (stageId: string, status: any) => void
  setStageStatuses: (statuses: any) => void
  selectTask: (taskId: string) => void
  selectArtifact: (artifactId: string) => void
  setArtifactContent: (content: string) => void
  setEditing: (editing: boolean) => void
  setExecutionStatus: (status: string) => void
  setExecutionProgress: (progress: number) => void
  appendExecutionLog: (log: string) => void
  clearExecutionLogs: () => void
  addAnnotation: (annotation: Omit<Annotation, 'id' | 'createdAt'>) => void
  removeAnnotation: (id: string) => void
  setSizeEstimate: (estimate: SizeEstimate | null) => void
  setProjectStatus: (status: 'draft' | 'active' | 'archived') => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useRequirementStudioStore = create<RequirementStudioState>((set) => ({
  projectId: '',
  currentStage: 'requirement-outline',
  currentView: 'outline',
  selectedTab: 'user-stories',
  stageStatus: {},
  selectedTaskId: null,
  selectedArtifactId: null,
  artifactContent: '',
  artifactVersions: [],
  isEditing: false,
  hasConflict: false,
  annotations: [],
  executionStatus: 'idle',
  executionProgress: 0,
  executionLogs: [],
  sizeEstimate: null,
  projectStatus: 'draft',
  loading: false,
  error: null,

  setProjectId: (id) => set({ projectId: id }),
  setCurrentStage: (stage) => set({ currentStage: stage }),
  setCurrentView: (view) => set({ currentView: view }),
  setSelectedTab: (tab) => set({ selectedTab: tab }),
  setStageStatus: (stageId, status) =>
    set((state) => ({
      stageStatus: { ...state.stageStatus, [stageId]: status },
    })),
  setStageStatuses: (statuses) => set({ stageStatus: statuses }),
  selectTask: (taskId) => set({ selectedTaskId: taskId }),
  selectArtifact: (artifactId) => set({ selectedArtifactId: artifactId }),
  setArtifactContent: (content) => set({ artifactContent: content }),
  setEditing: (editing) => set({ isEditing: editing }),
  setExecutionStatus: (status) => set({ executionStatus: status }),
  setExecutionProgress: (progress) => set({ executionProgress: progress }),
  appendExecutionLog: (log) =>
    set((state) => ({
      executionLogs: [...state.executionLogs, log],
    })),
  clearExecutionLogs: () => set({ executionLogs: [] }),
  addAnnotation: (annotation) =>
    set((state) => ({
      annotations: [
        ...state.annotations,
        {
          ...annotation,
          id: `ann-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
          createdAt: new Date().toISOString(),
        },
      ],
    })),
  removeAnnotation: (id) =>
    set((state) => ({
      annotations: state.annotations.filter((a) => a.id !== id),
    })),
  setSizeEstimate: (estimate) => set({ sizeEstimate: estimate }),
  setProjectStatus: (status) => set({ projectStatus: status }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}))
