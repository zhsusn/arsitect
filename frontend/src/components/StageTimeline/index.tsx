import type { TemplateStage } from '../../services/template'

interface StageTimelineProps {
  stages: TemplateStage[]
  executedStageIds?: Set<string>
  frozenStageIds?: Set<string>
  removedStageIds?: Set<string>
  addedStageIds?: Set<string>
}

function groupByMergeGroup(stages: TemplateStage[]): Map<string | null, TemplateStage[]> {
  const map = new Map<string | null, TemplateStage[]>()
  for (const s of stages) {
    const key = s.merge_group_id ?? null
    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(s)
  }
  return map
}

export default function StageTimeline({
  stages,
  executedStageIds = new Set(),
  frozenStageIds = new Set(),
  removedStageIds = new Set(),
  addedStageIds = new Set(),
}: StageTimelineProps) {
  const groups = groupByMergeGroup(stages)
  const sortedKeys = Array.from(groups.keys()).sort((a, b) => {
    const aIdx = groups.get(a)![0].order_index
    const bIdx = groups.get(b)![0].order_index
    return aIdx - bIdx
  })

  const getStageStyle = (stage: TemplateStage): React.CSSProperties => {
    if (frozenStageIds.has(stage.stage_id)) {
      return { background: '#fef3c7', borderColor: '#f59e0b' }
    }
    if (removedStageIds.has(stage.stage_id)) {
      return { background: '#fee2e2', borderColor: '#ef4444', opacity: 0.6 }
    }
    if (addedStageIds.has(stage.stage_id)) {
      return { background: '#dcfce7', borderColor: '#22c55e' }
    }
    if (executedStageIds.has(stage.stage_id)) {
      return { background: '#e0e7ff', borderColor: '#6366f1' }
    }
    return { background: '#fff', borderColor: '#e5e7eb' }
  }

  return (
    <div style={{ padding: '16px 0' }}>
      <h3 style={{ margin: '0 0 16px 0', fontSize: 16 }}>Stage 时间线</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
        {sortedKeys.map((groupKey, groupIdx) => {
          const groupStages = groups.get(groupKey)!
          const isMergeGroup = groupKey !== null && groupStages.length > 1

          return (
            <div key={groupKey ?? `seq-${groupIdx}`} style={{ display: 'flex', alignItems: 'stretch' }}>
              {/* Timeline line */}
              <div
                style={{
                  width: 32,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  position: 'relative',
                }}
              >
                <div
                  style={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    background: isMergeGroup ? '#a855f7' : '#3b82f6',
                    marginTop: 14,
                    zIndex: 1,
                  }}
                />
                {groupIdx < sortedKeys.length - 1 && (
                  <div
                    style={{
                      width: 2,
                      flex: 1,
                      background: '#e5e7eb',
                      marginTop: 4,
                    }}
                  />
                )}
              </div>

              {/* Stage card(s) */}
              <div
                style={{
                  flex: 1,
                  padding: '8px 0',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 8,
                }}
              >
                {isMergeGroup && (
                  <div
                    style={{
                      fontSize: 11,
                      color: '#a855f7',
                      fontWeight: 600,
                      paddingLeft: 4,
                    }}
                  >
                    合并组: {groupKey}
                  </div>
                )}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {groupStages.map((stage) => (
                    <div
                      key={stage.stage_id}
                      style={{
                        border: '1px solid',
                        borderRadius: 6,
                        padding: '10px 14px',
                        minWidth: 140,
                        flex: isMergeGroup ? 1 : 'none',
                        ...getStageStyle(stage),
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          marginBottom: 4,
                        }}
                      >
                        <span style={{ fontWeight: 600, fontSize: 14 }}>
                          {stage.stage_name}
                        </span>
                        {stage.skippable && (
                          <span
                            style={{
                              fontSize: 10,
                              padding: '1px 6px',
                              borderRadius: 4,
                              background: '#f3f4f6',
                              color: '#6b7280',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            可跳过
                          </span>
                        )}
                      </div>
                      {stage.gate_id && (
                        <div
                          style={{
                            fontSize: 11,
                            color: '#dc2626',
                            fontWeight: 500,
                            marginTop: 4,
                          }}
                        >
                          🚧 Gate: {stage.gate_id}
                        </div>
                      )}
                      <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 4 }}>
                        #{stage.order_index}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Legend */}
      <div
        style={{
          marginTop: 16,
          display: 'flex',
          gap: 16,
          flexWrap: 'wrap',
          fontSize: 12,
          color: '#6b7280',
        }}
      >
        <LegendItem color="#6366f1" label="已执行" />
        <LegendItem color="#f59e0b" label="冻结" />
        <LegendItem color="#ef4444" label="将被移除" />
        <LegendItem color="#22c55e" label="新增" />
        <LegendItem color="#e5e7eb" label="未执行" />
      </div>
    </div>
  )
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div
        style={{
          width: 12,
          height: 12,
          borderRadius: 3,
          background: color,
          border: `1px solid ${color}`,
        }}
      />
      <span>{label}</span>
    </div>
  )
}
