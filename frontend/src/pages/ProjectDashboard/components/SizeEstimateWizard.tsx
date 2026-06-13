import { useState } from 'react'
import { calculateComplexity, createSizeEstimate, bindSizeEstimate } from '../../../services/project'
import type { ComplexityAssessResult } from '../../../services/project'

interface SizeEstimateWizardProps {
  projectId: string
  onClose: () => void
  onApplied?: () => void
}

interface SliderConfig {
  key: string
  label: string
  min: number
  max: number
  step: number
  value: number
}

export default function SizeEstimateWizard({ projectId, onClose, onApplied }: SizeEstimateWizardProps) {
  const [sliders, setSliders] = useState<SliderConfig[]>([
    { key: 'module_count', label: '功能模块数', min: 1, max: 50, step: 1, value: 5 },
    { key: 'interface_complexity', label: '接口复杂度', min: 1, max: 10, step: 1, value: 3 },
    { key: 'page_count', label: '页面数', min: 1, max: 100, step: 1, value: 10 },
    { key: 'entity_count', label: '数据实体数', min: 1, max: 50, step: 1, value: 5 },
    { key: 'integration_count', label: '集成系统数', min: 1, max: 20, step: 1, value: 2 },
  ])
  const [score, setScore] = useState<ComplexityAssessResult | null>(null)
  const [calculating, setCalculating] = useState(false)
  const [applying, setApplying] = useState(false)

  const updateSlider = (key: string, value: number) => {
    setSliders((prev) => prev.map((s) => (s.key === key ? { ...s, value } : s)))
    setScore(null)
  }

  const handleCalculate = async () => {
    setCalculating(true)
    try {
      const payload = {
        module_count: sliders.find((s) => s.key === 'module_count')?.value ?? 5,
        interface_complexity: sliders.find((s) => s.key === 'interface_complexity')?.value ?? 3,
        page_count: sliders.find((s) => s.key === 'page_count')?.value ?? 10,
        entity_count: sliders.find((s) => s.key === 'entity_count')?.value ?? 5,
        integration_count: sliders.find((s) => s.key === 'integration_count')?.value ?? 2,
      }
      const result = await calculateComplexity(payload)
      setScore(result)
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : '计算失败')
    } finally {
      setCalculating(false)
    }
  }

  const handleApply = async () => {
    if (!score) return
    setApplying(true)
    try {
      // Map 5 dimensions to existing backend fields
      const moduleCount = sliders.find((s) => s.key === 'module_count')?.value ?? 5
      const interfaceComplexity = sliders.find((s) => s.key === 'interface_complexity')?.value ?? 3
      const pageCount = sliders.find((s) => s.key === 'page_count')?.value ?? 10
      const entityCount = sliders.find((s) => s.key === 'entity_count')?.value ?? 5
      const integrationCount = sliders.find((s) => s.key === 'integration_count')?.value ?? 2

      const techComplexity = interfaceComplexity >= 8 ? 'High' : interfaceComplexity >= 4 ? 'Medium' : 'Low'
      const riskLevel = integrationCount >= 13 ? 'High' : integrationCount >= 6 ? 'Medium' : 'Low'

      const estimate = await createSizeEstimate(projectId, {
        module_count: moduleCount,
        interface_count: pageCount,
        page_count: entityCount,
        tech_complexity: techComplexity,
        risk_level: riskLevel,
      })

      await bindSizeEstimate(projectId, estimate.estimate_id)
      onApplied?.()
      onClose()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : '应用失败')
    } finally {
      setApplying(false)
    }
  }

  const levelBadge: Record<string, { bg: string; color: string; label: string }> = {
    Trivial: { bg: '#f3f4f6', color: '#6b7280', label: 'S — 轻量' },
    Light: { bg: '#eff6ff', color: '#3b82f6', label: 'M — 轻量' },
    Standard: { bg: '#fff7ed', color: '#f97316', label: 'L — 标准' },
    Deep: { bg: '#fef2f2', color: '#ef4444', label: 'XL — 深度' },
  }

  const currentBadge = score ? levelBadge[score.complexity_level] || levelBadge.Standard : null

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.4)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1200,
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
          width: 520,
          maxHeight: '85vh',
          overflow: 'auto',
          padding: 24,
        }}
      >
        <h2 style={{ margin: '0 0 20px 0', fontSize: 18 }}>规模评估向导</h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {sliders.map((slider) => (
            <div key={slider.key}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 14 }}>
                <span>{slider.label}</span>
                <span style={{ fontWeight: 600, color: '#3b82f6' }}>{slider.value}</span>
              </div>
              <input
                type="range"
                min={slider.min}
                max={slider.max}
                step={slider.step}
                value={slider.value}
                onChange={(e) => updateSlider(slider.key, Number(e.target.value))}
                style={{
                  width: '100%',
                  accentColor: '#3b82f6',
                }}
              />
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: 11,
                  color: '#9ca3af',
                  marginTop: 2,
                }}
              >
                <span>{slider.min}</span>
                <span>{slider.max}</span>
              </div>
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', marginTop: 20 }}>
          <button
            onClick={handleCalculate}
            disabled={calculating}
            style={{
              padding: '8px 24px',
              borderRadius: 6,
              border: 'none',
              background: '#3b82f6',
              color: '#fff',
              cursor: calculating ? 'not-allowed' : 'pointer',
              fontSize: 14,
              opacity: calculating ? 0.7 : 1,
            }}
          >
            {calculating ? '计算中...' : '实时计算'}
          </button>
        </div>

        {score && currentBadge && (
          <div
            style={{
              marginTop: 20,
              padding: 16,
              background: '#f9fafb',
              borderRadius: 8,
              textAlign: 'center',
            }}
          >
            <div
              style={{
                display: 'inline-block',
                padding: '4px 16px',
                borderRadius: 999,
                fontSize: 16,
                fontWeight: 700,
                backgroundColor: currentBadge.bg,
                color: currentBadge.color,
                border: `1px solid ${currentBadge.color}`,
                marginBottom: 16,
              }}
            >
              {currentBadge.label}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
              <ScoreBlock label="乐观" value={score.optimistic_score} color="#10b981" />
              <ScoreBlock label="预期" value={score.expected_score} color="#3b82f6" />
              <ScoreBlock label="保守" value={score.conservative_score} color="#f59e0b" />
            </div>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 24 }}>
          <button
            onClick={onClose}
            style={{
              padding: '8px 16px',
              borderRadius: 6,
              border: '1px solid #e5e7eb',
              background: '#fff',
              cursor: 'pointer',
              fontSize: 14,
            }}
          >
            取消
          </button>
          <button
            onClick={handleApply}
            disabled={!score || applying}
            style={{
              padding: '8px 16px',
              borderRadius: 6,
              border: 'none',
              background: score && !applying ? '#3b82f6' : '#d1d5db',
              color: '#fff',
              cursor: score && !applying ? 'pointer' : 'not-allowed',
              fontSize: 14,
            }}
          >
            {applying ? '应用中...' : '应用此结果'}
          </button>
        </div>
      </div>
    </div>
  )
}

function ScoreBlock({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div
      style={{
        background: '#fff',
        borderRadius: 6,
        padding: 12,
        border: '1px solid #e5e7eb',
      }}
    >
      <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 700, color }}>{value}</div>
    </div>
  )
}
