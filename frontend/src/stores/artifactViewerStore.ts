import { create } from 'zustand'
import api from '@/services/api'

export interface ArtifactFile {
  artifact_id: string
  project_id: string
  stage_id: string | null
  skill_id: string | null
  execution_id: string | null
  file_name: string
  file_path: string
  file_type: 'md' | 'yaml' | 'json' | 'mermaid' | 'openapi' | 'txt' | 'other'
  file_size_bytes: number
  current_version: number
  external_status: 'normal' | 'modified' | 'deleted'
  stale_flag: boolean
  created_at: string | null
  updated_at: string | null
}

export interface ArtifactVersion {
  version_id: string
  artifact_id: string
  version_number: number
  operation_type: 'snapshot' | 'rollback'
  content: string | null
  created_by: string | null
  created_at: string
}

export interface ArtifactContentResponse {
  content: string
  total_lines: number
  content_hash: string
  is_partial: boolean
}

export interface ArtifactStatusResponse {
  artifact_id: string
  external_status: 'normal' | 'modified' | 'deleted'
  file_size_bytes: number
  current_version: number
  content_hash: string
  updated_at: string | null
}

interface ArtifactTreeResponse {
  directories: string[]
  files: ArtifactFile[]
}

export interface TreeFilters {
  stageId: string
  skillId: string
}

interface ArtifactViewerState {
  tree: ArtifactTreeResponse
  selectedArtifact: ArtifactFile | null
  content: string
  contentMeta: { totalLines: number; contentHash: string; isPartial: boolean }
  versions: ArtifactVersion[]
  loading: boolean
  searchQuery: string
  filterType: string
  filterStage: string
  filterSkill: string

  fetchTree: (projectId: string, filters?: Partial<TreeFilters>) => Promise<void>
  selectArtifact: (artifact: ArtifactFile | null) => void
  findArtifactById: (artifactId: string) => ArtifactFile | null
  fetchContent: (artifactId: string, offset?: number, limit?: number, append?: boolean) => Promise<void>
  saveContent: (artifactId: string, content: string, expectedHash?: string) => Promise<void>
  fetchVersions: (artifactId: string) => Promise<void>
  rollback: (artifactId: string, versionNumber: number) => Promise<void>
  fetchArtifactStatus: (artifactId: string) => Promise<ArtifactStatusResponse | null>
  updateArtifactStatus: (artifactId: string, patch: Partial<ArtifactFile>) => void
  setSearchQuery: (q: string) => void
  setFilterType: (type: string) => void
  setFilterStage: (stageId: string) => void
  setFilterSkill: (skillId: string) => void
}

export const useArtifactViewerStore = create<ArtifactViewerState>((set, get) => ({
  tree: { directories: [], files: [] },
  selectedArtifact: null,
  content: '',
  contentMeta: { totalLines: 0, contentHash: '', isPartial: false },
  versions: [],
  loading: false,
  searchQuery: '',
  filterType: '',
  filterStage: '',
  filterSkill: '',

  fetchTree: async (projectId, filters) => {
    const { filterStage, filterSkill } = get()
    const stageId = filters?.stageId !== undefined ? filters.stageId : filterStage
    const skillId = filters?.skillId !== undefined ? filters.skillId : filterSkill
    set({ loading: true })
    try {
      const params: Record<string, unknown> = { project_id: projectId }
      if (stageId) params.filter_stage = stageId
      if (skillId) params.filter_skill = skillId
      const res = await api.get<ArtifactTreeResponse>('/v1/artifacts/tree', { params })
      set({ tree: res.data, loading: false })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载文件树失败'
      console.error('fetchTree error:', msg)
      set({ loading: false })
    }
  },

  selectArtifact: (artifact) => {
    set({ selectedArtifact: artifact, content: '', contentMeta: { totalLines: 0, contentHash: '', isPartial: false } })
    if (artifact) {
      void get().fetchContent(artifact.artifact_id)
      void get().fetchVersions(artifact.artifact_id)
    } else {
      set({ content: '', versions: [] })
    }
  },

  findArtifactById: (artifactId) => {
    return get().tree.files.find((f) => f.artifact_id === artifactId) || null
  },

  fetchContent: async (artifactId, offset = 0, limit, append = false) => {
    try {
      const params: Record<string, unknown> = { offset }
      if (limit !== undefined) params.limit = limit
      const res = await api.get<ArtifactContentResponse>(`/v1/artifacts/${artifactId}/content`, { params })
      set((state) => ({
        content: append && state.content
          ? state.content + '\n' + res.data.content
          : res.data.content,
        contentMeta: {
          totalLines: res.data.total_lines,
          contentHash: res.data.content_hash,
          isPartial: res.data.is_partial,
        },
      }))
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载内容失败'
      console.error('fetchContent error:', msg)
      if (!append) {
        set({ content: '', contentMeta: { totalLines: 0, contentHash: '', isPartial: false } })
      }
    }
  },

  saveContent: async (artifactId, content, expectedHash) => {
    try {
      await api.put(`/v1/artifacts/${artifactId}/content`, { content, expected_hash: expectedHash })
      await get().fetchContent(artifactId)
      await get().fetchVersions(artifactId)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '保存失败'
      console.error('saveContent error:', msg)
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } }
        if (axiosErr.response?.status === 409) {
          const detail = axiosErr.response?.data?.detail || '文件已被外部修改'
          throw new Error(`CONFLICT:${detail}`)
        }
      }
      throw new Error(msg)
    }
  },

  fetchVersions: async (artifactId) => {
    try {
      const res = await api.get<ArtifactVersion[]>(`/v1/artifacts/${artifactId}/versions`)
      set({ versions: res.data })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载版本历史失败'
      console.error('fetchVersions error:', msg)
      set({ versions: [] })
    }
  },

  rollback: async (artifactId, versionNumber) => {
    try {
      await api.post(`/v1/artifacts/${artifactId}/versions/${versionNumber}/rollback`)
      await get().fetchContent(artifactId)
      await get().fetchVersions(artifactId)
      const { selectedArtifact } = get()
      if (selectedArtifact) {
        await get().fetchTree(selectedArtifact.project_id)
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '回滚失败'
      console.error('rollback error:', msg)
      alert(`回滚失败: ${msg}`)
      throw err
    }
  },

  fetchArtifactStatus: async (artifactId) => {
    try {
      const res = await api.get<ArtifactStatusResponse>(`/v1/artifacts/${artifactId}/status`)
      return res.data
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '获取状态失败'
      console.error('fetchArtifactStatus error:', msg)
      return null
    }
  },

  updateArtifactStatus: (artifactId, patch) => {
    set((state) => {
      const newTree = {
        ...state.tree,
        files: state.tree.files.map((f) =>
          f.artifact_id === artifactId ? { ...f, ...patch } : f
        ),
      }
      const newSelected =
        state.selectedArtifact?.artifact_id === artifactId
          ? { ...state.selectedArtifact, ...patch }
          : state.selectedArtifact
      return { tree: newTree, selectedArtifact: newSelected }
    })
  },

  setSearchQuery: (q) => set({ searchQuery: q }),
  setFilterType: (type) => set({ filterType: type }),
  setFilterStage: (stageId) => set({ filterStage: stageId }),
  setFilterSkill: (skillId) => set({ filterSkill: skillId }),
}))
