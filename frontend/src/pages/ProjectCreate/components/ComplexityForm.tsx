import React, { useMemo, useState } from 'react'
import { useComplexityStore } from '../../../stores/complexityStore'
import { ScoreRadarChart } from '../../../components/ScoreRadarChart'

interface ComplexityFormProps {
  projectId: string
  onComplete?: () => void
}

const ComplexityForm: React.FC<ComplexityFormProps> = ({ projectId, onComplete }) => {
  const [moduleCount, setModuleCount] = useState(5)
  const [interfaceCount, setInterfaceCount] = useState(5)
  const [pageCount, setPageCount] = useState(3)
  const [techComplexity, setTechComplexity] = useState('Medium')
  const [riskLevel, setRiskLevel] = useState('Medium')

  const { createEstimate, estimate, loading, error } = useComplexityStore()

  const radarScores = useMemo(
    () => ({
      module_count: moduleCount,
      interface_count: interfaceCount,
      page_count: pageCount,
      tech_complexity: techComplexity === 'Low' ? 1 : techComplexity === 'Medium' ? 2 : 3,
      risk_level: riskLevel === 'Low' ? 1 : riskLevel === 'Medium' ? 2 : 3,
    }),
    [moduleCount, interfaceCount, pageCount, techComplexity, riskLevel],
  )

  const handleSubmit = async () => {
    await createEstimate(projectId, {
      module_count: moduleCount,
      interface_count: interfaceCount,
      page_count: pageCount,
      tech_complexity: techComplexity,
      risk_level: riskLevel,
    })
    onComplete?.()
  }

  return (
    <div style={{ display: 'flex', gap: 32, flexWrap: 'wrap' }}>
      <div style={{ flex: 1, minWidth: 280 }}>
        <h3 style={{ marginBottom: 16 }}>五维度评估</h3>
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 4, fontSize: 14, color: '#374151' }}>
            模块数 ({moduleCount})
          </label>
          <input
            type="range"
            min={1}
            max={50}
            value={moduleCount}
            onChange={(e) => setModuleCount(Number(e.target.value))}
            style={{ width: '100%' }}
          />
        </div>
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 4, fontSize: 14, color: '#374151' }}>
            接口数 ({interfaceCount})
          </label>
          <input
            type="range"
            min={0}
            max={100}
            value={interfaceCount}
            onChange={(e) => setInterfaceCount(Number(e.target.value))}
            style={{ width: '100%' }}
          />
        </div>
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 4, fontSize: 14, color: '#374151' }}>
            页面数 ({pageCount})
          </label>
          <input
            type="range"
            min={0}
            max={50}
            value={pageCount}
            onChange={(e) => setPageCount(Number(e.target.value))}
            style={{ width: '100%' }}
          />
        </div>
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 4, fontSize: 14, color: '#374151' }}>
            技术复杂度
          </label>
          <select
            value={techComplexity}
            onChange={(e) => setTechComplexity(e.target.value)}
            style={{ width: '100%', padding: '6px 8px', borderRadius: 4, border: '1px solid #d1d5db' }}
          >
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
          </select>
        </div>
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 4, fontSize: 14, color: '#374151' }}>
            风险等级
          </label>
          <select
            value={riskLevel}
            onChange={(e) => setRiskLevel(e.target.value)}
            style={{ width: '100%', padding: '6px 8px', borderRadius: 4, border: '1px solid #d1d5db' }}
          >
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
          </select>
        </div>
        <button
          onClick={handleSubmit}
          disabled={loading}
          style={{
            padding: '8px 16px',
            background: '#2563eb',
            color: '#fff',
            border: 'none',
            borderRadius: 4,
            cursor: 'pointer',
            opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? '计算中...' : '保存评估'}
        </button>
        {error && <p style={{ color: '#ef4444', marginTop: 8, fontSize: 14 }}>{error}</p>}
      </div>

      <div style={{ minWidth: 260 }}>
        <h3 style={{ marginBottom: 16 }}>雷达图</h3>
        <ScoreRadarChart scores={radarScores} level={estimate?.complexity_level || 'Standard'} />
        {estimate && (
          <div style={{ marginTop: 16, fontSize: 14 }}>
            <p>
              <strong>乐观:</strong> {estimate.optimistic_score}
            </p>
            <p>
              <strong>预期:</strong> {estimate.expected_score}
            </p>
            <p>
              <strong>保守:</strong> {estimate.conservative_score}
            </p>
            <p>
              <strong>等级:</strong>{' '}
              <span
                style={{
                  color:
                    estimate.complexity_level === 'Trivial'
                      ? '#9ca3af'
                      : estimate.complexity_level === 'Light'
                        ? '#3b82f6'
                        : estimate.complexity_level === 'Standard'
                          ? '#f97316'
                          : '#ef4444',
                  fontWeight: 600,
                }}
              >
                {estimate.complexity_level}
              </span>
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default ComplexityForm
