import { useState } from 'react'
import { useAppDashboardStore } from '../../../stores/appDashboardStore'

interface AppDeleteConfirmProps {
  appId: string
  appName: string
  onClose: () => void
}

export function AppDeleteConfirm({ appId, appName, onClose }: AppDeleteConfirmProps) {
  const deleteApplication = useAppDashboardStore((s) => s.deleteApplication)
  const [error, setError] = useState('')

  const handleConfirm = async () => {
    setError('')
    try {
      await deleteApplication(appId)
      onClose()
    } catch (err: unknown) {
      const detail =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined
      setError(detail || '删除失败')
    }
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0,0,0,0.4)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 100,
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: '#fff',
          padding: 24,
          borderRadius: 12,
          width: 360,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 style={{ marginTop: 0 }}>确认删除</h3>
        <p>
          确定要删除 <strong>{appName}</strong> 吗？此操作不可恢复。
        </p>
        {error && <div style={{ color: '#ef4444', marginBottom: 12 }}>{error}</div>}
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <button type="button" onClick={onClose}>
            取消
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            style={{ backgroundColor: '#ef4444', color: '#fff' }}
          >
            删除
          </button>
        </div>
      </div>
    </div>
  )
}
