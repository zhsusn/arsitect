import { useCallback, useEffect, useMemo, useState } from 'react'
import { useStageDetailStore } from '../../stores/stageDetailStore'
import ResizeHandle from './components/ResizeHandle'
import SkillSnapshotTab from './components/SkillSnapshotTab'
import PocketFlowStatusTab from './components/PocketFlowStatusTab'
import ArtifactCardsTab from './components/ArtifactCardsTab'
import ExecutionLogsTab from './components/ExecutionLogsTab'
import AnnotationTab from './components/AnnotationTab'
import GateLinkTab from './components/GateLinkTab'
import BadgeManager from './components/BadgeManager'
import {
  fetchStageProgress,
  executeProjectStage,
  advanceProjectStage,
  decideProjectStageGate,
  fetchProjectStageGate,
  fetchStageExecutionStatus,
  type StageProgressItem,
  type StageGateDecision,
  type StageExecutionStatus,
} from '../../services/stage'
import { useProjectSSE } from '../../services/sse'
import StageAdjustmentModal from '../../pages/ProjectDashboard/components/StageAdjustmentModal'

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

const STATUS_LABEL: Record<string, string> = {
  not_started: '未开始',
  ready: '就绪',
  in_progress: '进行中',
  review_pending: '待审查',
  gate_pending: '待确认',
  passed: '已通过',
  blocked: '已阻塞',
  skipped: '已跳过',
}

export default function StageDetailPanel() {
  const {
    isOpen,
    projectId,
    stageId,
    activeTab,
    width,
    hasUnreadReview,
    closePanel,
    setActiveTab,
    markReviewViewed,
  } = useStageDetailStore()

  const [stage, setStage] = useState<StageProgressItem | null>(null)
  const [projectStrategy, setProjectStrategy] = useState<string>('semi_auto')
  const [gateInfo, setGateInfo] = useState<StageGateDecision | null>(null)
  const [gateReason, setGateReason] = useState('')
  const [loading, setLoading] = useState(false)
  const [adjustOpen, setAdjustOpen] = useState(false)
  const [executionStatus, setExecutionStatus] = useState<StageExecutionStatus | null>(null)

  const loadExecutionStatus = useCallback(async () => {
    if (!stageId) return
    try {
      const status = await fetchStageExecutionStatus(stageId)
      setExecutionStatus(status)
    } catch (err) {
      console.error('Failed to load stage execution status:', err)
    }
  }, [stageId])

  const refreshStageData = useCallback(() => {
    if (!projectId || !stageId) return
    Promise.all([fetchStageProgress(projectId), fetchProjectStageGate(projectId, stageId)])
      .then(([progress, gate]) => {
        const matched = progress.stages.find((s) => s.project_stage_id === stageId)
        setStage(matched || null)
        setProjectStrategy(progress.execution_strategy || 'semi_auto')
        setGateInfo(gate)
      })
      .catch((err) => {
        console.error('Failed to refresh stage data:', err)
      })
    void loadExecutionStatus()
  }, [projectId, stageId, loadExecutionStatus])

  useProjectSSE(projectId, {
    'stage.status_changed': refreshStageData,
    'skill.execution_updated': refreshStageData,
    'project.strategy_changed': refreshStageData,
  })

  useEffect(() => {
    if (!isOpen || !projectId || !stageId) return
    let cancelled = false
    setLoading(true)
    Promise.all([
      fetchStageProgress(projectId),
      fetchProjectStageGate(projectId, stageId),
      fetchStageExecutionStatus(stageId),
    ])
      .then(([progress, gate, execStatus]) => {
        if (cancelled) return
        const matched = progress.stages.find((s) => s.project_stage_id === stageId)
        setStage(matched || null)
        setProjectStrategy(progress.execution_strategy || 'semi_auto')
        setGateInfo(gate)
        setGateReason(gate?.reason || '')
        setExecutionStatus(execStatus)
      })
      .catch((err) => {
        console.error('Failed to load stage progress:', err)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [isOpen, projectId, stageId])

  useEffect(() => {
    if (!stageId) return
    const shouldPoll =
      executionStatus?.running_execution_ids.length ||
      executionStatus?.overall_status === 'RUNNING' ||
      executionStatus?.overall_status === 'NOT_STARTED'
    if (!shouldPoll) return

    const timer = setInterval(() => {
      void loadExecutionStatus()
    }, 3000)
    return () => clearInterval(timer)
  }, [stageId, executionStatus, loadExecutionStatus])

  const handleAction = useCallback(
    async (action: 'execute' | 'advance' | 'pass' | 'reject') => {
      if (!projectId || !stageId) return
      try {
        if (action === 'execute') {
          await executeProjectStage(projectId, stageId)
        } else if (action === 'advance') {
          await advanceProjectStage(projectId, stageId)
        } else if (action === 'pass') {
          await decideProjectStageGate(projectId, stageId, 'pass', gateReason || undefined)
        } else if (action === 'reject') {
          await decideProjectStageGate(projectId, stageId, 'reject', gateReason || '需要修改')
        }
        refreshStageData()
      } catch (err) {
        console.error('Stage action failed:', err)
      }
    },
    [projectId, stageId, gateReason, refreshStageData],
  )

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        closePanel()
      }
    },
    [closePanel],
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
    [setActiveTab, markReviewViewed],
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

  const statusLabel = stage ? STATUS_LABEL[stage.runtime_status] || stage.runtime_status : ''

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
          <div className="flex items-center gap-2">
            {projectId && stageId && (
              <button
                type="button"
                onClick={() => setAdjustOpen(true)}
                className="rounded border border-amber-300 bg-amber-50 px-3 py-1 text-sm font-medium text-amber-700 hover:bg-amber-100"
              >
                调整阶段
              </button>
            )}
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
        </div>

        {/* Runtime status summary */}
        {stage && (
          <div className="border-b border-gray-200 bg-gray-50 px-4 py-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-500">阶段状态</div>
                <div className="flex items-center gap-2">
                  <div className="text-base font-semibold text-gray-800">{statusLabel}</div>
                  <span className="rounded bg-gray-200 px-2 py-0.5 text-xs text-gray-700">
                    {projectStrategy === 'full_auto'
                      ? '全自动'
                      : projectStrategy === 'full_manual'
                        ? '全人工'
                        : '半自动'}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-500">进度</div>
                <div className="text-base font-semibold text-gray-800">{stage.progress_percent}%</div>
              </div>
            </div>

            {/* Progress bar */}
            <div className="mt-3 h-2 w-full rounded-full bg-gray-200">
              <div
                className="h-2 rounded-full bg-blue-600 transition-all"
                style={{ width: `${stage.progress_percent}%` }}
              />
            </div>

            {/* Blocked reason */}
            {stage.runtime_status === 'blocked' && executionStatus?.error_summary && (
              <div className="mt-3 rounded-md bg-red-100 p-2 text-xs text-red-700">
                <span className="font-semibold">阻塞原因:</span> {executionStatus.error_summary}
              </div>
            )}

            {(stage.runtime_status === 'review_pending' || stage.runtime_status === 'gate_pending') && (
              <div className="mt-3">
                <label className="block text-sm text-gray-600 mb-1">审批意见</label>
                <input
                  type="text"
                  value={gateReason}
                  onChange={(e) => setGateReason(e.target.value)}
                  placeholder="输入通过/驳回原因（可选）"
                  className="w-full rounded border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
                />
                {gateInfo && (
                  <div className="mt-2 text-xs text-gray-500">
                    Gate ID: {gateInfo.decision_id} | 创建于 {gateInfo.created_at ? new Date(gateInfo.created_at).toLocaleString() : '-'}
                  </div>
                )}
              </div>
            )}

            <div className="mt-3 flex flex-wrap gap-2">
              {stage.runtime_status === 'ready' && (
                <button
                  type="button"
                  onClick={() => handleAction('execute')}
                  className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
                >
                  执行
                </button>
              )}
              {stage.runtime_status === 'in_progress' && (
                <span className="rounded bg-blue-100 px-3 py-1.5 text-sm font-medium text-blue-800">
                  执行中...
                </span>
              )}
              {(stage.runtime_status === 'review_pending' || stage.runtime_status === 'gate_pending') && (
                <>
                  <button
                    type="button"
                    onClick={() => handleAction('pass')}
                    className="rounded bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700"
                  >
                    确认通过
                  </button>
                  <button
                    type="button"
                    onClick={() => handleAction('reject')}
                    className="rounded bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700"
                  >
                    返回修改
                  </button>
                </>
              )}
              {stage.runtime_status === 'blocked' && (
                <button
                  type="button"
                  onClick={() => handleAction('execute')}
                  className="rounded bg-yellow-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-yellow-700"
                >
                  重试
                </button>
              )}
              {stage.runtime_status === 'passed' && (
                <span className="rounded bg-green-100 px-3 py-1.5 text-sm font-medium text-green-800">
                  已完成
                </span>
              )}
            </div>
          </div>
        )}
        {loading && (
          <div className="border-b border-gray-200 bg-gray-50 px-4 py-2 text-sm text-gray-500">
            加载中...
          </div>
        )}

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

      {projectId && (
        <StageAdjustmentModal
          open={adjustOpen}
          projectId={projectId}
          currentStageId={stageId ?? undefined}
          onClose={() => setAdjustOpen(false)}
          onAction={refreshStageData}
        />
      )}
    </div>
  )
}
