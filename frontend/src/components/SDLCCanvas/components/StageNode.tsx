import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'

interface StageNodeData {
  label?: string
  status?: string
  progress?: number
  onExecute?: () => void
  gateStatus?: string
  isExecuting?: boolean
}

// Runtime status colors aligned with design.md section 7.2.1
const STATUS_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  // legacy statuses
  DEFINED: { bg: '#f3f4f6', border: '#d1d5db', text: '#6b7280' },
  SCHEDULED: { bg: '#dbeafe', border: '#3b82f6', text: '#1e40af' },
  EXECUTED: { bg: '#dcfce7', border: '#22c55e', text: '#166534' },
  FAILED: { bg: '#fee2e2', border: '#ef4444', text: '#991b1b' },
  SKIPPED: { bg: '#f3f4f6', border: '#9ca3af', text: '#6b7280' },
  Executing: { bg: '#eff6ff', border: '#3b82f6', text: '#1e40af' },
  Success: { bg: '#dcfce7', border: '#22c55e', text: '#166534' },
  Pending: { bg: '#f3f4f6', border: '#d1d5db', text: '#6b7280' },
  // runtime statuses
  not_started: { bg: '#f3f4f6', border: '#d1d5db', text: '#6b7280' },
  ready: { bg: '#dbeafe', border: '#3b82f6', text: '#1e40af' },
  in_progress: { bg: '#eff6ff', border: '#3b82f6', text: '#1e40af' },
  review_pending: { bg: '#fef9c3', border: '#eab308', text: '#854d0e' },
  gate_pending: { bg: '#ffedd5', border: '#f97316', text: '#9a3412' },
  passed: { bg: '#dcfce7', border: '#22c55e', text: '#166534' },
  blocked: { bg: '#fee2e2', border: '#ef4444', text: '#991b1b' },
  skipped: { bg: '#f3f4f6', border: '#9ca3af', text: '#6b7280' },
}

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

const StageNode = memo(function StageNode(props: NodeProps) {
  const data = props.data as StageNodeData
  const status = data?.status || 'not_started'
  const label = data?.label || 'Stage'
  const progress = data?.progress ?? 0
  const isSkipped = status === 'skipped' || status === 'SKIPPED'

  const onExecute = data?.onExecute
  const gateStatus = data?.gateStatus
  const isExecuting = data?.isExecuting

  const gatePassed = !gateStatus || gateStatus === 'passed'
  const canExecute = onExecute && !isExecuting && gatePassed && status === 'ready'
  const effectiveStatus = isExecuting ? 'Executing' : status
  const effectiveColors = STATUS_COLORS[effectiveStatus] || STATUS_COLORS.not_started
  const statusLabel = STATUS_LABEL[status] || status

  return (
    <div
      style={{
        minWidth: 160,
        padding: '8px 12px',
        borderRadius: 8,
        backgroundColor: effectiveColors.bg,
        border: `2px ${isSkipped ? 'dashed' : 'solid'} ${effectiveColors.border}`,
        color: effectiveColors.text,
        fontSize: 13,
        fontWeight: 600,
        textAlign: 'center',
        position: 'relative',
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: effectiveColors.border }} />
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
          <span>{label}</span>
          {onExecute && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                if (canExecute) onExecute()
              }}
              disabled={!canExecute}
              title={
                !gatePassed
                  ? 'Gate未通过'
                  : isExecuting
                    ? '执行中...'
                    : status !== 'ready'
                      ? '阶段未就绪'
                      : '执行该Stage'
              }
              style={{
                padding: '2px 8px',
                fontSize: 11,
                borderRadius: 4,
                border: '1px solid',
                borderColor: canExecute ? effectiveColors.border : '#d1d5db',
                background: canExecute ? '#fff' : '#f3f4f6',
                color: canExecute ? effectiveColors.text : '#9ca3af',
                cursor: canExecute ? 'pointer' : 'not-allowed',
                opacity: canExecute ? 1 : 0.6,
                lineHeight: 1.4,
              }}
            >
              {isExecuting ? '执行中' : '执行'}
            </button>
          )}
        </div>
        <div
          style={{
            fontSize: 11,
            fontWeight: 500,
            padding: '1px 6px',
            borderRadius: 10,
            background: '#fff',
            border: `1px solid ${effectiveColors.border}`,
            color: effectiveColors.text,
          }}
        >
          {statusLabel}
        </div>
      </div>
      {progress > 0 && (
        <div
          style={{
            width: '100%',
            height: 4,
            backgroundColor: '#e5e7eb',
            borderRadius: 2,
            overflow: 'hidden',
            marginTop: 6,
          }}
        >
          <div
            style={{
              width: `${Math.min(progress, 100)}%`,
              height: '100%',
              backgroundColor: effectiveColors.border,
              borderRadius: 2,
              transition: 'width 0.3s ease',
            }}
          />
        </div>
      )}
      <Handle type="source" position={Position.Bottom} style={{ background: effectiveColors.border }} />
    </div>
  )
})

export default StageNode