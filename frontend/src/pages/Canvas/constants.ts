/** 10-color status coloring system for SDLC Canvas nodes. */

export const STATUS_COLORS: Record<
  string,
  { bg: string; border: string; text: string; ring: string; dot: string }
> = {
  Pending: {
    bg: '#f3f4f6',
    border: '#9ca3af',
    text: '#4b5563',
    ring: 'ring-gray-400',
    dot: '#9ca3af',
  },
  Executing: {
    bg: '#eff6ff',
    border: '#3b82f6',
    text: '#1e40af',
    ring: 'ring-blue-500',
    dot: '#3b82f6',
  },
  Success: {
    bg: '#dcfce7',
    border: '#22c55e',
    text: '#166534',
    ring: 'ring-green-500',
    dot: '#22c55e',
  },
  Failed: {
    bg: '#fee2e2',
    border: '#ef4444',
    text: '#991b1b',
    ring: 'ring-red-500',
    dot: '#ef4444',
  },
  Blocked: {
    bg: '#fff7ed',
    border: '#f97316',
    text: '#9a3412',
    ring: 'ring-orange-500',
    dot: '#f97316',
  },
  Skipped: {
    bg: '#f1f5f9',
    border: '#94a3b8',
    text: '#475569',
    ring: 'ring-slate-400',
    dot: '#94a3b8',
  },
  Bypass: {
    bg: '#fefce8',
    border: '#facc15',
    text: '#854d0e',
    ring: 'ring-yellow-400',
    dot: '#facc15',
  },
  Warning: {
    bg: '#fffbeb',
    border: '#f59e0b',
    text: '#92400e',
    ring: 'ring-amber-500',
    dot: '#f59e0b',
  },
  Frozen: {
    bg: '#ecfeff',
    border: '#06b6d4',
    text: '#155e75',
    ring: 'ring-cyan-500',
    dot: '#06b6d4',
  },
  Draft: {
    bg: '#faf5ff',
    border: '#a855f7',
    text: '#6b21a8',
    ring: 'ring-purple-500',
    dot: '#a855f7',
  },
}

export const STATUS_LABELS: Record<string, string> = {
  Pending: '待执行',
  Executing: '执行中',
  Success: '成功',
  Failed: '失败',
  Blocked: '阻塞',
  Skipped: '跳过',
  Bypass: '旁路',
  Warning: '警告',
  Frozen: '冻结',
  Draft: '草稿',
}

export const NODE_TYPE_LABELS: Record<string, string> = {
  stage: '阶段',
  gate: '闸门',
  skill: '技能',
  planNode: '计划节点',
}

export const VIEW_MODE_LABELS: Record<string, string> = {
  stage: '阶段视图',
  execution: '执行视图',
  swimlane: '泳道视图',
  list: '列表视图',
}

export type ViewMode = 'stage' | 'execution' | 'swimlane' | 'list'

export type NodeTypeFilter = 'stage' | 'gate' | 'skill'

export type StatusFilter =
  | 'Pending'
  | 'Executing'
  | 'Success'
  | 'Failed'
  | 'Blocked'
  | 'Skipped'
  | 'Bypass'
  | 'Warning'
  | 'Frozen'
  | 'Draft'

export interface CanvasFilters {
  statuses: StatusFilter[]
  stages: string[]
  types: NodeTypeFilter[]
  keyword: string
  onlyBlocked: boolean
}

export const DEFAULT_FILTERS: CanvasFilters = {
  statuses: [],
  stages: [],
  types: [],
  keyword: '',
  onlyBlocked: false,
}
