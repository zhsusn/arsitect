import { useEffect } from 'react'
import { useAppStore } from '../stores/appStore'

export function GlobalToast() {
  const { error, clearError } = useAppStore()

  useEffect(() => {
    if (error) {
      const timer = setTimeout(clearError, 5000)
      return () => clearTimeout(timer)
    }
  }, [error, clearError])

  if (!error) return null

  return (
    <div
      style={{
        position: 'fixed',
        top: 16,
        right: 16,
        padding: '12px 16px',
        backgroundColor: '#ef4444',
        color: '#fff',
        borderRadius: 8,
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
        zIndex: 9999,
        maxWidth: 400,
      }}
      role="alert"
    >
      <div style={{ fontWeight: 600, marginBottom: 4 }}>错误</div>
      <div style={{ fontSize: 14 }}>{error}</div>
      <button
        onClick={clearError}
        style={{
          position: 'absolute',
          top: 8,
          right: 8,
          background: 'none',
          border: 'none',
          color: '#fff',
          cursor: 'pointer',
          fontSize: 16,
        }}
        aria-label="关闭"
      >
        ×
      </button>
    </div>
  )
}
