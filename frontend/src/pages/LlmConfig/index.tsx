import { useState } from 'react'
import { Settings, Shield, Cpu } from 'lucide-react'
import ProviderNodePanel from './components/ProviderNodePanel'
import PermissionPolicyPanel from './components/PermissionPolicyPanel'

type TabKey = 'provider' | 'permission'

export default function LlmConfig() {
  const [activeTab, setActiveTab] = useState<TabKey>('provider')
  const projectId = 'demo-project-001'

  const tabs: { key: TabKey; label: string; icon: React.ReactNode }[] = [
    { key: 'provider', label: 'Provider 节点', icon: <Cpu size={16} /> },
    { key: 'permission', label: '权限策略', icon: <Shield size={16} /> },
  ]

  return (
    <div className="h-full flex flex-col">
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <Settings size={20} className="text-gray-700" />
          <h1 className="text-xl font-bold text-gray-900">LLM 配置中心</h1>
        </div>
        <p className="text-sm text-gray-500">
          统一管理 LLM Provider 节点与 AI 工具访问权限策略。配置节点支持全局 / 项目 / 用户多层作用域，后续其他配置项也会统一在此扩展。
        </p>
      </div>

      <div className="border-b border-gray-200 mb-6">
        <nav className="flex gap-6">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 pb-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? 'border-gray-900 text-gray-900'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="flex-1 overflow-y-auto">
        {activeTab === 'provider' && <ProviderNodePanel projectId={projectId} />}
        {activeTab === 'permission' && <PermissionPolicyPanel projectId={projectId} />}
      </div>
    </div>
  )
}
