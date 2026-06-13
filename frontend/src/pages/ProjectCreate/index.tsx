import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router'
import { useTemplateStore } from '../../stores/templateStore'
import { fetchApplications } from '../../services/project'
import { createProject } from '../../services/project'
import type { ApplicationItem } from '../../services/project'
import TemplateSelector from './components/TemplateSelector'
import StageTimeline from '../../components/StageTimeline'
import TemplateDeviationModal from '../../components/TemplateDeviationModal'
import TemplatePreviewModal from './components/TemplatePreviewModal'
import api from '../../services/api'

interface SkillOption {
  skill_id: string
  skill_name: string
}

export default function ProjectCreate() {
  const navigate = useNavigate()
  const { stages, selectedTemplateId, templates } = useTemplateStore()

  const [apps, setApps] = useState<ApplicationItem[]>([])
  const [selectedAppId, setSelectedAppId] = useState('')
  const [projectName, setProjectName] = useState('')
  const [projectDesc, setProjectDesc] = useState('')
  const [showDeviation, setShowDeviation] = useState(false)
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const [previewTemplateId, setPreviewTemplateId] = useState<string | null>(null)
  const [skills, setSkills] = useState<SkillOption[]>([])

  useEffect(() => {
    fetchApplications()
      .then((res) => {
        setApps(res.data)
        if (res.data.length > 0) {
          setSelectedAppId(res.data[0].application_id)
        }
      })
      .catch(() => setApps([]))

    api
      .get<{ data: SkillOption[]; total_count: number }>('/v1/skills')
      .then((res) => setSkills(res.data.data))
      .catch(() => setSkills([]))
  }, [])

  const skillMap = useMemo(() => {
    const map: Record<string, string> = {}
    for (const s of skills) map[s.skill_id] = s.skill_name
    return map
  }, [skills])

  const previewTemplate = useMemo(
    () => templates.find((t) => t.template_id === previewTemplateId),
    [templates, previewTemplateId],
  )

  const handleCreate = async () => {
    if (!selectedAppId || !projectName.trim() || !selectedTemplateId) return
    setCreating(true)
    setCreateError(null)
    try {
      await createProject(selectedAppId, {
        project_name: projectName.trim(),
        project_description: projectDesc.trim() || null,
        template_level: selectedTemplateId,
      })
      navigate(`/projects`)
    } catch (e: unknown) {
      setCreateError(e instanceof Error ? e.message : '创建失败')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div style={{ maxWidth: 900 }}>
      <h1 style={{ margin: '0 0 24px 0' }}>创建项目</h1>

      {createError && (
        <div style={{ color: '#ef4444', marginBottom: 16, padding: 12, background: '#fef2f2', borderRadius: 6 }}>
          错误: {createError}
        </div>
      )}

      {/* Step 1: Select Application */}
      <section style={{ marginBottom: 32 }}>
        <h2 style={{ margin: '0 0 16px 0', fontSize: 18 }}>选择所属应用</h2>
        {apps.length === 0 ? (
          <div style={{ color: '#6b7280', padding: 16, background: '#f9fafb', borderRadius: 6 }}>
            暂无应用，请先在 <strong>Application 治理</strong> 中创建应用
          </div>
        ) : (
          <select
            value={selectedAppId}
            onChange={(e) => setSelectedAppId(e.target.value)}
            style={{ padding: 10, border: '1px solid #e5e7eb', borderRadius: 6, minWidth: 280, fontSize: 14 }}
          >
            {apps.map((app) => (
              <option key={app.application_id} value={app.application_id}>
                {app.application_name}
              </option>
            ))}
          </select>
        )}
      </section>

      {/* Step 2: Project Info */}
      <section style={{ marginBottom: 32 }}>
        <h2 style={{ margin: '0 0 16px 0', fontSize: 18 }}>项目信息</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <input
            type="text"
            placeholder="项目名称 *"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            style={{ padding: 10, border: '1px solid #e5e7eb', borderRadius: 6, fontSize: 14 }}
          />
          <textarea
            placeholder="项目描述（可选）"
            value={projectDesc}
            onChange={(e) => setProjectDesc(e.target.value)}
            rows={3}
            style={{ padding: 10, border: '1px solid #e5e7eb', borderRadius: 6, fontSize: 14, resize: 'vertical' }}
          />
        </div>
      </section>

      {/* Step 3: Template Selection */}
      <section style={{ marginBottom: 32 }}>
        <TemplateSelector
          onSelect={(id) => {
            console.log('Selected template:', id)
          }}
          onPreview={(id) => setPreviewTemplateId(id)}
        />
      </section>

      {/* Step 4: Stage Preview */}
      {selectedTemplateId && stages.length > 0 && (
        <section
          style={{
            marginBottom: 32,
            border: '1px solid #e5e7eb',
            borderRadius: 8,
            padding: '16px 24px',
            background: '#fafafa',
          }}
        >
          <StageTimeline stages={stages} />

          <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
            <button
              onClick={() => setShowDeviation(true)}
              style={{
                padding: '8px 16px',
                borderRadius: 6,
                border: '1px solid #e5e7eb',
                background: '#fff',
                cursor: 'pointer',
              }}
            >
              预览模板切换影响
            </button>
          </div>
        </section>
      )}

      {/* Step 5: Action buttons */}
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
        <button
          onClick={() => navigate('/projects')}
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
          disabled={!selectedAppId || !projectName.trim() || !selectedTemplateId || creating}
          onClick={handleCreate}
          style={{
            padding: '8px 16px',
            borderRadius: 6,
            border: 'none',
            background: selectedAppId && projectName.trim() && selectedTemplateId ? '#3b82f6' : '#d1d5db',
            color: '#fff',
            cursor: selectedAppId && projectName.trim() && selectedTemplateId ? 'pointer' : 'not-allowed',
          }}
        >
          {creating ? '创建中...' : '确认创建'}
        </button>
      </div>

      {showDeviation && selectedTemplateId && (
        <TemplateDeviationModal
          projectId="demo-project-001"
          newTemplateId={selectedTemplateId}
          newTemplateName={
            useTemplateStore.getState().templates.find(
              (t) => t.template_id === selectedTemplateId,
            )?.template_name ?? selectedTemplateId
          }
          onClose={() => setShowDeviation(false)}
          onConfirmed={() => {
            setShowDeviation(false)
            alert('模板切换已确认')
          }}
        />
      )}

      {/* Template preview modal */}
      {previewTemplateId && previewTemplate && (
        <TemplatePreviewModal
          templateId={previewTemplateId}
          templateName={previewTemplate.template_name}
          skillMap={skillMap}
          onClose={() => setPreviewTemplateId(null)}
          onUse={() => {
            useTemplateStore.getState().selectTemplate(previewTemplateId)
            setPreviewTemplateId(null)
          }}
        />
      )}
    </div>
  )
}
