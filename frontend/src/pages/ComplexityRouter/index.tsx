import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router'
import { ScoreRadarChart } from '../../components/ScoreRadarChart'
import {
  assessComplexity,
  listAllTemplates,
  listDecisions,
  createDecision,
  type ComplexityAssessResult,
  type ComplexityTemplate,
  type PathDecision,
} from '../../services/complexity'
import { fetchTemplateDetail, type TemplateStage } from '../../services/template'
import DowngradeModal from './components/DowngradeModal'
import DecisionPanel from './components/DecisionPanel'

const PATH_META: Record<string, { name: string; scenario: string; hours: string }> = {
  Deep: { name: '完整路径', scenario: '大型复杂项目，需严格SDLC治理与全阶段管控', hours: '80-120h' },
  Standard: { name: '精简路径', scenario: '中等规模项目，保留核心阶段，跳过部分可选产物', hours: '40-60h' },
  Light: { name: '敏捷路径', scenario: '小型功能迭代，聚焦需求、编码、测试与归档', hours: '20-30h' },
  Trivial: { name: '自定义路径', scenario: '脚本或工具类微型变更，最小化流程开销', hours: '4-8h' },
}

const LEVEL_BADGES: Record<string, { text: string; color: string; bg: string }> = {
  Trivial: { text: 'S', color: '#15803d', bg: '#dcfce7' },
  Light: { text: 'M', color: '#0369a1', bg: '#e0f2fe' },
  Standard: { text: 'L', color: '#7c3aed', bg: '#ede9fe' },
  Deep: { text: 'XL', color: '#be123c', bg: '#ffe4e6' },
}

export default function ComplexityRouter() {
  const [searchParams] = useSearchParams()
  const projectId = searchParams.get('projectId') || undefined

  const [inputs, setInputs] = useState({
    module_count: 10,
    interface_complexity: 3,
    page_count: 15,
    entity_count: 8,
    integration_count: 2,
  })

  const [result, setResult] = useState<ComplexityAssessResult | null>(null)
  const [assessing, setAssessing] = useState(false)
  const [assessError, setAssessError] = useState<string | null>(null)

  const [templates, setTemplates] = useState<ComplexityTemplate[]>([])
  const [templateStages, setTemplateStages] = useState<Record<string, TemplateStage[]>>({})
  const [stagesLoading, setStagesLoading] = useState(false)

  const [selectedPathKey, setSelectedPathKey] = useState<string | null>(null)
  const [appliedPathKey, setAppliedPathKey] = useState<string | null>(null)

  const [showDowngradeModal, setShowDowngradeModal] = useState(false)
  const [pendingPathKey, setPendingPathKey] = useState<string | null>(null)

  const [showDecisionPanel, setShowDecisionPanel] = useState(false)
  const [decisions, setDecisions] = useState<PathDecision[]>([])
  const [decisionsLoading, setDecisionsLoading] = useState(false)

  const [mismatchDismissed, setMismatchDismissed] = useState(false)

  // Load templates and stages on mount
  useEffect(() => {
    listAllTemplates().then(setTemplates).catch(() => setTemplates([]))
    setStagesLoading(true)
    Promise.all(
      (['Trivial', 'Light', 'Standard', 'Deep'] as const).map((level) =>
        fetchTemplateDetail(level)
          .then((d) => {
            const seen = new Set<string>()
            const unique = d.stages.filter((s) => {
              const key = `${s.order_index}|${s.stage_name}`
              if (seen.has(key)) return false
              seen.add(key)
              return true
            })
            return [level, unique] as const
          })
          .catch(() => [level, []] as const),
      ),
    ).then((results) => {
      const map: Record<string, TemplateStage[]> = {}
      for (const [level, stages] of results) {
        map[level] = stages as TemplateStage[]
      }
      setTemplateStages(map)
      setStagesLoading(false)
    })
  }, [])

  const baselineStages = useMemo(() => {
    return templateStages['Deep'] || []
  }, [templateStages])

  const recommendedPathKey = result?.complexity_level || null

  const isMismatch = useMemo(() => {
    if (!result || !appliedPathKey) return false
    const resultStages =
      templates.find((t) => t.level === result.complexity_level)?.stage_count ?? 0
    const appliedStages =
      templates.find((t) => t.level === appliedPathKey)?.stage_count ?? 0
    return resultStages !== appliedStages
  }, [result, appliedPathKey, templates])

  const handleAssess = async () => {
    setAssessing(true)
    setAssessError(null)
    try {
      const data = await assessComplexity({
        module_count: inputs.module_count,
        interface_complexity: inputs.interface_complexity,
        page_count: inputs.page_count,
        entity_count: inputs.entity_count,
        integration_count: inputs.integration_count,
      })
      setResult(data)
      setMismatchDismissed(false)
      // Auto-select recommended path
      const rec = data.complexity_level
      setSelectedPathKey(rec)
      setAppliedPathKey(rec)
    } catch (err: unknown) {
      setAssessError(err instanceof Error ? err.message : '评估失败')
    } finally {
      setAssessing(false)
    }
  }

  const handleSelectPath = (pathKey: string) => {
    if (!result) return
    const recStages =
      templates.find((t) => t.level === result.complexity_level)?.stage_count ?? 0
    const targetStages =
      templates.find((t) => t.level === pathKey)?.stage_count ?? 0
    if (targetStages < recStages) {
      setPendingPathKey(pathKey)
      setShowDowngradeModal(true)
      return
    }
    setSelectedPathKey(pathKey)
    setAppliedPathKey(pathKey)
    setMismatchDismissed(false)
  }

  const handleConfirmDowngrade = async (reason: string) => {
    if (!pendingPathKey || !result) return
    try {
      await createDecision({
        project_id: projectId || null,
        decision_type: 'downgrade',
        from_path: PATH_META[result.complexity_level]?.name || result.complexity_level,
        to_path: PATH_META[pendingPathKey]?.name || pendingPathKey,
        reason,
      })
    } catch {
      // ignore log failure
    }
    setSelectedPathKey(pendingPathKey)
    setAppliedPathKey(pendingPathKey)
    setShowDowngradeModal(false)
    setPendingPathKey(null)
    setMismatchDismissed(false)
    refreshDecisions()
  }

  const refreshDecisions = async () => {
    setDecisionsLoading(true)
    try {
      const data = await listDecisions(projectId)
      setDecisions(data)
    } catch {
      setDecisions([])
    } finally {
      setDecisionsLoading(false)
    }
  }

  const skippedStagesForDowngrade = useMemo(() => {
    if (!pendingPathKey || !baselineStages.length) return []
    const targetStages = templateStages[pendingPathKey] || []
    const targetNames = new Set(targetStages.map((s) => s.stage_name))
    return baselineStages
      .filter((s) => !targetNames.has(s.stage_name))
      .map((s) => s.stage_name)
  }, [pendingPathKey, baselineStages, templateStages])

  const radarLabels = ['功能模块数', '接口复杂度', '页面/交互数', '数据实体数', '集成系统数']
  const radarMaxValues = [50, 10, 100, 50, 20]
  const radarScores = {
    '功能模块数': inputs.module_count,
    '接口复杂度': inputs.interface_complexity,
    '页面/交互数': inputs.page_count,
    '数据实体数': inputs.entity_count,
    '集成系统数': inputs.integration_count,
  }

  return (
    <div className="max-w-6xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">复杂度路由面板</h1>
        <button
          onClick={() => {
            setShowDecisionPanel(true)
            refreshDecisions()
          }}
          className="text-sm px-3 py-1.5 border border-gray-300 rounded-md bg-white hover:bg-gray-50 text-gray-700"
        >
          决策日志
        </button>
      </div>

      {/* Mismatch warning */}
      {isMismatch && !mismatchDismissed && result && (
        <div className="mb-4 bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-yellow-800">
            <span>⚠️</span>
            <span>
              当前评估等级为 <strong>{result.complexity_level}</strong>
              ，与已选路径不匹配
            </span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleAssess}
              className="text-sm px-3 py-1 bg-yellow-100 hover:bg-yellow-200 text-yellow-900 rounded-md"
            >
              重新评估
            </button>
            <button
              onClick={() => setMismatchDismissed(true)}
              className="text-sm px-3 py-1 text-yellow-700 hover:text-yellow-900"
            >
              忽略
            </button>
          </div>
        </div>
      )}

      {/* Triage Panel */}
      <section className="bg-white border border-gray-200 rounded-xl p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">项目规模评估</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
          {[
            { key: 'module_count' as const, label: '功能模块数', max: 50 },
            { key: 'interface_complexity' as const, label: '接口复杂度', max: 10 },
            { key: 'page_count' as const, label: '页面/交互数', max: 100 },
            { key: 'entity_count' as const, label: '数据实体数', max: 50 },
            { key: 'integration_count' as const, label: '集成系统数', max: 20 },
          ].map((item) => (
            <div key={item.key}>
              <div className="flex justify-between mb-1">
                <label className="text-sm font-medium text-gray-700">
                  {item.label}
                </label>
                <span className="text-sm text-gray-500">{inputs[item.key]}</span>
              </div>
              <input
                type="range"
                min={1}
                max={item.max}
                value={inputs[item.key]}
                onChange={(e) =>
                  setInputs((prev) => ({ ...prev, [item.key]: Number(e.target.value) }))
                }
                className="w-full accent-blue-600"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>1</span>
                <span>{item.max}</span>
              </div>
            </div>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleAssess}
            disabled={assessing}
            className="px-5 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {assessing ? '计算中...' : '重新计算'}
          </button>
          {assessError && (
            <span className="text-sm text-red-600">{assessError}</span>
          )}
        </div>
      </section>

      {/* Result Panel */}
      {result && (
        <section className="bg-white border border-gray-200 rounded-xl p-6 mb-6">
          <div className="flex flex-col lg:flex-row gap-8">
            {/* Scores */}
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-4">
                <h2 className="text-lg font-semibold text-gray-900">评估结果</h2>
                <span
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                  style={{
                    color: LEVEL_BADGES[result.complexity_level]?.color || '#374151',
                    backgroundColor:
                      LEVEL_BADGES[result.complexity_level]?.bg || '#f3f4f6',
                  }}
                >
                  {LEVEL_BADGES[result.complexity_level]?.text || result.complexity_level}{' '}
                  级
                </span>
              </div>

              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                  <div className="text-xs text-green-700 mb-1">乐观</div>
                  <div className="text-2xl font-bold text-green-800">
                    {result.optimistic_score}
                  </div>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
                  <div className="text-xs text-blue-700 mb-1">预期</div>
                  <div className="text-2xl font-bold text-blue-800">
                    {result.expected_score}
                  </div>
                </div>
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 text-center">
                  <div className="text-xs text-orange-700 mb-1">保守</div>
                  <div className="text-2xl font-bold text-orange-800">
                    {result.conservative_score}
                  </div>
                </div>
              </div>

              <div className="text-sm text-gray-500">
                推荐模板：
                <span className="font-medium text-gray-800 ml-1">
                  {templates.find((t) => t.level === result.complexity_level)
                    ?.description || '-'}
                </span>
              </div>
            </div>

            {/* Radar Chart */}
            <div className="flex flex-col items-center">
              <h3 className="text-sm font-medium text-gray-700 mb-2">复杂度雷达图</h3>
              <ScoreRadarChart
                scores={radarScores}
                labels={radarLabels}
                maxValues={radarMaxValues}
                level={result.complexity_level}
                size={260}
              />
            </div>
          </div>
        </section>
      )}

      {/* Path Comparison */}
      <section className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          四级路径可视化对比
        </h2>
        {stagesLoading ? (
          <div className="text-sm text-gray-500 py-8 text-center">
            加载路径数据...
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            {(['Deep', 'Standard', 'Light', 'Trivial'] as const).map((key) => {
              const meta = PATH_META[key]
              const tpl = templates.find((t) => t.level === key)
              const isRecommended = recommendedPathKey === key
              const isSelected = selectedPathKey === key
              const isApplied = appliedPathKey === key
              const stages = templateStages[key] || []
              const baselineNames = baselineStages.map((s) => s.stage_name)
              const stageNames = new Set(stages.map((s) => s.stage_name))

              return (
                <div
                  key={key}
                  onClick={() => handleSelectPath(key)}
                  className={[
                    'bg-white border-2 rounded-xl p-4 cursor-pointer transition-all relative',
                    isSelected
                      ? 'border-blue-500 shadow-md'
                      : 'border-gray-200 hover:border-gray-300',
                  ].join(' ')}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') handleSelectPath(key)
                  }}
                >
                  {isRecommended && (
                    <span className="absolute -top-2 -right-2 bg-blue-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow">
                      推荐
                    </span>
                  )}
                  {isApplied && (
                    <span className="absolute -top-2 left-4 bg-green-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow">
                      已应用
                    </span>
                  )}
                  <div className="text-sm font-semibold text-gray-900 mb-1">
                    {meta.name}
                  </div>
                  <div className="text-xs text-gray-500 mb-3">{meta.scenario}</div>
                  <div className="flex gap-3 text-xs text-gray-500 mb-3">
                    <span>{tpl?.stage_count ?? '-'} 个阶段</span>
                    <span>预计 {meta.hours}</span>
                  </div>
                  <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
                    {baselineNames.length === 0 ? (
                      <div className="text-xs text-gray-400">暂无阶段数据</div>
                    ) : (
                      baselineNames.map((name) => {
                        const included = stageNames.has(name)
                        return (
                          <div
                            key={name}
                            className={[
                              'text-xs py-0.5 px-1.5 rounded',
                              included
                                ? 'text-gray-700'
                                : 'text-gray-400 line-through bg-gray-50',
                            ].join(' ')}
                          >
                            {included ? '✓' : '✗'} {name}
                          </div>
                        )
                      })
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </section>

      {/* Downgrade Modal */}
      {showDowngradeModal && pendingPathKey && result && (
        <DowngradeModal
          fromPath={
            PATH_META[result.complexity_level]?.name || result.complexity_level
          }
          toPath={PATH_META[pendingPathKey]?.name || pendingPathKey}
          skippedStages={skippedStagesForDowngrade}
          onConfirm={handleConfirmDowngrade}
          onCancel={() => {
            setShowDowngradeModal(false)
            setPendingPathKey(null)
          }}
        />
      )}

      {/* Decision Panel */}
      {showDecisionPanel && (
        <>
          <div
            className="fixed inset-0 bg-black/20 z-30"
            onClick={() => setShowDecisionPanel(false)}
          />
          <DecisionPanel
            decisions={decisions}
            loading={decisionsLoading}
            onRefresh={refreshDecisions}
            onClose={() => setShowDecisionPanel(false)}
          />
        </>
      )}
    </div>
  )
}
