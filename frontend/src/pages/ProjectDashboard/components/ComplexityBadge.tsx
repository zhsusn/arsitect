import React from 'react'

interface ComplexityBadgeProps {
  level: string
}

const LEVEL_STYLES: Record<string, { bg: string; color: string; label: string }> = {
  Trivial: { bg: '#f3f4f6', color: '#6b7280', label: '轻量' },
  Light: { bg: '#eff6ff', color: '#3b82f6', label: '轻量' },
  Standard: { bg: '#fff7ed', color: '#f97316', label: '标准' },
  Deep: { bg: '#fef2f2', color: '#ef4444', label: '深度' },
}

export const ComplexityBadge: React.FC<ComplexityBadgeProps> = ({ level }) => {
  const style = LEVEL_STYLES[level] || LEVEL_STYLES.Standard

  return (
    <span
      style={{
        display: 'inline-block',
        padding: '2px 10px',
        borderRadius: 999,
        fontSize: 12,
        fontWeight: 500,
        backgroundColor: style.bg,
        color: style.color,
        border: `1px solid ${style.color}`,
      }}
    >
      {style.label}
    </span>
  )
}

export default ComplexityBadge
