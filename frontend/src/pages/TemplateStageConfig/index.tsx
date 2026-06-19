import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  fetchTemplates,
  fetchTemplateDetail,
  updateTemplateExecutionStrategy,
  updateTemplateStage,
  type Template,
  type TemplateStage,
} from '../../services/template'
import api from '../../services/api'
import DeviationConfirmModal from './components/DeviationConfirmModal'
import StageDefinitionPanel from './components/StageDefinitionPanel'
import DeviationLogDrawer from './components/DeviationLogDrawer'
import ScaleMismatchBanner from './components/ScaleMismatchBanner'

interface SkillOption {
  skill_id: string
  skill_name: string
}

const TEMPLATE_LEVELS = ['Trivial', 'Light', 'Standard', 'Deep']

export default function TemplateStageConfig() {
  const [templates, setTemplates] = useState<Template[]>([])
  const [selectedLevel, setSelectedLevel] = useState<string>('Light')
  const [stages, setStages] = useState<TemplateStage[]>([])
  const [skills, setSkills] = useState<SkillOption[]>([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState<Record<string, boolean>>({})
  const [savingStrategy, setSavingStrategy] = useState(false)
  const [executionStrategy, setExecutionStrategy] = useState<string>('semi_auto')
  const [mergeGroups, setMergeGroups] = useState<
    Array<{
      group_id: string
      label: string
      business_stage_keys: string[]
      gate_at_end?: boolean
      auto_advance?: boolean
    }>
  >([])
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Modals / panels
  const [showDeviation, setShowDeviation] = useState(false)
  const [deviationTargetLevel, setDeviationTargetLevel] = useState<string | null>(null)
  const [deviationTargetStages, setDeviationTargetStages] = useState<TemplateStage[]>([])
  const [showStagePanel, setShowStagePanel] = useState(false)
  const [showLogDrawer, setShowLogDrawer] = useState(false)
  const [dismissMismatch, setDismissMismatch] = useState(false)

  // Mock project context for demo — in real app this comes from route params
  const projectId = 'demo-project-001'
  const isFrozen = false // Would be derived from project status

  // Load templates and skills on mount
  useEffect(() => {
    fetchTemplates()
      .then((data) => setTemplates(data))
      .catch(() => setTemplates([]))

    api
      .get<{ data: SkillOption[]; total_count: number }>('/v1/skills')
      .then((res) => setSkills(res.data.data))
      .catch(() => setSkills([]))
  }, [])

  // Load stages when template changes
  useEffect(() => {
    if (!selectedLevel) return
    setLoading(true)
    setError(null)
    fetchTemplateDetail(selectedLevel)
      .then((detail) => {
        const seen = new Set<string>()
        const unique = detail.stages.filter((s) => {
          const key = `${s.order_index}|${s.stage_name}`
          if (seen.has(key)) return false
          seen.add(key)
          return true
        })
        setStages(unique)
        setExecutionStrategy(detail.template.default_execution_strategy || 'semi_auto')
        setMergeGroups(detail.template.merge_policy_json?.groups ?? [])
        setLoading(false)
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : '加载失败')
        setLoading(false)
      })
  }, [selectedLevel])

  const skillMap = useMemo(() => {
    const map: Record<string, string> = {}
    for (const s of skills) map[s.skill_id] = s.skill_name
    return map
  }, [skills])

  const getMergeTag = useCallback(
    (stage: TemplateStage): string | null => {
      const key = stage.business_stage_key
      if (!key) return null
      const group = mergeGroups.find((g) => g.business_stage_keys.includes(key))
      if (!group || group.business_stage_keys.length <= 1) return null
      return `(合并: ${group.business_stage_keys.join('+')})`
    },
    [mergeGroups],
  )

  const handleStrategyChange = async (value: string) => {
    setExecutionStrategy(value)
    setSavingStrategy(true)
    setSuccessMsg(null)
    setError(null)
    try {
      await updateTemplateExecutionStrategy(selectedLevel, {
        default_execution_strategy: value,
      })
      setSuccessMsg('执行策略已保存')
      setTimeout(() => setSuccessMsg(null), 2000)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '保存执行策略失败')
    } finally {
      setSavingStrategy(false)
    }
  }

  const handlePrimarySkillChange = (stageId: string, value: string) => {
    setStages((prev) =>
      prev.map((s) =>
        s.stage_id === stageId ? { ...s, primary_skill_id: value || null } : s,
      ),
    )
  }

  const handleAuxToggle = (stageId: string, skillId: string, checked: boolean) => {
    setStages((prev) =>
      prev.map((s) => {
        if (s.stage_id !== stageId) return s
        const current = s.auxiliary_skill_ids || []
        const next = checked
          ? [...current, skillId]
          : current.filter((id) => id !== skillId)
        return { ...s, auxiliary_skill_ids: next.length ? next : null }
      }),
    )
  }

  const saveStage = async (stage: TemplateStage) => {
    setSaving((prev) => ({ ...prev, [stage.stage_id]: true }))
    setSuccessMsg(null)
    try {
      await updateTemplateStage(selectedLevel, stage.stage_id, {
        primary_skill_id: stage.primary_skill_id,
        auxiliary_skill_ids: stage.auxiliary_skill_ids,
      })
      setSuccessMsg(`已保存：${stage.stage_name}`)
      setTimeout(() => setSuccessMsg(null), 2000)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '保存失败')
    } finally {
      setSaving((prev) => ({ ...prev, [stage.stage_id]: false }))
    }
  }

  const tpl = templates.find((t) => t.template_id === selectedLevel)

  const handleTemplateCardClick = (level: string) => {
    if (level === selectedLevel) return
    // Simulate deviation check: if target has different stages, show confirm
    const currentNames = new Set(stages.map((s) => s.stage_name))
    fetchTemplateDetail(level).then((detail) => {
      const seen = new Set<string>()
      const targetStages = detail.stages.filter((s) => {
        const key = `${s.order_index}|${s.stage_name}`
        if (seen.has(key)) return false
        seen.add(key)
        return true
      })
      const targetNames = new Set(targetStages.map((s) => s.stage_name))
      const hasDiff =
        currentNames.size !== targetNames.size ||
        [...currentNames].some((n) => !targetNames.has(n)) ||
        [...targetNames].some((n) => !currentNames.has(n))

      if (hasDiff) {
        setDeviationTargetLevel(level)
        setDeviationTargetStages(targetStages)
        setShowDeviation(true)
      } else {
        setSelectedLevel(level)
      }
    })
  }

  return (
    <div style={{ maxWidth: 1200 }}>
      <h1 style={{ margin: '0 0 16px 0' }}>模板阶段配置</h1>

      {/* Scale mismatch warning */}
      {!dismissMismatch && (
        <ScaleMismatchBanner
          projectId={projectId}
          onDismiss={() => setDismissMismatch(true)}
        />
      )}

      {/* Toolbar */}
      <div className="flex items-center gap-3 mb-4">
        <button
          onClick={() => setShowStagePanel(true)}
          className="text-sm px-3 py-1.5 border border-gray-300 rounded-md bg-white hover:bg-gray-50 text-gray-700"
        >
          Stage 定义管理
        </button>
        <button
          onClick={() => setShowLogDrawer(true)}
          className="text-sm px-3 py-1.5 border border-gray-300 rounded-md bg-white hover:bg-gray-50 text-gray-700"
        >
          决策日志
        </button>
        {isFrozen && (
          <span className="text-xs text-amber-700 bg-amber-50 border border-amber-200 px-2 py-1 rounded-md">
            模板已冻结
          </span>
        )}
      </div>

      {/* Template selector */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 12,
          marginBottom: 24,
        }}
      >
        {TEMPLATE_LEVELS.map((level) => {
          const t = templates.find((x) => x.template_id === level)
          const active = selectedLevel === level
          return (
            <button
              key={level}
              onClick={() => handleTemplateCardClick(level)}
              style={{
                padding: 16,
                borderRadius: 8,
                border: active ? '2px solid #3b82f6' : '1px solid #e5e7eb',
                background: active ? '#eff6ff' : '#fff',
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>
                {t?.template_name || level}
              </div>
              <div style={{ fontSize: 12, color: '#6b7280', lineHeight: 1.4 }}>
                {t?.description || '-'}
              </div>
              <div
                style={{
                  fontSize: 11,
                  color: '#9ca3af',
                  marginTop: 6,
                }}
              >
                {t
                  ? `${t.stage_count} 个阶段 / ${t.estimated_skill_count} 个 Skill`
                  : ''}
              </div>
              {t && (
                <div
                  style={{
                    fontSize: 11,
                    color: '#3b82f6',
                    marginTop: 4,
                    fontWeight: 500,
                  }}
                >
                  策略：{t.default_execution_strategy === 'full_auto'
                    ? '全自动'
                    : t.default_execution_strategy === 'full_manual'
                      ? '全人工'
                      : '半自动'}
                </div>
              )}
            </button>
          )
        })}
      </div>

      {/* Info bar */}
      {tpl && (
        <div
          style={{
            padding: '12px 16px',
            background: '#f9fafb',
            borderRadius: 8,
            marginBottom: 16,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 12,
          }}
        >
          <span style={{ fontSize: 14, fontWeight: 500 }}>
            当前模板：{tpl.template_name}
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 13 }}>
            <label style={{ color: '#374151', fontWeight: 500 }}>执行策略：</label>
            <select
              value={executionStrategy}
              onChange={(e) => handleStrategyChange(e.target.value)}
              disabled={savingStrategy || isFrozen}
              style={{
                padding: '6px 8px',
                borderRadius: 4,
                border: '1px solid #d1d5db',
                fontSize: 13,
                background: '#fff',
                opacity: savingStrategy || isFrozen ? 0.6 : 1,
              }}
            >
              <option value="full_auto">全自动 (full_auto)</option>
              <option value="semi_auto">半自动 (semi_auto)</option>
              <option value="full_manual">全人工 (full_manual)</option>
            </select>
            <span style={{ fontSize: 12, color: '#6b7280' }}>
              复杂度：{tpl.applicable_complexity} | 阶段数：{tpl.stage_count}
            </span>
          </div>
        </div>
      )}

      {skills.length === 0 && (
        <div
          style={{
            padding: 12,
            background: '#fefce8',
            border: '1px solid #fde047',
            borderRadius: 8,
            marginBottom: 16,
            fontSize: 13,
            color: '#854d0e',
          }}
        >
          ⚠️ Skill 注册中心暂无数据，请先前往「Skill 注册中心」导入 Skill，否则下拉列表为空。
        </div>
      )}

      {error && (
        <div
          style={{
            padding: 12,
            background: '#fee2e2',
            borderRadius: 8,
            marginBottom: 16,
            color: '#991b1b',
            fontSize: 13,
          }}
        >
          {error}
        </div>
      )}

      {successMsg && (
        <div
          style={{
            padding: 12,
            background: '#dcfce7',
            borderRadius: 8,
            marginBottom: 16,
            color: '#166534',
            fontSize: 13,
          }}
        >
          {successMsg}
        </div>
      )}

      {loading ? (
        <div style={{ padding: 40, textAlign: 'center', color: '#6b7280' }}>
          加载阶段列表...
        </div>
      ) : (
        <>
          <div className="text-xs text-amber-700 mb-2">
            * 每个阶段必须绑定 1 个主 Skill，未绑定的阶段无法保存。
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e5e7eb', textAlign: 'left' }}>
                <th style={{ padding: '12px 8px', width: 60 }}>序号</th>
                <th style={{ padding: '12px 8px', width: 140 }}>阶段名称</th>
                <th style={{ padding: '12px 8px' }}>主 Skill</th>
                <th style={{ padding: '12px 8px', minWidth: 280 }}>辅助 Skills</th>
                <th style={{ padding: '12px 8px', width: 80 }}>可跳过</th>
                <th style={{ padding: '12px 8px', width: 90 }}>操作</th>
              </tr>
            </thead>
          <tbody>
            {stages.map((stage) => (
              <tr key={stage.stage_id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                <td style={{ padding: '10px 8px' }}>{stage.order_index}</td>
                <td style={{ padding: '10px 8px', fontWeight: 500 }}>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span>{stage.stage_name}</span>
                    {(() => {
                      const tag = getMergeTag(stage)
                      return tag ? (
                        <span
                          className="text-[10px] px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200"
                          title={tag}
                        >
                          {tag}
                        </span>
                      ) : null
                    })()}
                  </div>
                </td>
                <td style={{ padding: '10px 8px' }}>
                  <select
                    value={stage.primary_skill_id || ''}
                    onChange={(e) =>
                      handlePrimarySkillChange(stage.stage_id, e.target.value)
                    }
                    className={[
                      'w-full text-sm rounded px-2 py-1.5 border',
                      stage.primary_skill_id
                        ? 'border-gray-300'
                        : 'border-amber-400 bg-amber-50',
                    ].join(' ')}
                    style={{ fontSize: 13 }}
                  >
                    <option value="">-- 未选择 --</option>
                    {skills.map((sk) => (
                      <option key={sk.skill_id} value={sk.skill_id}>
                        {sk.skill_name}
                      </option>
                    ))}
                  </select>
                  {!stage.primary_skill_id && (
                    <div className="text-xs text-amber-700 mt-1">
                      每个阶段必须绑定 1 个主 Skill
                    </div>
                  )}
                </td>
                <td style={{ padding: '10px 8px' }}>
                  <div
                    style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: 6,
                      maxHeight: 120,
                      overflowY: 'auto',
                    }}
                  >
                    {skills.map((sk) => {
                      const checked = (stage.auxiliary_skill_ids || []).includes(
                        sk.skill_id,
                      )
                      return (
                        <label
                          key={sk.skill_id}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 4,
                            padding: '3px 8px',
                            borderRadius: 4,
                            border: checked
                              ? '1px solid #3b82f6'
                              : '1px solid #e5e7eb',
                            background: checked ? '#eff6ff' : '#fff',
                            fontSize: 12,
                            cursor: 'pointer',
                            userSelect: 'none',
                          }}
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={(e) =>
                              handleAuxToggle(
                                stage.stage_id,
                                sk.skill_id,
                                e.target.checked,
                              )
                            }
                            style={{ cursor: 'pointer' }}
                          />
                          {sk.skill_name}
                        </label>
                      )
                    })}
                  </div>
                </td>
                <td style={{ padding: '10px 8px' }}>
                  <input
                    type="checkbox"
                    checked={stage.skippable}
                    readOnly
                    style={{ cursor: 'default' }}
                  />
                </td>
                <td style={{ padding: '10px 8px' }}>
                  <button
                    onClick={() => saveStage(stage)}
                    disabled={!stage.primary_skill_id || saving[stage.stage_id]}
                    title={
                      stage.primary_skill_id
                        ? '保存当前阶段配置'
                        : '每个阶段必须绑定 1 个主 Skill 后才能保存'
                    }
                    style={{
                      padding: '4px 10px',
                      fontSize: 12,
                      borderRadius: 4,
                      border: '1px solid #3b82f6',
                      background: '#fff',
                      color: stage.primary_skill_id ? '#3b82f6' : '#9ca3af',
                      cursor:
                        !stage.primary_skill_id || saving[stage.stage_id]
                          ? 'not-allowed'
                          : 'pointer',
                      opacity: !stage.primary_skill_id || saving[stage.stage_id] ? 0.6 : 1,
                    }}
                  >
                    {saving[stage.stage_id] ? '保存中' : '保存'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </>
      )}

      {/* Deviation confirm modal */}
      {showDeviation && deviationTargetLevel && (
        <DeviationConfirmModal
          projectId={projectId}
          currentTemplateId={selectedLevel}
          targetTemplateId={deviationTargetLevel}
          currentStages={stages}
          targetStages={deviationTargetStages}
          skillMap={skillMap}
          onClose={() => {
            setShowDeviation(false)
            setDeviationTargetLevel(null)
          }}
          onConfirmed={() => {
            setShowDeviation(false)
            if (deviationTargetLevel) setSelectedLevel(deviationTargetLevel)
            setDeviationTargetLevel(null)
          }}
        />
      )}

      {/* Stage definition panel modal */}
      {showStagePanel && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowStagePanel(false)
          }}
        >
          <div className="w-full max-w-5xl h-[80vh] bg-white rounded-xl shadow-2xl overflow-hidden flex flex-col">
            <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Stage 定义管理</h2>
              <button
                onClick={() => setShowStagePanel(false)}
                className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
              >
                ×
              </button>
            </div>
            <div className="flex-1 p-4 overflow-hidden">
              <StageDefinitionPanel
                projectId={projectId}
                stages={stages.map((s) => ({
                  project_stage_id: s.stage_id,
                  project_id: projectId,
                  stage_id: s.stage_id,
                  order_index: s.order_index,
                  status: 'DEFINED',
                  primary_skill_id: s.primary_skill_id,
                  skippable: s.skippable,
                  is_frozen: isFrozen,
                  merge_group_id: s.merge_group_id,
                  execution_status: 'NOT_STARTED',
                }))}
                skills={skills}
                readonly={isFrozen}
                onStagesChange={(updated) => {
                  // Map back to TemplateStage shape for local state if needed
                  console.log('Stages updated', updated)
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Deviation log drawer */}
      {showLogDrawer && (
        <DeviationLogDrawer
          projectId={projectId}
          onClose={() => setShowLogDrawer(false)}
        />
      )}
    </div>
  )
}
