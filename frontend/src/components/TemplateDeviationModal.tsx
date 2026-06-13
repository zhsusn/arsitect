import { useEffect } from 'react'
import { useTemplateStore } from '../stores/templateStore'

interface TemplateDeviationModalProps {
  projectId: string
  newTemplateId: string
  newTemplateName: string
  onClose: () => void
  onConfirmed: () => void
}

export default function TemplateDeviationModal({
  projectId,
  newTemplateId,
  newTemplateName,
  onClose,
  onConfirmed,
}: TemplateDeviationModalProps) {
  const { impact, impactLoading, error, previewImpact, confirmSwitch, clearImpact } =
    useTemplateStore()

  useEffect(() => {
    previewImpact(projectId, newTemplateId)
    return () => clearImpact()
  }, [projectId, newTemplateId, previewImpact, clearImpact])

  if (impactLoading) {
    return (
      <ModalOverlay onClose={onClose}>
        <div style={{ padding: 40, textAlign: 'center' }}>计算影响范围...</div>
      </ModalOverlay>
    )
  }

  if (error) {
    return (
      <ModalOverlay onClose={onClose}>
        <div style={{ padding: 24, color: '#ef4444' }}>错误: {error}</div>
      </ModalOverlay>
    )
  }

  if (!impact) return null

  const total = impact.frozen_count + impact.removed_count + impact.added_count + impact.retained_count

  return (
    <ModalOverlay onClose={onClose}>
      <div style={{ padding: 24, maxWidth: 480 }}>
        <h2 style={{ margin: '0 0 8px 0', fontSize: 18 }}>模板切换确认</h2>
        <p style={{ margin: '0 0 16px 0', fontSize: 14, color: '#6b7280' }}>
          即将切换至 <strong>{newTemplateName}</strong>，影响范围预览如下：
        </p>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: 12,
            marginBottom: 20,
          }}
        >
          <ImpactCard
            label="已执行（冻结）"
            count={impact.frozen_count}
            color="#f59e0b"
            bg="#fffbeb"
          />
          <ImpactCard
            label="将被移除"
            count={impact.removed_count}
            color="#ef4444"
            bg="#fef2f2"
          />
          <ImpactCard
            label="新增"
            count={impact.added_count}
            color="#22c55e"
            bg="#f0fdf4"
          />
          <ImpactCard
            label="保持不变"
            count={impact.retained_count}
            color="#6b7280"
            bg="#f9fafb"
          />
        </div>

        <div
          style={{
            fontSize: 13,
            color: '#6b7280',
            marginBottom: 20,
            padding: 12,
            background: '#f9fafb',
            borderRadius: 6,
          }}
        >
          总计 {total} 个 Stage 受影响。
          {impact.frozen_count > 0 && ' 已执行的 Stage 将被冻结，不可修改。'}
          {impact.removed_count > 0 && ' 未执行且不在新模板中的 Stage 将被移除。'}
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <button
            onClick={onClose}
            style={{
              padding: '8px 16px',
              borderRadius: 6,
              border: '1px solid #e5e7eb',
              background: '#fff',
              cursor: 'pointer',
            }}
          >
            取消
          </button>
          <button
            onClick={async () => {
              const ok = await confirmSwitch(projectId, newTemplateId)
              if (ok) onConfirmed()
            }}
            disabled={impactLoading}
            style={{
              padding: '8px 16px',
              borderRadius: 6,
              border: 'none',
              background: '#3b82f6',
              color: '#fff',
              cursor: 'pointer',
              opacity: impactLoading ? 0.6 : 1,
            }}
          >
            {impactLoading ? '处理中...' : '确认切换'}
          </button>
        </div>
      </div>
    </ModalOverlay>
  )
}

function ModalOverlay({
  children,
  onClose,
}: {
  children: React.ReactNode
  onClose: () => void
}) {
  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.4)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        style={{
          background: '#fff',
          borderRadius: 8,
          boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)',
          minWidth: 360,
        }}
      >
        {children}
      </div>
    </div>
  )
}

function ImpactCard({
  label,
  count,
  color,
  bg,
}: {
  label: string
  count: number
  color: string
  bg: string
}) {
  return (
    <div
      style={{
        padding: 14,
        borderRadius: 8,
        background: bg,
        textAlign: 'center',
      }}
    >
      <div style={{ fontSize: 24, fontWeight: 700, color }}>{count}</div>
      <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>{label}</div>
    </div>
  )
}

