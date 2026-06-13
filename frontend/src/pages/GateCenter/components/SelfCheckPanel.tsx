import type { GateDecision } from '@/services/gate'
import type { SelfCheckData } from '@/services/selfCheck'

interface SelfCheckPanelProps {
  gate: GateDecision
  data: SelfCheckData | null
  loading?: boolean
}

export default function SelfCheckPanel({ gate, data, loading }: SelfCheckPanelProps) {
  const statusColor = (value: string) => {
    if (value === '通过' || value === '高') return 'text-green-600'
    if (value === '缺失' || value === '未通过' || value === '高' || value === '已超时，需补审') return 'text-red-600'
    if (value === '中') return 'text-yellow-600'
    return 'text-gray-600'
  }

  return (
    <div className="rounded-lg border border-gray-200 p-4 bg-white">
      <h3 className="text-lg font-semibold mb-3">自检摘要</h3>
      {loading && (
        <div className="text-sm text-gray-500">加载自检数据中...</div>
      )}
      {!loading && !data && (
        <div className="text-sm text-gray-500">暂无自检数据</div>
      )}
      {!loading && data && (
        <div className="space-y-2 text-sm text-gray-700">
          <div className="flex justify-between">
            <span>置信度</span>
            <span className="font-medium">{gate.confidence ?? '未评估'}</span>
          </div>
          <div className="flex justify-between">
            <span>产物完整性</span>
            <span className={`font-medium ${statusColor(data.artifact_integrity)}`}>
              {data.artifact_integrity}
            </span>
          </div>
          <div className="flex justify-between">
            <span>质量门禁</span>
            <span className={`font-medium ${statusColor(data.quality_gate)}`}>
              {data.quality_gate}
            </span>
          </div>
          <div className="flex justify-between">
            <span>风险点</span>
            <span className={`font-medium ${statusColor(data.risk_level)}`}>
              {data.risk_level}
            </span>
          </div>
          <div className="pt-1 text-xs text-gray-400">
            已检产物 {data.artifact_count} / 需 {data.required_artifacts}
          </div>
        </div>
      )}
    </div>
  )
}
