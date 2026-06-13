import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'

interface GateNodeData {
  label?: string
  gateType?: string
  decisionStatus?: string
}

const DECISION_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  passed: { bg: '#dcfce7', border: '#22c55e', text: '#166534' },
  rejected: { bg: '#fee2e2', border: '#ef4444', text: '#991b1b' },
  pending: { bg: '#fef9c3', border: '#eab308', text: '#854d0e' },
  bypassed: { bg: '#ffedd5', border: '#f97316', text: '#9a3412' },
}

const GateNode = memo(function GateNode(props: NodeProps) {
  const data = props.data as GateNodeData
  const status = data?.decisionStatus || 'pending'
  const label = data?.label || 'Gate'
  const gateType = data?.gateType || ''
  const colors = DECISION_COLORS[status] || DECISION_COLORS.pending

  return (
    <div
      style={{
        minWidth: 120,
        padding: '8px 12px',
        borderRadius: 9999,
        backgroundColor: colors.bg,
        border: `2px solid ${colors.border}`,
        color: colors.text,
        fontSize: 12,
        fontWeight: 600,
        textAlign: 'center',
        position: 'relative',
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: colors.border }} />
      <div style={{ fontSize: 10, opacity: 0.7, marginBottom: 2 }}>{gateType}</div>
      <div>{label}</div>
      <Handle type="source" position={Position.Right} style={{ background: colors.border }} />
    </div>
  )
})

export default GateNode
