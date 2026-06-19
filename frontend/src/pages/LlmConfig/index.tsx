import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Cpu, Shield, Settings } from 'lucide-react'
import { llmPolicyApi, llmProviderApi } from '../../services/llm'
import DetailPanel from './components/DetailPanel'
import MasterList from './components/MasterList'
import ResizableSplit from './components/ResizableSplit'
import { useLlmEntities } from './hooks/useLlmEntities'
import { useUnsavedGuard } from './hooks/useUnsavedGuard'
import { buildEmptyPolicy, buildEmptyProvider, type ConfigEntity, type TabKey } from './types'

const TABS: { key: TabKey; label: string; icon: React.ReactNode }[] = [
  { key: 'provider', label: 'Provider 节点', icon: <Cpu size={16} /> },
  { key: 'permission', label: '权限策略', icon: <Shield size={16} /> },
]

type PendingNavigation =
  | { type: 'tab'; target: TabKey }
  | { type: 'select'; target: string }

export default function LlmConfig() {
  const [activeTab, setActiveTab] = useState<TabKey>('provider')
  const { entities, loading, error, refresh, removeEntity } = useLlmEntities({ tab: activeTab })

  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [isNew, setIsNew] = useState(false)
  const [unsavedNodeId, setUnsavedNodeId] = useState<string | null>(null)
  const [mobileDetailOpen, setMobileDetailOpen] = useState(false)
  const [pendingNav, setPendingNav] = useState<PendingNavigation | null>(null)
  const hasAutoSelectedRef = useRef(false)

  const selectedNode = useMemo(
    () => (entities.find((n) => n.id === selectedId) as ConfigEntity | undefined) || null,
    [entities, selectedId]
  )

  // 首次加载默认选中第一项
  useEffect(() => {
    if (!loading && entities.length > 0 && !selectedId && !hasAutoSelectedRef.current) {
      hasAutoSelectedRef.current = true
      setSelectedId(entities[0].id)
    }
  }, [loading, entities, selectedId])

  // Tab 切换时重置选中
  const prevTabRef = useRef<TabKey>(activeTab)
  useEffect(() => {
    if (prevTabRef.current === activeTab) return
    prevTabRef.current = activeTab
    setSelectedId(entities[0]?.id || null)
    setIsNew(false)
    setUnsavedNodeId(null)
    setPendingNav(null)
    hasAutoSelectedRef.current = false
  }, [activeTab, entities])

  useUnsavedGuard(!!unsavedNodeId)

  // 保存成功后执行之前被拦截的导航
  useEffect(() => {
    if (!unsavedNodeId && pendingNav) {
      if (pendingNav.type === 'tab') {
        setActiveTab(pendingNav.target)
      } else {
        setSelectedId(pendingNav.target)
        setMobileDetailOpen(true)
      }
      setPendingNav(null)
    }
  }, [unsavedNodeId, pendingNav])

  const executeNavigation = useCallback((nav: PendingNavigation) => {
    if (nav.type === 'tab') {
      setActiveTab(nav.target)
    } else {
      setSelectedId(nav.target)
      setIsNew(false)
      setMobileDetailOpen(true)
    }
    setPendingNav(null)
  }, [])

  const handleSelect = useCallback(
    (id: string) => {
      if (unsavedNodeId && unsavedNodeId !== id) {
        setPendingNav({ type: 'select', target: id })
        return
      }
      setSelectedId(id)
      setIsNew(false)
      setMobileDetailOpen(true)
    },
    [unsavedNodeId]
  )

  const handleTabChange = useCallback(
    (tab: TabKey) => {
      if (unsavedNodeId) {
        setPendingNav({ type: 'tab', target: tab })
        return
      }
      setActiveTab(tab)
    },
    [unsavedNodeId]
  )

  const handleAdd = useCallback(() => {
    if (unsavedNodeId) {
      setPendingNav({ type: 'tab', target: activeTab })
      return
    }

    const createEmpty = async () => {
      try {
        const created =
          activeTab === 'provider'
            ? await llmProviderApi.create(buildEmptyProvider())
            : await llmPolicyApi.create(buildEmptyPolicy())
        await refresh()
        setSelectedId(created.id)
        setIsNew(true)
        setUnsavedNodeId(created.id)
        setMobileDetailOpen(true)
      } catch (err) {
        alert(err instanceof Error ? err.message : '创建失败')
      }
    }

    void createEmpty()
  }, [activeTab, refresh, unsavedNodeId])

  const handleSaved = useCallback(() => {
    setIsNew(false)
    setUnsavedNodeId(null)
    void refresh()
  }, [refresh])

  const handleCancel = useCallback(() => {
    setIsNew(false)
    setUnsavedNodeId(null)
    if (isNew && selectedId) {
      const apiCall = activeTab === 'provider' ? llmProviderApi.remove(selectedId) : llmPolicyApi.remove(selectedId)
      apiCall
        .then(() => {
          removeEntity(selectedId)
          setSelectedId(entities[0]?.id || null)
        })
        .catch(() => {
          // ignore
        })
    }
  }, [activeTab, entities, isNew, removeEntity, selectedId])

  const handleDeleted = useCallback(() => {
    setIsNew(false)
    setUnsavedNodeId(null)
    setSelectedId(entities[0]?.id || null)
    void refresh()
  }, [entities, refresh])

  const handleMarkUnsaved = useCallback(() => {
    if (selectedId) {
      setUnsavedNodeId(selectedId)
    }
  }, [selectedId])

  const handleSetDefault = useCallback(
    async (id: string) => {
      try {
        await llmProviderApi.setDefault(id)
        await refresh()
      } catch (err) {
        alert(err instanceof Error ? err.message : '设置默认失败')
      }
    },
    [refresh]
  )

  const handleSaveAndLeave = useCallback(() => {
    const form = document.getElementById('llm-config-form') as HTMLFormElement | null
    form?.requestSubmit()
  }, [])

  const handleDiscardAndLeave = useCallback(() => {
    handleCancel()
    if (pendingNav) {
      executeNavigation(pendingNav)
    }
  }, [handleCancel, pendingNav, executeNavigation])

  const handleCancelNavigation = useCallback(() => {
    setPendingNav(null)
  }, [])

  const dirtyNodeName = useMemo(() => {
    if (!unsavedNodeId) return ''
    return entities.find((n) => n.id === unsavedNodeId)?.name || ''
  }, [entities, unsavedNodeId])

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="px-6 pt-6 pb-4 shrink-0">
        <div className="flex items-center gap-2 mb-2">
          <Settings size={20} className="text-gray-700" />
          <h1 className="text-xl font-bold text-gray-900">LLM 配置中心</h1>
        </div>
        <p className="text-sm text-gray-500">
          统一管理 LLM Provider 节点与 AI 工具访问权限策略。配置节点支持全局 / 项目 / 用户多层作用域。
        </p>
      </div>

      <div className="px-6 shrink-0">
        <div className="border-b border-gray-200">
          <nav className="flex gap-6">
            {TABS.map((tab) => (
              <button
                key={tab.key}
                onClick={() => handleTabChange(tab.key)}
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
      </div>

      <div className="flex-1 min-h-0 mt-4 relative">
        {error && (
          <div className="absolute top-0 left-0 right-0 z-10 bg-red-50 text-red-700 px-6 py-2 text-sm">
            {error}
          </div>
        )}

        {/* 桌面端 Master-Detail */}
        <div className="hidden md:block h-full">
          <ResizableSplit
            left={
              <MasterList
                tab={activeTab}
                entities={entities}
                selectedId={selectedId}
                draftNodeId={unsavedNodeId}
                loading={loading}
                onSelect={handleSelect}
                onAdd={handleAdd}
                onSetDefault={activeTab === 'provider' ? handleSetDefault : undefined}
              />
            }
            right={
              <DetailPanel
                tab={activeTab}
                node={selectedNode}
                isNew={isNew}
                onSaved={handleSaved}
                onCancel={handleCancel}
                onDeleted={handleDeleted}
                onMarkUnsaved={handleMarkUnsaved}
              />
            }
          />
        </div>

        {/* 移动端串行流程 */}
        <div className="md:hidden h-full">
          {!mobileDetailOpen ? (
            <MasterList
              tab={activeTab}
              entities={entities}
              selectedId={selectedId}
              draftNodeId={unsavedNodeId}
              loading={loading}
              onSelect={(id) => {
                handleSelect(id)
                setMobileDetailOpen(true)
              }}
              onAdd={handleAdd}
              onSetDefault={activeTab === 'provider' ? handleSetDefault : undefined}
            />
          ) : (
            <div className="h-full flex flex-col bg-white">
              <div className="p-3 border-b border-gray-200">
                <button
                  type="button"
                  onClick={() => setMobileDetailOpen(false)}
                  className="text-sm text-blue-600"
                >
                  ← 返回列表
                </button>
              </div>
              <div className="flex-1 min-h-0 overflow-hidden">
                <DetailPanel
                  tab={activeTab}
                  node={selectedNode}
                  isNew={isNew}
                  onSaved={() => {
                    handleSaved()
                    setMobileDetailOpen(false)
                  }}
                  onCancel={() => {
                    handleCancel()
                    setMobileDetailOpen(false)
                  }}
                  onDeleted={() => {
                    handleDeleted()
                    setMobileDetailOpen(false)
                  }}
                  onMarkUnsaved={handleMarkUnsaved}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {pendingNav && (
        <DirtyCheckModal
          name={dirtyNodeName}
          onSave={handleSaveAndLeave}
          onDiscard={handleDiscardAndLeave}
          onCancel={handleCancelNavigation}
        />
      )}
    </div>
  )
}

function DirtyCheckModal({
  name,
  onSave,
  onDiscard,
  onCancel,
}: {
  name: string
  onSave: () => void
  onDiscard: () => void
  onCancel: () => void
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6" role="dialog" aria-modal="true" aria-labelledby="dirty-check-title">
        <h3 id="dirty-check-title" className="text-base font-semibold text-gray-900 mb-2">未保存的更改</h3>
        <p className="text-sm text-gray-600 mb-6">
          「{name || '当前项'}」有未保存的修改，是否保存后再离开？
        </p>
        <div className="flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            取消
          </button>
          <button
            type="button"
            onClick={onDiscard}
            className="px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg"
          >
            放弃并切换
          </button>
          <button
            type="button"
            onClick={onSave}
            className="px-4 py-2 text-sm bg-gray-900 text-white rounded-lg hover:bg-gray-800"
          >
            保存并切换
          </button>
        </div>
      </div>
    </div>
  )
}
