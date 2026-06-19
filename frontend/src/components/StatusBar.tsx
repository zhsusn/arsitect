interface StatusBarProps {
  projectName: string
  stageName: string
  artifactName: string
  version: string
  gateStatus?: 'pending' | 'approved' | 'rejected' | null
  projectStatus?: 'draft' | 'active' | 'archived'
}

export default function StatusBar({ projectName, stageName, artifactName, version, gateStatus, projectStatus }: StatusBarProps) {
  const gateIndicator = gateStatus === 'pending' ? '🔒 待审批' : gateStatus === 'approved' ? '✅ 已审批' : gateStatus === 'rejected' ? '❌ 已驳回' : null
  const statusIndicator = projectStatus === 'draft' ? '草稿' : projectStatus === 'active' ? '执行中' : '已归档'

  return (
    <div
      style={{
        height: 32,
        borderTop: '1px solid #e5e7eb',
        background: '#f9fafb',
        display: 'flex',
        alignItems: 'center',
        padding: '0 16px',
        gap: 12,
        fontSize: 12,
        color: '#6b7280',
      }}
    >
      <span>项目: {projectName || '-'}</span>
      <span style={{ color: '#d1d5db' }}>|</span>
      <span>状态: {statusIndicator}</span>
      <span style={{ color: '#d1d5db' }}>|</span>
      <span>阶段: {stageName || '-'}</span>
      <span style={{ color: '#d1d5db' }}>|</span>
      <span>产物: {artifactName || '-'}</span>
      <span style={{ color: '#d1d5db' }}>|</span>
      <span>版本: {version || '-'}</span>
      {gateIndicator && (
        <>
          <span style={{ color: '#d1d5db' }}>|</span>
          <span style={{ fontWeight: 600, color: gateStatus === 'rejected' ? '#dc2626' : gateStatus === 'approved' ? '#16a34a' : '#f59e0b' }}>
            {gateIndicator}
          </span>
        </>
      )}
    </div>
  )
}
