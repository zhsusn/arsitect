import { BarChart3, Clock, Layers, Database, Monitor, AlertTriangle } from 'lucide-react'

export interface SizeEstimate {
  moduleCount: number
  interfaceCount: number
  pageCount: number
  entityCount: number
  complexity: 'low' | 'medium' | 'high'
  riskLevel: 'low' | 'medium' | 'high'
  recommendedPath: 'lite' | 'standard' | 'complex'
  estimatedWeeks: number
  estimatedPersonMonths: number
  breakdown?: Array<{
    moduleName: string
    estimatedHours: number
  }>
}

const complexityLabels: Record<string, string> = {
  low: '低',
  medium: '中',
  high: '高',
}

const riskLabels: Record<string, string> = {
  low: '低',
  medium: '中',
  high: '高',
}

const pathLabels: Record<string, string> = {
  lite: 'Lite',
  standard: 'Standard',
  complex: 'Complex',
}

const complexityColors: Record<string, string> = {
  low: '#16a34a',
  medium: '#ca8a04',
  high: '#dc2626',
}

const riskColors: Record<string, string> = {
  low: '#16a34a',
  medium: '#ca8a04',
  high: '#dc2626',
}

interface SizeEstimateCardProps {
  estimate?: SizeEstimate
  onExpand?: () => void
}

export default function SizeEstimateCard({ estimate, onExpand }: SizeEstimateCardProps) {
  if (!estimate) {
    return (
      <div
        style={{
          padding: '12px 16px',
          background: '#f9fafb',
          borderTop: '1px solid #e5e7eb',
          fontSize: 13,
          color: '#6b7280',
          textAlign: 'center',
        }}
      >
        暂无规模初估数据
      </div>
    )
  }

  const stats = [
    { icon: Layers, label: '模块数', value: estimate.moduleCount },
    { icon: Database, label: '接口数', value: estimate.interfaceCount },
    { icon: Monitor, label: '页面数', value: estimate.pageCount },
    { icon: BarChart3, label: '实体数', value: estimate.entityCount },
  ]

  return (
    <div
      style={{
        padding: '12px 16px',
        background: '#f9fafb',
        borderTop: '1px solid #e5e7eb',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 10,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <BarChart3 size={14} color="#2563eb" />
          <span style={{ fontSize: 13, fontWeight: 600, color: '#111827' }}>
            规模初估参考
          </span>
        </div>
        {onExpand && (
          <button
            onClick={onExpand}
            style={{
              fontSize: 12,
              color: '#2563eb',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            查看详情 →
          </button>
        )}
      </div>

      {/* 核心指标 */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 8,
          marginBottom: 10,
        }}
      >
        {stats.map((stat) => (
          <div
            key={stat.label}
            style={{
              textAlign: 'center',
              padding: '8px 4px',
              background: '#fff',
              borderRadius: 6,
              border: '1px solid #e5e7eb',
            }}
          >
            <div style={{ fontSize: 16, fontWeight: 700, color: '#111827' }}>
              {stat.value}
            </div>
            <div
              style={{
                fontSize: 11,
                color: '#6b7280',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 3,
                marginTop: 2,
              }}
            >
              <stat.icon size={10} />
              {stat.label}
            </div>
          </div>
        ))}
      </div>

      {/* 评估标签 */}
      <div
        style={{
          display: 'flex',
          gap: 8,
          alignItems: 'center',
          flexWrap: 'wrap',
        }}
      >
        <span style={{ fontSize: 12, color: '#6b7280' }}>复杂度:</span>
        <span
          style={{
            fontSize: 12,
            fontWeight: 600,
            color: complexityColors[estimate.complexity],
            padding: '2px 8px',
            background: `${complexityColors[estimate.complexity]}15`,
            borderRadius: 4,
          }}
        >
          {complexityLabels[estimate.complexity]}
        </span>

        <span style={{ fontSize: 12, color: '#6b7280' }}>风险:</span>
        <span
          style={{
            fontSize: 12,
            fontWeight: 600,
            color: riskColors[estimate.riskLevel],
            padding: '2px 8px',
            background: `${riskColors[estimate.riskLevel]}15`,
            borderRadius: 4,
          }}
        >
          {riskLabels[estimate.riskLevel]}
        </span>

        <span style={{ fontSize: 12, color: '#6b7280' }}>推荐:</span>
        <span
          style={{
            fontSize: 12,
            fontWeight: 600,
            color: '#2563eb',
            padding: '2px 8px',
            background: '#eff6ff',
            borderRadius: 4,
          }}
        >
          {pathLabels[estimate.recommendedPath]}
        </span>

        <div
          style={{
            marginLeft: 'auto',
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            fontSize: 12,
            color: '#6b7280',
          }}
        >
          <Clock size={12} />
          <span>约 {estimate.estimatedWeeks} 周 / {estimate.estimatedPersonMonths} 人月</span>
        </div>
      </div>

      {/* 风险警告 */}
      {estimate.riskLevel === 'high' && (
        <div
          style={{
            marginTop: 8,
            padding: '8px 10px',
            background: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: 6,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            fontSize: 12,
            color: '#dc2626',
          }}
        >
          <AlertTriangle size={14} />
          <span>高风险项目，建议增加架构评审与缓冲时间</span>
        </div>
      )}
    </div>
  )
}
