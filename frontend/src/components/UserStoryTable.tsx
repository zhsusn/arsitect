import React, { useState } from 'react'
import { Plus, Trash2, CheckCircle2, Circle } from 'lucide-react'

export interface UserStory {
  id: string
  role: string
  description: string
  priority: 'P0' | 'P1' | 'P2' | 'P3'
  status: 'generated' | 'modified' | 'confirmed'
  acceptanceCriteria: string[]
  createdAt: string
  updatedAt: string
}

const priorityColors: Record<string, { bg: string; color: string }> = {
  P0: { bg: '#fef2f2', color: '#dc2626' },
  P1: { bg: '#fef3c7', color: '#92400e' },
  P2: { bg: '#eff6ff', color: '#2563eb' },
  P3: { bg: '#f3f4f6', color: '#6b7280' },
}

const statusIcons: Record<string, typeof Circle> = {
  generated: Circle,
  modified: Circle,
  confirmed: CheckCircle2,
}

const statusLabels: Record<string, string> = {
  generated: '已生成',
  modified: '已修改',
  confirmed: '已确认',
}

interface UserStoryTableProps {
  stories: UserStory[]
  onAdd?: () => void
  onDelete?: (id: string) => void
  onConfirm?: (id: string) => void
  onImport?: () => void
  loading?: boolean
}

export default function UserStoryTable({ stories, onAdd, onDelete, onConfirm, onImport, loading }: UserStoryTableProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null)

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 头部 */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '12px 16px',
          borderBottom: '1px solid #e5e7eb',
        }}
      >
        <div>
          <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600, color: '#111827' }}>
            用户故事列表
          </h3>
          <p style={{ margin: '4px 0 0', fontSize: 12, color: '#6b7280' }}>
            共 {stories.length} 条用户故事，已确认 {stories.filter((s) => s.status === 'confirmed').length} 条
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {onImport && (
            <button
              onClick={onImport}
              disabled={loading}
              style={{
                padding: '6px 12px',
                fontSize: 12,
                background: '#fff',
                color: '#6b7280',
                border: '1px solid #e5e7eb',
                borderRadius: 4,
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.6 : 1,
                display: 'flex',
                alignItems: 'center',
                gap: 4,
              }}
            >
              📥 从需求导入
            </button>
          )}
          <button
            onClick={onAdd}
            disabled={loading}
            style={{
              padding: '6px 12px',
              fontSize: 12,
              background: '#fff',
              color: '#2563eb',
              border: '1px solid #2563eb',
              borderRadius: 4,
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.6 : 1,
              display: 'flex',
              alignItems: 'center',
              gap: 4,
            }}
          >
            <Plus size={14} />
            新增
          </button>
        </div>
      </div>

      {/* 表格 */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {stories.length === 0 ? (
          <div
            style={{
              padding: 40,
              textAlign: 'center',
              color: '#9ca3af',
              fontSize: 13,
            }}
          >
            暂无用户故事，请先执行"用户故事"生成 Skill
          </div>
        ) : (
          <table style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
                <th style={{ textAlign: 'left', padding: '10px 12px', fontWeight: 600, color: '#374151', width: 80 }}>ID</th>
                <th style={{ textAlign: 'left', padding: '10px 12px', fontWeight: 600, color: '#374151', width: 100 }}>角色</th>
                <th style={{ textAlign: 'left', padding: '10px 12px', fontWeight: 600, color: '#374151' }}>需求描述</th>
                <th style={{ textAlign: 'left', padding: '10px 12px', fontWeight: 600, color: '#374151', width: 70 }}>优先级</th>
                <th style={{ textAlign: 'left', padding: '10px 12px', fontWeight: 600, color: '#374151', width: 80 }}>状态</th>
                <th style={{ textAlign: 'left', padding: '10px 12px', fontWeight: 600, color: '#374151', width: 80 }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {stories.map((story) => {
                const isExpanded = expandedId === story.id
                const StatusIcon = statusIcons[story.status]
                return (
                  <React.Fragment key={story.id}>
                    <tr
                      onClick={() => setExpandedId(isExpanded ? null : story.id)}
                      style={{
                        borderBottom: '1px solid #f3f4f6',
                        cursor: 'pointer',
                        background: isExpanded ? '#f9fafb' : 'transparent',
                      }}
                    >
                      <td style={{ padding: '10px 12px', color: '#2563eb', fontWeight: 500 }}>{story.id}</td>
                      <td style={{ padding: '10px 12px', color: '#374151' }}>{story.role}</td>
                      <td style={{ padding: '10px 12px', color: '#374151' }}>{story.description}</td>
                      <td style={{ padding: '10px 12px' }}>
                        <span
                          style={{
                            fontSize: 11,
                            fontWeight: 600,
                            padding: '2px 8px',
                            borderRadius: 4,
                            background: priorityColors[story.priority].bg,
                            color: priorityColors[story.priority].color,
                          }}
                        >
                          {story.priority}
                        </span>
                      </td>
                      <td style={{ padding: '10px 12px' }}>
                        <span
                          style={{
                            fontSize: 12,
                            display: 'flex',
                            alignItems: 'center',
                            gap: 4,
                            color: story.status === 'confirmed' ? '#16a34a' : '#6b7280',
                          }}
                        >
                          <StatusIcon size={14} />
                          {statusLabels[story.status]}
                        </span>
                      </td>
                      <td style={{ padding: '10px 12px' }}>
                        <div style={{ display: 'flex', gap: 6 }}>
                          {story.status !== 'confirmed' && onConfirm && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                onConfirm(story.id)
                              }}
                              style={{
                                padding: '2px 6px',
                                fontSize: 11,
                                background: '#eff6ff',
                                color: '#2563eb',
                                border: 'none',
                                borderRadius: 4,
                                cursor: 'pointer',
                              }}
                            >
                              确认
                            </button>
                          )}
                          {onDelete && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                onDelete(story.id)
                              }}
                              style={{
                                padding: 2,
                                background: 'none',
                                border: 'none',
                                cursor: 'pointer',
                                color: '#9ca3af',
                              }}
                            >
                              <Trash2 size={14} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                    {isExpanded && (
                      <tr>
                        <td colSpan={6} style={{ padding: '0 12px 12px', background: '#f9fafb' }}>
                          <div
                            style={{
                              padding: 12,
                              background: '#fff',
                              borderRadius: 6,
                              border: '1px solid #e5e7eb',
                            }}
                          >
                            <div style={{ fontSize: 12, fontWeight: 600, color: '#374151', marginBottom: 6 }}>
                              验收标准
                            </div>
                            {story.acceptanceCriteria.length === 0 ? (
                              <div style={{ fontSize: 12, color: '#9ca3af' }}>暂无验收标准</div>
                            ) : (
                              <ul style={{ margin: 0, paddingLeft: 20, fontSize: 12, color: '#4b5563' }}>
                                {story.acceptanceCriteria.map((ac, i) => (
                                  <li key={i} style={{ marginBottom: 4 }}>{ac}</li>
                                ))}
                              </ul>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
