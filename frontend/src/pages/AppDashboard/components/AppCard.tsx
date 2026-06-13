export interface AppCardProps {
  application_name: string
  local_path: string
  path_accessible: boolean
  description?: string | null
}

export function AppCard({
  application_name,
  local_path,
  path_accessible,
  description,
}: AppCardProps) {
  return (
    <div
      style={{
        border: '1px solid #e5e7eb',
        borderRadius: 8,
        padding: 16,
        marginBottom: 12,
        backgroundColor: '#fff',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <h3 style={{ margin: 0, fontSize: 16 }}>{application_name}</h3>
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            backgroundColor: path_accessible ? '#22c55e' : '#ef4444',
          }}
          title={path_accessible ? 'Accessible' : 'Inaccessible'}
        />
      </div>
      <p style={{ margin: '4px 0', fontSize: 12, color: '#6b7280' }}>
        {local_path}
      </p>
      {description && (
        <p style={{ margin: '4px 0', fontSize: 13, color: '#374151' }}>
          {description}
        </p>
      )}
    </div>
  )
}
