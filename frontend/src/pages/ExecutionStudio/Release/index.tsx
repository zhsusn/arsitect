import { useState, useMemo, useEffect } from 'react'
import { useProjectContext } from '../../../App'
import {
  listProjectReviews,
  createProjectReview,
  updateProjectReview,
} from '../../../services/projectReview'

interface ChecklistItem {
  id: string
  category: 'preparation' | 'staging' | 'production' | 'verification'
  label: string
  checked: boolean
  risk: 'low' | 'medium' | 'high'
  assignee?: string
}

interface RollbackStep {
  id: string
  level: 'A' | 'B' | 'C'
  description: string
  command: string
}

const CATEGORIES = [
  { id: 'preparation', label: '发布准备', icon: '📋' },
  { id: 'staging', label: '预发布', icon: '🧪' },
  { id: 'production', label: '正式发布', icon: '🚀' },
  { id: 'verification', label: '发布后验证', icon: '✅' },
]

const DEFAULT_CHECKLIST: ChecklistItem[] = [
  { id: 'c1', category: 'preparation', label: '代码已合并到 main 分支', checked: false, risk: 'high', assignee: '开发' },
  { id: 'c2', category: 'preparation', label: '版本号已更新', checked: false, risk: 'medium', assignee: '开发' },
  { id: 'c3', category: 'preparation', label: 'CHANGELOG 已生成', checked: false, risk: 'low', assignee: 'PM' },
  { id: 'c4', category: 'preparation', label: '数据库迁移脚本已测试', checked: false, risk: 'high', assignee: 'DBA' },
  { id: 'c5', category: 'preparation', label: '环境变量配置已确认', checked: false, risk: 'high', assignee: '运维' },
  { id: 'c6', category: 'staging', label: '预发布环境部署成功', checked: false, risk: 'medium', assignee: '运维' },
  { id: 'c7', category: 'staging', label: '冒烟测试通过', checked: false, risk: 'high', assignee: 'QA' },
  { id: 'c8', category: 'staging', label: '性能基准测试通过', checked: false, risk: 'medium', assignee: 'QA' },
  { id: 'c9', category: 'production', label: '灰度发布 5% 流量', checked: false, risk: 'high', assignee: '运维' },
  { id: 'c10', category: 'production', label: '监控指标正常', checked: false, risk: 'high', assignee: 'SRE' },
  { id: 'c11', category: 'production', label: '全量发布', checked: false, risk: 'high', assignee: '运维' },
  { id: 'c12', category: 'verification', label: '核心业务流程验证', checked: false, risk: 'high', assignee: 'QA' },
  { id: 'c13', category: 'verification', label: '错误率 < 0.1%', checked: false, risk: 'medium', assignee: 'SRE' },
  { id: 'c14', category: 'verification', label: '响应时间 P99 < 200ms', checked: false, risk: 'medium', assignee: 'SRE' },
]

const ROLLBACK_STEPS: RollbackStep[] = [
  { id: 'r1', level: 'A', description: '产物级回滚 — Git checkout 上一个稳定版本', command: 'git checkout v{prev_version} && ./deploy.sh' },
  { id: 'r2', level: 'B', description: '数据库级回滚 — 执行回滚迁移脚本', command: 'alembic downgrade -1 && ./restore-db.sh' },
  { id: 'r3', level: 'C', description: '项目级回滚 — 整体 Git reset + 状态重置', command: 'git reset --hard HEAD~1 && ./full-rollback.sh' },
]

export default function ReleasePage() {
  const { currentProjectId } = useProjectContext()
  const projectId = currentProjectId

  const [checklist, setChecklist] = useState<ChecklistItem[]>(DEFAULT_CHECKLIST)
  const [selectedCategory, setSelectedCategory] = useState<string>('preparation')
  const [showReleaseModal, setShowReleaseModal] = useState(false)
  const [releaseNotes, setReleaseNotes] = useState('')
  const [version, setVersion] = useState('1.0.0')
  const [riskLevel, setRiskLevel] = useState<'low' | 'medium' | 'high'>('medium')

  // 加载持久化的 checklist 状态
  useEffect(() => {
    if (!projectId) return
    listProjectReviews(projectId, 'release')
      .then((reviews) => {
        setChecklist((prev) =>
          prev.map((item) => {
            const review = reviews.find((r) => r.item_id === item.id)
            if (review) {
              return { ...item, checked: review.status === 'checked' }
            }
            return item
          })
        )
      })
      .catch((err) => console.error('加载发布清单状态失败:', err))
  }, [projectId])

  const toggleCheck = async (id: string) => {
    const item = checklist.find((c) => c.id === id)
    if (!item) return
    const newChecked = !item.checked
    setChecklist((prev) => prev.map((i) => (i.id === id ? { ...i, checked: newChecked } : i)))
    if (!projectId) return
    try {
      const reviews = await listProjectReviews(projectId, 'release')
      const existing = reviews.find((r) => r.item_id === id)
      if (existing) {
        await updateProjectReview(projectId, existing.review_id, { status: newChecked ? 'checked' : 'pending' })
      } else {
        await createProjectReview(projectId, {
          review_type: 'release',
          item_id: id,
          item_type: 'checklist',
          status: newChecked ? 'checked' : 'pending',
        })
      }
    } catch (err) {
      console.error('保存 checklist 状态失败:', err)
    }
  }

  const filteredChecklist = checklist.filter((item) => item.category === selectedCategory)

  const stats = {
    total: checklist.length,
    checked: checklist.filter((i) => i.checked).length,
    highRisk: checklist.filter((i) => i.risk === 'high' && !i.checked).length,
    mediumRisk: checklist.filter((i) => i.risk === 'medium' && !i.checked).length,
  }

  const allChecked = stats.checked === stats.total

  const riskScore = useMemo(() => {
    const high = checklist.filter((i) => i.risk === 'high' && !i.checked).length
    const medium = checklist.filter((i) => i.risk === 'medium' && !i.checked).length
    return high * 3 + medium * 1
  }, [checklist])

  const riskLabel = riskScore === 0 ? '低风险' : riskScore <= 3 ? '中风险' : '高风险'
  const riskColor = riskScore === 0 ? '#16a34a' : riskScore <= 3 ? '#f59e0b' : '#dc2626'

  if (!projectId) {
    return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280' }}>请先在顶部选择项目</div>
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#fff', borderRadius: 8, border: '1px solid #e5e7eb', overflow: 'hidden' }}>
      {/* 顶部 */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>发布管理</h2>
          <div style={{ display: 'flex', gap: 8 }}>
            {CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                style={{
                  padding: '4px 10px',
                  fontSize: 12,
                  borderRadius: 4,
                  border: '1px solid #e5e7eb',
                  background: selectedCategory === cat.id ? '#eff6ff' : '#fff',
                  color: selectedCategory === cat.id ? '#2563eb' : '#374151',
                  cursor: 'pointer',
                }}
              >
                {cat.icon} {cat.label}
              </button>
            ))}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ fontSize: 13, color: '#6b7280' }}>
            清单: <span style={{ color: '#16a34a' }}>{stats.checked}</span>/{stats.total} | 高风险: <span style={{ color: '#dc2626' }}>{stats.highRisk}</span>
          </div>
          <button
            onClick={() => setShowReleaseModal(true)}
            disabled={!allChecked}
            style={{
              padding: '6px 16px',
              fontSize: 13,
              background: allChecked ? '#2563eb' : '#e5e7eb',
              color: allChecked ? '#fff' : '#9ca3af',
              border: 'none',
              borderRadius: 4,
              cursor: allChecked ? 'pointer' : 'not-allowed',
              fontWeight: 600,
            }}
          >
            🚀 执行发布
          </button>
        </div>
      </div>

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* 左侧：发布清单 */}
        <div style={{ width: 400, minWidth: 400, borderRight: '1px solid #e5e7eb', overflowY: 'auto', background: '#fff' }}>
          <div style={{ padding: '10px 12px', borderBottom: '1px solid #e5e7eb', fontSize: 13, fontWeight: 600, color: '#374151' }}>
            {CATEGORIES.find((c) => c.id === selectedCategory)?.label} ({filteredChecklist.length} 项)
          </div>
          {filteredChecklist.map((item) => (
            <div
              key={item.id}
              style={{
                padding: '10px 14px',
                borderBottom: '1px solid #f3f4f6',
                display: 'flex',
                alignItems: 'flex-start',
                gap: 10,
                background: item.checked ? '#f0fdf4' : 'transparent',
              }}
            >
              <input
                type="checkbox"
                checked={item.checked}
                onChange={() => toggleCheck(item.id)}
                style={{ marginTop: 2, cursor: 'pointer' }}
              />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, color: item.checked ? '#6b7280' : '#111827', textDecoration: item.checked ? 'line-through' : 'none' }}>
                  {item.label}
                </div>
                <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>
                  责任人: {item.assignee} | 风险:
                  <span
                    style={{
                      color: item.risk === 'high' ? '#dc2626' : item.risk === 'medium' ? '#f59e0b' : '#6b7280',
                      marginLeft: 4,
                    }}
                  >
                    {item.risk === 'high' ? '高' : item.risk === 'medium' ? '中' : '低'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* 中间：发布说明 */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 24, borderRight: '1px solid #e5e7eb' }}>
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: '#374151' }}>发布版本</div>
            <input
              value={version}
              onChange={(e) => setVersion(e.target.value)}
              style={{ width: 200, padding: 8, border: '1px solid #e5e7eb', borderRadius: 4, fontSize: 13 }}
              placeholder="例如: 1.0.0"
            />
          </div>

          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: '#374151' }}>发布说明 (Release Notes)</div>
            <textarea
              value={releaseNotes}
              onChange={(e) => setReleaseNotes(e.target.value)}
              style={{ width: '100%', padding: 12, border: '1px solid #e5e7eb', borderRadius: 6, fontSize: 13, minHeight: 200, resize: 'vertical' }}
              placeholder={`## v${version} 发布说明

### 新功能
- 

### 修复
- 

### 优化
- 

### 破坏性变更
- 

### 回滚方案
- 产物级: git checkout v{prev_version}
- 数据库级: alembic downgrade -1
`}
            />
          </div>

          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: '#374151' }}>风险评估</div>
            <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
              {(['low', 'medium', 'high'] as const).map((level) => (
                <button
                  key={level}
                  onClick={() => setRiskLevel(level)}
                  style={{
                    padding: '6px 14px',
                    fontSize: 13,
                    borderRadius: 4,
                    border: '1px solid #e5e7eb',
                    background: riskLevel === level ? (level === 'low' ? '#d1fae5' : level === 'medium' ? '#fef3c7' : '#fef2f2') : '#fff',
                    color: riskLevel === level ? (level === 'low' ? '#065f46' : level === 'medium' ? '#92400e' : '#dc2626') : '#374151',
                    cursor: 'pointer',
                    fontWeight: riskLevel === level ? 600 : 400,
                  }}
                >
                  {level === 'low' ? '🟢 低风险' : level === 'medium' ? '🟡 中风险' : '🔴 高风险'}
                </button>
              ))}
            </div>
            <div style={{ padding: 12, background: '#f9fafb', borderRadius: 6, fontSize: 13, color: '#374151', lineHeight: 1.6 }}>
              <div><strong>当前风险评分:</strong> <span style={{ color: riskColor, fontWeight: 700 }}>{riskScore}</span> ({riskLabel})</div>
              <div style={{ marginTop: 4 }}><strong>未检查高风险项:</strong> {stats.highRisk} 个</div>
              <div style={{ marginTop: 4 }}><strong>未检查中风险项:</strong> {stats.mediumRisk} 个</div>
            </div>
          </div>

          <div>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: '#374151' }}>三级回滚策略</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {ROLLBACK_STEPS.map((step) => (
                <div key={step.id} style={{ padding: 12, background: '#f9fafb', borderRadius: 6, border: '1px solid #e5e7eb' }}>
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 4 }}>
                    层级 {step.level}: {step.description}
                  </div>
                  <code style={{ fontSize: 12, padding: '6px 10px', background: '#1f2937', color: '#e5e7eb', borderRadius: 4, display: 'block', fontFamily: 'monospace' }}>
                    {step.command}
                  </code>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 右侧：发布概览 */}
        <div style={{ width: 300, minWidth: 300, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ padding: 16, borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12, color: '#374151' }}>发布概览</div>
            <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
              <div style={{ flex: 1, textAlign: 'center', padding: 10, background: '#d1fae5', borderRadius: 6 }}>
                <div style={{ fontSize: 20, fontWeight: 700, color: '#065f46' }}>{stats.checked}</div>
                <div style={{ fontSize: 11, color: '#065f46' }}>已完成</div>
              </div>
              <div style={{ flex: 1, textAlign: 'center', padding: 10, background: '#fef3c7', borderRadius: 6 }}>
                <div style={{ fontSize: 20, fontWeight: 700, color: '#92400e' }}>{stats.total - stats.checked}</div>
                <div style={{ fontSize: 11, color: '#92400e' }}>待完成</div>
              </div>
            </div>
            <div style={{ marginBottom: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                <span>清单完成度</span>
                <span style={{ color: '#6b7280' }}>{Math.round((stats.checked / stats.total) * 100)}%</span>
              </div>
              <div style={{ height: 8, background: '#f3f4f6', borderRadius: 4, overflow: 'hidden' }}>
                <div style={{ width: `${(stats.checked / stats.total) * 100}%`, height: '100%', background: allChecked ? '#16a34a' : '#2563eb', borderRadius: 4, transition: 'width 0.3s' }} />
              </div>
            </div>
            <div style={{ fontSize: 12, color: '#6b7280' }}>
              版本: <strong>{version}</strong>
            </div>
            <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>
              风险: <strong style={{ color: riskColor }}>{riskLabel}</strong>
            </div>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 12, color: '#374151' }}>发布检查清单</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {CATEGORIES.map((cat) => {
                const catItems = checklist.filter((i) => i.category === cat.id)
                const catChecked = catItems.filter((i) => i.checked).length
                const allDone = catChecked === catItems.length
                return (
                  <label key={cat.id} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, cursor: 'pointer' }}>
                    <input type="checkbox" checked={allDone} readOnly />
                    <span style={{ color: allDone ? '#16a34a' : '#374151' }}>
                      {cat.icon} {cat.label} ({catChecked}/{catItems.length})
                    </span>
                  </label>
                )
              })}
            </div>

            {allChecked && (
              <div style={{ marginTop: 16, padding: 12, background: '#d1fae5', borderRadius: 6, fontSize: 13, color: '#065f46' }}>
                ✅ 所有清单项已完成，可以执行发布
              </div>
            )}

            {stats.highRisk > 0 && (
              <div style={{ marginTop: 16, padding: 12, background: '#fef2f2', borderRadius: 6, fontSize: 13, color: '#dc2626' }}>
                ⚠️ 还有 {stats.highRisk} 个高风险项未完成
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 发布确认弹窗 */}
      {showReleaseModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50 }}>
          <div style={{ background: '#fff', borderRadius: 8, padding: 24, width: 520, maxWidth: '90vw' }}>
            <h3 style={{ margin: '0 0 16px', fontSize: 18 }}>🚀 确认执行发布</h3>
            <div style={{ marginBottom: 16, fontSize: 13, color: '#374151', lineHeight: 1.6 }}>
              <p><strong>发布版本:</strong> {version}</p>
              <p><strong>风险等级:</strong> <span style={{ color: riskColor }}>{riskLabel}</span></p>
              <p><strong>回滚策略:</strong> 三级回滚已就绪</p>
              <div style={{ marginTop: 8, padding: 12, background: '#f9fafb', borderRadius: 6 }}>
                <div style={{ fontWeight: 600, marginBottom: 4 }}>发布清单已全部完成</div>
                <div style={{ fontSize: 12, color: '#6b7280' }}>
                  共 {stats.total} 项，已完成 {stats.checked} 项
                </div>
              </div>
              <p style={{ color: '#dc2626', marginTop: 8 }}>发布后将触发线上监控，请确保监控规则已配置。</p>
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button onClick={() => setShowReleaseModal(false)} style={{ padding: '8px 16px', fontSize: 13, border: '1px solid #e5e7eb', background: '#fff', borderRadius: 4, cursor: 'pointer' }}>取消</button>
              <button onClick={() => { setShowReleaseModal(false); alert(`版本 ${version} 发布成功！`) }} style={{ padding: '8px 16px', fontSize: 13, background: '#2563eb', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}>确认发布</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
