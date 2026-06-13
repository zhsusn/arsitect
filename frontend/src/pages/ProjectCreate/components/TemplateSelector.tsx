import { useEffect } from 'react'
import { useTemplateStore } from '../../../stores/templateStore'

const complexityColors: Record<string, string> = {
  low: '#22c55e',
  medium: '#f59e0b',
  high: '#ef4444',
}

const complexityLabels: Record<string, string> = {
  low: '低复杂度',
  medium: '中复杂度',
  high: '高复杂度',
}

const templateBadges: Record<string, { color: string; bg: string }> = {
  Trivial: { color: '#15803d', bg: '#dcfce7' },
  Light: { color: '#0369a1', bg: '#e0f2fe' },
  Standard: { color: '#7c3aed', bg: '#ede9fe' },
  Deep: { color: '#be123c', bg: '#ffe4e6' },
}

interface TemplateSelectorProps {
  onSelect?: (templateId: string) => void
  onPreview?: (templateId: string) => void
}

export default function TemplateSelector({ onSelect, onPreview }: TemplateSelectorProps) {
  const { templates, selectedTemplateId, loading, error, fetchTemplates } =
    useTemplateStore()

  useEffect(() => {
    fetchTemplates()
  }, [fetchTemplates])

  if (loading) return <div style={{ padding: 24 }}>加载模板...</div>
  if (error) return <div style={{ padding: 24, color: '#ef4444' }}>错误: {error}</div>

  return (
    <div>
      <h2 style={{ margin: '0 0 16px 0', fontSize: 18 }}>选择项目模板</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}>
        {templates.map((tpl) => {
          const selected = selectedTemplateId === tpl.template_id
          const badge = templateBadges[tpl.template_id] || { color: '#374151', bg: '#f3f4f6' }
          return (
            <div
              key={tpl.template_id}
              style={{
                border: `2px solid ${selected ? '#3b82f6' : '#e5e7eb'}`,
                borderRadius: 8,
                padding: 16,
                cursor: 'pointer',
                background: selected ? '#eff6ff' : '#fff',
                transition: 'all 0.2s',
                position: 'relative',
              }}
              role="button"
              tabIndex={0}
              onClick={() => {
                useTemplateStore.getState().selectTemplate(tpl.template_id)
                onSelect?.(tpl.template_id)
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  useTemplateStore.getState().selectTemplate(tpl.template_id)
                  onSelect?.(tpl.template_id)
                }
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <span
                  style={{
                    fontSize: 12,
                    fontWeight: 600,
                    padding: '2px 8px',
                    borderRadius: 4,
                    color: badge.color,
                    background: badge.bg,
                  }}
                >
                  {tpl.template_id}
                </span>
                <span
                  style={{
                    fontSize: 11,
                    color: complexityColors[tpl.applicable_complexity] || '#6b7280',
                    fontWeight: 500,
                  }}
                >
                  {complexityLabels[tpl.applicable_complexity] || tpl.applicable_complexity}
                </span>
              </div>
              <h3 style={{ margin: '0 0 8px 0', fontSize: 16 }}>{tpl.template_name}</h3>
              <p
                style={{
                  margin: 0,
                  fontSize: 13,
                  color: '#6b7280',
                  lineHeight: 1.5,
                  minHeight: 40,
                }}
              >
                {tpl.description}
              </p>
              <div
                style={{
                  marginTop: 12,
                  display: 'flex',
                  gap: 12,
                  fontSize: 12,
                  color: '#6b7280',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div style={{ display: 'flex', gap: 12 }}>
                  <span>{tpl.stage_count} 个阶段</span>
                  <span>{tpl.estimated_skill_count} 个 Skill</span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onPreview?.(tpl.template_id)
                  }}
                  className="text-xs px-2 py-1 rounded border border-gray-200 bg-white hover:bg-gray-50 text-gray-600"
                >
                  预览
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
