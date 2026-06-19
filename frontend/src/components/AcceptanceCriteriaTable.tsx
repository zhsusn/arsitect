import { Plus, Trash2 } from 'lucide-react'

export interface AcceptanceCriterion {
  id: string
  relatedStoryId: string
  relatedStoryName?: string
  description: string
  priority: 'P0' | 'P1' | 'P2' | 'P3'
  status: 'generated' | 'modified' | 'confirmed'
  createdAt: string
}

const priorityColors: Record<string, { bg: string; color: string }> = {
  P0: { bg: '#fef2f2', color: '#dc2626' },
  P1: { bg: '#fef3c7', color: '#92400e' },
  P2: { bg: '#eff6ff', color: '#2563eb' },
  P3: { bg: '#f3f4f6', color: '#6b7280' },
}

const statusLabels: Record<string, string> = {
  generated: '已生成',
  modified: '已修改',
  confirmed: '已确认',
}

interface AcceptanceCriteriaTableProps {
  criteria: AcceptanceCriterion[]
  onAdd?: () => void
  onDelete?: (id: string) => void
  onConfirm?: (id: string) => void
  onValidate?: () => void
}

export default function AcceptanceCriteriaTable({
  criteria,
  onAdd,
  onDelete,
  onConfirm,
  onValidate,
}: AcceptanceCriteriaTableProps) {
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
            验收标准列表
          </h3>
          <p style={{ margin: '4px 0 0', fontSize: 12, color: '#6b7280' }}>
            共 {criteria.length} 条验收标准，已确认 {criteria.filter((c) => c.status === 'confirmed').length} 条
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {onValidate && (
            <button
              onClick={onValidate}
              style={{
                padding: '6px 12px',
                fontSize: 12,
                background: '#fff',
                color: '#16a34a',
                border: '1px solid #16a34a',
                borderRadius: 4,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 4,
              }}
            >
              ✅ 校验
            </button>
          )}
          <button
            onClick={onAdd}
            style={{
              padding: '6px 12px',
              fontSize: 12,
              background: '#fff',
              color: '#2563eb',
              border: '1px solid #2563eb',
              borderRadius: 4,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
            }}
          >
            <Plus size={14} />
            新增标准
          </button>
        </div>
      </div>

      {/* 表格 */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {criteria.length === 0 ? (
          <div
            style={{
              padding: 40,
              textAlign: 'center',
              color: '#9ca3af',
              fontSize: 13,
            }}
          >
            暂无验收标准，请先执行"验收标准"生成 Skill
          </div>
        ) : (
          <table style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
                <th style={{ textAlign: 'left', padding: '10px 12px', fontWeight: 600, color: '#374151', width: 70 }}>ID</th>
                <th style={{ textAlign: 'left', padding: '10px 12px', fontWeight: 600, color: '#374151', width: 100 }}>关联故事</th>
                <th style={{ textAlign: 'left', padding: '10px 12px', fontWeight: 600, color: '#374151' }}>验收标准描述</th>
                <th style={{ textAlign: 'left', padding: '10px 12px', fontWeight: 600, color: '#374151', width: 70 }}>优先级</th>
                <th style={{ textAlign: 'left', padding: '10px 12px', fontWeight: 600, color: '#374151', width: 70 }}>状态</th>
                <th style={{ textAlign: 'left', padding: '10px 12px', fontWeight: 600, color: '#374151', width: 80 }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {criteria.map((criterion) => (
                <tr key={criterion.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                  <td style={{ padding: '10px 12px', color: '#2563eb', fontWeight: 500 }}>
                    {criterion.id}
                  </td>
                  <td style={{ padding: '10px 12px', color: '#374151', fontSize: 12 }}>
                    {criterion.relatedStoryName || criterion.relatedStoryId}
                  </td>
                  <td style={{ padding: '10px 12px', color: '#374151' }}>
                    {criterion.description}
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <span
                      style={{
                        fontSize: 11,
                        fontWeight: 600,
                        padding: '2px 8px',
                        borderRadius: 4,
                        background: priorityColors[criterion.priority].bg,
                        color: priorityColors[criterion.priority].color,
                      }}
                    >
                      {criterion.priority}
                    </span>
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <span style={{ fontSize: 12, color: '#6b7280' }}>
                      {statusLabels[criterion.status]}
                    </span>
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <div style={{ display: 'flex', gap: 6 }}>
                      {criterion.status !== 'confirmed' && onConfirm && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            onConfirm(criterion.id)
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
                            onDelete(criterion.id)
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
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
