import { useEffect, useState } from 'react'
import { useProjectDashboardStore } from '../../../stores/projectDashboardStore'
import type { RiskAlert } from '../../../services/project'

interface RiskAlertPanelProps {
  projectId: string
}

const severityOrder: Record<string, number> = {
  High: 0,
  Medium: 1,
  Low: 2,
}

const severityColors: Record<string, { bg: string; border: string; text: string }> = {
  High: { bg: '#fef2f2', border: '#fecaca', text: '#b91c1c' },
  Medium: { bg: '#fff7ed', border: '#fed7aa', text: '#c2410c' },
  Low: { bg: '#fefce8', border: '#fde047', text: '#a16207' },
}

export default function RiskAlertPanel({ projectId }: RiskAlertPanelProps) {
  const { riskAlerts, fetchRiskAlerts } = useProjectDashboardStore()
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    fetchRiskAlerts(projectId)
  }, [projectId, fetchRiskAlerts])

  const grouped = riskAlerts.reduce<Record<string, RiskAlert[]>>((acc, alert) => {
    if (!acc[alert.severity]) acc[alert.severity] = []
    acc[alert.severity].push(alert)
    return acc
  }, {})

  const sortedSeverities = Object.keys(grouped).sort(
    (a, b) => severityOrder[a] - severityOrder[b],
  )

  const top3 = riskAlerts
    .slice()
    .sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity])
    .slice(0, 3)

  const highestSeverity = sortedSeverities[0] as 'High' | 'Medium' | 'Low' | undefined
  const bannerStyle = highestSeverity
    ? severityColors[highestSeverity]
    : { bg: '#f0fdf4', border: '#bbf7d0', text: '#15803d' }

  if (riskAlerts.length === 0) {
    return (
      <div
        style={{
          padding: '10px 16px',
          background: '#f0fdf4',
          borderRadius: 8,
          border: '1px solid #bbf7d0',
          fontSize: 13,
          color: '#15803d',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <span>✅</span>
        当前项目无风险预警
      </div>
    )
  }

  return (
    <div
      style={{
        border: `1px solid ${bannerStyle.border}`,
        borderRadius: 8,
        overflow: 'hidden',
        background: bannerStyle.bg,
      }}
    >
      <div
        style={{
          padding: '10px 16px',
          cursor: 'pointer',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <span style={{ fontWeight: 600, fontSize: 13, color: bannerStyle.text }}>
            ⚠️ 风险预警 ({riskAlerts.length})
          </span>
          {!expanded &&
            top3.map((alert, idx) => (
              <span
                key={idx}
                style={{
                  fontSize: 12,
                  color: bannerStyle.text,
                  background: 'rgba(255,255,255,0.6)',
                  padding: '2px 8px',
                  borderRadius: 4,
                  maxWidth: 220,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
                title={alert.message}
              >
                {alert.message}
              </span>
            ))}
        </div>
        <span style={{ fontSize: 12, color: bannerStyle.text, fontWeight: 500 }}>
          {expanded ? '收起' : '查看全部'}
        </span>
      </div>

      {expanded && (
        <div style={{ padding: 12, background: '#fff' }}>
          {sortedSeverities.map((sev) => (
            <div key={sev} style={{ marginBottom: 12 }}>
              <div
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  color: severityColors[sev]?.text || '#6b7280',
                  marginBottom: 6,
                  textTransform: 'uppercase',
                }}
              >
                {sev} ({grouped[sev].length})
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {grouped[sev].map((alert, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '8px 12px',
                      borderRadius: 6,
                      background: '#fafafa',
                      borderLeft: `3px solid ${severityColors[sev]?.text || '#6b7280'}`,
                      fontSize: 13,
                    }}
                  >
                    <div style={{ fontWeight: 500, marginBottom: 2 }}>{alert.alert_type}</div>
                    <div style={{ color: '#6b7280' }}>{alert.message}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
