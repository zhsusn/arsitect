import { useState, useRef, useEffect } from 'react'
import type { Project } from '../../../services/project'

const riskColors: Record<string, { bg: string; text: string; border: string }> = {
  None: { bg: '#f9fafb', text: '#6b7280', border: '#e5e7eb' },
  Low: { bg: '#f0fdf4', text: '#15803d', border: '#bbf7d0' },
  Medium: { bg: '#fefce8', text: '#a16207', border: '#fde047' },
  High: { bg: '#fef2f2', text: '#b91c1c', border: '#fecaca' },
}

const statusColors: Record<string, string> = {
  Draft: '#6b7280',
  Active: '#2563eb',
  Archived: '#6b7280',
  Cancelled: '#ef4444',
}

interface ProjectCardProps {
  project: Project
  onActivate?: (id: string) => void
  onArchive?: (id: string) => void
  onCancel?: (id: string) => void
  onEnter?: (id: string) => void
  onViewDetail?: (id: string) => void
  onEdit?: (id: string) => void
  onSizeEstimate?: (id: string) => void
  onSelect?: (id: string) => void
  onAdjustStage?: (id: string) => void
}

export default function ProjectCard({
  project,
  onActivate,
  onArchive,
  onCancel,
  onEnter,
  onViewDetail,
  onEdit,
  onSizeEstimate,
  onSelect,
  onAdjustStage,
}: ProjectCardProps) {
  const risk = riskColors[project.risk_level] || riskColors.None
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  return (
    <div
      style={{
        border: `1px solid ${risk.border}`,
        borderRadius: 8,
        padding: 16,
        background: risk.bg,
        marginBottom: 12,
        position: 'relative',
        cursor: onSelect ? 'pointer' : 'default',
      }}
      onClick={() => onSelect?.(project.project_id)}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: 8,
        }}
      >
        <div>
          <h3 style={{ margin: '0 0 4px 0', fontSize: 16 }}>{project.project_name}</h3>
          <p
            style={{
              margin: 0,
              fontSize: 13,
              color: '#6b7280',
              lineHeight: 1.4,
            }}
          >
            {project.project_description || '无描述'}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
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
            {project.risk_level} 风险
          </span>
          {/* More actions menu */}
          <div ref={menuRef} style={{ position: 'relative' }}>
            <button
              onClick={(e) => {
                e.stopPropagation()
                setMenuOpen(!menuOpen)
              }}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                fontSize: 16,
                color: '#6b7280',
                padding: '2px 6px',
                borderRadius: 4,
              }}
            >
              ⋮
            </button>
            {menuOpen && (
              <div
                style={{
                  position: 'absolute',
                  top: '100%',
                  right: 0,
                  marginTop: 4,
                  background: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: 6,
                  boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)',
                  zIndex: 100,
                  minWidth: 120,
                  overflow: 'hidden',
                }}
              >
                <MenuItem onClick={() => { onViewDetail?.(project.project_id); setMenuOpen(false) }}>
                  查看详情
                </MenuItem>
                <MenuItem onClick={() => { onEdit?.(project.project_id); setMenuOpen(false) }}>
                  编辑信息
                </MenuItem>
                <MenuItem onClick={() => { onSizeEstimate?.(project.project_id); setMenuOpen(false) }}>
                  规模评估
                </MenuItem>
                {(project.project_status === 'Draft' || project.project_status === 'Active') && onArchive && (
                  <MenuItem
                    onClick={() => { onArchive(project.project_id); setMenuOpen(false) }}
                    danger
                  >
                    归档
                  </MenuItem>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <div
        style={{
          display: 'flex',
          gap: 16,
          fontSize: 12,
          color: '#6b7280',
          marginBottom: 12,
        }}
      >
        <span>模板: {project.template_level}</span>
        <span>进度: {project.progress_percent}%</span>
        <span>当前阶段: {project.current_stage || '-'}</span>
      </div>

      {/* Progress bar */}
      <div
        style={{
          width: '100%',
          height: 6,
          background: '#e5e7eb',
          borderRadius: 3,
          marginBottom: 12,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${project.progress_percent}%`,
            height: '100%',
            background: '#3b82f6',
            borderRadius: 3,
            transition: 'width 0.3s',
          }}
        />
      </div>

      {/* Action buttons */}
      <div style={{ display: 'flex', gap: 8 }}>
        {(project.project_status === 'Active' || project.project_status === 'Archived') &&
          onEnter && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onEnter(project.project_id)
              }}
              style={{
                padding: '4px 10px',
                fontSize: 12,
                borderRadius: 4,
                border: '1px solid #10b981',
                background: '#fff',
                color: '#10b981',
                cursor: 'pointer',
              }}
            >
              进入画布
            </button>
          )}
        {project.project_status === 'Draft' && onActivate && (
          <button
            onClick={() => onActivate(project.project_id)}
            style={{
              padding: '4px 10px',
              fontSize: 12,
              borderRadius: 4,
              border: '1px solid #3b82f6',
              background: '#fff',
              color: '#3b82f6',
              cursor: 'pointer',
            }}
          >
            立项
          </button>
        )}
        {(project.project_status === 'Draft' || project.project_status === 'Active') &&
          onArchive && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onArchive(project.project_id)
              }}
              style={{
                padding: '4px 10px',
                fontSize: 12,
                borderRadius: 4,
                border: '1px solid #6b7280',
                background: '#fff',
                color: '#6b7280',
                cursor: 'pointer',
              }}
            >
              归档
            </button>
          )}
        {project.project_status !== 'Cancelled' && onCancel && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              onCancel(project.project_id)
            }}
            style={{
              padding: '4px 10px',
              fontSize: 12,
              borderRadius: 4,
              border: '1px solid #ef4444',
              background: '#fff',
              color: '#ef4444',
              cursor: 'pointer',
            }}
          >
            取消
          </button>
        )}
        {(project.project_status === 'Active' || project.project_status === 'Draft') &&
          onAdjustStage && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onAdjustStage(project.project_id)
              }}
              style={{
                padding: '4px 10px',
                fontSize: 12,
                borderRadius: 4,
                border: '1px solid #f59e0b',
                background: '#fff',
                color: '#d97706',
                cursor: 'pointer',
              }}
            >
              调整阶段
            </button>
          )}
      </div>
    </div>
  )
}

function MenuItem({
  children,
  onClick,
  danger,
}: {
  children: React.ReactNode
  onClick: () => void
  danger?: boolean
}) {
  return (
    <div
      onClick={(e) => {
        e.stopPropagation()
        onClick()
      }}
      style={{
        padding: '8px 12px',
        fontSize: 13,
        cursor: 'pointer',
        color: danger ? '#dc2626' : '#374151',
        whiteSpace: 'nowrap',
      }}
      onMouseEnter={(e) => {
        ;(e.currentTarget as HTMLDivElement).style.background = '#f9fafb'
      }}
      onMouseLeave={(e) => {
        ;(e.currentTarget as HTMLDivElement).style.background = '#fff'
      }}
    >
      {children}
    </div>
  )
}
