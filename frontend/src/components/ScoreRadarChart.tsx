import React from 'react'

interface ScoreRadarChartProps {
  scores: Record<string, number> | number[]
  labels?: string[]
  maxValues?: number[]
  level?: string
  size?: number
}

const DEFAULT_LABELS = ['模块数', '接口数', '页面数', '技术复杂度', '风险等级']
const DEFAULT_MAX_VALUES = [50, 100, 50, 3, 3]

const LEVEL_COLORS: Record<string, string> = {
  Trivial: '#9ca3af',
  Light: '#3b82f6',
  Standard: '#f97316',
  Deep: '#ef4444',
}

export const ScoreRadarChart: React.FC<ScoreRadarChartProps> = ({
  scores,
  labels,
  maxValues,
  level = 'Standard',
  size = 240,
}) => {
  const effectiveLabels = labels ?? DEFAULT_LABELS
  const effectiveMaxValues = maxValues ?? DEFAULT_MAX_VALUES
  const dimensionCount = effectiveLabels.length

  const center = size / 2
  const radius = size * 0.38
  const angleStep = (Math.PI * 2) / dimensionCount

  const getPoint = (index: number, value: number, max: number) => {
    const angle = index * angleStep - Math.PI / 2
    const r = (value / max) * radius
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
    }
  }

  const isArrayScores = Array.isArray(scores)
  const values = isArrayScores
    ? (scores as number[]).slice(0, dimensionCount)
    : effectiveLabels.map((l) => (scores as Record<string, number>)[l] ?? 0)

  const points = values.map((v, i) => getPoint(i, v, effectiveMaxValues[i]))
  const polygonPoints = points.map((p) => `${p.x},${p.y}`).join(' ')

  const gridRings = [0.2, 0.4, 0.6, 0.8, 1.0]
  const color = LEVEL_COLORS[level] || LEVEL_COLORS.Standard

  return (
    <svg width={size} height={size} style={{ display: 'block' }}>
      {/* Background grid rings */}
      {gridRings.map((ratio) => {
        const ringPoints = Array.from({ length: dimensionCount }, (_, i) => {
          const angle = i * angleStep - Math.PI / 2
          const r = radius * ratio
          return `${center + r * Math.cos(angle)},${center + r * Math.sin(angle)}`
        }).join(' ')
        return (
          <polygon
            key={ratio}
            points={ringPoints}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth={1}
          />
        )
      })}
      {/* Axis lines */}
      {Array.from({ length: dimensionCount }, (_, i) => {
        const angle = i * angleStep - Math.PI / 2
        const x = center + radius * Math.cos(angle)
        const y = center + radius * Math.sin(angle)
        return (
          <line
            key={i}
            x1={center}
            y1={center}
            x2={x}
            y2={y}
            stroke="#e5e7eb"
            strokeWidth={1}
          />
        )
      })}
      {/* Data polygon */}
      <polygon
        points={polygonPoints}
        fill={color}
        fillOpacity={0.2}
        stroke={color}
        strokeWidth={2}
      />
      {/* Data points */}
      {points.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r={3} fill={color} />
      ))}
      {/* Labels */}
      {effectiveLabels.map((label, i) => {
        const angle = i * angleStep - Math.PI / 2
        const r = radius + 18
        const x = center + r * Math.cos(angle)
        const y = center + r * Math.sin(angle)
        return (
          <text
            key={label}
            x={x}
            y={y}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize={12}
            fill="#6b7280"
          >
            {label}
          </text>
        )
      })}
    </svg>
  )
}

export default ScoreRadarChart
