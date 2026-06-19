import { useState } from 'react'

interface ExecutionPanelProps {
  status: string
  logs: string[]
  skillName: string
  onExecute: () => void
  onRetry: () => void
  onAbort: () => void
}

const flowStages = ['PREP', 'EXEC', 'POST']

export default function ExecutionPanel({ status, logs, skillName, onExecute, onRetry, onAbort }: ExecutionPanelProps) {
  const [logsExpanded, setLogsExpanded] = useState(true)
  const isExecuting = status === 'prep' || status === 'exec' || status === 'post'
  const currentStageIndex = flowStages.indexOf(status.toUpperCase())

  return (
    <div
      style={{
        width: 300,
        minWidth: 300,
        borderLeft: '1px solid #e5e7eb',
        background: '#fff',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div style={{ padding: 16, borderBottom: '1px solid #e5e7eb' }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: '#111827', marginBottom: 12 }}>
          Skill: {skillName}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 16 }}>
          {flowStages.map((s, i) => (
            <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <div
                style={{
                  width: 20,
                  height: 20,
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: i <= currentStageIndex && currentStageIndex >= 0 ? '#2563eb' : '#e5e7eb',
                  color: i <= currentStageIndex && currentStageIndex >= 0 ? '#fff' : '#9ca3af',
                  fontSize: 10,
                  fontWeight: 700,
                }}
              >
                {i < currentStageIndex ? '✓' : i + 1}
              </div>
              <span
                style={{
                  fontSize: 11,
                  color: i <= currentStageIndex && currentStageIndex >= 0 ? '#2563eb' : '#9ca3af',
                  fontWeight: 500,
                }}
              >
                {s}
              </span>
              {i < flowStages.length - 1 && (
                <div style={{ width: 12, height: 2, background: i < currentStageIndex ? '#2563eb' : '#e5e7eb' }} />
              )}
            </div>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={onExecute}
            disabled={isExecuting}
            style={{
              flex: 1,
              padding: '6px 12px',
              fontSize: 12,
              background: '#2563eb',
              color: '#fff',
              border: 'none',
              borderRadius: 4,
              cursor: isExecuting ? 'not-allowed' : 'pointer',
              opacity: isExecuting ? 0.6 : 1,
            }}
          >
            执行
          </button>
          <button
            onClick={onRetry}
            disabled={isExecuting}
            style={{
              flex: 1,
              padding: '6px 12px',
              fontSize: 12,
              background: '#fff',
              color: '#2563eb',
              border: '1px solid #2563eb',
              borderRadius: 4,
              cursor: isExecuting ? 'not-allowed' : 'pointer',
              opacity: isExecuting ? 0.6 : 1,
            }}
          >
            重试
          </button>
          <button
            onClick={onAbort}
            disabled={!isExecuting}
            style={{
              flex: 1,
              padding: '6px 12px',
              fontSize: 12,
              background: '#fff',
              color: '#dc2626',
              border: '1px solid #dc2626',
              borderRadius: 4,
              cursor: !isExecuting ? 'not-allowed' : 'pointer',
              opacity: !isExecuting ? 0.6 : 1,
            }}
          >
            中断
          </button>
        </div>
      </div>
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
        <button
          onClick={() => setLogsExpanded((v) => !v)}
          style={{
            width: '100%',
            textAlign: 'left',
            padding: '8px 16px',
            border: 'none',
            borderBottom: logsExpanded ? '1px solid #e5e7eb' : 'none',
            background: '#f9fafb',
            cursor: 'pointer',
            fontSize: 12,
            fontWeight: 600,
            color: '#374151',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          实时日志
          <span style={{ fontSize: 10 }}>{logsExpanded ? '▲' : '▼'}</span>
        </button>
        {logsExpanded && (
          <div
            style={{
              padding: 12,
              fontFamily: 'monospace',
              fontSize: 11,
              color: '#374151',
              background: '#f3f4f6',
              overflowY: 'auto',
              maxHeight: 300,
              lineHeight: 1.5,
            }}
          >
            {logs.length === 0 && <span style={{ color: '#9ca3af' }}>暂无日志</span>}
            {logs.map((log, i) => (
              <div key={i} style={{ marginBottom: 4 }}>
                {log}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
