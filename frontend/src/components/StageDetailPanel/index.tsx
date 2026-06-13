import { useCallback, useEffect, useMemo } from 'react'
import { useStageDetailStore } from '../../stores/stageDetailStore'
import ResizeHandle from './components/ResizeHandle'
import SkillSnapshotTab from './components/SkillSnapshotTab'
import PocketFlowStatusTab from './components/PocketFlowStatusTab'
import ArtifactCardsTab from './components/ArtifactCardsTab'
import ExecutionLogsTab from './components/ExecutionLogsTab'
import AnnotationTab from './components/AnnotationTab'
import GateLinkTab from './components/GateLinkTab'
import BadgeManager from './components/BadgeManager'

interface TabConfig {
  key: string
  label: string
}

const TABS: TabConfig[] = [
  { key: 'skill', label: 'SkillSnapshot' },
  { key: 'pocketflow', label: 'PocketFlow' },
  { key: 'artifact', label: 'Artifact' },
  { key: 'logs', label: 'Logs' },
  { key: 'annotation', label: 'Annotation' },
  { key: 'gatelink', label: 'GateLink' },
]

export default function StageDetailPanel() {
  const {
    isOpen,
    stageId,
    activeTab,
    width,
    hasUnreadReview,
    closePanel,
    setActiveTab,
    markReviewViewed,
  } = useStageDetailStore()

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        closePanel()
      }
    },
    [closePanel]
  )

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown)
      return () => document.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen, handleKeyDown])

  const handleTabClick = useCallback(
    (tabKey: string) => {
      setActiveTab(tabKey)
      if (tabKey === 'annotation') {
        markReviewViewed()
      }
    },
    [setActiveTab, markReviewViewed]
  )

  const tabContent = useMemo(() => {
    switch (activeTab) {
      case 'skill':
        return <SkillSnapshotTab />
      case 'pocketflow':
        return <PocketFlowStatusTab />
      case 'artifact':
        return <ArtifactCardsTab />
      case 'logs':
        return <ExecutionLogsTab />
      case 'annotation':
        return <AnnotationTab />
      case 'gatelink':
        return <GateLinkTab />
      default:
        return <SkillSnapshotTab />
    }
  }, [activeTab])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div
        className="flex-1 bg-black/30"
        onClick={closePanel}
        role="presentation"
      />

      {/* Drawer */}
      <div
        className="relative flex h-full flex-col bg-white shadow-xl"
        style={{ width }}
      >
        <ResizeHandle />

        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
          <h2 className="text-lg font-semibold text-gray-800">
            {stageId ?? 'Stage Detail'}
          </h2>
          <button
            type="button"
            onClick={closePanel}
            className="flex h-8 w-8 items-center justify-center rounded-md text-gray-500 hover:bg-gray-100 hover:text-gray-700"
            aria-label="关闭"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        </div>

        {/* Tab bar */}
        <div className="flex border-b border-gray-200 bg-gray-50">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => handleTabClick(tab.key)}
              className={`relative flex-1 px-2 py-2.5 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              <span className="relative inline-block">
                {tab.label}
                <BadgeManager
                  tabKey={tab.key}
                  hasUnread={hasUnreadReview}
                />
              </span>
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4">{tabContent}</div>
      </div>
    </div>
  )
}
