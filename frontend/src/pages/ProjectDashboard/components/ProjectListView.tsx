import type { Project } from '../../../services/project'

interface ProjectListViewProps {
  projects: Project[]
  onViewDetail: (project: Project) => void
  onEdit: (project: Project) => void
  onArchive: (project: Project) => void
  onActivate: (project: Project) => void
  onCancel: (project: Project) => void
  onEnter: (project: Project) => void
}

const statusColors: Record<string, string> = {
  Draft: '#6b7280',
  Active: '#2563eb',
  Archived: '#6b7280',
  Cancelled: '#ef4444',
}

const riskColors: Record<string, { bg: string; text: string }> = {
  None: { bg: '#f9fafb', text: '#6b7280' },
  Low: { bg: '#f0fdf4', text: '#15803d' },
  Medium: { bg: '#fefce8', text: '#a16207' },
  High: { bg: '#fef2f2', text: '#b91c1c' },
}

export default function ProjectListView({
  projects,
  onViewDetail,
  onEdit,
  onArchive,
  onActivate,
  onCancel,
  onEnter,
}: ProjectListViewProps) {
  if (projects.length === 0) {
    return (
      <div
        style={{
          padding: 40,
          textAlign: 'center',
          color: '#6b7280',
          border: '2px dashed #e5e7eb',
          borderRadius: 8,
        }}
      >
        无匹配结果
      </div>
    )
  }

  return (
    <div
      style={{
        border: '1px solid #e5e7eb',
        borderRadius: 8,
        overflow: 'hidden',
      }}
    >
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <thead>
          <tr style={{ background: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
            <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: '#374151' }}>项目名称</th>
            <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: '#374151' }}>状态</th>
            <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: '#374151' }}>阶段进度</th>
            <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: '#374151' }}>风险等级</th>
            <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: '#374151' }}>创建时间</th>
            <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600, color: '#374151' }}>操作</th>
          </tr>
        </thead>
        <tbody>
          {projects.map((project) => {
            const risk = riskColors[project.risk_level] || riskColors.None
            return (
              <tr
                key={project.project_id}
                style={{ borderBottom: '1px solid #f3f4f6' }}
                onClick={() => onViewDetail(project)}
              >
                <td style={{ padding: '12px 16px' }}>
                  <div style={{ fontWeight: 500, color: '#111827' }}>{project.project_name}</div>
                  {project.project_description && (
                    <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>
                      {project.project_description}
                    </div>
                  )}
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      padding: '2px 8px',
                      borderRadius: 4,
                      background: statusColors[project.project_status] || '#6b7280',
                      color: '#fff',
                    }}
                  >
                    {project.project_status}
                  </span>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div
                      style={{
                        width: 80,
                        height: 6,
                        background: '#e5e7eb',
                        borderRadius: 3,
                        overflow: 'hidden',
                      }}
                    >
                      <div
                        style={{
                          width: `${project.progress_percent}%`,
                          height: '100%',
                          background: '#3b82f6',
                          borderRadius: 3,
                        }}
                      />
                    </div>
                    <span style={{ fontSize: 12, color: '#6b7280' }}>{project.progress_percent}%</span>
                  </div>
                  <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>
                    {project.current_stage || '-'}
                  </div>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      padding: '2px 8px',
                      borderRadius: 4,
                      background: risk.text,
                      color: '#fff',
                    }}
                  >
                    {project.risk_level}
                  </span>
                </td>
                <td style={{ padding: '12px 16px', color: '#6b7280', fontSize: 12 }}>
                  {new Date(project.created_at).toLocaleDateString('zh-CN')}
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <div style={{ display: 'flex', gap: 6 }} onClick={(e) => e.stopPropagation()}>
                    <ActionBtn onClick={() => onViewDetail(project)}>查看</ActionBtn>
                    <ActionBtn onClick={() => onEdit(project)}>编辑</ActionBtn>
                    {project.project_status === 'Draft' && (
                      <ActionBtn onClick={() => onActivate(project)}>立项</ActionBtn>
                    )}
                    {(project.project_status === 'Draft' || project.project_status === 'Active') && (
                      <ActionBtn onClick={() => onArchive(project)}>归档</ActionBtn>
                    )}
                    {project.project_status !== 'Cancelled' && (
                      <ActionBtn onClick={() => onCancel(project)}>取消</ActionBtn>
                    )}
                    {(project.project_status === 'Active' || project.project_status === 'Archived') && (
                      <ActionBtn onClick={() => onEnter(project)}>画布</ActionBtn>
                    )}
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function ActionBtn({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '2px 8px',
        fontSize: 11,
        borderRadius: 4,
        border: '1px solid #e5e7eb',
        background: '#fff',
        color: '#374151',
        cursor: 'pointer',
      }}
    >
      {children}
    </button>
  )
}
