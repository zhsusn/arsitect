import { useMemo } from 'react'
import { STATUS_COLORS, STATUS_LABELS } from '../constants'

interface SkillItem {
  skillId: string
  skillName: string
  status: string
  durationSec?: number
}

interface StageProgress {
  stageId: string
  stageName: string
  status: string
  progress: number
  skills: SkillItem[]
}

interface BatchExecutionPanelProps {
  open: boolean
  onClose: () => void
  stages: StageProgress[]
  onStartAll: () => void
  onStopAll: () => void
  onStopStage?: (stageId: string) => void
}

function formatDuration(sec?: number): string {
  if (sec === undefined || sec === null) return '-'
  if (sec < 60) return `${sec}s`
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}m${s}s`
}

export default function BatchExecutionPanel({
  open,
  onClose,
  stages,
  onStartAll,
  onStopAll,
  onStopStage,
}: BatchExecutionPanelProps) {
  const hasRunning = useMemo(
    () => stages.some((s) => s.status === 'Executing' || s.skills.some((sk) => sk.status === 'Executing')),
    [stages],
  )

  if (!open) return null

  return (
    <div
      className="absolute bottom-0 left-0 right-0 z-40 bg-white border-t border-gray-200 shadow-2xl"
      style={{
        maxHeight: '50vh',
        animation: 'slideUp 0.25s ease-out',
      }}
    >
      <style>{`
        @keyframes slideUp {
          from { transform: translateY(100%); }
          to { transform: translateY(0); }
        }
      `}</style>

      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-semibold text-gray-800">批量执行总览</h3>
          <span className="text-xs text-gray-500">
            {stages.length} 个 Stage
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onStartAll}
            disabled={hasRunning}
            className="px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            全部启动
          </button>
          <button
            onClick={onStopAll}
            disabled={!hasRunning}
            className="px-3 py-1.5 text-xs font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            全部停止
          </button>
          <button
            onClick={onClose}
            className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            收起
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="overflow-auto p-4" style={{ maxHeight: 'calc(50vh - 52px)' }}>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {stages.map((stage) => {
            const colors = STATUS_COLORS[stage.status] || STATUS_COLORS.Pending
            const completedCount = stage.skills.filter(
              (s) => s.status === 'Success' || s.status === 'Executed',
            ).length
            const totalCount = stage.skills.length || 1

            return (
              <div
                key={stage.stageId}
                className="border border-gray-200 rounded-lg overflow-hidden bg-white"
              >
                <div
                  className="px-3 py-2 flex items-center justify-between"
                  style={{ backgroundColor: colors.bg, borderBottom: `1px solid ${colors.border}` }}
                >
                  <span className="text-sm font-semibold" style={{ color: colors.text }}>
                    {stage.stageName}
                  </span>
                  <div className="flex items-center gap-2">
                    <span
                      className="text-xs font-medium px-2 py-0.5 rounded-full"
                      style={{
                        backgroundColor: colors.bg,
                        color: colors.text,
                        border: `1px solid ${colors.border}`,
                      }}
                    >
                      {STATUS_LABELS[stage.status] || stage.status}
                    </span>
                    {onStopStage && (stage.status === 'Executing' || stage.skills.some((s) => s.status === 'Executing')) && (
                      <button
                        onClick={() => onStopStage(stage.stageId)}
                        className="text-xs px-2 py-0.5 rounded text-white bg-red-500 hover:bg-red-600 transition-colors"
                      >
                        停止
                      </button>
                    )}
                  </div>
                </div>

                <div className="px-3 py-2">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${Math.min(stage.progress, 100)}%`,
                          backgroundColor: colors.border,
                        }}
                      />
                    </div>
                    <span className="text-xs text-gray-500 tabular-nums">
                      {Math.round(stage.progress)}%
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mb-2">
                    {completedCount}/{totalCount} Skill 已完成
                  </div>

                  {stage.skills.length > 0 && (
                    <div className="space-y-1 max-h-32 overflow-auto">
                      {stage.skills.map((skill) => {
                        const sc = STATUS_COLORS[skill.status] || STATUS_COLORS.Pending
                        return (
                          <div
                            key={skill.skillId}
                            className="flex items-center justify-between text-xs px-2 py-1 rounded"
                            style={{ backgroundColor: sc.bg }}
                          >
                            <span className="font-medium truncate" style={{ color: sc.text }}>
                              {skill.skillName}
                            </span>
                            <div className="flex items-center gap-2 shrink-0 ml-2">
                              <span style={{ color: sc.text }}>
                                {STATUS_LABELS[skill.status] || skill.status}
                              </span>
                              <span className="text-gray-400 tabular-nums">
                                {formatDuration(skill.durationSec)}
                              </span>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {stages.length === 0 && (
          <div className="text-center text-sm text-gray-400 py-8">暂无执行数据</div>
        )}
      </div>
    </div>
  )
}
