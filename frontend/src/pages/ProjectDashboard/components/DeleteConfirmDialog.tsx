import { useState } from 'react'

interface DeleteConfirmDialogProps {
  projectName: string
  onConfirm: () => void
  onCancel: () => void
}

export default function DeleteConfirmDialog({ projectName, onConfirm, onCancel }: DeleteConfirmDialogProps) {
  const [input, setInput] = useState('')
  const confirmed = input.trim() === projectName.trim()

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.4)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1300,
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onCancel()
      }}
    >
      <div
        style={{
          background: '#fff',
          borderRadius: 8,
          boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)',
          width: 440,
          maxWidth: '90%',
          padding: 24,
        }}
      >
        <h2
          style={{
            margin: '0 0 12px 0',
            fontSize: 18,
            color: '#dc2626',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <span>⚠️</span>
          确认归档项目？
        </h2>
        <p style={{ margin: '0 0 16px 0', fontSize: 14, color: '#374151', lineHeight: 1.6 }}>
          此操作不可撤销。请输入项目名称 <strong style={{ color: '#dc2626' }}>{projectName}</strong> 以确认。
        </p>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={`请输入 "${projectName}"`}
          style={{
            width: '100%',
            padding: 10,
            borderRadius: 6,
            border: '1px solid #d1d5db',
            fontSize: 14,
            boxSizing: 'border-box',
            marginBottom: 20,
          }}
          autoFocus
        />
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <button
            onClick={onCancel}
            style={{
              padding: '8px 16px',
              borderRadius: 6,
              border: '1px solid #e5e7eb',
              background: '#fff',
              cursor: 'pointer',
              fontSize: 14,
            }}
          >
            取消
          </button>
          <button
            onClick={onConfirm}
            disabled={!confirmed}
            style={{
              padding: '8px 16px',
              borderRadius: 6,
              border: 'none',
              background: confirmed ? '#dc2626' : '#d1d5db',
              color: '#fff',
              cursor: confirmed ? 'pointer' : 'not-allowed',
              fontSize: 14,
            }}
          >
            确认归档
          </button>
        </div>
      </div>
    </div>
  )
}
