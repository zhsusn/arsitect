import { useState, useMemo } from 'react'
import { ChevronDown, ChevronRight, FileText, Play, Eye } from 'lucide-react'

export interface TaskItem {
  taskId: string
  name: string
  status: 'NOT_STARTED' | 'IN_PROGRESS' | 'PASSED' | 'FAILED' | 'BLOCKED' | 'INHERITED'
  type: string
  description?: string
  module?: string
  isReadOnly?: boolean
}

interface TaskTreeProps {
  tasks: TaskItem[]
  selectedTaskId: string | null
  onTaskSelect: (taskId: string) => void
  onTaskExecute: (taskId: string) => void
  onTaskView?: (taskId: string) => void
}

const statusColors: Record<string, string> = {
  NOT_STARTED: '#9ca3af',
  IN_PROGRESS: '#2563eb',
  PASSED: '#16a34a',
  FAILED: '#dc2626',
  BLOCKED: '#ea580c',
  INHERITED: '#6b7280',
}

const statusLabels: Record<string, string> = {
  NOT_STARTED: '未开始',
  IN_PROGRESS: '执行中',
  PASSED: '通过',
  FAILED: '失败',
  BLOCKED: '阻塞',
  INHERITED: '继承',
}

export default function TaskTree({ tasks, selectedTaskId, onTaskSelect, onTaskExecute, onTaskView }: TaskTreeProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})

  const grouped = useMemo(() => {
    const groups: Record<string, TaskItem[]> = {}
    tasks.forEach((task) => {
      const mod = task.module || '默认模块'
      if (!groups[mod]) groups[mod] = []
      groups[mod].push(task)
    })
    return groups
  }, [tasks])

  const toggleGroup = (mod: string) => {
    setExpanded((prev) => ({ ...prev, [mod]: !prev[mod] }))
  }

  return (
    <div
      style={{
        width: 260,
        minWidth: 260,
        borderRight: '1px solid #e5e7eb',
        background: '#fff',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {Object.entries(grouped).map(([mod, modTasks]) => {
        const isExpanded = expanded[mod] !== false
        return (
          <div key={mod}>
            <button
              onClick={() => toggleGroup(mod)}
              style={{
                width: '100%',
                textAlign: 'left',
                padding: '8px 12px',
                border: 'none',
                borderBottom: '1px solid #f3f4f6',
                background: '#f9fafb',
                cursor: 'pointer',
                fontSize: 13,
                fontWeight: 600,
                color: '#374151',
                display: 'flex',
                alignItems: 'center',
                gap: 4,
              }}
            >
              {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              {mod}
            </button>
            {isExpanded && (
              <div>
                {modTasks.map((task) => (
                  <div
                    key={task.taskId}
                    onClick={() => onTaskSelect(task.taskId)}
                    style={{
                      padding: '8px 12px 8px 28px',
                      cursor: 'pointer',
                      borderLeft:
                        selectedTaskId === task.taskId ? '3px solid #2563eb' : '3px solid transparent',
                      background: selectedTaskId === task.taskId ? '#eff6ff' : 'transparent',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: 8,
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        flex: 1,
                        minWidth: 0,
                      }}
                    >
                      <FileText size={14} color="#6b7280" />
                      <span
                        style={{
                          fontSize: 13,
                          color: '#374151',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {task.name}
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexShrink: 0 }}>
                      <span
                        style={{
                          fontSize: 11,
                          padding: '2px 6px',
                          borderRadius: 4,
                          background: `${statusColors[task.status]}20`,
                          color: statusColors[task.status],
                          fontWeight: 500,
                          whiteSpace: 'nowrap',
                        }}
                        title={task.description || statusLabels[task.status]}
                      >
                        {task.status}
                      </span>
                      {task.isReadOnly || task.status === 'INHERITED' ? (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            onTaskView?.(task.taskId)
                          }}
                          style={{
                            padding: 2,
                            border: 'none',
                            background: 'transparent',
                            cursor: 'pointer',
                            color: '#6b7280',
                            display: 'flex',
                            alignItems: 'center',
                          }}
                          title="查看（继承自上游阶段）"
                        >
                          <Eye size={14} />
                        </button>
                      ) : (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            onTaskExecute(task.taskId)
                          }}
                          style={{
                            padding: 2,
                            border: 'none',
                            background: 'transparent',
                            cursor: 'pointer',
                            color: '#2563eb',
                            display: 'flex',
                            alignItems: 'center',
                          }}
                          title="执行 Skill"
                        >
                          <Play size={14} />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
