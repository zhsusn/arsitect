import { useState } from 'react'
import { useProjectDashboardStore } from '../../../stores/projectDashboardStore'
import TemplateSelector from '../../ProjectCreate/components/TemplateSelector'
import StageTimeline from '../../../components/StageTimeline'
import { useTemplateStore } from '../../../stores/templateStore'

interface ProjectCreateModalProps {
  appId: string
  onClose: () => void
}

type Step = 1 | 2 | 3 | 4

export default function ProjectCreateModal({ appId, onClose }: ProjectCreateModalProps) {
  const [step, setStep] = useState<Step>(1)
  const [projectName, setProjectName] = useState('')
  const [projectDescription, setProjectDescription] = useState('')
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null)
  const { createProject } = useProjectDashboardStore()
  const { stages } = useTemplateStore()

  const canProceed = () => {
    if (step === 1) return projectName.trim().length > 0
    if (step === 2) return true
    if (step === 3) return selectedTemplateId !== null
    return true
  }

  const handleConfirm = async () => {
    if (!selectedTemplateId) return
    await createProject(appId, {
      project_name: projectName,
      project_description: projectDescription || null,
      template_level: selectedTemplateId,
    })
    onClose()
  }

  const stepTitles = ['基本信息', '应用确认', '选择模板', '确认创建']

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
          width: 640,
          maxHeight: '80vh',
          overflow: 'auto',
          padding: 24,
        }}
      >
        <h2 style={{ margin: '0 0 16px 0', fontSize: 18 }}>创建项目</h2>

        {/* Step indicator */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
          {stepTitles.map((title, idx) => {
            const s = (idx + 1) as Step
            const active = s === step
            const done = s < step
            return (
              <div
                key={title}
                style={{
                  flex: 1,
                  padding: '8px 0',
                  textAlign: 'center',
                  fontSize: 12,
                  borderRadius: 4,
                  background: active ? '#3b82f6' : done ? '#dbeafe' : '#f3f4f6',
                  color: active ? '#fff' : done ? '#1d4ed8' : '#9ca3af',
                  fontWeight: active ? 600 : 400,
                }}
              >
                {idx + 1}. {title}
              </div>
            )
          })}
        </div>

        {/* Step content */}
        {step === 1 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <label style={{ fontSize: 14, fontWeight: 500 }}>
              项目名称 *
              <input
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="输入项目名称"
                style={{
                  width: '100%',
                  padding: 8,
                  marginTop: 4,
                  boxSizing: 'border-box',
                  borderRadius: 4,
                  border: '1px solid #d1d5db',
                }}
              />
            </label>
            <label style={{ fontSize: 14, fontWeight: 500 }}>
              项目描述
              <textarea
                value={projectDescription}
                onChange={(e) => setProjectDescription(e.target.value)}
                placeholder="可选：输入项目描述"
                rows={3}
                style={{
                  width: '100%',
                  padding: 8,
                  marginTop: 4,
                  boxSizing: 'border-box',
                  borderRadius: 4,
                  border: '1px solid #d1d5db',
                  resize: 'vertical',
                }}
              />
            </label>
          </div>
        )}

        {step === 2 && (
          <div>
            <p style={{ fontSize: 14, color: '#374151' }}>
              确认将项目创建在 Application: <strong>{appId}</strong>
            </p>
            <div
              style={{
                marginTop: 12,
                padding: 12,
                background: '#f9fafb',
                borderRadius: 6,
                fontSize: 13,
                color: '#6b7280',
              }}
            >
              <div>项目名称: {projectName}</div>
              <div>描述: {projectDescription || '无'}</div>
            </div>
          </div>
        )}

        {step === 3 && (
          <div>
            <TemplateSelector
              onSelect={(id) => setSelectedTemplateId(id)}
            />
            {selectedTemplateId && stages.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <StageTimeline stages={stages} />
              </div>
            )}
          </div>
        )}

        {step === 4 && (
          <div>
            <p style={{ fontSize: 14, marginBottom: 16 }}>请确认以下信息：</p>
            <div
              style={{
                padding: 16,
                background: '#f9fafb',
                borderRadius: 6,
                fontSize: 14,
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
              }}
            >
              <div>
                <strong>项目名称:</strong> {projectName}
              </div>
              <div>
                <strong>描述:</strong> {projectDescription || '无'}
              </div>
              <div>
                <strong>应用:</strong> {appId}
              </div>
              <div>
                <strong>模板:</strong> {selectedTemplateId}
              </div>
            </div>
          </div>
        )}

        {/* Footer buttons */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            gap: 8,
            marginTop: 24,
          }}
        >
          {step > 1 && (
            <button
              onClick={() => setStep(((step - 1) as unknown) as Step)}
              style={{
                padding: '8px 16px',
                borderRadius: 6,
                border: '1px solid #e5e7eb',
                background: '#fff',
                cursor: 'pointer',
              }}
            >
              上一步
            </button>
          )}
          {step < 4 ? (
            <button
              onClick={() => setStep(((step + 1) as unknown) as Step)}
              disabled={!canProceed()}
              style={{
                padding: '8px 16px',
                borderRadius: 6,
                border: 'none',
                background: canProceed() ? '#3b82f6' : '#d1d5db',
                color: '#fff',
                cursor: canProceed() ? 'pointer' : 'not-allowed',
              }}
            >
              下一步
            </button>
          ) : (
            <button
              onClick={handleConfirm}
              style={{
                padding: '8px 16px',
                borderRadius: 6,
                border: 'none',
                background: '#3b82f6',
                color: '#fff',
                cursor: 'pointer',
              }}
            >
              确认创建
            </button>
          )}
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
        </div>
      </div>
    </div>
  )
}
