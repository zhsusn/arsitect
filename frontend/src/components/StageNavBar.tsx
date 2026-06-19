import { Lock, CheckCircle, Circle, ChevronRight, AlertCircle, XCircle } from 'lucide-react'

export interface StageInfo {
  id: string
  name: string
  status: 'locked' | 'not_started' | 'in_progress' | 'passed' | 'current'
  progress?: number
  gateStatus?: 'pending' | 'approved' | 'rejected' | null
}

interface StageNavBarProps {
  stages: StageInfo[]
  currentStage: string
  onStageChange: (stage: string) => void
}

export default function StageNavBar({ stages, currentStage, onStageChange }: StageNavBarProps) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '12px 16px',
        borderBottom: '1px solid #e5e7eb',
        background: '#fff',
        overflowX: 'auto',
      }}
    >
      {stages.map((stage, index) => {
        const isLocked = stage.status === 'locked'
        const isCurrent = stage.id === currentStage
        const isPassed = stage.status === 'passed'
        const gatePending = stage.gateStatus === 'pending'
        const gateRejected = stage.gateStatus === 'rejected'
        return (
          <div key={stage.id} style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
            <button
              onClick={() => !isLocked && onStageChange(stage.id)}
              disabled={isLocked}
              title={isLocked ? '阶段锁定，需完成前置阶段并审批通过' : stage.name}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '8px 16px',
                borderRadius: 6,
                border: isCurrent ? '2px solid #2563eb' : gateRejected ? '2px solid #dc2626' : gatePending ? '2px solid #f59e0b' : '1px solid #e5e7eb',
                background: isCurrent ? '#eff6ff' : gateRejected ? '#fef2f2' : gatePending ? '#fffbeb' : '#fff',
                color: isLocked ? '#9ca3af' : isCurrent ? '#2563eb' : '#374151',
                cursor: isLocked ? 'not-allowed' : 'pointer',
                opacity: isLocked ? 0.6 : 1,
                fontSize: 13,
                fontWeight: 600,
                whiteSpace: 'nowrap',
              }}
            >
              {isLocked && <Lock size={14} />}
              {isPassed && <CheckCircle size={14} color="#16a34a" />}
              {gatePending && <AlertCircle size={14} color="#f59e0b" />}
              {gateRejected && <XCircle size={14} color="#dc2626" />}
              {!isLocked && !isPassed && !gatePending && !gateRejected && <Circle size={14} color={isCurrent ? '#2563eb' : '#9ca3af'} />}
              <span>{stage.name}</span>
              {typeof stage.progress === 'number' && stage.progress > 0 && (
                <span style={{ fontSize: 11, fontWeight: 400, color: '#6b7280' }}>{stage.progress}%</span>
              )}
            </button>
            {index < stages.length - 1 && <ChevronRight size={16} color="#d1d5db" />}
          </div>
        )
      })}
    </div>
  )
}
