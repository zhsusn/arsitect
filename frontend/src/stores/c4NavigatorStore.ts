import { create } from 'zustand'
import {
  getC4DslCurrent,
  editC4Dsl,
  listC4DslVersions,
  rollbackC4Dsl,
  extractC4Registry,
  getC4RegistryStats,
  toggleIntentionalOrphan,
  type C4DslVersion,
  type C4RegistryStats,
} from '../services/c4'
import { getProject } from '../services/project'

export interface C4NodeInfo {
  id: string
  name: string
  type: 'Person' | 'System' | 'Container' | 'Component' | 'Boundary' | 'unknown'
  description?: string
  tech?: string[]
  filePath?: string
  interfaces?: string[]
}

export interface BreadcrumbItem {
  label: string
  href?: string
}

interface C4NavigatorState {
  dslContent: string
  previewLevel: string
  loading: boolean
  error: string | null
  currentProjectName: string
  selectedNode: C4NodeInfo | null
  isNodeDetailOpen: boolean
  exportPanelOpen: boolean
  breadcrumb: BreadcrumbItem[]
  versions: C4DslVersion[]
  versionsOpen: boolean
  registryStats: C4RegistryStats | null
  syncLoading: boolean
  orphanDrawerOpen: boolean

  fetchDslCurrent: (projectId: string) => Promise<void>
  editDsl: (projectId: string, content: string, editReason?: string, editor?: string) => Promise<void>
  listVersions: (projectId: string) => Promise<void>
  rollback: (projectId: string, version: string) => Promise<void>
  setPreviewLevel: (level: string) => void
  fetchProjectName: (projectId: string) => Promise<void>
  setSelectedNode: (node: C4NodeInfo | null) => void
  openNodeDetail: () => void
  closeNodeDetail: () => void
  openExportPanel: () => void
  closeExportPanel: () => void
  initBreadcrumb: (projectId: string, projectName: string) => void
  openVersionsPanel: () => void
  closeVersionsPanel: () => void
  syncRegistry: (projectId: string) => Promise<void>
  fetchRegistryStats: (projectId: string) => Promise<void>
  openOrphanDrawer: () => void
  closeOrphanDrawer: () => void
  toggleOrphanIntentional: (projectId: string, componentId: string) => Promise<void>
}

export const useC4NavigatorStore = create<C4NavigatorState>((set, get) => ({
  dslContent: '',
  previewLevel: 'L1',
  loading: false,
  error: null,
  currentProjectName: '',
  selectedNode: null,
  isNodeDetailOpen: false,
  exportPanelOpen: false,
  breadcrumb: [],
  versions: [],
  versionsOpen: false,
  registryStats: null,
  syncLoading: false,
  orphanDrawerOpen: false,

  fetchDslCurrent: async (projectId) => {
    set({ loading: true, error: null })
    try {
      const data = await getC4DslCurrent(projectId)
      set({ dslContent: data.content, loading: false })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载失败'
      set({ error: msg, loading: false })
    }
  },

  editDsl: async (projectId, content, editReason, editor) => {
    set({ loading: true, error: null })
    try {
      await editC4Dsl({ project_id: projectId, content, edit_reason: editReason, editor })
      set({ loading: false, error: null })
      await get().fetchDslCurrent(projectId)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '保存失败'
      set({ error: msg, loading: false })
    }
  },

  listVersions: async (projectId) => {
    set({ loading: true, error: null })
    try {
      const data = await listC4DslVersions(projectId)
      set({ versions: data.versions, loading: false })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载版本历史失败'
      set({ error: msg, loading: false })
    }
  },

  rollback: async (projectId, version) => {
    set({ loading: true, error: null })
    try {
      await rollbackC4Dsl({ project_id: projectId, version })
      set({ loading: false, error: null })
      await get().fetchDslCurrent(projectId)
      await get().listVersions(projectId)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '回滚失败'
      set({ error: msg, loading: false })
    }
  },

  setPreviewLevel: (level) => set({ previewLevel: level }),

  fetchProjectName: async (projectId) => {
    try {
      const project = await getProject(projectId)
      set({ currentProjectName: project.project_name })
    } catch {
      set({ currentProjectName: projectId })
    }
  },

  setSelectedNode: (node) => set({ selectedNode: node }),

  openNodeDetail: () => set({ isNodeDetailOpen: true }),

  closeNodeDetail: () => set({ isNodeDetailOpen: false, selectedNode: null }),

  openExportPanel: () => set({ exportPanelOpen: true }),

  closeExportPanel: () => set({ exportPanelOpen: false }),

  initBreadcrumb: (projectId, projectName) => {
    set({
      breadcrumb: [
        { label: projectName, href: `/projects/${projectId}` },
        { label: 'C4 架构' },
      ],
    })
  },

  openVersionsPanel: () => set({ versionsOpen: true }),

  closeVersionsPanel: () => set({ versionsOpen: false }),

  openOrphanDrawer: () => set({ orphanDrawerOpen: true }),

  closeOrphanDrawer: () => set({ orphanDrawerOpen: false }),

  toggleOrphanIntentional: async (projectId, componentId) => {
    try {
      await toggleIntentionalOrphan(projectId, componentId)
      await get().fetchRegistryStats(projectId)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '标记失败'
      set({ error: msg })
    }
  },

  syncRegistry: async (projectId) => {
    set({ syncLoading: true, error: null })
    try {
      const result = await extractC4Registry(projectId)
      set({ registryStats: result.stats, syncLoading: false, error: null })
      await get().fetchDslCurrent(projectId)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '同步失败'
      set({ error: msg, syncLoading: false })
    }
  },

  fetchRegistryStats: async (projectId) => {
    try {
      const stats = await getC4RegistryStats(projectId)
      set({ registryStats: stats })
    } catch {
      // ignore non-fatal stats load
    }
  },
}))
