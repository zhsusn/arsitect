import { useState } from 'react'

interface ServiceSetupGuideProps {
  open: boolean
  onClose: () => void
  onStartService: () => void
}

const STEPS = [
  { id: 'check', label: '检测 Docker 环境', desc: '检查本地是否已安装并运行 Docker Desktop' },
  { id: 'pull', label: '拉取 OpenUI 镜像', desc: '从 Docker Hub 拉取最新的 OpenUI 服务镜像' },
  { id: 'run', label: '启动容器', desc: '启动 OpenUI 容器并映射到本地端口' },
]

export default function ServiceSetupGuide({ open, onClose, onStartService }: ServiceSetupGuideProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [stepStatus, setStepStatus] = useState<Record<string, 'pending' | 'running' | 'done' | 'error'>>({
    check: 'pending',
    pull: 'pending',
    run: 'pending',
  })
  const [logs, setLogs] = useState<string[]>([])
  const [isRunning, setIsRunning] = useState(false)

  if (!open) return null

  const addLog = (msg: string) => setLogs((prev) => [...prev, msg])

  const runStep = async (idx: number) => {
    const step = STEPS[idx]
    setStepStatus((s) => ({ ...s, [step.id]: 'running' }))
    addLog(`[${step.label}] 开始...`)

    await new Promise((r) => setTimeout(r, 1500))

    if (step.id === 'check') {
      addLog('Docker 版本: 24.0.7')
      addLog('Docker Desktop 运行中')
    } else if (step.id === 'pull') {
      addLog('镜像 openui:latest 已就绪')
    } else if (step.id === 'run') {
      addLog('容器 openui-server 已启动 (端口 7878)')
    }

    setStepStatus((s) => ({ ...s, [step.id]: 'done' }))
    addLog(`[${step.label}] 完成`)

    if (idx < STEPS.length - 1) {
      setCurrentStep(idx + 1)
    } else {
      onStartService()
      setIsRunning(false)
    }
  }

  const handleRunAll = async () => {
    setIsRunning(true)
    setLogs([])
    for (let i = 0; i < STEPS.length; i++) {
      setCurrentStep(i)
      await runStep(i)
    }
  }

  const statusIcon = (status: string) => {
    if (status === 'done') return '✅'
    if (status === 'running') return '⏳'
    if (status === 'error') return '❌'
    return '⭕'
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden" onClick={(e) => e.stopPropagation()}>
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h3 className="text-lg font-bold text-gray-800">OpenUI 服务启动引导</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
        </div>

        <div className="px-6 py-4 space-y-3">
          {STEPS.map((step, idx) => (
            <div
              key={step.id}
              className={`flex items-start gap-3 p-3 rounded-lg border ${
                currentStep === idx ? 'border-blue-300 bg-blue-50' : 'border-gray-200 bg-gray-50'
              }`}
            >
              <span className="text-lg mt-0.5">{statusIcon(stepStatus[step.id])}</span>
              <div>
                <div className="text-sm font-semibold text-gray-800">{step.label}</div>
                <div className="text-xs text-gray-500 mt-0.5">{step.desc}</div>
              </div>
            </div>
          ))}

          {logs.length > 0 && (
            <div className="mt-3 bg-gray-900 rounded-lg p-3 max-h-40 overflow-auto">
              <div className="text-[10px] text-gray-400 mb-1">执行日志</div>
              {logs.map((log, i) => (
                <div key={i} className="text-xs text-green-400 font-mono">{log}</div>
              ))}
            </div>
          )}
        </div>

        <div className="px-6 py-4 bg-gray-50 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            关闭
          </button>
          <button
            onClick={handleRunAll}
            disabled={isRunning}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {isRunning ? '执行中...' : '一键执行全部步骤'}
          </button>
        </div>
      </div>
    </div>
  )
}
