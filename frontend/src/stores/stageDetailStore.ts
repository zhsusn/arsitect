import { create } from 'zustand'

const STORAGE_KEY = 'stage-detail-width'

function getInitialWidth(): number {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const parsed = parseInt(stored, 10)
      if (!Number.isNaN(parsed) && parsed >= 400 && parsed <= 1200) {
        return parsed
      }
    }
  } catch {
    // ignore storage errors
  }
  return 600
}

export interface StageDetailState {
  isOpen: boolean
  projectId: string | null
  stageId: string | null
  activeTab: string
  width: number
  hasUnreadReview: boolean
  openPanel: (projectId: string, stageId: string) => void
  closePanel: () => void
  setActiveTab: (tab: string) => void
  setWidth: (width: number) => void
  markReviewViewed: () => void
}

export const useStageDetailStore = create<StageDetailState>((set) => ({
  isOpen: false,
  projectId: null,
  stageId: null,
  activeTab: 'skill',
  width: getInitialWidth(),
  hasUnreadReview: false,
  openPanel: (projectId, stageId) =>
    set({ isOpen: true, projectId, stageId, activeTab: 'skill', hasUnreadReview: true }),
  closePanel: () => set({ isOpen: false, projectId: null, stageId: null }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setWidth: (width) => {
    set({ width })
    try {
      localStorage.setItem(STORAGE_KEY, String(width))
    } catch {
      // ignore storage errors
    }
  },
  markReviewViewed: () => set({ hasUnreadReview: false }),
}))
