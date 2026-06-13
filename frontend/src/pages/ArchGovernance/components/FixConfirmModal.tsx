import { useCallback, useEffect, useState } from 'react'
import { api } from '@/services/api'
import type { C4FixPlanResponse, C4ChangeSet } from '../types'

interface FixConfirmModalProps {
  projectId: string
  plan: C4FixPlanResponse
  defaultStrategyPrompt?: string
  onClose: () => void
  onConfirm: (plan: C4FixPlanResponse) => void
  onRegenerate?: (strategyPrompt: string) => Promise<void> | void
}

const DEFAULT_STRATEGY_PROMPT =
  '请先分析以上问题，确定根因是文档不完善还是代码未实现还是其他原因，然后根据分析结果再修复问题。'

export default function FixConfirmModal({
  projectId,
  plan,
  defaultStrategyPrompt,
  onClose,
  onConfirm,
  onRegenerate,
}: FixConfirmModalProps) {
  const [editedPlan, setEditedPlan] = useState<C4FixPlanResponse>(() => structuredClone(plan))
  const [optimizing, setOptimizing] = useState<Record<string, boolean>>({})
  const [strategyPrompt, setStrategyPrompt] = useState(defaultStrategyPrompt || DEFAULT_STRATEGY_PROMPT)
  const [regenerating, setRegenerating] = useState(false)

  // Keep the strategy prompt inside the confirmed plan so it can be forwarded
  // to the AI CLI terminal during fix execution.
  useEffect(() => {
    setEditedPlan((prev) => ({
      ...prev,
      strategy_prompt: strategyPrompt,
    }))
  }, [strategyPrompt])

  const allChanges = editedPlan.plans.flatMap((p) => p.changes)
  const hasHighRisk = allChanges.some((c) => c.risk_level === 'HIGH')

  const updateChange = useCallback((planIdx: number, changeIdx: number, updater: (c: C4ChangeSet) => C4ChangeSet) => {
    setEditedPlan((prev) => {
      const next = structuredClone(prev)
      const change = next.plans[planIdx].changes[changeIdx]
      next.plans[planIdx].changes[changeIdx] = updater(change)
      return next
    })
  }, [])

  const handleAfterChange = useCallback((planIdx: number, changeIdx: number, value: string) => {
    updateChange(planIdx, changeIdx, (c) => ({ ...c, after: value }))
  }, [updateChange])

  const handleOptimize = useCallback(async (planIdx: number, changeIdx: number, prompt: string) => {
    if (!prompt.trim()) return
    const key = `${planIdx}-${changeIdx}`
    setOptimizing((prev) => ({ ...prev, [key]: true }))
    try {
      const change = editedPlan.plans[planIdx].changes[changeIdx]
      const res = await api.post<{ change: C4ChangeSet }>(`/v1/c4/governance/optimize-change?project_id=${projectId}`, {
        prompt,
        change,
      })
      updateChange(planIdx, changeIdx, () => res.data.change)
    } finally {
      setOptimizing((prev) => ({ ...prev, [key]: false }))
    }
  }, [editedPlan.plans, projectId, updateChange])

  const handleRegenerate = useCallback(async () => {
    if (!onRegenerate || !strategyPrompt.trim()) return
    setRegenerating(true)
    try {
      await onRegenerate(strategyPrompt)
    } finally {
      setRegenerating(false)
    }
  }, [onRegenerate, strategyPrompt])

  // Keep local plan in sync when the parent passes a newly regenerated plan.
  useEffect(() => {
    setEditedPlan(structuredClone(plan))
  }, [plan])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[85vh] flex flex-col">
        <div className="flex items-center justify-between border-b px-4 py-3">
          <h2 className="text-lg font-bold text-gray-800">修复方案确认</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>

        <div className="overflow-auto p-4 space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded p-3 space-y-2">
            <label className="text-sm font-medium text-blue-900">修复策略提示词</label>
            <textarea
              value={strategyPrompt}
              onChange={(e) => setStrategyPrompt(e.target.value)}
              placeholder="输入修复策略提示词，AI 会根据该提示词先分析根因再生成方案"
              className="w-full h-24 p-2 text-xs border rounded bg-white"
              spellCheck={false}
            />
            <div className="flex items-center justify-between">
              <span className="text-xs text-blue-700">
                AI 会先按该提示词分析选中问题的根因，再生成修复方案。
              </span>
              <button
                onClick={handleRegenerate}
                disabled={regenerating || !strategyPrompt.trim() || !onRegenerate}
                className="px-3 py-1.5 text-xs rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {regenerating ? '重新生成中...' : '重新生成方案'}
              </button>
            </div>
          </div>

          {editedPlan.analysis && (
            <div className="bg-gray-50 border rounded p-3 space-y-1">
              <div className="text-xs font-medium text-gray-700">AI 根因分析</div>
              <div className="text-xs text-gray-600 whitespace-pre-wrap">{editedPlan.analysis}</div>
            </div>
          )}

          {hasHighRisk && (
            <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">
              ⚠️ 方案中包含 HIGH 风险变更，执行前将在终端中二次确认。
            </div>
          )}

          {allChanges.length === 0 && (
            <div className="text-gray-500">暂无可自动生成的修复方案。</div>
          )}

          {editedPlan.plans.map((planItem, pidx) =>
            planItem.changes.map((change, cidx) => (
              <ChangeEditor
                key={`${pidx}-${cidx}`}
                planIdx={pidx}
                changeIdx={cidx}
                change={change}
                onAfterChange={handleAfterChange}
                onOptimize={handleOptimize}
                optimizing={optimizing[`${pidx}-${cidx}`] ?? false}
              />
            ))
          )}
        </div>

        <div className="border-t px-4 py-3 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-3 py-1.5 text-sm rounded border hover:bg-gray-50"
          >
            取消
          </button>
          <button
            onClick={() => onConfirm(editedPlan)}
            disabled={allChanges.length === 0}
            className="px-3 py-1.5 text-sm rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            确认修复方案，进入 AI CLI 终端
          </button>
        </div>
      </div>
    </div>
  )
}

interface ChangeEditorProps {
  planIdx: number
  changeIdx: number
  change: C4ChangeSet
  onAfterChange: (planIdx: number, changeIdx: number, value: string) => void
  onOptimize: (planIdx: number, changeIdx: number, prompt: string) => Promise<void>
  optimizing: boolean
}

function ChangeEditor({ planIdx, changeIdx, change, onAfterChange, onOptimize, optimizing }: ChangeEditorProps) {
  const [prompt, setPrompt] = useState('')
  const [expanded, setExpanded] = useState(true)

  const riskColor =
    change.risk_level === 'HIGH'
      ? 'bg-red-100 text-red-700'
      : change.risk_level === 'MEDIUM'
        ? 'bg-amber-100 text-amber-700'
        : 'bg-green-100 text-green-700'

  return (
    <div className="border rounded">
      <div className="bg-gray-50 px-3 py-2 border-b flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs">
          <span className="font-mono px-1.5 py-0.5 rounded bg-blue-100 text-blue-700">{change.action}</span>
          <span className="font-mono text-gray-600">{change.target_path}</span>
          <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${riskColor}`}>{change.risk_level}</span>
          {change.requires_confirmation && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">需确认</span>
          )}
        </div>
        <button onClick={() => setExpanded((v) => !v)} className="text-xs text-gray-500 hover:text-gray-700">
          {expanded ? '折叠' : '展开'}
        </button>
      </div>

      {expanded && (
        <div className="p-3 space-y-3">
          <div className="text-sm text-gray-700">{change.rationale}</div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">变更后内容（可编辑）</label>
            <textarea
              value={change.after || ''}
              onChange={(e) => onAfterChange(planIdx, changeIdx, e.target.value)}
              className="w-full h-32 p-2 text-xs font-mono border rounded bg-gray-50"
              spellCheck={false}
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="输入 AI 优化提示词，例如：添加异常处理"
              className="flex-1 text-sm border rounded px-2 py-1"
            />
            <button
              onClick={() => onOptimize(planIdx, changeIdx, prompt)}
              disabled={optimizing || !prompt.trim()}
              className="px-3 py-1.5 text-sm rounded bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50"
            >
              {optimizing ? '优化中...' : '优化'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
