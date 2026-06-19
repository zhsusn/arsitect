import { useState, useEffect, useCallback } from 'react'
import { useProjectContext } from '../../../App'
import { useRequirementStudioStore } from '../../../stores/requirementStudioStore'
import { useExecutionStore } from '../../../stores/executionStore'
import {
  fetchStudioStatus, executeStage, fetchArtifacts,
} from '../../../services/requirementStudio'
import { getArtifactContent, saveArtifactContent } from '../../../services/artifact'
import { createProjectReview } from '../../../services/projectReview'
import { fetchProjectOverview } from '../../../services/project'
import ArtifactRenderer from '../../../components/ArtifactRenderer'
import ExecutionPanel from '../../../components/ExecutionPanel'
import ReviewPanel from '../../../components/ReviewPanel'
import SizeEstimateCard, { type SizeEstimate } from '../../../components/SizeEstimateCard'
import StatusBar from '../../../components/StatusBar'

const TABS = [
  { id: 'brainstorm', label: '🧠 脑暴纪要' },
  { id: 'competitive', label: '🔍 竞品分析' },
  { id: 'estimate', label: '📊 规模初估' },
]

const DEMO_BRAINSTORM = `# 订单系统脑暴纪要

## 核心场景
1. 多渠道订单接入（Web、App、API）
2. 订单全生命周期管理（创建 → 支付 → 发货 → 完成）
3. 库存实时联动与预警

## 痛点假设
- 当前订单状态不透明，客户反复询问
- 库存扣减与订单创建非原子性，偶发超卖
- 多渠道订单格式不统一，人工整理耗时

## 价值主张
- 统一订单中心，全渠道状态实时可查
- 库存原子扣减，杜绝超卖
- 自动化通知，减少 80% 客服咨询

## 竞品对标
| 维度 | 本方案 | 竞品 A | 竞品 B |
|------|--------|--------|--------|
| 实时库存 | ✓ | ✓ | ✗ |
| 多渠道 | 3 | 2 | 4 |
| 通知自动化 | 全渠道 | 仅邮件 | 仅短信 |
`

const DEMO_COMPETITIVE = `# 竞品分析报告

## 竞品 A — 传统 ERP 订单模块
- **优势**: 功能全面、报表丰富
- **劣势**: 部署重、API 封闭、定制难
- **差异化**: 我们更轻量、API-first

## 竞品 B — SaaS 电商中台
- **优势**: 开箱即用、生态完善
- **劣势**:  vendor lock-in、数据不出境
- **差异化**: 可私有化、源码可控

## 结论
聚焦"中小团队 + 私有化部署 + 快速定制"差异化定位。
`

export default function BrainstormPage() {
  const { currentProjectId } = useProjectContext()
  const projectId = currentProjectId
  const [activeTab, setActiveTab] = useState('brainstorm')
  const [brainstormContent, setBrainstormContent] = useState(DEMO_BRAINSTORM)
  const [competitiveContent, setCompetitiveContent] = useState(DEMO_COMPETITIVE)
  const [sizeEstimate, setSizeEstimate] = useState<SizeEstimate | null>(null)
  const [showBreakdown, setShowBreakdown] = useState(false)

  const {
    executionStatus,
    executionLogs,
    annotations,
    setExecutionStatus,
    appendExecutionLog,
    setStageStatuses,
    setLoading,
    setError,
  } = useRequirementStudioStore()

  const { connectSSE, disconnectSSE } = useExecutionStore()

  const [brainstormArtifactId, setBrainstormArtifactId] = useState<string | null>(null)
  const [competitiveArtifactId, setCompetitiveArtifactId] = useState<string | null>(null)

  // Load artifacts from backend
  const loadArtifacts = useCallback(async () => {
    if (!projectId) return
    try {
      const artifacts = await fetchArtifacts(projectId)
      const brainstormArt = artifacts.find((a) =>
        a.file_name.toLowerCase().includes('brainstorm') || a.file_name.toLowerCase().includes('脑暴')
      )
      const competitiveArt = artifacts.find((a) =>
        a.file_name.toLowerCase().includes('competitive') || a.file_name.toLowerCase().includes('竞品')
      )
      if (brainstormArt) {
        setBrainstormArtifactId(brainstormArt.artifact_id)
        const content = await getArtifactContent(brainstormArt.artifact_id)
        setBrainstormContent(content)
      }
      if (competitiveArt) {
        setCompetitiveArtifactId(competitiveArt.artifact_id)
        const content = await getArtifactContent(competitiveArt.artifact_id)
        setCompetitiveContent(content)
      }
    } catch (err) {
      console.warn('加载脑暴产物失败:', err)
    }
  }, [projectId])

  useEffect(() => {
    loadArtifacts()
  }, [loadArtifacts])

  useEffect(() => {
    if (!projectId) return
    setLoading(true)
    fetchStudioStatus(projectId)
      .then((data) => {
        const newStatus: Record<string, any> = {}
        data.stages.forEach((stage) => {
          newStatus[stage.stage_id] = {
            status: stage.status,
            progress: stage.progress_percent,
            tasks: [],
          }
        })
        setStageStatuses(newStatus)
      })
      .catch((err) => setError(err instanceof Error ? err.message : '加载失败'))
      .finally(() => setLoading(false))
  }, [projectId, setLoading, setError, setStageStatuses])

  useEffect(() => {
    if (!projectId) return
    fetchProjectOverview(projectId)
      .then((overview) => {
        const est = overview.size_estimate
        if (est) {
          setSizeEstimate({
            moduleCount: est.module_count || 0,
            interfaceCount: est.interface_count || 0,
            pageCount: est.page_count || 0,
            entityCount: 0,
            complexity: (est.tech_complexity as 'medium' | 'low' | 'high') || 'medium',
            riskLevel: (est.risk_level as 'low' | 'medium' | 'high') || 'low',
            recommendedPath: 'standard',
            estimatedWeeks: 3,
            estimatedPersonMonths: 1.5,
            breakdown: [
              { moduleName: '订单管理', estimatedHours: 40 },
              { moduleName: '库存联动', estimatedHours: 24 },
              { moduleName: '通知系统', estimatedHours: 16 },
            ],
          })
        }
      })
      .catch(() => setSizeEstimate(null))
  }, [projectId])

  const handleExecute = useCallback(async () => {
    if (!projectId) return
    setExecutionStatus('prep')
    appendExecutionLog('> 触发脑暴 Skill...')
    try {
      connectSSE(projectId)
      await executeStage(projectId, 'brainstorm')
      setExecutionStatus('exec')
      appendExecutionLog('> 执行中...')
      // Poll for completion then refresh artifacts
      setTimeout(async () => {
        setExecutionStatus('post')
        appendExecutionLog('> 脑暴纪要生成完成，刷新产物...')
        await loadArtifacts()
        setExecutionStatus('success')
        disconnectSSE()
      }, 2000)
    } catch (err) {
      setExecutionStatus('failed')
      appendExecutionLog(`> 执行失败: ${err instanceof Error ? err.message : '未知错误'}`)
      disconnectSSE()
    }
  }, [projectId, setExecutionStatus, appendExecutionLog, connectSSE, disconnectSSE, loadArtifacts])

  const handleSaveBrainstorm = useCallback(async (content: string) => {
    setBrainstormContent(content)
    if (!brainstormArtifactId) {
      appendExecutionLog('> 警告: 未找到脑暴纪要产物，仅本地保存')
      return
    }
    try {
      await saveArtifactContent(brainstormArtifactId, content)
      appendExecutionLog('> 脑暴纪要已保存')
    } catch (err) {
      appendExecutionLog(`> 保存脑暴纪要失败: ${err instanceof Error ? err.message : '未知错误'}`)
    }
  }, [brainstormArtifactId, appendExecutionLog])

  const handleSaveCompetitive = useCallback(async (content: string) => {
    setCompetitiveContent(content)
    if (!competitiveArtifactId) {
      appendExecutionLog('> 警告: 未找到竞品分析产物，仅本地保存')
      return
    }
    try {
      await saveArtifactContent(competitiveArtifactId, content)
      appendExecutionLog('> 竞品分析已保存')
    } catch (err) {
      appendExecutionLog(`> 保存竞品分析失败: ${err instanceof Error ? err.message : '未知错误'}`)
    }
  }, [competitiveArtifactId, appendExecutionLog])

  const renderContent = () => {
    switch (activeTab) {
      case 'brainstorm':
        return (
          <ArtifactRenderer
            content={brainstormContent}
            type="markdown"
            onEdit={handleSaveBrainstorm}
          />
        )
      case 'competitive':
        return (
          <ArtifactRenderer
            content={competitiveContent}
            type="markdown"
            onEdit={handleSaveCompetitive}
          />
        )
      case 'estimate':
        return (
          <div style={{ padding: 24 }}>
            {sizeEstimate ? (
              <div>
                <SizeEstimateCard estimate={sizeEstimate} />
                <button
                  onClick={() => setShowBreakdown(true)}
                  style={{
                    marginTop: 16,
                    padding: '8px 16px',
                    fontSize: 13,
                    background: '#fff',
                    color: '#2563eb',
                    border: '1px solid #2563eb',
                    borderRadius: 4,
                    cursor: 'pointer',
                  }}
                >
                  查看详细 breakdown
                </button>
              </div>
            ) : (
              <div style={{ color: '#6b7280', textAlign: 'center', padding: 40 }}>
                暂无规模初估数据，请先执行脑暴 Skill
              </div>
            )}
          </div>
        )
      default:
        return null
    }
  }

  if (!projectId) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280' }}>
        请先在顶部选择项目
      </div>
    )
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: '#fff',
        borderRadius: 8,
        border: '1px solid #e5e7eb',
        overflow: 'hidden',
      }}
    >
      <div style={{ display: 'flex', borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '10px 20px',
              fontSize: 13,
              border: 'none',
              background: activeTab === tab.id ? '#fff' : 'transparent',
              color: activeTab === tab.id ? '#2563eb' : '#6b7280',
              borderBottom: activeTab === tab.id ? '2px solid #2563eb' : '2px solid transparent',
              cursor: 'pointer',
              fontWeight: activeTab === tab.id ? 600 : 400,
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <div style={{ flex: 1, overflow: 'auto', borderRight: '1px solid #e5e7eb' }}>
          {renderContent()}
        </div>
        <div style={{ width: 300, minWidth: 300, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <ExecutionPanel
            status={executionStatus}
            logs={executionLogs}
            skillName="skill-brainstorming"
            onExecute={handleExecute}
            onRetry={() => setExecutionStatus('idle')}
            onAbort={() => {
              setExecutionStatus('idle')
              appendExecutionLog('> 已中断')
              disconnectSSE()
            }}
          />
          <ReviewPanel
            annotations={annotations as any}
            onSubmit={async (comment) => {
              if (!projectId) return
              try {
                await createProjectReview(projectId, {
                  review_type: 'code_review',
                  item_id: `brainstorm-${activeTab}-${Date.now()}`,
                  item_type: 'annotation',
                  status: 'pending',
                  notes: comment,
                })
                appendExecutionLog('> 审查批注已保存')
              } catch (err) {
                appendExecutionLog(`> 保存批注失败: ${err instanceof Error ? err.message : '未知错误'}`)
              }
            }}
          />
        </div>
      </div>

      <StatusBar
        projectName={projectId}
        stageName="脑暴室"
        artifactName={activeTab === 'brainstorm' ? '脑暴纪要' : activeTab === 'competitive' ? '竞品分析' : '规模初估'}
        version="v1"
      />

      {/* Breakdown 弹窗 */}
      {showBreakdown && sizeEstimate && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50
        }}>
          <div style={{ background: '#fff', borderRadius: 8, padding: 24, width: 480 }}>
            <h3 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 600 }}>规模初估详细 breakdown</h3>
            <table style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                  <th style={{ textAlign: 'left', padding: '8px 12px', fontWeight: 600, color: '#374151' }}>模块</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px', fontWeight: 600, color: '#374151' }}>预估工时</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px', fontWeight: 600, color: '#374151' }}>风险等级</th>
                </tr>
              </thead>
              <tbody>
                {sizeEstimate.breakdown?.map((item) => (
                  <tr key={item.moduleName} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td style={{ padding: '8px 12px', color: '#374151' }}>{item.moduleName}</td>
                    <td style={{ padding: '8px 12px', textAlign: 'right', color: '#374151' }}>{item.estimatedHours}h</td>
                    <td style={{ padding: '8px 12px', textAlign: 'right', color: '#16a34a' }}>低</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr style={{ borderTop: '2px solid #e5e7eb', fontWeight: 600 }}>
                  <td style={{ padding: '8px 12px', color: '#111827' }}>总计</td>
                  <td style={{ padding: '8px 12px', textAlign: 'right', color: '#111827' }}>
                    {sizeEstimate.breakdown?.reduce((sum, item) => sum + item.estimatedHours, 0)}h
                  </td>
                  <td style={{ padding: '8px 12px', textAlign: 'right', color: '#111827' }}>
                    {sizeEstimate.recommendedPath}
                  </td>
                </tr>
              </tfoot>
            </table>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 20 }}>
              <button
                onClick={() => setShowBreakdown(false)}
                style={{ padding: '8px 16px', fontSize: 13, background: '#2563eb', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
