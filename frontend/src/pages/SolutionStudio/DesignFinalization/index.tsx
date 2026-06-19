import { useEffect, useMemo, useState } from 'react'
import { useProjectContext } from '../../../App'
import { useGateCenterStore } from '../../../stores/gateCenterStore'
import { approveGate, rejectGate, retryGate } from '../../../services/gate'
import type { AnalyzeResponse, C4FixPlanResponse } from '../../ArchGovernance/types'
import FixConfirmModal from '../../ArchGovernance/components/FixConfirmModal'
import ChatSidePanel from '../../ArchGovernance/components/ChatSidePanel'
import { RefreshCw, Wrench, CheckCircle, XCircle, RotateCcw } from 'lucide-react'

const SEVERITY_ORDER = ['BLOCKER', 'ERROR', 'WARNING', 'INFO']
const SEVERITY_COLORS: Record<string, string> = {
  BLOCKER: 'text-red-700 bg-red-50 border-red-200',
  ERROR: 'text-orange-700 bg-orange-50 border-orange-200',
  WARNING: 'text-yellow-700 bg-yellow-50 border-orange-200',
  INFO: 'text-blue-700 bg-blue-50 border-blue-200',
}

export default function DesignFinalizationPage() {
  const { currentProjectId } = useProjectContext()
  const projectId = currentProjectId

  // 基线化/治理相关
  const [data, setData] = useState<AnalyzeResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [filterLevel, setFilterLevel] = useState('all')
  const [filterSeverity, setFilterSeverity] = useState('all')
  const [selectedIssueIds, setSelectedIssueIds] = useState<Set<string>>(new Set())
  const [confirmPlan, setConfirmPlan] = useState<C4FixPlanResponse | null>(null)
  const [fixPlan, setFixPlan] = useState<C4FixPlanResponse | null>(null)

  // 审批相关
  const { gates, loading: gateLoading, error, fetchGates: fetchGateList } = useGateCenterStore()
  const [pendingGateId, setPendingGateId] = useState<string | null>(null)
  const [rejectReason, setRejectReason] = useState('')
  const [showRejectModal, setShowRejectModal] = useState(false)

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
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAnalysis()
    fetchGateList()
  }, [projectId, fetchGateList])

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
    [allIssues, selectedIssueIds]
  )

  const toggleIssue = (id: string) => {
    setSelectedIssueIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
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

  // 审批操作
  const handleApprove = async (gateId: string) => {
    try {
      await approveGate(gateId)
      fetchGateList()
    } catch (e) {
      console.error('审批失败', e)
    }
  }

  const handleReject = async () => {
    if (!pendingGateId || !rejectReason) return
    try {
      await rejectGate(pendingGateId, rejectReason)
      setShowRejectModal(false)
      setRejectReason('')
      setPendingGateId(null)
      fetchGateList()
    } catch (e) {
      console.error('驳回失败', e)
    }
  }

  const handleRetry = async (gateId: string) => {
    try {
      await retryGate(gateId)
      fetchGateList()
    } catch (e) {
      console.error('重试失败', e)
    }
  }

  // 基线产物清单（演示）
  const baselineArtifacts = [
    { id: 'hld', name: 'HLD.md', locked: true, version: 'v3' },
    { id: 'c4-l2', name: 'c4-l2.dsl.yml', locked: true, version: 'v3' },
    { id: 'api-contract', name: 'api-contract.yaml', locked: true, version: 'v3' },
    { id: 'openui', name: 'openui-prototype.html', locked: false, version: 'v2' },
  ]

  const pendingGates = gates.filter((g) => g.status === 'pending')

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-800">设计定稿</h1>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">项目: {projectId || '未选择'}</span>
          <button
            onClick={fetchAnalysis}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            {loading ? '分析中...' : '重新分析'}
          </button>
        </div>
      </div>

      {/* 步骤进度条 */}
      <div className="bg-white border rounded p-4">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2 text-green-600">
            <CheckCircle size={16} />
            <span>选择产物</span>
          </div>
          <div className="flex-1 h-px bg-gray-200 mx-3" />
          <div className="flex items-center gap-2 text-green-600">
            <CheckCircle size={16} />
            <span>锁定基线</span>
          </div>
          <div className="flex-1 h-px bg-gray-200 mx-3" />
          <div className={`flex items-center gap-2 ${pendingGates.length > 0 ? 'text-amber-600' : 'text-green-600'}`}>
            {pendingGates.length > 0 ? <RotateCcw size={16} /> : <CheckCircle size={16} />}
            <span>提交审批</span>
          </div>
          <div className="flex-1 h-px bg-gray-200 mx-3" />
          <div className="flex items-center gap-2 text-gray-400">
            <CheckCircle size={16} />
            <span>审批通过</span>
          </div>
          <div className="flex-1 h-px bg-gray-200 mx-3" />
          <div className="flex items-center gap-2 text-gray-400">
            <CheckCircle size={16} />
            <span>进入开发</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {/* 左侧：待基线产物清单 */}
        <div className="bg-white border rounded p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">待基线产物清单</h3>
          <div className="space-y-2">
            {baselineArtifacts.map((art) => (
              <div key={art.id} className="flex items-center justify-between p-2 rounded border border-gray-100">
                <div className="flex items-center gap-2">
                  <input type="checkbox" checked={art.locked} readOnly className="accent-blue-600" />
                  <span className="text-sm text-gray-800">{art.name}</span>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded ${art.locked ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                  {art.locked ? '已锁定' : '未锁定'}
                </span>
              </div>
            ))}
          </div>
          <button className="mt-3 w-full py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors">
            一键锁定基线
          </button>
        </div>

        {/* 中间：基线状态与架构分析 */}
        <div className="bg-white border rounded p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">基线状态与变更影响</h3>
          <div className="grid grid-cols-2 gap-2 mb-3">
            <div className="bg-gray-50 rounded p-2">
              <div className="text-xs text-gray-500">架构健康评分</div>
              <div className={`text-lg font-bold ${healthScore >= 80 ? 'text-green-600' : healthScore >= 60 ? 'text-amber-600' : 'text-red-600'}`}>
                {healthScore}
              </div>
            </div>
            <div className="bg-gray-50 rounded p-2">
              <div className="text-xs text-gray-500">当前基线</div>
              <div className="text-lg font-bold text-gray-800">v3</div>
            </div>
          </div>
          <div className="text-sm text-gray-600 mb-2">
            影响范围: <span className="text-amber-600 font-medium">3 个任务待更新</span>
          </div>
          <div className="text-xs text-gray-400 mb-3">
            基线时间: 2026-06-17 15:30
          </div>

          {/* 筛选器 */}
          <div className="flex items-center gap-2 mb-2">
            <select className="text-xs border rounded px-2 py-1" value={filterLevel} onChange={(e) => setFilterLevel(e.target.value)}>
              <option value="all">全部层级</option>
              <option value="L1">L1</option>
              <option value="L2">L2</option>
              <option value="L3">L3</option>
              <option value="L4">L4</option>
              <option value="CON">一致性</option>
            </select>
            <select className="text-xs border rounded px-2 py-1" value={filterSeverity} onChange={(e) => setFilterSeverity(e.target.value)}>
              <option value="all">全部级别</option>
              {SEVERITY_ORDER.map((s) => (
                <option key={s} value={s}>{s} ({severityCounts[s] || 0})</option>
              ))}
            </select>
          </div>

          <div className="max-h-48 overflow-y-auto">
            {filteredIssues.length === 0 ? (
              <div className="text-xs text-gray-400 py-2">{allIssues.length === 0 ? '暂无问题，架构健康' : '没有符合筛选条件的问题'}</div>
            ) : (
              filteredIssues.slice(0, 5).map((issue) => {
                const color = SEVERITY_COLORS[issue.severity] || SEVERITY_COLORS.INFO
                return (
                  <div key={issue.id} className="flex items-start gap-2 p-2 border-b border-gray-50 last:border-b-0">
                    <input type="checkbox" checked={selectedIssueIds.has(issue.id)} onChange={() => toggleIssue(issue.id)} />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${color}`}>{issue.severity}</span>
                        <span className="text-xs text-gray-500">{issue.level === 'CON' ? '一致' : issue.level}</span>
                      </div>
                      <div className="text-xs text-gray-700 mt-0.5">{issue.message}</div>
                    </div>
                  </div>
                )
              })
            )}
            {filteredIssues.length > 5 && (
              <div className="text-xs text-gray-400 text-center py-1">还有 {filteredIssues.length - 5} 条...</div>
            )}
          </div>

          {selectedIssues.length > 0 && (
            <button
              className="mt-2 w-full py-1.5 text-xs bg-gray-900 text-white rounded hover:bg-gray-800 transition-colors flex items-center justify-center gap-1"
              onClick={() => setConfirmPlan({ project_id: projectId, plans: [{ issue_ids: selectedIssues.map((i) => i.id), changes: [], dry_run: true }] })}
            >
              <Wrench size={12} />
              修复架构问题 ({selectedIssues.length})
            </button>
          )}
        </div>

        {/* 右侧：审批面板 */}
        <div className="bg-white border rounded p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">审批面板</h3>
          {gateLoading && <div className="text-xs text-gray-500">加载中...</div>}
          {error && <div className="text-xs text-red-500 mb-2">{error}</div>}

          {pendingGates.length === 0 ? (
            <div className="text-sm text-gray-500 py-4 text-center">
              <CheckCircle size={24} className="mx-auto mb-2 text-green-500" />
              当前无待审批 Gate
            </div>
          ) : (
            <div className="space-y-3">
              {pendingGates.map((gate) => (
                <div key={gate.gate_id} className="border rounded p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-800">{gate.gate_type}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-amber-50 text-amber-700">待审批</span>
                  </div>
                  <div className="text-xs text-gray-500 mb-3">
                    项目: {gate.project_id?.slice(-6)} | 提交时间: {gate.created_at?.slice(0, 10)}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleApprove(gate.gate_id)}
                      className="flex-1 py-1.5 text-xs bg-green-600 text-white rounded hover:bg-green-700 transition-colors flex items-center justify-center gap-1"
                    >
                      <CheckCircle size={12} /> 通过
                    </button>
                    <button
                      onClick={() => {
                        setPendingGateId(gate.gate_id)
                        setShowRejectModal(true)
                      }}
                      className="flex-1 py-1.5 text-xs bg-red-600 text-white rounded hover:bg-red-700 transition-colors flex items-center justify-center gap-1"
                    >
                      <XCircle size={12} /> 驳回
                    </button>
                    <button
                      onClick={() => handleRetry(gate.gate_id)}
                      className="flex-1 py-1.5 text-xs bg-white border border-gray-300 text-gray-700 rounded hover:bg-gray-50 transition-colors flex items-center justify-center gap-1"
                    >
                      <RotateCcw size={12} /> 重试
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="mt-4 pt-3 border-t border-gray-100">
            <div className="text-xs text-gray-500 mb-2">历史审批</div>
            <div className="text-xs text-gray-400">
              CR-001 已拒绝 | CR-002 已基线化
            </div>
          </div>
        </div>
      </div>

      {/* 驳回弹窗 */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-[90vw]">
            <h3 className="text-sm font-semibold mb-3">驳回原因</h3>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              className="w-full border rounded p-2 text-sm min-h-[80px]"
              placeholder="填写驳回原因..."
            />
            <div className="flex gap-2 justify-end mt-3">
              <button
                onClick={() => {
                  setShowRejectModal(false)
                  setRejectReason('')
                  setPendingGateId(null)
                }}
                className="px-3 py-1.5 text-xs border rounded hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={handleReject}
                disabled={!rejectReason}
                className="px-3 py-1.5 text-xs bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
              >
                确认驳回
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Fix confirm modal */}
      {confirmPlan && (
        <FixConfirmModal
          projectId={projectId}
          plan={confirmPlan}
          onClose={() => setConfirmPlan(null)}
          onConfirm={(plan) => setFixPlan(plan)}
          onRegenerate={() => setConfirmPlan(null)}
        />
      )}

      {/* AI 修复侧边栏 */}
      {fixPlan && (
        <ChatSidePanel
          projectId={projectId}
          plan={fixPlan}
          onClose={() => setFixPlan(null)}
          onCompleted={() => {
            setFixPlan(null)
            void fetchAnalysis()
          }}
        />
      )}
    </div>
  )
}
