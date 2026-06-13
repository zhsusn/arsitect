import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router'
import FixConfirmModal from './components/FixConfirmModal'
import FixTerminalModal from './components/FixTerminalModal'
import type { AnalyzeResponse, C4FixPlanResponse } from './types'

const LEVEL_NAMES: Record<string, string> = {
  L1: '系统上下文 (L1)',
  L2: '容器 (L2)',
  L3: '组件 (L3)',
  L4: '代码 (L4)',
}

const SEVERITY_ORDER = ['BLOCKER', 'ERROR', 'WARNING', 'INFO']
const SEVERITY_COLORS: Record<string, string> = {
  BLOCKER: 'text-red-700 bg-red-50 border-red-200',
  ERROR: 'text-orange-700 bg-orange-50 border-orange-200',
  WARNING: 'text-yellow-700 bg-yellow-50 border-orange-200',
  INFO: 'text-blue-700 bg-blue-50 border-blue-200',
}

const FIX_ACTION_LABELS: Record<string, string> = {
  UPDATE_DOC: '📝 改文档',
  UPDATE_CODE: '💻 改代码',
  BOTH: '🔧 两者都改',
  '': '',
}

export default function ArchGovernancePage() {
  const { projectId: urlProjectId } = useParams<{ projectId: string }>()
  const projectId = urlProjectId || localStorage.getItem('arsitect:lastProjectId') || ''
  const [data, setData] = useState<AnalyzeResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [filterLevel, setFilterLevel] = useState('all')
  const [filterSeverity, setFilterSeverity] = useState('all')
  const [fixLoading, setFixLoading] = useState(false)
  const [selectedIssueIds, setSelectedIssueIds] = useState<Set<string>>(new Set())
  const [confirmPlan, setConfirmPlan] = useState<C4FixPlanResponse | null>(null)
  const [fixPlan, setFixPlan] = useState<C4FixPlanResponse | null>(null)

  const fetchAnalysis = async () => {
    if (!projectId) return
    setLoading(true)
    try {
      const res = await fetch(`/api/v1/c4/analyze?project_id=${projectId}&_t=${Date.now()}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const d = await res.json()
      setData(d)
      setSelectedIssueIds(new Set())
    } catch (e) {
      console.error(e)
      alert('分析失败，请检查后端服务')
    } finally {
      setLoading(false)
    }
  }

  const fetchFixPlan = async (strategyPrompt?: string): Promise<C4FixPlanResponse> => {
    if (!projectId || selectedIssues.length === 0) {
      throw new Error('请先选择要修复的问题')
    }
    const payload = {
      issues: selectedIssues.map((issue) => ({
        issue_id: issue.id,
        source: issue.source,
        rule_id: issue.rule_id,
        severity: issue.severity,
        message: issue.message,
        node_ids: issue.node_ids || [],
        c4_node_id: issue.c4_node_id || '',
        code_entity_id: issue.code_entity_id || '',
        fix_hint: issue.fix_hint || '',
        fix_action: issue.fix_action || '',
      })),
      context: {
        strategy_prompt: strategyPrompt || '',
      },
    }
    const res = await fetch(`/api/v1/c4/governance/fix-plan?project_id=${projectId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return (await res.json()) as C4FixPlanResponse
  }

  const generateFixPlan = async () => {
    setFixLoading(true)
    try {
      const plan = await fetchFixPlan()
      setConfirmPlan(plan)
    } catch (e) {
      console.error(e)
      alert('生成修复方案失败，请检查后端服务')
    } finally {
      setFixLoading(false)
    }
  }

  const handleRegeneratePlan = async (strategyPrompt: string) => {
    try {
      const plan = await fetchFixPlan(strategyPrompt)
      setConfirmPlan(plan)
    } catch (e) {
      console.error(e)
      alert('重新生成修复方案失败，请检查后端服务')
    }
  }

  const handleConfirmPlan = (confirmedPlan: C4FixPlanResponse) => {
    setFixPlan(confirmedPlan)
    setConfirmPlan(null)
  }

  const handleFixCompleted = () => {
    setFixPlan(null)
    void fetchAnalysis()
  }

  useEffect(() => {
    fetchAnalysis()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId])

  // Flatten all issues from all levels + consistency
  const allIssues = useMemo(() => {
    if (!data) return []
    const list: Array<{
      id: string
      level: string
      rule_id: string
      severity: string
      message: string
      fix_hint: string
      node_ids?: string[]
      fix_action?: string
      c4_node_id?: string
      code_entity_id?: string
      source: 'structural' | 'consistency'
    }> = []

    data.levels.forEach((lvl) => {
      lvl.issues.forEach((issue, idx) => {
        list.push({
          id: `${lvl.level}-${idx}`,
          level: lvl.level,
          rule_id: issue.rule_id,
          severity: issue.severity,
          message: issue.message,
          fix_hint: issue.fix_hint,
          node_ids: issue.node_ids,
          source: 'structural',
        })
      })
    })

    if (data.consistency) {
      data.consistency.issues.forEach((issue, idx) => {
        list.push({
          id: `con-${idx}`,
          level: 'CON',
          rule_id: issue.rule_id,
          severity: issue.severity,
          message: issue.message,
          fix_hint: issue.fix_hint,
          fix_action: issue.fix_action,
          c4_node_id: issue.c4_node_id,
          code_entity_id: issue.code_entity_id,
          source: 'consistency',
        })
      })
    }

    // Sort by severity order
    list.sort((a, b) => {
      const ai = SEVERITY_ORDER.indexOf(a.severity)
      const bi = SEVERITY_ORDER.indexOf(b.severity)
      return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi)
    })

    return list
  }, [data])

  const filteredIssues = useMemo(() => {
    return allIssues.filter((i) => {
      const levelOk = filterLevel === 'all' || i.level === filterLevel
      const severityOk = filterSeverity === 'all' || i.severity === filterSeverity
      return levelOk && severityOk
    })
  }, [allIssues, filterLevel, filterSeverity])

  const selectedIssues = useMemo(
    () => allIssues.filter((i) => selectedIssueIds.has(i.id)),
    [allIssues, selectedIssueIds],
  )

  const toggleIssue = (id: string) => {
    setSelectedIssueIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const toggleAll = () => {
    if (selectedIssueIds.size === filteredIssues.length && filteredIssues.length > 0) {
      setSelectedIssueIds(new Set())
    } else {
      setSelectedIssueIds(new Set(filteredIssues.map((i) => i.id)))
    }
  }

  const severityCounts = useMemo(() => {
    const counts: Record<string, number> = {}
    allIssues.forEach((i) => {
      counts[i.severity] = (counts[i.severity] || 0) + 1
    })
    return counts
  }, [allIssues])

  const healthScore = useMemo(() => {
    if (!data) return 0
    const total = allIssues.length
    if (total === 0) return 100
    const weighted =
      (severityCounts.BLOCKER || 0) * 25 +
      (severityCounts.ERROR || 0) * 15 +
      (severityCounts.WARNING || 0) * 5 +
      (severityCounts.INFO || 0) * 1
    return Math.max(0, Math.min(100, 100 - weighted))
  }, [data, allIssues, severityCounts])

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-800">架构治理中心</h1>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">项目: {projectId || '未选择'}</span>
          <button
            onClick={fetchAnalysis}
            disabled={loading}
            className="px-3 py-1.5 text-sm rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? '分析中...' : '⟳ 重新分析'}
          </button>
          <button
            onClick={generateFixPlan}
            disabled={fixLoading || selectedIssues.length === 0}
            className="px-3 py-1.5 text-sm rounded bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50"
          >
            {fixLoading ? '生成中...' : `修复架构问题 (${selectedIssues.length})`}
          </button>
        </div>
      </div>

      {/* Health score cards */}
      <div className="grid grid-cols-4 gap-3">
        <div className="bg-white border rounded p-3">
          <div className="text-xs text-gray-500 mb-1">架构健康评分</div>
          <div
            className={`text-2xl font-bold ${
              healthScore >= 80 ? 'text-green-600' : healthScore >= 60 ? 'text-amber-600' : 'text-red-600'
            }`}
          >
            {healthScore}
          </div>
        </div>
        <div className="bg-white border rounded p-3">
          <div className="text-xs text-gray-500 mb-1">总体状态</div>
          <div className={`text-lg font-semibold ${data?.overall_passed ? 'text-green-600' : 'text-red-600'}`}>
            {data?.overall_passed ? '✓ 通过' : '✗ 未通过'}
          </div>
        </div>
        <div className="bg-white border rounded p-3">
          <div className="text-xs text-gray-500 mb-1">架构问题</div>
          <div className="text-lg font-semibold text-gray-800">
            {data?.levels.reduce((sum, l) => sum + l.issues.length, 0) || 0}
          </div>
        </div>
        <div className="bg-white border rounded p-3">
          <div className="text-xs text-gray-500 mb-1">一致性问题</div>
          <div className="text-lg font-semibold text-gray-800">
            {data?.consistency?.issues.length || 0}
          </div>
        </div>
      </div>

      {/* Per-level summary */}
      {data && (
        <div className="grid grid-cols-4 gap-3">
          {data.levels.map((lvl) => (
            <div key={lvl.level} className="bg-white border rounded p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-gray-600">{LEVEL_NAMES[lvl.level] || lvl.level}</span>
                <span className={`text-xs ${lvl.passed ? 'text-green-600' : 'text-red-600'}`}>
                  {lvl.passed ? '✓' : '✗'}
                </span>
              </div>
              <div className="text-sm text-gray-700">
                {lvl.issues.length > 0 ? (
                  <span>
                    {SEVERITY_ORDER.filter((s) => lvl.summary[s]).map((s) => `${s}:${lvl.summary[s]}`).join(' ')}
                  </span>
                ) : (
                  <span className="text-gray-400">无问题</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-3 bg-white border rounded p-3">
        <span className="text-sm text-gray-600 font-medium">筛选:</span>
        <select
          className="text-sm border rounded px-2 py-1"
          value={filterLevel}
          onChange={(e) => setFilterLevel(e.target.value)}
        >
          <option value="all">全部层级</option>
          <option value="L1">L1 系统上下文</option>
          <option value="L2">L2 容器</option>
          <option value="L3">L3 组件</option>
          <option value="L4">L4 代码</option>
          <option value="CON">一致性</option>
        </select>
        <select
          className="text-sm border rounded px-2 py-1"
          value={filterSeverity}
          onChange={(e) => setFilterSeverity(e.target.value)}
        >
          <option value="all">全部级别</option>
          {SEVERITY_ORDER.map((s) => (
            <option key={s} value={s}>
              {s} ({severityCounts[s] || 0})
            </option>
          ))}
        </select>
        <span className="text-sm text-gray-400 ml-auto">
          共 {filteredIssues.length} 条
        </span>
      </div>

      {/* Issues table */}
      <div className="bg-white border rounded overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-3 py-2 font-medium text-gray-600 w-10">
                <input
                  type="checkbox"
                  checked={filteredIssues.length > 0 && filteredIssues.every((i) => selectedIssueIds.has(i.id))}
                  onChange={toggleAll}
                />
              </th>
              <th className="text-left px-3 py-2 font-medium text-gray-600 w-16">级别</th>
              <th className="text-left px-3 py-2 font-medium text-gray-600 w-24">规则</th>
              <th className="text-left px-3 py-2 font-medium text-gray-600 w-20">严重度</th>
              <th className="text-left px-3 py-2 font-medium text-gray-600">问题描述</th>
              <th className="text-left px-3 py-2 font-medium text-gray-600 w-24">修复方向</th>
            </tr>
          </thead>
          <tbody>
            {filteredIssues.length === 0 && (
              <tr>
                <td colSpan={6} className="px-3 py-6 text-center text-gray-400">
                  {allIssues.length === 0 ? '暂无问题，架构健康' : '没有符合筛选条件的问题'}
                </td>
              </tr>
            )}
            {filteredIssues.map((issue) => {
              const color = SEVERITY_COLORS[issue.severity] || SEVERITY_COLORS.INFO
              return (
                <tr key={issue.id} className="border-b last:border-b-0 hover:bg-gray-50">
                  <td className="px-3 py-2">
                    <input
                      type="checkbox"
                      checked={selectedIssueIds.has(issue.id)}
                      onChange={() => toggleIssue(issue.id)}
                    />
                  </td>
                  <td className="px-3 py-2 text-gray-500">
                    {issue.level === 'CON' ? '一致' : issue.level}
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-gray-600">{issue.rule_id}</td>
                  <td className="px-3 py-2">
                    <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold ${color}`}>
                      {issue.severity}
                    </span>
                  </td>
                  <td className="px-3 py-2">
                    <div className="text-gray-800">{issue.message}</div>
                    {issue.fix_hint && (
                      <div className="text-xs text-gray-500 mt-0.5">💡 {issue.fix_hint}</div>
                    )}
                    {issue.node_ids && issue.node_ids.length > 0 && (
                      <div className="text-xs text-gray-400 mt-0.5">节点: {issue.node_ids.join(', ')}</div>
                    )}
                    {issue.c4_node_id && (
                      <div className="text-xs text-gray-400 mt-0.5">C4: {issue.c4_node_id}</div>
                    )}
                    {issue.code_entity_id && (
                      <div className="text-xs text-gray-400 mt-0.5">Code: {issue.code_entity_id}</div>
                    )}
                  </td>
                  <td className="px-3 py-2 text-xs text-gray-600">
                    {issue.fix_action ? FIX_ACTION_LABELS[issue.fix_action] || issue.fix_action : '-'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Rules legend */}
      <div className="bg-white border rounded p-3">
        <div className="text-sm font-medium text-gray-700 mb-2">规则说明</div>
        <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
          <div><span className="font-mono text-gray-800">C4-ORPHAN-001</span> — 孤立节点（无关联关系）</div>
          <div><span className="font-mono text-gray-800">C4-CYCLE-001</span> — 循环依赖</div>
          <div><span className="font-mono text-gray-800">C4-NAME-001</span> — 节点 ID 命名不规范</div>
          <div><span className="font-mono text-gray-800">C4-LEVEL-001</span> — L3 组件引用了不存在的 L2 容器</div>
          <div><span className="font-mono text-gray-800">C4-DISCONN-001</span> — 图被拆分为多个不连通子图</div>
          <div><span className="font-mono text-gray-800">CON-C2M-001</span> — 容器在代码中未找到对应模块</div>
          <div><span className="font-mono text-gray-800">CON-M2C-001</span> — 代码目录未在 C4 L2 中定义为容器</div>
          <div><span className="font-mono text-gray-800">CON-C2F-001</span> — 组件在代码中未找到对应类/函数</div>
        </div>
      </div>

      {/* Fix confirm modal */}
      {confirmPlan && (
        <FixConfirmModal
          projectId={projectId}
          plan={confirmPlan}
          onClose={() => setConfirmPlan(null)}
          onConfirm={handleConfirmPlan}
          onRegenerate={handleRegeneratePlan}
        />
      )}

      {/* Fix terminal modal */}
      {fixPlan && (
        <FixTerminalModal
          projectId={projectId}
          plan={fixPlan}
          onClose={() => setFixPlan(null)}
          onCompleted={handleFixCompleted}
        />
      )}
    </div>
  )
}
