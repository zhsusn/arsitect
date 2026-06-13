import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import { STATUS_COLORS } from '../constants'

interface SkillNodeData {
  label?: string
  status?: string
  progress?: number
  skillType?: 'primary' | 'auxiliary'
  stageId?: string
}

const SkillNode = memo(function SkillNode(props: NodeProps) {
  const data = props.data as SkillNodeData
  const status = data?.status || 'Pending'
  const label = data?.label || 'Skill'
  const progress = data?.progress ?? 0
  const skillType = data?.skillType || 'primary'
  const colors = STATUS_COLORS[status] || STATUS_COLORS.Pending
  const isAux = skillType === 'auxiliary'

  return (
    <div
      style={{
        minWidth: 140,
        padding: '8px 12px',
        borderRadius: 8,
        backgroundColor: colors.bg,
        border: `2px ${isAux ? 'dashed' : 'solid'} ${colors.border}`,
        color: colors.text,
        fontSize: 13,
        fontWeight: isAux ? 400 : 600,
        textAlign: 'center',
        position: 'relative',
        opacity: isAux ? 0.9 : 1,
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: colors.border }} />
      <div style={{ marginBottom: progress > 0 ? 6 : 0 }}>
        {isAux && (
          <span
            style={{
              fontSize: 10,
              opacity: 0.7,
              display: 'block',
              marginBottom: 2,
            }}
          >
            辅助
          </span>
        )}
        {label}
      </div>
      {progress > 0 && (
        <div
          style={{
            width: '100%',
            height: 4,
            backgroundColor: '#e5e7eb',
            borderRadius: 2,
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              width: `${Math.min(progress, 100)}%`,
              height: '100%',
              backgroundColor: colors.border,
              borderRadius: 2,
              transition: 'width 0.3s ease',
            }}
          />
        </div>
      )}
      <Handle type="source" position={Position.Bottom} style={{ background: colors.border }} />
    </div>
  )
})

export default SkillNode
