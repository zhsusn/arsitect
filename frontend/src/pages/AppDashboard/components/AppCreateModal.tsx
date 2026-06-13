import { useState } from 'react'
import { useAppDashboardStore } from '../../../stores/appDashboardStore'

interface AppCreateModalProps {
  onClose: () => void
}

export function AppCreateModal({ onClose }: AppCreateModalProps) {
  const [name, setName] = useState('')
  const [path, setPath] = useState('')
  const [desc, setDesc] = useState('')
  const [error, setError] = useState('')
  const createApplication = useAppDashboardStore((s) => s.createApplication)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await createApplication({
        application_id: crypto.randomUUID(),
        application_name: name,
        local_path: path,
        description: desc || null,
        workspace_id: 'default',
      })
      onClose()
    } catch (err: unknown) {
      const detail =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined
      setError(detail || '创建失败')
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
          width: 400,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 style={{ marginTop: 0 }}>新建 Application</h2>
        {error && (
          <div style={{ color: '#ef4444', marginBottom: 12 }}>{error}</div>
        )}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', fontSize: 14, marginBottom: 4 }}>
              名称
            </label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              style={{ width: '100%', padding: 8, boxSizing: 'border-box' }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', fontSize: 14, marginBottom: 4 }}>
              本地路径
            </label>
            <input
              value={path}
              onChange={(e) => setPath(e.target.value)}
              required
              placeholder="如: D:\\projects\\my-app"
              style={{ width: '100%', padding: 8, boxSizing: 'border-box' }}
            />
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: 14, marginBottom: 4 }}>
              描述
            </label>
            <textarea
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              rows={3}
              style={{ width: '100%', padding: 8, boxSizing: 'border-box' }}
            />
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
            <button type="button" onClick={onClose}>
              取消
            </button>
            <button type="submit">创建</button>
          </div>
        </form>
      </div>
    </div>
  )
}
